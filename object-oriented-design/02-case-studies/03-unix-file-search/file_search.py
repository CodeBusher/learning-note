"""A small, extensible re-implementation of the ideas behind Unix `find`.

The design has four layers that never reach into each other's internals:

1. Nodes (Composite pattern): File, Directory and Symlink share one Node
   interface. DiskNode adapts a real path to the same interface.
2. Attributes and operators: FileAttribute knows how to read one property of a
   node; Operator knows how to compare two values.
3. Predicates (Specification pattern): AttributePredicate is a leaf test; And,
   Or and Not combine tests into a tree. `&`, `|` and `~` build that tree.
4. FileSearch: walks the tree lazily (an iterative DFS generator) and yields
   every node the predicate accepts. It knows nothing about *what* is tested.

`parse_find_expression` turns `find`-style arguments into a predicate tree with
a recursive-descent parser, the same job GNU find's parser does.
"""

from __future__ import annotations

import fnmatch
import re
import stat
from abc import ABC, abstractmethod
from collections.abc import Callable, Hashable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, ClassVar

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
MAX_SYMLINK_HOPS = 40  # Linux gives up with ELOOP after 40 hops too.


# --------------------------------------------------------------------------
# 1. Nodes: the Composite
# --------------------------------------------------------------------------


class FileType(Enum):
    """What kind of directory entry a node is (the letters match `find -type`)."""

    FILE = "f"
    DIRECTORY = "d"
    SYMLINK = "l"


class Node(ABC):
    """Anything that can appear in a directory listing.

    Leaves (files, symlinks) return no children; directories return their
    entries. The search code only ever talks to this interface.
    """

    name: str
    owner: str
    size: int
    modified: datetime

    @property
    @abstractmethod
    def file_type(self) -> FileType: ...

    @property
    @abstractmethod
    def path(self) -> str: ...

    @abstractmethod
    def children(self) -> Sequence[Node]:
        """Entries of a directory, sorted by name; empty for everything else."""

    @abstractmethod
    def identity(self) -> Hashable:
        """A key that is equal for two handles to the same underlying object.

        On a real disk this is (device, inode); in memory it is id(). Cycle
        detection compares identities, never names or paths.
        """

    def resolve(self) -> Node | None:
        """Follow symlinks to the final target; None if the link is dangling."""
        return self

    @property
    def is_dir(self) -> bool:
        return self.file_type is FileType.DIRECTORY

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.path!r})"


class MemoryNode(Node):
    """Shared state for the in-memory file system used by demos and tests."""

    def __init__(
        self,
        name: str,
        *,
        owner: str = "root",
        size: int = 0,
        modified: datetime = EPOCH,
    ) -> None:
        if not name or "/" in name or name in (".", ".."):
            raise ValueError(f"invalid file name: {name!r}")
        if size < 0:
            raise ValueError("size cannot be negative")
        self.name = name
        self.owner = owner
        self.size = size
        self.modified = modified
        self.parent: Directory | None = None

    @property
    def path(self) -> str:
        parts: list[str] = []
        node: MemoryNode | None = self
        while node is not None and node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))

    def children(self) -> Sequence[Node]:
        return ()

    def identity(self) -> Hashable:
        return id(self)


class File(MemoryNode):
    """A regular file: a leaf in the tree."""

    @property
    def file_type(self) -> FileType:
        return FileType.FILE


class Directory(MemoryNode):
    """A directory: a node that owns other nodes."""

    def __init__(self, name: str, **attrs: Any) -> None:
        super().__init__(name, **attrs)
        self._entries: dict[str, MemoryNode] = {}

    @property
    def file_type(self) -> FileType:
        return FileType.DIRECTORY

    def add(self, node: MemoryNode) -> MemoryNode:
        if node.parent is not None:
            raise ValueError(f"{node.name!r} already belongs to {node.parent.path}")
        if node.name in self._entries:
            raise FileExistsError(f"{self.path.rstrip('/')}/{node.name} already exists")
        node.parent = self
        self._entries[node.name] = node
        return node

    def remove(self, name: str) -> MemoryNode:
        node = self._entries.pop(name)
        node.parent = None
        return node

    def get(self, name: str) -> MemoryNode | None:
        return self._entries.get(name)

    def children(self) -> Sequence[Node]:
        # Return a snapshot so a concurrent add() cannot break an ongoing walk.
        return tuple(self._entries[name] for name in sorted(self._entries))


