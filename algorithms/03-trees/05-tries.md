# Tries — A Tree Keyed by Letters

## 1. Many prefix questions over one word list

**Problem.** A word list is fixed; queries arrive by the thousands: "is `cart` a word?", "does any word start with `ca`?", "how many words start with `do`?".

**Brute force.** Compare the query with every word: O(total length of all words) per query.

**The key observation.** Words that share a prefix can share the work of matching it. Put the words in a tree where each edge is a letter: every word is a path from the root, and words with a common prefix share the start of their paths. This tree is a **trie** (from re*trie*val; also called a prefix tree). For `car, cart, cat, do, dog`:

```text
(root)
├── c
│   └── a
│       ├── r *        car
│       │   └── t *    cart
│       └── t *        cat
└── d
    └── o *            do
        └── g *        dog
```

Each node is a dictionary `children` from letter to child node, plus a flag `end` marking where a word stops (the `*`). The flag is needed because a path can be a word and also the prefix of a longer one: `car` ends inside the path of `cart`. Unlike the trees of the previous chapters, a node can have any number of children, and the values sit on the edges, not in the nodes.

**Insert** walks the letters from the root, creating missing children, and sets `end` on the last node. **Search** and **starts-with** walk the same way and fail as soon as a letter has no child. They differ only at the end:

| Query | Walk | Stops at | `search` (needs `end`) | `starts_with` |
|---|---|---|---|---|
| `cart` | c, a, r, t | the `t` under `r` | true | true |
| `ca` | c, a | `a` | false: no `*` | true |
| `cab` | c, a, then no `b` | fails | false | false |
| `dot` | d, o, then no `t` | fails | false | false |

Each operation costs O(L) for a word of length `L`, whatever the number of words.

## 2. Counting and deleting

**Counting prefixes.** Store in every node `passes`: how many inserted words go through it. Then "how many words start with `ca`" is the `passes` of the node at the end of `ca`: 3 (`car`, `cart`, `cat`). Keep `ends` as a count instead of a flag, and repeated inserts of the same word are counted too.

**Delete** undoes an insert: walk the word, decrement `passes` along the way, decrement `ends` at the last node. A child whose `passes` drops to 0 is no longer used by any word: cut it off, and everything below it goes with it.

- **Delete `car`.** `cart` still passes through `r`, so `passes(r)` goes from 2 to 1 and only `ends(r)` changes. Nothing is cut.
- **Delete `cart`** (after that). `passes(r)` drops to 0, so the whole `r → t` branch is cut at `a`. `cat` is untouched.

Check that the word exists before changing any count; otherwise deleting `cab` would decrement `c` and `a` and then find no `b`.

**Wildcards.** Some problems allow `.` in a query to match any single letter. At a `.` the walk can't choose one child, so it tries every child, depth first; `c.t` tries `c → a → t` and finds `cat`. A query with many dots can visit much of the trie, but each letter that is not a dot still prunes.

The script checks every operation against a plain list of words on random inserts and deletes over a small alphabet, so prefixes collide often.

