"""Tests for the recommended design (file_search) and key alternatives."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import alternatives as alt
from file_search import (
    MATCH_ALL,
    And,
    AttributePredicate,
    Directory,
    DiskNode,
    File,
    FileAttribute,
    FileSearch,
    FileSystem,
    FileType,
    GREATER_THAN,
    Not,
    Or,
    REGEX,
    SearchOptions,
    Symlink,
    build_sample_fs,
    parse_find_expression,
    where,
)

NAME, SIZE, OWNER, TYPE, EXT, MODIFIED = (
    FileAttribute.NAME,
    FileAttribute.SIZE,
    FileAttribute.OWNER,
    FileAttribute.TYPE,
    FileAttribute.EXTENSION,
    FileAttribute.MODIFIED,
)


def paths(search: FileSearch, root, predicate=MATCH_ALL) -> list[str]:
    return [m.path for m in search.search(root, predicate)]


class TreeModelTests(unittest.TestCase):
    def test_paths_are_built_from_parents(self):
        fs = FileSystem()
        f = fs.touch("/a/b/c.txt")
        self.assertEqual(f.path, "/a/b/c.txt")
        self.assertEqual(fs.root.path, "/")

    def test_duplicate_names_rejected(self):
        d = Directory("d")
        d.add(File("x"))
        with self.assertRaises(FileExistsError):
            d.add(File("x"))

    def test_node_cannot_have_two_parents(self):
        a, b, f = Directory("a"), Directory("b"), File("f")
        a.add(f)
        with self.assertRaises(ValueError):
            b.add(f)

    def test_invalid_names_and_sizes(self):
        for bad in ("", "a/b", ".", ".."):
            with self.assertRaises(ValueError):
                File(bad)
        with self.assertRaises(ValueError):
            File("x", size=-1)

    def test_mkdir_through_a_file_fails(self):
        fs = FileSystem()
        fs.touch("/a")
        with self.assertRaises(NotADirectoryError):
            fs.mkdir("/a/b")

    def test_children_are_sorted_snapshot(self):
        d = Directory("d")
        for name in ("b", "a", "c"):
            d.add(File(name))
        kids = d.children()
        d.add(File("z"))
        self.assertEqual([k.name for k in kids], ["a", "b", "c"])

    def test_remove_detaches(self):
        d = Directory("d")
        f = d.add(File("x"))
        d.remove("x")
        self.assertIsNone(f.parent)
        self.assertIsNone(d.get("x"))


class SymlinkResolutionTests(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()
        self.target = self.fs.touch("/data/real.txt", size=7)

    def test_absolute_and_relative_targets(self):
        a = self.fs.symlink("/links/abs", "/data/real.txt")
        r = self.fs.symlink("/links/rel", "../data/real.txt")
        self.assertIs(a.resolve(), self.target)
        self.assertIs(r.resolve(), self.target)

    def test_chain_of_links(self):
        self.fs.symlink("/l1", "/data/real.txt")
        l2 = self.fs.symlink("/l2", "/l1")
        self.assertIs(l2.resolve(), self.target)

    def test_link_through_linked_directory(self):
        self.fs.symlink("/d", "/data")
        link = self.fs.symlink("/via", "/d/real.txt")
        self.assertIs(link.resolve(), self.target)

    def test_dangling_link_resolves_to_none(self):
        self.assertIsNone(self.fs.symlink("/broken", "/nope").resolve())

    def test_self_referencing_link_gives_up(self):
        self.assertIsNone(self.fs.symlink("/me", "/me").resolve())

    def test_unattached_link(self):
        self.assertIsNone(Symlink("x", "/anything").resolve())


class AttributeAndOperatorTests(unittest.TestCase):
    def test_extraction(self):
        t = datetime(2026, 1, 1, tzinfo=timezone.utc)
        f = File("photo.JPG", owner="ann", size=10, modified=t)
        self.assertEqual(EXT.extract(f), "JPG")
        self.assertEqual(TYPE.extract(f), FileType.FILE)
        self.assertEqual(MODIFIED.extract(f), t)
        self.assertEqual(EXT.extract(File("Makefile")), "")

    def test_type_mismatch_rejected_at_construction(self):
        with self.assertRaises(TypeError):
            where(SIZE).eq("big")
        with self.assertRaises(TypeError):
            AttributePredicate(SIZE, REGEX, "1.*")
        with self.assertRaises(TypeError):
            AttributePredicate(OWNER, GREATER_THAN, "bob")

    def test_bad_regex_fails_fast(self):
        with self.assertRaises(ValueError):
            where(NAME).matches("([")

    def test_regex_is_whole_string(self):
        f = File("logger")
        self.assertTrue(where(NAME).matches("log.*").matches(f))
        self.assertFalse(where(NAME).matches("log").matches(f))

    def test_glob_and_case_insensitive_glob(self):
        f = File("Report.PDF")
        self.assertFalse(where(NAME).glob("*.pdf").matches(f))
        self.assertTrue(where(NAME).glob("*.pdf", ignore_case=True).matches(f))

    def test_date_comparison(self):
        cutoff = datetime(2026, 6, 1, tzinfo=timezone.utc)
        new = File("n", modified=datetime(2026, 7, 1, tzinfo=timezone.utc))
        self.assertTrue(where(MODIFIED).gt(cutoff).matches(new))
        self.assertFalse(where(MODIFIED).lt(cutoff).matches(new))


class PredicateCompositionTests(unittest.TestCase):
    def setUp(self):
        self.small = File("a.txt", owner="alice", size=50)
        self.big = File("prefix.bin", owner="bob", size=5_000)

    def test_operators_build_tree(self):
        p = where(SIZE).gt(10) & where(OWNER).eq("alice")
        self.assertIsInstance(p, And)
        self.assertIsInstance(p | p, Or)
        self.assertIsInstance(~p, Not)

    def test_and_flattens(self):
        a, b, c = where(SIZE).gt(1), where(SIZE).gt(2), where(SIZE).gt(3)
        self.assertEqual(len(((a & b) & c).operands), 3)

    def test_empty_junction_rejected(self):
        with self.assertRaises(ValueError):
            And()

    def test_book_style_nested_expression(self):
        # ((size > 10 and size < 1000 and owner = alice) or (size > 1000 and not name ~ prefix.*))
        left = where(SIZE).gt(10) & where(SIZE).lt(1000) & where(OWNER).eq("alice")
        right = where(SIZE).gt(1000) & ~where(NAME).matches("prefix.*")
        expr = left | right
        self.assertTrue(expr.matches(self.small))
        self.assertFalse(expr.matches(self.big))
        self.assertTrue(expr.matches(File("other.bin", size=5_000)))

    def test_and_short_circuits(self):
        calls = []

        class Spy(AttributePredicate):
            def matches(self, node):
                calls.append(node)
                return True

        (where(SIZE).gt(10_000) & Spy(SIZE, GREATER_THAN, 0)).matches(self.small)
        self.assertEqual(calls, [])

    def test_str_is_readable(self):
        p = where(SIZE).gt(10) & ~where(TYPE).eq(FileType.DIRECTORY)
        self.assertEqual(str(p), "(size > 10 and not type == 'd')")


class FileSearchTests(unittest.TestCase):
    def setUp(self):
        self.fs = build_sample_fs()
        self.root = self.fs.root

    def test_preorder_sorted_output(self):
        found = paths(FileSearch(), self.fs.get("/home/bob"))
        self.assertEqual(found, ["/home/bob", "/home/bob/main.py", "/home/bob/todo.txt"])

    def test_directories_can_match(self):
        dirs = paths(FileSearch(), self.root, where(TYPE).eq(FileType.DIRECTORY))
        self.assertIn("/", dirs)
        self.assertIn("/home/alice/photos", dirs)

    def test_owner_and_regex_like_book_example(self):
        p = ~where(TYPE).eq(FileType.DIRECTORY) & where(OWNER).matches("b.*")
        found = paths(FileSearch(), self.fs.get("/home"), p)
        self.assertEqual(found, ["/home/bob/main.py", "/home/bob/todo.txt"])

    def test_max_and_min_depth(self):
        opts = SearchOptions(min_depth=1, max_depth=1)
        self.assertEqual(paths(FileSearch(opts), self.root), ["/home", "/projects", "/var"])

    def test_negative_depth_rejected(self):
        with self.assertRaises(ValueError):
            SearchOptions(max_depth=-1)

    def test_prune_skips_subtree_but_reports_dir(self):
        opts = SearchOptions(prune=where(NAME).eq("node_modules"))
        found = paths(FileSearch(opts), self.root)
        self.assertIn("/projects/app/node_modules", found)
        self.assertNotIn("/projects/app/node_modules/left-pad", found)

    def test_symlinks_not_followed_by_default(self):
        found = paths(FileSearch(), self.root, where(TYPE).eq(FileType.SYMLINK))
        self.assertEqual(found, ["/projects/app/latest-report", "/projects/app/loop"])
        self.assertNotIn("/projects/app/loop/app", paths(FileSearch(), self.root))

    def test_follow_symlinks_detects_loop(self):
        warnings: list[str] = []
        opts = SearchOptions(follow_symlinks=True, on_warning=warnings.append)
        found = paths(FileSearch(opts), self.fs.get("/projects"))
        self.assertIn("/projects/app/loop", found)
        self.assertNotIn("/projects/app/loop/app", found)
        self.assertEqual(warnings, ["file system loop detected at /projects/app/loop"])

    def test_follow_symlinks_evaluates_target(self):
        opts = SearchOptions(follow_symlinks=True)
        hits = list(FileSearch(opts).search(self.root, where(SIZE).eq(250_000)))
        self.assertEqual(
            [m.path for m in hits],
            ["/home/alice/report-2026.pdf", "/projects/app/latest-report"],
        )

    def test_dangling_link_reported_as_link_when_following(self):
        self.fs.symlink("/tmp/broken", "/missing")
        opts = SearchOptions(follow_symlinks=True)
        found = paths(FileSearch(opts), self.root, where(TYPE).eq(FileType.SYMLINK))
        self.assertEqual(found, ["/tmp/broken"])

    def test_same_dir_via_two_links_is_reported_twice(self):
        self.fs.symlink("/x/a", "/var/log")
        self.fs.symlink("/x/b", "/var/log")
        opts = SearchOptions(follow_symlinks=True)
        found = paths(FileSearch(opts), self.fs.get("/x"), where(NAME).eq("syslog"))
        self.assertEqual(found, ["/x/a/syslog", "/x/b/syslog"])

    def test_start_symlink_is_followed_like_find_H(self):
        link = self.fs.symlink("/shortcut", "/home/bob")
        self.assertIn("/shortcut/todo.txt", paths(FileSearch(), link))

    def test_search_is_lazy(self):
        visited = []

        class Counting(AttributePredicate):
            def matches(self, node):
                visited.append(node)
                return super().matches(node)

        it = FileSearch().search(self.root, Counting(OWNER, REGEX, "alice"))
        first = next(it)
        self.assertEqual(first.path, "/home/alice/notes.txt")
        self.assertLess(len(visited), 6)

    def test_depth_reported(self):
        hit = next(FileSearch().search(self.root, where(NAME).eq("syslog")))
        self.assertEqual(hit.depth, 3)

    def test_unreadable_directory_warns_and_continues(self):
        class Locked(Directory):
            def children(self):
                raise PermissionError("denied")

        self.fs.root.add(Locked("secret"))
        warnings: list[str] = []
        found = paths(FileSearch(SearchOptions(on_warning=warnings.append)), self.root)
        self.assertIn("/secret", found)
        self.assertIn("/var/log/syslog", found)
        self.assertTrue(warnings[0].startswith("cannot read /secret"))

    def test_deep_tree_does_not_overflow(self):
        root = alt.build_deep_chain(5_000)
        hit = next(FileSearch().search(root, where(NAME).eq("bottom.txt")))
        self.assertEqual(hit.depth, 5_001)


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.fs = build_sample_fs()

    def run_find(self, expr: str) -> list[str]:
        return paths(FileSearch(), self.fs.root, parse_find_expression(expr.split()))

    def test_empty_matches_all(self):
        self.assertIs(parse_find_expression([]), MATCH_ALL)

    def test_implicit_and_binds_tighter_than_or(self):
        tree = parse_find_expression("-user bob -name *.py -o -name *.pdf".split())
        self.assertEqual(
            str(tree), "((owner == 'bob' and name glob '*.py') or name glob '*.pdf')"
        )

    def test_not_and_parentheses(self):
        found = self.run_find("-type f ! ( -user alice -o -user bob )")
        self.assertEqual(found, ["/var/log/syslog"])

    def test_size_units(self):
        self.assertEqual(self.run_find("-size +4M"), ["/var/log/syslog"])
        self.assertEqual(self.run_find("-size -100c -type f"), ["/home/bob/todo.txt"])
        self.assertEqual(self.run_find("-size 8 -type f"), ["/home/bob/main.py"])  # 8 * 512

    def test_iname_and_regex(self):
        self.fs.touch("/home/bob/README.MD")
        self.assertEqual(self.run_find("-iname readme.md"), ["/home/bob/README.MD"])
        self.assertEqual(self.run_find("-regex t.*o.*"), ["/home/bob/todo.txt"])

    def test_errors(self):
        for bad in ("-name", "( -user bob", "-colour red", "-type x", "-size big",
                    "-user bob )"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_find_expression(bad.split())


class DiskAdapterTests(unittest.TestCase):
    def test_real_directory_walk(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "src").mkdir()
            (base / "src" / "a.py").write_text("print('hi')\n")
            (base / "notes.txt").write_text("x" * 100)
            os.symlink(base, base / "src" / "up")  # a real cycle
            warnings: list[str] = []
            opts = SearchOptions(follow_symlinks=True, on_warning=warnings.append)
            found = [m.node.name for m in FileSearch(opts).search(DiskNode(base), where(EXT).eq("py"))]
            self.assertEqual(found, ["a.py"])
            self.assertEqual(len(warnings), 1)
            big = [m.node.name for m in FileSearch().search(DiskNode(base), where(SIZE).eq(100))]
            self.assertEqual(big, ["notes.txt"])

    def test_disk_identity_is_inode_based(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = DiskNode(tmp), DiskNode(tmp)
            self.assertEqual(a.identity(), b.identity())
            self.assertEqual(a.file_type, FileType.DIRECTORY)


class AlternativeTests(unittest.TestCase):
    def setUp(self):
        self.fs = build_sample_fs()
        self.root = self.fs.root

    def test_four_filter_styles_agree(self):
        expected = ["/home/alice/notes.txt"]
        self.assertEqual(alt.search_with_params(self.root, name_glob="*.txt", owner="alice"), expected)
        chain = alt.FilterChain(alt.NameFilter("*.txt"), alt.OwnerFilter("alice"))
        self.assertEqual(chain.search(self.root), expected)
        test = alt.all_of(lambda n: n.name.endswith(".txt"), alt.negate(lambda n: n.owner != "alice"))
        self.assertEqual(alt.search_with_function(self.root, test), expected)

    def test_any_of(self):
        test = alt.any_of(lambda n: n.name == "syslog", lambda n: n.name == "todo.txt")
        self.assertEqual(alt.search_with_function(self.root, test), ["/home/bob/todo.txt", "/var/log/syslog"])

    def test_size_and_type_filters(self):
        chain = alt.FilterChain(alt.SizeFilter(above=1_000_000), alt.TypeFilter(FileType.FILE))
        self.assertEqual(len(chain.search(self.root)), 3)

    def test_traversals_find_same_set(self):
        test = lambda n: n.name.endswith(".txt")
        results = [sorted(w(self.root, test)) for w in (alt.recursive_dfs, alt.iterative_dfs, alt.bfs)]
        results.append(sorted(alt.lazy_dfs(self.root, test)))
        self.assertTrue(all(r == results[0] for r in results))

    def test_recursive_dfs_overflows_on_deep_tree(self):
        with self.assertRaises(RecursionError):
            alt.recursive_dfs(alt.build_deep_chain(5_000), lambda n: False)

    def test_bfs_frontier_grows_with_width(self):
        wide = alt.build_wide_tree(fanout=10, depth=3)
        d, b = alt.WalkStats(), alt.WalkStats()
        alt.iterative_dfs(wide, lambda n: False, d)
        alt.bfs(wide, lambda n: False, b)
        self.assertEqual(d.visited, b.visited)
        self.assertGreater(b.peak_frontier, 10 * d.peak_frontier)

    def test_operator_representations(self):
        self.assertTrue(alt.compare_with_string("bob", "~", "b.*"))
        with self.assertRaises(ValueError):
            alt.compare_with_string(1, "=>", 2)
        self.assertTrue(alt.Op.LT.apply(1, 2))
        self.assertTrue(alt.Op.REGEX.apply("bob", "b.b"))

    def test_naive_follow_hits_cap(self):
        self.assertEqual(alt.follow_naive(self.fs.get("/projects"), cap=500), 500)

    def test_visited_set_vs_ancestor_chain(self):
        self.fs.symlink("/x/a", "/var/log")
        self.fs.symlink("/x/b", "/var/log")
        x = self.fs.get("/x")
        seen = [p for p in alt.follow_with_visited_set(x) if p.endswith("syslog")]
        chain = [p for p in alt.follow_with_ancestor_chain(x) if p.endswith("syslog")]
        self.assertEqual(seen, ["/x/a/syslog"])
        self.assertEqual(chain, ["/x/a/syslog", "/x/b/syslog"])

    def test_index_is_stale_until_rebuilt(self):
        index = alt.PathIndex()
        index.rebuild(self.root)
        self.fs.touch("/home/bob/fresh.txt")
        self.assertEqual(index.locate("fresh"), [])
        index.rebuild(self.root)
        self.assertEqual(index.locate("fresh"), ["/home/bob/fresh.txt"])

    def test_parallel_matches_sequential(self):
        test = lambda n: n.size > 1_000
        self.assertEqual(alt.parallel_search(self.root, test, workers=8),
                         sorted(alt.iterative_dfs(self.root, test)))

    def test_parallel_reraises_worker_error(self):
        def boom(node):
            if node.name == "syslog":
                raise RuntimeError("bad predicate")
            return False

        with self.assertRaises(RuntimeError):
            alt.parallel_search(self.root, boom, workers=2)


if __name__ == "__main__":
    unittest.main()