class Symlink(MemoryNode):
    """A symbolic link: stores a path, not a reference, so it can dangle."""

    def __init__(self, name: str, target: str, **attrs: Any) -> None:
        super().__init__(name, size=len(target), **attrs)
        self.target = target

    @property
    def file_type(self) -> FileType:
        return FileType.SYMLINK

    def resolve(self) -> Node | None:
        return _follow(self, [MAX_SYMLINK_HOPS])


def _root_of(node: MemoryNode) -> MemoryNode:
    while node.parent is not None:
        node = node.parent
    return node


def _follow(node: MemoryNode | None, budget: list[int]) -> MemoryNode | None:
    """Resolve a chain of symlinks, sharing one hop budget across the chain."""
    while isinstance(node, Symlink):
        budget[0] -= 1
        if budget[0] < 0 or node.parent is None:
            return None
        node = _lookup(node.parent, node.target, budget)
    return node


def _lookup(base: MemoryNode, target: str, budget: list[int]) -> MemoryNode | None:
    """Resolve `target` relative to directory `base`, like the kernel's namei()."""
    node: MemoryNode | None = _root_of(base) if target.startswith("/") else base
    for part in PurePosixPath(target).parts:
        if part in ("/", "."):
            continue
        node = _follow(node, budget)
        if not isinstance(node, Directory):
            return None
        node = (node.parent or node) if part == ".." else node.get(part)
        if node is None:
            return None
    return _follow(node, budget)


class FileSystem:
    """Convenience builder for an in-memory tree rooted at '/'."""

    def __init__(self) -> None:
        self.root = Directory("root")
        self.root.name = "/"  # the one name validation forbids for ordinary entries

    def get(self, path: str) -> MemoryNode | None:
        return _lookup(self.root, path, [MAX_SYMLINK_HOPS]) if path != "/" else self.root

    def mkdir(self, path: str, **attrs: Any) -> Directory:
        """Create a directory and any missing parents (like `mkdir -p`)."""
        node: Directory = self.root
        for part in PurePosixPath(path).parts[1:]:
            child = node.get(part)
            if child is None:
                child = node.add(Directory(part, **attrs))
            if not isinstance(child, Directory):
                raise NotADirectoryError(child.path)
            node = child
        return node

    def touch(self, path: str, **attrs: Any) -> File:
        parent, name = self._split(path)
        return parent.add(File(name, **attrs))  # type: ignore[return-value]

    def symlink(self, path: str, target: str, **attrs: Any) -> Symlink:
        parent, name = self._split(path)
        return parent.add(Symlink(name, target, **attrs))  # type: ignore[return-value]

    def _split(self, path: str) -> tuple[Directory, str]:
        pure = PurePosixPath(path)
        return self.mkdir(str(pure.parent)), pure.name


