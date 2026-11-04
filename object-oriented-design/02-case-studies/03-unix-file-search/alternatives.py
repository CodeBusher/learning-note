"""Competing designs for the file-search problem, each runnable on its own.

Decision 1 - how to express filters
    A. search_with_params   : one function, keyword arguments, if-checks
    B. FilterChain          : Strategy object per filter, always AND-ed
    C. Specification        : see file_search.Predicate (And/Or/Not tree)
    D. Plain functions      : Callable[[Node], bool] plus combinator helpers

Decision 2 - how to traverse
    recursive_dfs, iterative_dfs, bfs (eager lists) vs lazy_dfs (generator)

Decision 3 - how to represent comparison operators
    strings looked up in a dict vs an Enum vs operator objects (file_search)

Decision 4 - symlink cycles when following links
    no detection (with a safety cap), global visited set, ancestor chain

Decision 5 - live walk vs prebuilt index (find vs locate)

Plus a thread-pool walker used in the concurrency discussion.
"""

from __future__ import annotations

import fnmatch
import operator
import queue
import re
import threading
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable, Hashable, Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Any

from file_search import (
    Directory,
    FileAttribute,
    FileSearch,
    FileSystem,
    FileType,
    Node,
    SearchOptions,
    build_sample_fs,
    where,
)


def _walk_all(root: Node) -> Iterator[tuple[str, Node]]:
    """Plain pre-order walk shared by the Decision 1 variants."""
    stack: list[tuple[str, Node]] = [(root.path, root)]
    while stack:
        path, node = stack.pop()
        yield path, node
        base = path.rstrip("/")
        for child in reversed(node.children()):
            stack.append((f"{base}/{child.name}", child))


# --------------------------------------------------------------------------
# Decision 1A: one function with keyword parameters
# --------------------------------------------------------------------------


def search_with_params(
    root: Node,
    *,
    name_glob: str | None = None,
    min_size: int | None = None,
    max_size: int | None = None,
    owner: str | None = None,
    file_type: FileType | None = None,
) -> list[str]:
    """Every new filter means a new parameter and a new if-block here."""
    results = []
    for path, node in _walk_all(root):
        if name_glob is not None and not fnmatch.fnmatchcase(node.name, name_glob):
            continue
        if min_size is not None and node.size <= min_size:
            continue
        if max_size is not None and node.size >= max_size:
            continue
        if owner is not None and node.owner != owner:
            continue
        if file_type is not None and node.file_type is not file_type:
            continue
        results.append(path)
    return results


# --------------------------------------------------------------------------
# Decision 1B: one Strategy class per filter, combined with AND only
# --------------------------------------------------------------------------


class Filter(ABC):
    """One pluggable filter (Strategy). Unaware of other filters."""

    @abstractmethod
    def apply(self, node: Node) -> bool: ...


class NameFilter(Filter):
    def __init__(self, pattern: str) -> None:
        self.pattern = pattern

    def apply(self, node: Node) -> bool:
        return fnmatch.fnmatchcase(node.name, self.pattern)


class SizeFilter(Filter):
    def __init__(self, *, above: int = -1, below: int | None = None) -> None:
        self.above, self.below = above, below

    def apply(self, node: Node) -> bool:
        return node.size > self.above and (self.below is None or node.size < self.below)


class OwnerFilter(Filter):
    def __init__(self, owner: str) -> None:
        self.owner = owner

    def apply(self, node: Node) -> bool:
        return node.owner == self.owner


class TypeFilter(Filter):
    def __init__(self, file_type: FileType) -> None:
        self.file_type = file_type

    def apply(self, node: Node) -> bool:
        return node.file_type is self.file_type


class FilterChain:
    """Holds a list of filters; a node must pass all of them."""

    def __init__(self, *filters: Filter) -> None:
        self.filters = list(filters)

    def search(self, root: Node) -> list[str]:
        return [p for p, n in _walk_all(root) if all(f.apply(n) for f in self.filters)]


