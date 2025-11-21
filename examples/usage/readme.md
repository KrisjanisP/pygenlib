# LIO task "Radiotorņi" test generation

## 1. Testlib.h generator

The params to the generator are:
1. `n`: no of vertices
2. `l`: min assigned radio tower frequency
3. `r`: max assigned radio tower frequency
4. `t`: type of tree ("star", "line", "random", "binary")
5. `w`: way to assign frequencies ("random", "walk")
6. `L`: lower bound on radio tower frequency
7. `R`: upper bound on radio tower frequency

### 1.1 Tree generation

Generator generates 4 different kinds of trees:
- "star": a tree with one internal node and $n-1$ leaves
- "line": a tree with $n$ vertices and $n-1$ edges
- "random": a random tree
- "binary": a (possibly non-full) binary tree

It then shuffles the vertices.

### 1.2 Frequency assignment

There are 3 ways to assign frequencies:
- random in range [l, r]
- incremental walk

"Incremental walk" algorithm:
1. start from a random vertex with random frequency
2. start by either incrementing or decrementing (random)
3. when reached the boundary, start going in the other direction
4. repeat until all vertices are visited

## 2. Task subtasks

1. Examples given in the statement (hand-crafted)
2. N <= 10
3. L = K + 1
4. No tower is connected to more than 2 others
5. All frequencies fi are the same
6. No additional restrictions


testgroup 0 is for statement examples
this task won't have testgroup 1