class DiskNode(Node):
    """Adapter: presents a real path on disk through the Node interface."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        st = self._path.lstat()  # lstat: describe a link itself, not its target
        self.name = self._path.name or str(self._path)
        self.size = st.st_size
        self.owner = _owner_name(st.st_uid)
        self.modified = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
        self._mode = st.st_mode
        self._key = (st.st_dev, st.st_ino)

    @property
    def file_type(self) -> FileType:
        if stat.S_ISLNK(self._mode):
            return FileType.SYMLINK
        if stat.S_ISDIR(self._mode):
            return FileType.DIRECTORY
        return FileType.FILE

    @property
    def path(self) -> str:
        return str(self._path)

    def children(self) -> Sequence[Node]:
        if not self.is_dir:
            return ()
        nodes: list[Node] = []
        for child in sorted(self._path.iterdir()):
            try:
                nodes.append(DiskNode(child))
            except FileNotFoundError:
                continue  # deleted between listing and stat: a normal race
        return nodes

    def identity(self) -> Hashable:
        return self._key

    def resolve(self) -> Node | None:
        if self.file_type is not FileType.SYMLINK:
            return self
        try:
            return DiskNode(self._path.resolve(strict=True))
        except (OSError, RuntimeError):
            return None


def _owner_name(uid: int) -> str:
    try:
        import pwd  # Unix only

        return pwd.getpwuid(uid).pw_name
    except (ImportError, KeyError):
        return str(uid)


# --------------------------------------------------------------------------
# 2. Attributes and comparison operators
# --------------------------------------------------------------------------


class FileAttribute(Enum):
    """A searchable property of a node and the Python type of its value."""

    NAME = ("name", str)
    EXTENSION = ("extension", str)
    SIZE = ("size", int)
    OWNER = ("owner", str)
    TYPE = ("type", FileType)
    MODIFIED = ("modified", datetime)

    def __init__(self, label: str, value_type: type) -> None:
        self.label = label
        self.value_type = value_type

    def extract(self, node: Node) -> Any:
        return _EXTRACTORS[self](node)


_EXTRACTORS: dict[FileAttribute, Callable[[Node], Any]] = {
    FileAttribute.NAME: lambda n: n.name,
    FileAttribute.EXTENSION: lambda n: PurePosixPath(n.name).suffix.lstrip("."),
    FileAttribute.SIZE: lambda n: n.size,
    FileAttribute.OWNER: lambda n: n.owner,
    FileAttribute.TYPE: lambda n: n.file_type,
    FileAttribute.MODIFIED: lambda n: n.modified,
}


class Operator(ABC):
    """Compares an attribute's actual value with an expected value."""

    symbol: ClassVar[str]

    @abstractmethod
    def accepts(self, value_type: type) -> bool:
        """Can this operator be applied to values of `value_type`?"""

    def prepare(self, expected: Any) -> Any:
        """Pre-process the expected value once (e.g. compile a regex)."""
        return expected

    @abstractmethod
    def test(self, actual: Any, prepared: Any) -> bool: ...


class Equals(Operator):
    symbol = "=="

    def accepts(self, value_type: type) -> bool:
        return True

    def test(self, actual: Any, prepared: Any) -> bool:
        return actual == prepared


class _Ordering(Operator):
    _ORDERED_TYPES = (int, float, datetime)

    def accepts(self, value_type: type) -> bool:
        return issubclass(value_type, self._ORDERED_TYPES)


class GreaterThan(_Ordering):
    symbol = ">"

    def test(self, actual: Any, prepared: Any) -> bool:
        return actual > prepared


class LessThan(_Ordering):
    symbol = "<"

    def test(self, actual: Any, prepared: Any) -> bool:
        return actual < prepared


class RegexMatch(Operator):
    """Whole-string regular-expression match (like `find -regex`)."""

    symbol = "~"

    def __init__(self, *, ignore_case: bool = False) -> None:
        self._flags = re.IGNORECASE if ignore_case else 0

    def accepts(self, value_type: type) -> bool:
        return value_type is str

    def prepare(self, expected: Any) -> re.Pattern[str]:
        try:
            return re.compile(expected, self._flags)
        except re.error as exc:
            raise ValueError(f"bad regular expression {expected!r}: {exc}") from exc

    def test(self, actual: Any, prepared: re.Pattern[str]) -> bool:
        return prepared.fullmatch(actual) is not None


class GlobMatch(RegexMatch):
    """Shell wildcard match (`*.py`, `report-??.pdf`), like `find -name`."""

    symbol = "glob"

    def prepare(self, expected: Any) -> re.Pattern[str]:
        return super().prepare(fnmatch.translate(expected))


EQUALS, GREATER_THAN, LESS_THAN = Equals(), GreaterThan(), LessThan()
REGEX, GLOB, IGLOB = RegexMatch(), GlobMatch(), GlobMatch(ignore_case=True)


# --------------------------------------------------------------------------
# 3. Predicates: the Specification pattern
# --------------------------------------------------------------------------


class Predicate(ABC):
    """A yes/no question about a node. Combine with `&`, `|` and `~`."""

    @abstractmethod
    def matches(self, node: Node) -> bool: ...

    def __and__(self, other: Predicate) -> Predicate:
        return And(self, other)

    def __or__(self, other: Predicate) -> Predicate:
        return Or(self, other)

    def __invert__(self) -> Predicate:
        return Not(self)