# --------------------------------------------------------------------------
# Decision 1D: plain functions and lambdas
# --------------------------------------------------------------------------

NodeTest = Callable[[Node], bool]


def all_of(*tests: NodeTest) -> NodeTest:
    return lambda node: all(t(node) for t in tests)


def any_of(*tests: NodeTest) -> NodeTest:
    return lambda node: any(t(node) for t in tests)


def negate(test: NodeTest) -> NodeTest:
    return lambda node: not test(node)


def search_with_function(root: Node, test: NodeTest) -> list[str]:
    return [path for path, node in _walk_all(root) if test(node)]


# --------------------------------------------------------------------------
# Decision 2: traversal strategies
# --------------------------------------------------------------------------


@dataclass
class WalkStats:
    """How much work a traversal did, for comparing strategies."""

    visited: int = 0
    peak_frontier: int = 0  # largest stack/queue size seen: a proxy for memory


def recursive_dfs(root: Node, test: NodeTest, stats: WalkStats | None = None) -> list[str]:
    stats = stats or WalkStats()
    results: list[str] = []

    def visit(node: Node, path: str) -> None:
        stats.visited += 1
        if test(node):
            results.append(path)
        for child in node.children():
            visit(child, f"{path.rstrip('/')}/{child.name}")  # one Python frame per level

    visit(root, root.path)
    return results


def iterative_dfs(root: Node, test: NodeTest, stats: WalkStats | None = None) -> list[str]:
    stats = stats or WalkStats()
    results: list[str] = []
    stack: list[tuple[Node, str]] = [(root, root.path)]
    while stack:
        stats.peak_frontier = max(stats.peak_frontier, len(stack))
        node, path = stack.pop()
        stats.visited += 1
        if test(node):
            results.append(path)
        for child in reversed(node.children()):
            stack.append((child, f"{path.rstrip('/')}/{child.name}"))
    return results


def bfs(root: Node, test: NodeTest, stats: WalkStats | None = None) -> list[str]:
    stats = stats or WalkStats()
    results: list[str] = []
    frontier: deque[tuple[Node, str]] = deque([(root, root.path)])
    while frontier:
        stats.peak_frontier = max(stats.peak_frontier, len(frontier))
        node, path = frontier.popleft()
        stats.visited += 1
        if test(node):
            results.append(path)
        for child in node.children():
            frontier.append((child, f"{path.rstrip('/')}/{child.name}"))
    return results


def lazy_dfs(root: Node, test: NodeTest, stats: WalkStats | None = None) -> Iterator[str]:
    """Same as iterative_dfs, but the caller pulls results one at a time."""
    stats = stats or WalkStats()
    stack: list[tuple[Node, str]] = [(root, root.path)]
    while stack:
        stats.peak_frontier = max(stats.peak_frontier, len(stack))
        node, path = stack.pop()
        stats.visited += 1
        if test(node):
            yield path
        for child in reversed(node.children()):
            stack.append((child, f"{path.rstrip('/')}/{child.name}"))


def build_deep_chain(depth: int) -> Directory:
    """/d/d/d/... `depth` levels deep with a file at the bottom."""
    fs = FileSystem()
    node = fs.root
    for _ in range(depth):
        node = node.add(Directory("d"))  # type: ignore[assignment]
    fs.touch(node.path + "/bottom.txt")
    return fs.root


def build_wide_tree(fanout: int, depth: int) -> Directory:
    """Every directory has `fanout` subdirectories, `depth` levels down."""
    fs = FileSystem()
    level = [fs.root]
    for _ in range(depth):
        nxt = []
        for parent in level:
            for i in range(fanout):
                nxt.append(parent.add(Directory(f"d{i}")))
        level = nxt
    return fs.root


# --------------------------------------------------------------------------
# Decision 3: representing comparison operators
# --------------------------------------------------------------------------

