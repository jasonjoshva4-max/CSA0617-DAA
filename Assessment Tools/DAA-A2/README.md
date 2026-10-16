# DAA Assignment 2 (CO2): Brute Force and Exhaustive Search

Python programs for Q1 to Q7. Each program prints its predictions, runs the experiments, checks its own answers against an independent method, and saves the evidence the submission asks for:

- `results/*.csv` holds the raw experimental data (measurements).
- `results/data/` holds the input datasets that were used.
- `results/graphs/*.png` holds the graphs.
- `results/qX_console.txt` holds the full console output of each question.

Operation counts are the primary evidence. Times are reported as extra evidence only, and they include the small overhead of the counters.

| File | Question | What is counted |
|---|---|---|
| `q1_sorting.py` | Q1: selection, bubble and insertion sort | key comparisons, swaps/shifts, element writes, passes |
| `q2_sequential_search.py` | Q2: tool-tracking lookups | key comparisons per lookup |
| `q3_string_matching.py` | Q3: log signature screening | character comparisons |
| `q4_closest_pair.py` | Q4: drone collision risk | pairs examined, distance calculations |
| `q5_convex_hull.py` | Q5: reserve boundary | pairs examined, orientation (cross-product) tests |
| `q6_knapsack_exhaustive.py` | Q6: airlift exhaustive search | subsets, feasible subsets, item checks, additions |
| `q7_redesign.py` | Q7: diagnose and redesign Q6 | nodes, candidate loads, bound steps, total operations |

`common.py` holds the shared helpers (banner, seed, tables, CSV, graphs). `run_all.py` runs everything.

---

## 1. Install Python and matplotlib (Windows, once)

**Option A: the MSYS2 UCRT64 terminal you already use for A1.** Use a hotspot if the college network is slow.

```
pacman -S --needed mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-matplotlib
python --version
```

**Option B: python.org.**

1. Download Python 3 from https://www.python.org/downloads/ and run the installer.
2. Tick **"Add python.exe to PATH"** on the first screen.
3. Open PowerShell and run:

```
py -m pip install matplotlib
py --version
```

Use the same command (`python` in MSYS2, `py` in PowerShell) everywhere below. Without matplotlib, everything still runs, but no graphs are drawn.

## 2. Put your details in `config.py`

```
REG_NO = 192511209          # your registration number, digits only
NAME = "JASON JOSHVA M J"   # your name in quotes
```

The programs refuse to run until this is set. The last 4 digits of the reg no seed every random dataset, so your data and results are your own. Every console screen and every graph shows your reg no, your name and the run time.

## 3. Run

In the terminal, go to this folder. For example, in MSYS2: `cd /c/Users/<you>/Downloads/DAA-A2`

```
python run_all.py --quick     # trial run with smaller sizes, about 20 s
python run_all.py             # the real run, about 1-2 minutes
```

You can also run a single question, for example `python q5_convex_hull.py`. Use the results of the **full** run (without `--quick`) in your report. Take screenshots of each question's output with the banner visible.

## 4. Values I chose, which you must justify (all can be changed at the top of the file)

| Where | Value | Starting point for the justification |
|---|---|---|
| Q1 | n = 1000, new batch = 5% | brief: 95% already in priority order plus small batches of new orders |
| Q2 `LATENCY_BUDGET_S` | 1 ms worst-case lookup | the search is one small part of a request that should feel instant (< 100 ms) |
| Q2 `CPU_SHARE` | 5% of one core | the lookup service shares the machine with other work |
| Q2 `HIT_RATE` | 90% | most questions are about tools that really are issued |
| Q2 hangar load | 300 tools, 120 lookups/hour | busy-shift estimate; the 20-facility case multiplies both by 20 |
| Q4 `RESPONSE_BUDGET_S` | 100 ms | positions arrive about once per second; the check must leave time to react |
| Q6 `DEADLINE_S` | 1 s | the planner re-plans interactively while packages are staged |
| Q6 `CAPACITY_SHARE` | 40% of total weight | keeps every instance size non-trivial (neither "take all" nor "take none") |

## 5. What each program does

**Q1** prints the theory table first. It then runs three designed datasets:

- D1 already sorted and D2 reverse sorted (the contrasting pair).
- D3 "turtle": sorted, with the most urgent order at the very end (the edge case).

There are two supporting datasets: random, and 95% sorted + 5% new batch. The program checks that bubble-sort swaps = insertion-sort shifts = inversions (counted independently). It also runs a growth test, and a sweep over new-batch size for the design decision.

**Q2** answers "Who currently has Tool T-184?". It then runs:

- successful searches at the first, 25%, middle, 75% and last positions;
- unsuccessful searches;
- list sizes of 100 to 100,000 (averaged over many lookups);
- an operating boundary (largest n for each lookup rate under the latency and load rules);
- the 1-hangar vs 20-facility re-evaluation, with a hash index for comparison.

**Q3** prints a prediction before each test, from a character-frequency model and, where useful, a structure-aware count. The designed tests are:

- T1: little work.
- T2: engineered worst case `AAAA…` / `AAA…AB`.
- T3: own test, a NOP-sled signature in a packet hex dump.

There are three supporting tests: S1 and S2 use the same pattern on an attack log and a normal log; S3 uses random text with the same n and m as T2. Two sweeps vary the pattern length m and the alphabet size. Every match position is verified with Python's `str.startswith`.

**Q4** starts with a hand-checkable 5-drone test that lists all 10 pairs, plus edge cases. It then runs:

- growth for n = 125 to 4000, with a doubling-ratio check;
- the same n in different arrangements (the work is input-insensitive);
- the share of pairs that could have been rejected from the x-coordinate alone (waste evidence);
- the response-time boundary.

**Q5** removes duplicates and then applies the pair test with a cross product. Collinear points must lie between the two endpoints. It builds the boundary by walking the accepted edges and verifies the result against an independent monotone-chain hull. The tests are:

- A: random stations.
- B: designed challenge with fence stations, duplicates, an interior collinear line, and one station 1 m outside the fence. The run also shows how the naive rule fails on this set.
- C: all stations collinear.

There are also edge cases, a growth test with full vs early-exit counts, and the plots.

**Q6** lists all 16 subsets of a 4-package instance (where greedy by value/kg is not optimal) and checks every optimum with dynamic programming. It runs growth for n = 8 to 20 on one manifest (bigger n = the same packages plus more) and makes the deployment decision from the measured cost per item check.

**Q7** works through the parts of the question:

- A: diagnosis numbers from the original (infeasible share, repeated additions).
- B: measurable objectives.
- D: printed predictions.
- E: V0 (original) vs V1 (reuse sums) vs V2 (+ capacity pruning) vs V3 (+ value/kg sort and an optimistic bound), on the same instances, with the same optimum checked; then larger airlifts up to 80 packages.
- F: a limitation test on strongly correlated packages (value ≈ weight), where the bound is weak.

Part C (the design and pseudocode) belongs in the report.

## 6. Before the viva

Run it yourself, read each program next to its output, and make sure you can explain these points:

- Why insertion sort wins on the 95% data while bubble sort does not (turtles).
- Why the unsuccessful search always costs n.
- Why T3's frequency prediction was wrong.
- Why n(n−1)/2 and n(n−1)(n−2)/2 hold.
- Why collinear points need the "between" rule.
- Why 2ⁿ doubles with every package.
- Why the bound in V3 is safe (it never cuts off the true optimum).