class AttributePredicate(Predicate):
    """Leaf test: `<attribute> <operator> <value>`, validated at construction."""

    def __init__(self, attribute: FileAttribute, operator: Operator, expected: Any) -> None:
        if not operator.accepts(attribute.value_type):
            raise TypeError(f"operator {operator.symbol!r} cannot compare {attribute.label}")
        if not isinstance(expected, attribute.value_type):
            raise TypeError(
                f"{attribute.label} needs a {attribute.value_type.__name__}, "
                f"got {type(expected).__name__}"
            )
        self.attribute = attribute
        self.operator = operator
        self.expected = expected
        self._prepared = operator.prepare(expected)  # fail fast on a bad regex

    def matches(self, node: Node) -> bool:
        return self.operator.test(self.attribute.extract(node), self._prepared)

    def __str__(self) -> str:
        value = self.expected.value if isinstance(self.expected, Enum) else self.expected
        return f"{self.attribute.label} {self.operator.symbol} {value!r}"


class _Junction(Predicate):
    _word: ClassVar[str]

    def __init__(self, *operands: Predicate) -> None:
        if not operands:
            raise ValueError(f"{type(self).__name__} needs at least one operand")
        flat: list[Predicate] = []
        for op in operands:  # (a & b) & c becomes And(a, b, c): shallower tree
            flat.extend(op.operands if type(op) is type(self) else (op,))
        self.operands: tuple[Predicate, ...] = tuple(flat)

    def __str__(self) -> str:
        return "(" + f" {self._word} ".join(str(op) for op in self.operands) + ")"


class And(_Junction):
    _word = "and"

    def matches(self, node: Node) -> bool:
        return all(op.matches(node) for op in self.operands)  # short-circuits


class Or(_Junction):
    _word = "or"

    def matches(self, node: Node) -> bool:
        return any(op.matches(node) for op in self.operands)


class Not(Predicate):
    def __init__(self, operand: Predicate) -> None:
        self.operand = operand

    def matches(self, node: Node) -> bool:
        return not self.operand.matches(node)

    def __str__(self) -> str:
        return f"not {self.operand}"


class MatchAll(Predicate):
    """The empty expression: `find .` with no tests prints everything."""

    def matches(self, node: Node) -> bool:
        return True

    def __str__(self) -> str:
        return "true"


MATCH_ALL = MatchAll()


@dataclass(frozen=True)
class Field:
    """Readable builder: `where(FileAttribute.SIZE).gt(1024)`."""

    attribute: FileAttribute

    def eq(self, value: Any) -> AttributePredicate:
        return AttributePredicate(self.attribute, EQUALS, value)

    def gt(self, value: Any) -> AttributePredicate:
        return AttributePredicate(self.attribute, GREATER_THAN, value)

    def lt(self, value: Any) -> AttributePredicate:
        return AttributePredicate(self.attribute, LESS_THAN, value)

    def matches(self, regex: str) -> AttributePredicate:
        return AttributePredicate(self.attribute, REGEX, regex)

    def glob(self, pattern: str, *, ignore_case: bool = False) -> AttributePredicate:
        return AttributePredicate(self.attribute, IGLOB if ignore_case else GLOB, pattern)


def where(attribute: FileAttribute) -> Field:
    return Field(attribute)


# --------------------------------------------------------------------------
# 4. The search engine: lazy iterative depth-first walk
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SearchOptions:
    """Walk settings, kept apart from *what* we test (the predicate)."""

    max_depth: int | None = None
    min_depth: int = 0
    follow_symlinks: bool = False
    prune: Predicate | None = None  # directories matching this are not entered
    on_warning: Callable[[str], None] | None = None

    def __post_init__(self) -> None:
        if self.min_depth < 0 or (self.max_depth is not None and self.max_depth < 0):
            raise ValueError("depths must be non-negative")


@dataclass(frozen=True)
class Match:
    """One search hit: where we found it, what it is, how deep it was."""

    path: str
    node: Node
    depth: int


@dataclass(frozen=True)
class _Frame:
    node: Node
    path: str
    depth: int
    ancestors: frozenset[Hashable]  # identities of directories above us