_STRING_OPS: dict[str, Callable[[Any, Any], bool]] = {
    "==": operator.eq,
    ">": operator.gt,
    "<": operator.lt,
    "~": lambda actual, pattern: re.fullmatch(pattern, actual) is not None,
}


def compare_with_string(actual: Any, op: str, expected: Any) -> bool:
    """Typos such as '=>' are only discovered when this line runs."""
    try:
        return _STRING_OPS[op](actual, expected)
    except KeyError:
        raise ValueError(f"unknown operator {op!r}") from None


class Op(Enum):
    """A closed set: safe and fast, but adding one means editing this class."""

    EQ = "=="
    GT = ">"
    LT = "<"
    REGEX = "~"

    def apply(self, actual: Any, expected: Any) -> bool:
        match self:
            case Op.EQ:
                return actual == expected
            case Op.GT:
                return actual > expected
            case Op.LT:
                return actual < expected
            case Op.REGEX:
                return re.fullmatch(expected, actual) is not None


# --------------------------------------------------------------------------
# Decision 4: symlink cycles when following links
# --------------------------------------------------------------------------


def follow_naive(root: Node, cap: int = 1_000) -> int:
    """No cycle check. Returns how many nodes it visited before hitting `cap`."""
    visited = 0
    stack = [root]
    while stack and visited < cap:
        node = stack.pop().resolve()
        if node is None:
            continue
        visited += 1
        stack.extend(node.children())
    return visited


def follow_with_visited_set(root: Node) -> list[str]:
    """Never enter the same directory twice anywhere in the walk."""
    seen: set[Hashable] = set()
    results: list[str] = []
    stack: list[tuple[Node, str]] = [(root, root.path)]
    while stack:
        raw, path = stack.pop()
        node = raw.resolve() or raw
        results.append(path)
        if not node.is_dir or node.identity() in seen:
            continue
        seen.add(node.identity())
        for child in reversed(node.children()):
            stack.append((child, f"{path.rstrip('/')}/{child.name}"))
    return results


def follow_with_ancestor_chain(root: Node) -> list[str]:
    """What file_search.FileSearch does: only refuse a directory we are inside."""
    search = FileSearch(SearchOptions(follow_symlinks=True))
    return [m.path for m in search.search(root)]


# --------------------------------------------------------------------------
# Decision 5: live walk vs prebuilt index (find vs locate)
# --------------------------------------------------------------------------


class PathIndex:
    """A toy `updatedb` + `locate`: snapshot all paths, then search the list."""

    def __init__(self) -> None:
        self._paths: list[str] = []
        self.builds = 0

    def rebuild(self, root: Node) -> None:
        self._paths = sorted(path for path, _ in _walk_all(root))
        self.builds += 1

    def locate(self, substring: str) -> list[str]:
        return [p for p in self._paths if substring in p]


# --------------------------------------------------------------------------
# Concurrency: a thread-pool walker (the fd / ripgrep idea)
# --------------------------------------------------------------------------


def parallel_search(root: Node, test: NodeTest, workers: int = 4) -> list[str]:
    """Workers pull directories from a shared queue and push subdirectories.

    On a real disk, listing a directory is a system call that releases the GIL,
    so several threads can wait on I/O at once. Output order is not stable, so
    we sort at the end (fd does the same when you ask for sorted output).
    """
    work: queue.Queue[tuple[Node, str] | None] = queue.Queue()
    results: list[str] = []
    errors: list[BaseException] = []
    lock = threading.Lock()

    def worker() -> None:
        while (item := work.get()) is not None:
            node, path = item
            try:
                if test(node):
                    with lock:  # list.append is atomic in CPython, but say what we mean
                        results.append(path)
                for child in node.children():
                    work.put((child, f"{path.rstrip('/')}/{child.name}"))
            except Exception as exc:  # a dead worker would otherwise be silent
                with lock:
                    errors.append(exc)
            finally:
                work.task_done()  # must run even on error, or join() hangs forever
        work.task_done()

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(workers)]
    for t in threads:
        t.start()
    work.put((root, root.path))
    work.join()  # returns once every queued directory has been processed
    for _ in threads:
        work.put(None)
    for t in threads:
        t.join()
    if errors:
        raise errors[0]
    return sorted(results)


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------