```python
import random


class TrieNode:
    def __init__(self):
        self.children = {}
        self.passes = 0  # words going through this node
        self.ends = 0  # words ending here


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        node.passes += 1
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
            node.passes += 1
        node.ends += 1

    def _walk(self, s):
        node = self.root
        for ch in s:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def count_word(self, word):
        node = self._walk(word)
        return node.ends if node else 0

    def search(self, word):
        return self.count_word(word) > 0

    def count_prefix(self, prefix):
        node = self._walk(prefix)
        return node.passes if node else 0

    def starts_with(self, prefix):
        return self.count_prefix(prefix) > 0

    def delete(self, word):
        """Remove one copy of word; return False if it was not there."""
        if not self.search(word):
            return False
        node = self.root
        node.passes -= 1
        for ch in word:
            child = node.children[ch]
            child.passes -= 1
            if child.passes == 0:
                del node.children[ch]  # no word uses this branch any more
                return True
            node = child
        node.ends -= 1
        return True

    def match(self, pattern):
        """search with '.' matching any one letter."""
        def go(node, i):
            if i == len(pattern):
                return node.ends > 0
            if pattern[i] == ".":
                return any(go(child, i + 1) for child in node.children.values())
            child = node.children.get(pattern[i])
            return child is not None and go(child, i + 1)

        return go(self.root, 0)


def matches(pattern, word):
    return len(pattern) == len(word) and all(p in (".", c) for p, c in zip(pattern, word))


def main():
    t = Trie()
    for w in ["car", "cart", "cat", "do", "dog"]:
        t.insert(w)
    assert t.search("cart") and not t.search("ca") and t.starts_with("ca")
    assert not t.starts_with("cab") and not t.search("dot")
    assert t.count_prefix("ca") == 3 and t.count_prefix("") == 5
    assert t.match("c.t") and t.match("...t") and not t.match("c.")
    assert t.delete("car") and not t.search("car") and t.search("cart")
    assert t.delete("cart") and "r" not in t.root.children["c"].children["a"].children
    assert not t.delete("cab") and t.count_prefix("c") == 1

    rng = random.Random(1)
    for _ in range(200):
        t, words = Trie(), []
        for _ in range(60):
            w = "".join(rng.choice("ab") for _ in range(rng.randint(0, 4)))
            if rng.random() < 0.6:
                t.insert(w)
                words.append(w)
            else:
                assert t.delete(w) == (w in words)
                if w in words:
                    words.remove(w)
            q = "".join(rng.choice("ab.") for _ in range(rng.randint(0, 4)))
            p = q.replace(".", "")
            assert t.count_word(p) == words.count(p)
            assert t.count_prefix(p) == sum(x.startswith(p) for x in words)
            assert t.match(q) == any(matches(q, x) for x in words)


if __name__ == "__main__":
    main()
```

**Time:** O(L) for insert, search, count and delete; wildcard matching can reach O(size of the trie). **Space:** O(total letters inserted), at most one node per letter.

## 3. Word search on a grid

**Problem.** Given a letter grid and a word list, find every word that can be spelled by a path of horizontally or vertically adjacent cells, using each cell at most once per word.

```text
c a t        words: car, cars, cart, cat, dog, rod, sad
a r s        found: car, cars, cat, dog, rod
d o g
```

`cart` fails: after `c a r` the `t` is diagonal to `r`. `sad` fails: no `a` touches the `s`.

**Brute force.** Run a grid search for each word separately: from every cell, a depth-first search over paths. With `W` words, the work for shared prefixes is repeated `W` times; `car`, `cars` and `cart` each rediscover the path `c → a → r`.

**The key observation.** Search the grid **once**, walking the trie at the same time. A path in the grid is worth extending only if its letters are a prefix in the trie; when the next cell's letter has no child, that whole direction is abandoned for every word at once. When the walk reaches a node with `end` set, a word is found.

The code tries neighbors in the order down, up, right, left. From the `c` at the top left:

| Path | Trie | Result |
|---|---|---|
| c → a (below) | `ca` is a prefix | continue |
| c → a → d | no child `d` | abandon |
| c → a → r | `car` ends here | report `car`, continue |
| c → a → r → s | `cars` ends here, no children | report `cars`; prune `s` on the way back |
| c → a → r → o | no child `o` | abandon |
| c → a (right) → r | `car` already reported; only `t` left below `r` | nothing new |
| c → a (right) → t | `cat` ends here | report `cat`; prune `t` |

Later starts find `dog` from the `d` and `rod` from the `r`. The `s` start dies at its second letter (no `a` touches it), and the others die at their first, since no word begins with `a`, `t`, `o` or `g`.

Three details make it correct and fast:

- **Mark the cell** as used while it is on the current path (overwrite it with `#`), and restore it when backtracking, so a word can't reuse a cell.
- **Unset `end` after reporting** a word, so a word reachable along two paths is reported once.
- **Prune finished branches.** After returning from a child, if it has no children and no `end` left, delete it from its parent. Later searches stop exploring words that are all found.