class FileSearch:
    """Walks a tree and yields every entry the predicate accepts."""

    def __init__(self, options: SearchOptions | None = None) -> None:
        self.options = options or SearchOptions()

    def search(self, start: Node, criteria: Predicate = MATCH_ALL) -> Iterator[Match]:
        min_depth = self.options.min_depth
        for entry in self._walk(start):
            if entry.depth >= min_depth and criteria.matches(entry.node):
                yield entry

    def _walk(self, start: Node) -> Iterator[Match]:
        opts = self.options
        stack = [_Frame(start, start.path, 0, frozenset())]
        while stack:
            frame = stack.pop()
            node = frame.node
            if opts.follow_symlinks or frame.depth == 0:
                # Like find -H/-L: look through the link; a dangling link stays a link.
                node = node.resolve() or node
            yield Match(frame.path, node, frame.depth)

            if not node.is_dir or not self._may_descend(node, frame):
                continue
            key = node.identity()
            if key in frame.ancestors:
                self._warn(f"file system loop detected at {frame.path}")
                continue
            try:
                kids = node.children()
            except OSError as exc:  # permission denied, vanished directory...
                self._warn(f"cannot read {frame.path}: {exc}")
                continue
            above = frame.ancestors | {key}
            base = frame.path.rstrip("/")
            # Push in reverse so the alphabetically first child is popped first.
            for child in reversed(kids):
                stack.append(_Frame(child, f"{base}/{child.name}", frame.depth + 1, above))

    def _may_descend(self, node: Node, frame: _Frame) -> bool:
        opts = self.options
        if opts.max_depth is not None and frame.depth >= opts.max_depth:
            return False
        return not (opts.prune is not None and opts.prune.matches(node))

    def _warn(self, message: str) -> None:
        if self.options.on_warning is not None:
            self.options.on_warning(message)


# --------------------------------------------------------------------------
# 5. Parsing find-style expressions (Interpreter + recursive descent)
# --------------------------------------------------------------------------

_SIZE_UNITS = {"": 512, "c": 1, "k": 1024, "M": 1024**2, "G": 1024**3}
_SIZE_RE = re.compile(r"([+-]?)(\d+)([ckMG]?)")


def parse_find_expression(args: Sequence[str]) -> Predicate:
    """Turn find-style tokens into a Predicate tree.

    Grammar (lowest precedence first), mirroring GNU find:
        expr    := and_expr  ( ('-o' | '-or')  and_expr )*
        and_expr:= unary     ( ['-a' | '-and'] unary   )*   # juxtaposition = AND
        unary   := ('!' | '-not') unary | primary
        primary := '(' expr ')' | test
    """
    if not args:
        return MATCH_ALL
    parser = _Parser(list(args))
    tree = parser.parse_or()
    if parser.peek() is not None:
        raise ValueError(f"unexpected token {parser.peek()!r}")
    return tree


class _Parser:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self) -> str:
        token = self.peek()
        if token is None:
            raise ValueError("expression ended unexpectedly")
        self.pos += 1
        return token

    def parse_or(self) -> Predicate:
        left = self.parse_and()
        while self.peek() in ("-o", "-or"):
            self.take()
            left = left | self.parse_and()
        return left

    def parse_and(self) -> Predicate:
        left = self.parse_unary()
        while self.peek() not in (None, "-o", "-or", ")"):
            if self.peek() in ("-a", "-and"):
                self.take()
            left = left & self.parse_unary()
        return left

    def parse_unary(self) -> Predicate:
        if self.peek() in ("!", "-not"):
            self.take()
            return ~self.parse_unary()
        if self.peek() == "(":
            self.take()
            inner = self.parse_or()
            if self.peek() != ")":
                raise ValueError("missing ')'")
            self.take()
            return inner
        return self.parse_test()

    def parse_test(self) -> Predicate:
        token = self.take()
        match token:
            case "-name":
                return where(FileAttribute.NAME).glob(self.take())
            case "-iname":
                return where(FileAttribute.NAME).glob(self.take(), ignore_case=True)
            case "-regex":
                return where(FileAttribute.NAME).matches(self.take())
            case "-user":
                return where(FileAttribute.OWNER).eq(self.take())
            case "-type":
                letter = self.take()
                try:
                    return where(FileAttribute.TYPE).eq(FileType(letter))
                except ValueError:
                    raise ValueError(f"unknown -type {letter!r}") from None
            case "-size":
                return _size_test(self.take())
            case _:
                raise ValueError(f"unknown test {token!r}")