def demo() -> None:
    fs = build_sample_fs()
    root = fs.root

    print("# Decision 1: four ways to ask for 'alice's .txt files'")
    print("  A params   :", search_with_params(root, name_glob="*.txt", owner="alice"))
    print("  B strategy :", FilterChain(NameFilter("*.txt"), OwnerFilter("alice")).search(root))
    spec = where(FileAttribute.NAME).glob("*.txt") & where(FileAttribute.OWNER).eq("alice")
    print("  C spec     :", [m.path for m in FileSearch().search(root, spec)], f"<- {spec}")
    test = all_of(lambda n: n.name.endswith(".txt"), lambda n: n.owner == "alice")
    print("  D functions:", search_with_function(root, test), f"<- {test.__qualname__}")

    print("\n# Decision 2: traversal")
    is_py: NodeTest = lambda n: n.name.endswith(".py")
    for walker in (recursive_dfs, iterative_dfs, bfs):
        print(f"  {walker.__name__:14}", walker(root, is_py))
    eager, lazy = WalkStats(), WalkStats()
    iterative_dfs(root, is_py, eager)
    next(lazy_dfs(root, is_py, lazy))
    print(f"  first match only: eager visited {eager.visited}, lazy visited {lazy.visited}")
    is_bottom: NodeTest = lambda n: n.name == "bottom.txt"
    try:
        recursive_dfs(build_deep_chain(5_000), is_bottom)
    except RecursionError:
        print("  recursive_dfs on a 5,000-level chain: RecursionError")
    found = iterative_dfs(build_deep_chain(5_000), is_bottom)
    print(f"  iterative_dfs on the same chain: found {len(found)} file, {found[0].count('/')} levels down")
    wide = build_wide_tree(fanout=10, depth=4)
    d, b = WalkStats(), WalkStats()
    iterative_dfs(wide, is_py, d)
    bfs(wide, is_py, b)
    print(f"  wide tree peak frontier: DFS {d.peak_frontier}, BFS {b.peak_frontier}")

    print("\n# Decision 3: operators")
    print("  string '>' :", compare_with_string(2_000, ">", 1_000))
    try:
        compare_with_string(2_000, "=>", 1_000)
    except ValueError as exc:
        print("  string '=>':", exc, "(found only at run time)")
    print("  enum GT    :", Op.GT.apply(2_000, 1_000))

    print("\n# Decision 4: following symlinks with a cycle")
    print("  naive follow visited", follow_naive(fs.get("/projects")), "nodes before the cap")
    fs.symlink("/home/bob/alias-a", "/home/alice/photos")
    fs.symlink("/home/bob/alias-b", "/home/alice/photos")
    bob = fs.get("/home/bob")
    seen = [p for p in follow_with_visited_set(bob) if p.endswith(".jpg")]
    chain = [p for p in follow_with_ancestor_chain(bob) if p.endswith(".jpg")]
    print("  visited set   :", seen)
    print("  ancestor chain:", chain)

    print("\n# Decision 5: locate-style index goes stale")
    index = PathIndex()
    index.rebuild(root)
    fs.touch("/home/alice/new-notes.txt", owner="alice")
    print("  locate 'new-notes':", index.locate("new-notes"))
    live = where(FileAttribute.NAME).glob("new-notes*")
    print("  live walk         :", [m.path for m in FileSearch().search(root, live)])

    print("\n# Concurrency: parallel walk")
    print("  ", parallel_search(root, is_py, workers=4))


if __name__ == "__main__":
    demo()
