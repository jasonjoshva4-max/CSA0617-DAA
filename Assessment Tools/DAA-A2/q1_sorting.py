"""Q1 - Selection, Bubble and Insertion Sort under different data conditions.

Context: orders in a fulfilment centre are arranged by dispatch priority score (ascending).
Every algorithm counts
  comparisons : key comparisons between two priority scores
  swaps       : exchanges of two elements (selection, bubble)
  shifts      : one element moved one place right (insertion)
  writes      : array element writes (a swap writes 2 slots, a shift writes 1, placing the key writes 1)
Time is measured as well, but the counts are the primary evidence.
"""
import random

import common as C


# ---------------------------------------------------------------------------- algorithms
def selection_sort(data):
    a = list(data)
    n = len(a)
    comps = swaps = writes = 0
    for i in range(n - 1):
        m = i                                   # position of the smallest score seen so far
        for j in range(i + 1, n):
            comps += 1
            if a[j] < a[m]:
                m = j
        if m != i:                              # one swap per pass at most
            a[i], a[m] = a[m], a[i]
            swaps += 1
            writes += 2
    return a, {"comparisons": comps, "moves": swaps, "writes": writes, "passes": max(n - 1, 0)}


def bubble_sort(data):
    """Bubble sort with the early-exit flag: stop after a pass that made no swap."""
    a = list(data)
    n = len(a)
    comps = swaps = writes = passes = 0
    for i in range(n - 1):
        passes += 1
        swapped = False
        for j in range(n - 1 - i):              # the last i elements are already in place
            comps += 1
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swaps += 1
                writes += 2
                swapped = True
        if not swapped:
            break
    return a, {"comparisons": comps, "moves": swaps, "writes": writes, "passes": passes}


def insertion_sort(data):
    a = list(data)
    n = len(a)
    comps = shifts = writes = 0
    for i in range(1, n):
        key = a[i]
        j = i - 1
        while j >= 0:
            comps += 1
            if a[j] > key:                      # larger element moves one place right
                a[j + 1] = a[j]
                shifts += 1
                writes += 1
                j -= 1
            else:
                break
        if j + 1 != i:                          # key only written back if it actually moved
            a[j + 1] = key
            writes += 1
    return a, {"comparisons": comps, "moves": shifts, "writes": writes, "passes": max(n - 1, 0)}


ALGORITHMS = [("Selection", selection_sort), ("Bubble", bubble_sort), ("Insertion", insertion_sort)]


def inversions(a):
    """Number of pairs (i < j) with a[i] > a[j], counted independently by merge sort.
    Theory: bubble-sort swaps = insertion-sort shifts = inversions."""
    def sort_count(x):
        if len(x) <= 1:
            return x, 0
        mid = len(x) // 2
        left, cl = sort_count(x[:mid])
        right, cr = sort_count(x[mid:])
        merged, c, i, j = [], cl + cr, 0, 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i]); i += 1
            else:
                merged.append(right[j]); j += 1
                c += len(left) - i
        merged += left[i:] + right[j:]
        return merged, c
    return sort_count(list(a))[1]


# ---------------------------------------------------------------------------- datasets
def scores(n, rng):
    """n distinct dispatch priority scores between 1 and 1,000,000 (distinct, so that every
    inversion count in the theory table is exact)."""
    return rng.sample(range(1, 1_000_001), n)


def make_datasets(n, rng):
    base = sorted(scores(n, rng))
    turtle = base[1:] + base[:1]                # sorted, but the most urgent order sits at the very end
    shuffled = list(base)
    rng.shuffle(shuffled)
    return [
        ("D1 already sorted", "designed pair (best case)", base),
        ("D2 reverse sorted", "designed pair (worst case)", base[::-1]),
        ("D3 turtle (min at end)", "own edge case", turtle),
        ("D4 random order", "supporting", shuffled),
        ("D5 95% sorted + 5% batch", "decision scenario", batch_dataset(n, 0.05, rng)),
    ]


def batch_dataset(n, fraction, rng):
    """Sorted existing orders followed by a newly arrived batch (fraction of n) in arrival order."""
    k = max(1, round(fraction * n))
    s = scores(n, rng)
    return sorted(s[k:]) + s[:k]