def _size_test(spec: str) -> Predicate:
    """`+N` bigger, `-N` smaller, `N` exactly. Units: c, k, M, G; none = 512 B.

    Simplification: GNU find rounds sizes *up* to whole units before comparing;
    we compare exact byte counts.
    """
    m = _SIZE_RE.fullmatch(spec)
    if m is None:
        raise ValueError(f"bad -size {spec!r}")
    sign, digits, unit = m.groups()
    size = where(FileAttribute.SIZE)
    limit = int(digits) * _SIZE_UNITS[unit]
    return {"+": size.gt, "-": size.lt, "": size.eq}[sign](limit)


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------


def build_sample_fs() -> FileSystem:
    """A small tree shared by the demo and the tests."""
    fs = FileSystem()
    t = datetime(2026, 10, 1, tzinfo=timezone.utc)
    fs.touch("/home/alice/notes.txt", owner="alice", size=1_200, modified=t)
    fs.touch("/home/alice/report-2026.pdf", owner="alice", size=250_000, modified=t)
    fs.touch("/home/alice/photos/cat.jpg", owner="alice", size=3_500_000)
    fs.touch("/home/alice/photos/prefix-draft.jpg", owner="alice", size=2_000_000)
    fs.touch("/home/bob/todo.txt", owner="bob", size=80)
    fs.touch("/home/bob/main.py", owner="bob", size=4_096)
    fs.touch("/projects/app/src/app.py", owner="bob", size=9_000)
    fs.touch("/projects/app/node_modules/left-pad/index.js", owner="bob", size=500)
    fs.symlink("/projects/app/latest-report", "/home/alice/report-2026.pdf", owner="bob")
    fs.symlink("/projects/app/loop", "..", owner="bob")  # points back up: a cycle
    fs.touch("/var/log/syslog", size=5_000_000)
    return fs


def demo() -> None:
    fs = build_sample_fs()

    def show(title: str, matches: Iterable[Match]) -> None:
        print(f"\n# {title}")
        for m in matches:
            print(f"  {m.path}  ({m.node.size:,} B, {m.node.owner})")

    big = where(FileAttribute.SIZE).gt(1_000_000)
    show("files larger than 1 MB", FileSearch().search(fs.root, big))

    tokens = "( -size +10c -size -1000c -user alice ) -o ( -size +1000c ! -name prefix* )"
    expr = parse_find_expression(tokens.split())
    print(f"\n# parsed: {expr}")
    show("alice's small files, or big files not named prefix*",
         FileSearch().search(fs.root, expr & where(FileAttribute.TYPE).eq(FileType.FILE)))

    skip = where(FileAttribute.NAME).eq("node_modules")
    js = where(FileAttribute.EXTENSION).eq("js")
    show("*.js, full walk", FileSearch().search(fs.root, js))
    show("*.js with node_modules pruned", FileSearch(SearchOptions(prune=skip)).search(fs.root, js))

    warnings: list[str] = []
    following = FileSearch(SearchOptions(follow_symlinks=True, on_warning=warnings.append))
    pdf = where(FileAttribute.NAME).glob("*.pdf")
    show("PDFs, following symlinks (find -L)", following.search(fs.get("/projects"), pdf))
    print("  warnings:", warnings)

    first = next(FileSearch().search(fs.root, where(FileAttribute.OWNER).eq("bob")))
    print(f"\n# lazy: first file owned by bob is {first.path} (walk stopped there)")

    here = DiskNode(Path(__file__).resolve().parent)
    py = where(FileAttribute.NAME).glob("*.py")
    names = [m.node.name for m in FileSearch(SearchOptions(max_depth=1)).search(here, py)]
    print(f"\n# real disk via DiskNode adapter: {names}")


if __name__ == "__main__":
    demo()