```python
import random


class TrieNode:
    def __init__(self):
        self.children = {}
        self.word = None  # the word ending here, if any


def find_words(grid, words):
    root = TrieNode()
    for w in words:
        node = root
        for ch in w:
            node = node.children.setdefault(ch, TrieNode())
        node.word = w
    rows, cols = len(grid), len(grid[0]) if grid else 0
    board = [list(row) for row in grid]
    found = []

    def go(r, c, parent):
        ch = board[r][c]
        node = parent.children.get(ch)
        if node is None:
            return
        if node.word is not None:
            found.append(node.word)
            node.word = None  # report once
        board[r][c] = "#"  # on the current path
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != "#":
                go(nr, nc, node)
        board[r][c] = ch
        if not node.children and node.word is None:
            del parent.children[ch]  # every word below is found

    for r in range(rows):
        for c in range(cols):
            go(r, c, root)
    return sorted(found)


def exists(grid, word):
    """Classic single-word search, the brute force."""
    rows, cols = len(grid), len(grid[0]) if grid else 0

    def go(r, c, i, used):
        if not (0 <= r < rows and 0 <= c < cols) or (r, c) in used or grid[r][c] != word[i]:
            return False
        if i == len(word) - 1:
            return True
        used.add((r, c))
        ok = any(go(r + dr, c + dc, i + 1, used) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        used.discard((r, c))
        return ok

    return bool(word) and any(go(r, c, 0, set()) for r in range(rows) for c in range(cols))


def main():
    grid = ["cat", "ars", "dog"]
    words = ["car", "cars", "cart", "cat", "dog", "rod", "sad"]
    assert find_words(grid, words) == ["car", "cars", "cat", "dog", "rod"]
    assert find_words(["aa"], ["aaa", "a", "aa"]) == ["a", "aa"]  # cells not reused
    assert find_words([], ["a"]) == []

    rng = random.Random(2)
    for _ in range(300):
        r, c = rng.randint(1, 4), rng.randint(1, 4)
        grid = ["".join(rng.choice("abc") for _ in range(c)) for _ in range(r)]
        words = list({"".join(rng.choice("abc") for _ in range(rng.randint(1, 6)))
                      for _ in range(15)})
        assert find_words(grid, words) == sorted(w for w in words if exists(grid, w))


if __name__ == "__main__":
    main()
```

**Time:** building the trie is O(total letters). The search starts from each of the `R·C` cells and follows at most `4 · 3^(L−1)` paths of length up to `L`, the longest word, but trie pruning cuts almost all of them in practice. **Space:** O(total letters) for the trie, O(L) for the recursion.

## 4. Representation and other tries

- **Dictionary or array.** A `dict` of children stores only the letters present. A fixed array of 26 slots (`children[ord(ch) − ord('a')]`) is faster in lower-level languages and gives the children in alphabetical order for free, at the cost of 26 slots per node. In Python the dictionary is usually the better choice; iterate `sorted(node.children)` when order matters, as in autocomplete suggestions listed alphabetically.
- **Binary tries.** Store numbers as bit strings, highest bit first, with two children per node. Walking toward the opposite bit at each level finds the number with the largest XOR against a query: [XOR](../11-bit-manipulation/03-xor.md#7-maximum-xor-of-two-numbers).
- **Compressed tries** (radix trees) merge chains of single-child nodes into one edge labeled with a string, which saves memory for long, sparse keys such as URLs.
- **Suffix structures.** Inserting every suffix of a string into a trie answers "is `p` a substring?" in O(|p|), but costs O(n²) nodes; suffix arrays and suffix automata do it in O(n) and are beyond this folder.

## 5. Summary

| Operation | How | Cost |
|---|---|---|
| Insert | walk letters, create missing children, mark the end | O(L) |
| Search word | walk; must end on a marked node | O(L) |
| Starts with / count prefix | walk; `passes` at the last node | O(L) |
| Delete | check it exists, decrement, cut the first branch that drops to 0 | O(L) |
| Wildcard `.` | try every child at a `.` | up to O(trie size) |
| Many words on a grid | one DFS per start cell, walking the trie; mark, unset, prune | far below one search per word |

## 6. Pitfalls and practice

1. **No end marker.** `search("ca")` returns true because the path exists (§1).
2. **Deleting a word that isn't there** and corrupting the counts (§2).
3. **Cutting a branch that another word still uses.** Cut only when `passes` reaches 0 (§2).
4. **Reporting a grid word twice.** Unset its `end` after the first find (§3).
5. **Forgetting to restore a marked cell** after backtracking (§3).

Practice: implement trie (prefix tree); implement trie II (count words and prefixes, erase); design add and search words data structure; replace words; longest word in dictionary; search suggestions system; word search I and II; maximum XOR of two numbers in an array; palindrome pairs.

Next: [Balanced Trees](06-balanced-trees.md).