# ---------------------------------------------------------------------------- experiments
def run_one(name, fn, data):
    t, (out, st) = C.time_it(lambda: fn(data), min_seconds=0.05)
    assert out == sorted(data), f"{name} sort produced a wrong order"
    st["time_ms"] = t * 1000
    return st


def prediction_table(n):
    C.section(f"Theory written BEFORE running (n = {n})")
    half, quarter = n * (n - 1) // 2, n * (n - 1) // 4
    rows = [
        ("Selection", "sorted", half, 0, "always scans the whole unsorted part"),
        ("Selection", "reverse", half, n // 2, "same comparisons; ~n/2 swaps"),
        ("Selection", "random", half, n - 1, "same comparisons; <= n-1 swaps"),
        ("Bubble", "sorted", n - 1, 0, "1 pass, no swap -> early exit"),
        ("Bubble", "reverse", half, half, "every pair is an inversion"),
        ("Bubble", "random", "~" + C.fmt(half), "~" + C.fmt(quarter), "swaps = inversions ~ n(n-1)/4"),
        ("Insertion", "sorted", n - 1, 0, "each key compared once, never moves"),
        ("Insertion", "reverse", half, half, "each key moves to the front"),
        ("Insertion", "random", "~" + C.fmt(quarter + n - 1), "~" + C.fmt(quarter), "shifts = inversions"),
    ]
    C.table(["algorithm", "input", "comparisons", "swaps/shifts", "reason"], rows)


def main():
    C.banner("Q1 Sorting under different data conditions")
    rng = random.Random(C.seed(1))
    n = 500 if C.QUICK else 1000
    prediction_table(n)

    # ---- main experiment: three designed conditions + two supporting ones
    C.section(f"Experiment 1: designed datasets, n = {n}")
    datasets = make_datasets(n, rng)
    C.save_data("q1_datasets.csv", ["index"] + [d[0] for d in datasets],
                [[i] + [d[2][i] for d in datasets] for i in range(n)])
    rows = []
    for dname, role, data in datasets:
        inv = inversions(data)
        for aname, fn in ALGORITHMS:
            st = run_one(aname, fn, data)
            rows.append([dname, role, n, inv, aname, st["comparisons"], st["moves"], st["writes"],
                         st["passes"], round(st["time_ms"], 4)])
    C.table(["dataset", "role", "n", "inversions", "algorithm", "comparisons", "swaps/shifts", "writes",
             "passes", "time_ms"], rows)
    C.save_csv("q1_main.csv", ["dataset", "role", "n", "inversions", "algorithm", "comparisons",
                               "swaps_or_shifts", "writes", "passes", "time_ms"], rows)
    ok = all(r[6] == r[3] for r in rows if r[4] in ("Bubble", "Insertion"))
    print(f"\n  Check: bubble swaps = insertion shifts = inversions on every dataset -> {'PASS' if ok else 'FAIL'}")

    # ---- growth with n
    sizes = [250, 500, 1000] if C.QUICK else [250, 500, 1000, 2000]
    C.section("Experiment 2: growth with n (random, already sorted, 95% sorted + 5% batch)")
    grow = []
    for size in sizes:
        r2 = random.Random(C.seed(100 + size))
        base = scores(size, r2)
        for dname, data in (("random", base), ("already sorted", sorted(base)),
                            ("95% sorted + 5% batch", batch_dataset(size, 0.05, r2))):
            for aname, fn in ALGORITHMS:
                st = run_one(aname, fn, data)
                grow.append([dname, size, aname, st["comparisons"], st["moves"], round(st["time_ms"], 4)])
    C.table(["dataset", "n", "algorithm", "comparisons", "swaps/shifts", "time_ms"], grow)
    C.save_csv("q1_growth.csv", ["dataset", "n", "algorithm", "comparisons", "swaps_or_shifts", "time_ms"], grow)

    # ---- design decision: how big may the new batch be?
    C.section(f"Experiment 3: design decision - sorted orders + new batch of size k, n = {n}")
    batch_rows = []
    for frac in (0.01, 0.02, 0.05, 0.10, 0.20, 0.50):
        data = batch_dataset(n, frac, random.Random(C.seed(200 + int(frac * 100))))
        for aname, fn in ALGORITHMS:
            st = run_one(aname, fn, data)
            batch_rows.append([f"{frac:.0%}", n, aname, st["comparisons"], st["moves"], st["writes"],
                               st["passes"], round(st["time_ms"], 4)])
    C.table(["new batch", "n", "algorithm", "comparisons", "swaps/shifts", "writes", "passes", "time_ms"],
            batch_rows)
    C.save_csv("q1_batch_sweep.csv", ["batch_fraction", "n", "algorithm", "comparisons", "swaps_or_shifts",
                                      "writes", "passes", "time_ms"], batch_rows)

    plots(rows, grow, batch_rows, n)


def plots(rows, grow, batch_rows, n):
    plt = C.pyplot()
    if not plt:
        return
    colours = {"Selection": C.BLUE, "Bubble": C.ORANGE, "Insertion": C.AQUA}
    style = {"Selection": dict(marker="o", ls="-", ms=8), "Bubble": dict(marker="s", ls="--", ms=5),
             "Insertion": dict(marker="^", ls="-", ms=6)}
    names = list(dict.fromkeys(r[0] for r in rows))

    for col, label, fname in ((5, "key comparisons", "q1_comparisons.png"), (6, "swaps / shifts", "q1_moves.png")):
        fig, ax = plt.subplots(figsize=(9, 4.2))
        w = 0.26
        for k, (aname, _) in enumerate(ALGORITHMS):
            vals = [next(r[col] for r in rows if r[0] == d and r[4] == aname) for d in names]
            xs = [i + (k - 1) * w for i in range(len(names))]
            ax.bar(xs, [v if v > 0 else float("nan") for v in vals], w, label=aname, color=colours[aname])
            for x, v in zip(xs, vals):
                ax.text(x, max(v, 1) * 1.15, C.fmt(v), ha="center", va="bottom", fontsize=6.5, rotation=90)
        ax.set_yscale("log")
        ax.set_ylim(0.8, max(r[col] for r in rows) * 40)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels([d.replace(" (", "\n(").replace(" + ", "\n+ ") for d in names], fontsize=8)
        ax.set_ylabel(f"{label} (log scale)")
        ax.set_title(f"Q1: {label} per dataset, n = {n}   [{C.who()}]", fontsize=10)
        ax.legend(ncol=3, loc="upper left")
        C.save_fig(plt, fig, fname)

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, dname in zip(axes, ("random", "already sorted", "95% sorted + 5% batch")):
        for aname, _ in ALGORITHMS:
            pts = [(r[1], r[3]) for r in grow if r[0] == dname and r[2] == aname]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=colours[aname], label=aname, **style[aname])
        C.log_xticks(ax, sorted(set(r[1] for r in grow)))
        ax.set_yscale("log")
        ax.set_title(dname, fontsize=10)
        ax.set_xlabel("n (log scale)")
    axes[0].set_ylabel("key comparisons (log scale)")
    axes[0].legend()
    fig.suptitle(f"Q1: comparisons vs n (dashed line drawn on top where two algorithms coincide)   [{C.who()}]",
                 fontsize=10)
    C.save_fig(plt, fig, "q1_growth.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    fr = list(dict.fromkeys(r[0] for r in batch_rows))
    for aname, _ in ALGORITHMS:
        ax.plot(fr, [next(r[3] for r in batch_rows if r[0] == f and r[2] == aname) for f in fr],
                color=colours[aname], label=aname, **style[aname])
    ax.set_yscale("log")
    ax.set_xlabel("size of the newly added batch (share of n)")
    ax.set_ylabel("key comparisons (log scale)")
    ax.set_title(f"Q1: sorted orders + new batch, n = {n}   [{C.who()}]", fontsize=10)
    ax.legend()
    C.save_fig(plt, fig, "q1_batch_sweep.png")


if __name__ == "__main__":
    C.run(main, "q1")
