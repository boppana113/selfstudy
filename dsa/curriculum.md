# DSA Curriculum

Goal: interview-ready for MAANG coding rounds by the time loops happen (Jan warm-ups, MAANG Feb–Mar 2027). Language: Python.

**Interview-ready means:** an unseen medium solved in ≤ 25 min while talking, clean code, correct complexity, hand-traced before running, on ~70% of tries. Plus the common hards.

Problem lists are a NeetCode-150-style core, picked for how often they show up in interviews. ✓ = accepted on LeetCode before this track started (July 2026). Having solved one in July doesn't mean you can do it cold now; those problems are good cold re-solves.

## Stages

| # | Slug | Week | Pattern triggers (say these out loud) |
|---|---|---|---|
| 1 | arrays-hashing | 1 | "have I seen X before?", counts, grouping → hash map / set |
| 2 | two-pointers | 1 | sorted input, pairs/triplets, palindromes, in-place → two pointers |
| 3 | sliding-window | 2 | contiguous subarray/substring + "longest/shortest/at most k" → window |
| 4 | stack | 2 | matching brackets, "next greater/smaller" → (monotonic) stack |
| 5 | binary-search | 2–3 | sorted / rotated, or "minimum X such that feasible" → binary search on the answer |
| 6 | linked-list | 3 | in-place reorder, cycle, kth from end → fast/slow pointers, dummy head |
| 7 | trees | 4 | recursion on subtrees, level order → DFS returning values / BFS with queue |
| 8 | heap | 4 | top k, kth largest, merge k, running median → heap |
| 9 | graphs | 5 | grid, dependencies, connectivity, shortest path → BFS/DFS, topo sort, union-find, Dijkstra |
| 10 | intervals-greedy | 5 | overlapping ranges, scheduling → sort by start/end; local choice provably safe → greedy |
| 11 | backtracking | 6 | "all combinations / permutations / subsets" → choose, explore, un-choose |
| 12 | dp | 6–7 | "count ways / min cost / max value" with overlapping subproblems → state, recurrence, base case |
| 13 | tries | 7 | prefix lookups over many words → trie |
| — | mocks | 8+ | mixed timed problems, company-format mocks, human mocks |

## Problems per stage

**1 arrays-hashing:** Valid Anagram ✓, Two Sum ✓, Group Anagrams ✓, Top K Frequent Elements ✓, Encode and Decode Strings ✓, Product of Array Except Self ✓, Longest Consecutive Sequence ✓, Valid Sudoku, Subarray Sum Equals K, Contains Duplicate II ✓

**2 two-pointers:** Valid Palindrome, Two Sum II, 3Sum ✓, Container With Most Water, Trapping Rain Water (H)

**3 sliding-window:** Best Time to Buy and Sell Stock, Longest Substring Without Repeating Characters ✓, Longest Repeating Character Replacement, Permutation in String, Minimum Window Substring (H), Sliding Window Maximum (H)

**4 stack:** Valid Parentheses, Min Stack, Evaluate Reverse Polish Notation, Daily Temperatures ✓, Next Greater Element II ✓, Car Fleet, Largest Rectangle in Histogram (H)

**5 binary-search:** Binary Search, Search a 2D Matrix, Koko Eating Bananas, Find Minimum in Rotated Sorted Array, Search in Rotated Sorted Array, Time Based Key-Value Store, Median of Two Sorted Arrays (H)

**6 linked-list:** Reverse Linked List, Merge Two Sorted Lists, Linked List Cycle, Reorder List, Remove Nth Node From End, Add Two Numbers ✓, Copy List with Random Pointer, LRU Cache, Merge k Sorted Lists (H)

**7 trees:** Invert Binary Tree, Maximum Depth, Diameter of Binary Tree, Balanced Binary Tree ✓, Subtree of Another Tree, Lowest Common Ancestor of a BST, Level Order Traversal, Right Side View, Validate BST, Kth Smallest in a BST, Construct Tree from Preorder and Inorder, Binary Tree Maximum Path Sum (H), Serialize and Deserialize Binary Tree (H)

**8 heap:** Kth Largest Element in a Stream ✓, Last Stone Weight, K Closest Points to Origin, Kth Largest Element in an Array, Task Scheduler, Find Median from Data Stream (H)

**9 graphs:** Number of Islands, Max Area of Island, Clone Graph, Rotting Oranges, Pacific Atlantic Water Flow, Course Schedule, Course Schedule II, Graph Valid Tree, Number of Connected Components, Redundant Connection, Network Delay Time, Word Ladder (H)

**10 intervals-greedy:** Meeting Rooms ✓, Meeting Rooms II, Merge Intervals, Insert Interval, Non-overlapping Intervals, Maximum Subarray ✓, Jump Game, Jump Game II, Gas Station

**11 backtracking:** Subsets, Subsets II, Combination Sum, Permutations, Letter Combinations of a Phone Number, Word Search, Palindrome Partitioning, N-Queens (H)

**12 dp:** Climbing Stairs ✓, House Robber, House Robber II ✓, Coin Change, Decode Ways, Maximum Product Subarray, Word Break, Longest Increasing Subsequence, Unique Paths, Longest Common Subsequence, Partition Equal Subset Sum, Edit Distance (H)

**13 tries:** Implement Trie, Design Add and Search Words, Word Search II (H)

## Rules

- **Stage status:** `not started` → `learning` (pattern guide read, first problems done) → `working` (3 mediums clean) → `ready` (2 unseen mediums in a row, cold, ≤ 25 min, ≤ 1 hint).
- **Move on by week, not by mastery.** The calendar is fixed. A stage that isn't `ready` by its week stays in the re-solve queue; don't stall the plan for it.
- **Order can bend.** If the pretest shows a stage is already `ready`, skip ahead and spend the week on the weakest stage.
- **Weeks 1–3 lean on volume** (easier patterns, where you're thinnest on speed). **Weeks 6–7 lean on DP**, where the Georgia Tech algorithms course gives you a head start.
- **From week 5:** one human mock a week (Pramp or interviewing.io).

## Company formats (for `/dsa mock`)

| Company | Format | What's under pressure |
|---|---|---|
| meta | 2 mediums in 40 min, no time to polish | speed, getting to optimal fast |
| google | 1 open-ended problem (45 min) + 1–2 twists | clarifying questions, optimizing step by step, follow-up twists |
| amazon | 1 leadership-principle story (~10 min) + 1 medium (35 min) | clean, readable code; the behavioral answer in STAR form |
| generic | 1 medium + 1 follow-up (45 min) | default |
