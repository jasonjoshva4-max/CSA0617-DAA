"""
Draws every graph for the report from YOUR OWN result files:
    results/results.csv   (written by  daa bench ...)
    results/task12.csv    (written by  daa task12)
Output: results/graphs/*.png

Run from the repository root:   python src/plot_results.py
Needs matplotlib:               pip install matplotlib
"""
import csv
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = "results"
OUT = os.path.join(RES, "graphs")

# One fixed colour per algorithm (validated colour-blind-safe set), same in every graph.
ALGOS = ["Linear search", "Binary search", "Hash table"]
COLOR = {"Linear search": "#2a78d6", "Binary search": "#eb6834", "Hash table": "#1baf7a"}
LABEL = {"Linear search": "Linear (iterative)", "Binary search": "Binary (recursive)",
         "Hash table": "Hash table (chaining)"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 160, "font.size": 10,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "axes.titlecolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "lines.linewidth": 2, "lines.markersize": 7, "axes.axisbelow": True,
})


def read(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def series(rows, algo, col):
    pts = sorted((int(r["n"]), float(r[col])) for r in rows if r["algorithm"] == algo)
    return [p[0] for p in pts], [p[1] for p in pts]


def who(rows):
    r = rows[0]
    return f"Reg No {r['reg_no']} | {r['name']}"


def num(v):
    return f"{v:,.0f}" if v >= 100 else f"{v:.3g}"


def end_label(ax, x, y, text, color, dy=0):
    ax.annotate(text, (x[-1], y[-1]), xytext=(6, dy), textcoords="offset points",
                color=INK, fontsize=9, va="center")


def save(fig, name):
    fig.tight_layout()
    path = os.path.join(OUT, name)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print("  wrote", path)


def fig_time_per_search(rows):
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    for a in ALGOS:
        x, y = series(rows, a, "us_per_search")
        ax.plot(x, y, marker="o", color=COLOR[a], label=LABEL[a])
        end_label(ax, x, y, f"{num(y[-1])} us", COLOR[a])
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Number of records n (log scale)")
    ax.set_ylabel("Average time per search (microseconds, log scale)")
    ax.set_title(f"Time per search vs n   ({who(rows)})", fontsize=10)
    ax.set_xlim(right=max(series(rows, ALGOS[0], 'us_per_search')[0]) * 4)
    ax.legend(loc="upper left")
    save(fig, "fig9_1_time_per_search.png")


def fig_comparisons(rows):
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    for a in ALGOS:
        x, y = series(rows, a, "avg_comp_all")
        ax.plot(x, y, marker="o", color=COLOR[a], label=LABEL[a])
        end_label(ax, x, y, f"{y[-1]:,.1f}", COLOR[a])
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Number of records n (log scale)")
    ax.set_ylabel("Average key comparisons per search (log scale)")
    ax.set_title(f"Comparisons per search vs n   ({who(rows)})", fontsize=10)
    ax.set_xlim(right=max(series(rows, ALGOS[0], 'avg_comp_all')[0]) * 4)
    ax.legend(loc="upper left")
    save(fig, "fig9_2_comparisons_per_search.png")


def fig_preprocessing(rows):
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    for a in ALGOS[1:]:
        x, y = series(rows, a, "preprocess_ms")
        ax.plot(x, y, marker="o", color=COLOR[a],
                label=LABEL[a] + (" - merge sort" if a == "Binary search" else " - build"))
        end_label(ax, x, y, f"{num(y[-1])} ms", COLOR[a])
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Number of records n (log scale)")
    ax.set_ylabel("Preprocessing time (ms, log scale)")
    ax.set_title(f"Preprocessing cost vs n (linear search needs none)   ({who(rows)})", fontsize=10)
    ax.set_xlim(right=max(series(rows, ALGOS[1], 'preprocess_ms')[0]) * 4)
    ax.legend(loc="upper left")
    save(fig, "fig9_3_preprocessing.png")


def fig_total(rows):
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    q = int(rows[0]["queries"])
    for a in ALGOS:
        x, y = series(rows, a, "total_ms")
        ax.plot(x, y, marker="o", color=COLOR[a], label=LABEL[a])
        end_label(ax, x, y, f"{num(y[-1])} ms", COLOR[a])
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Number of records n (log scale)")
    ax.set_ylabel(f"Preprocessing + {q:,} searches (ms, log scale)")
    ax.set_title(f"Total cost including preprocessing   ({who(rows)})", fontsize=10)
    ax.set_xlim(right=max(series(rows, ALGOS[0], 'total_ms')[0]) * 4)
    ax.legend(loc="upper left")
    save(fig, "fig9_4_total_cost.png")


def fig_theory_vs_experiment(rows):
    """Task 10: measured comparisons vs theory, and measured time vs theory-predicted growth."""
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.2))
    growth = {
        "Linear search": lambda n: 0.75 * n,                       # 50% found (n+1)/2, 50% absent n
        "Binary search": lambda n: math.log2(n + 1) - 0.5,
        "Hash table": lambda n: 1.0,                               # constant for fixed alpha
    }
    for i, a in enumerate(ALGOS):
        x, found = series(rows, a, "avg_comp_found")
        _, absent = series(rows, a, "avg_comp_absent")
        _, tf = series(rows, a, "theory_comp_found")
        _, ta = series(rows, a, "theory_comp_absent")
        ax = axes[0][i]
        ax.plot(x, tf, ls="--", color=INK2, lw=1.5, label="theory")
        ax.plot(x, ta, ls="--", color=INK2, lw=1.5)
        ax.plot(x, found, marker="o", ls="none", color=COLOR[a], label="measured: found")
        ax.plot(x, absent, marker="s", ls="none", mfc="white", mec=COLOR[a], mew=2,
                label="measured: absent")
        ax.set_xscale("log")
        if a == "Linear search":
            ax.set_yscale("log")
        if a == "Hash table":
            ax.set_ylim(0, 2.4)                                    # leave room for the legend
        ax.set_title(LABEL[a] + ": comparisons", fontsize=10)
        ax.set_xlabel("n (log scale)")
        ax.set_ylabel("key comparisons per search")
        ax.legend(fontsize=8, loc="upper left")

        _, t = series(rows, a, "us_per_search")
        g = growth[a]
        pred = [t[0] * g(n) / g(x[0]) for n in x]                  # theory curve anchored at smallest n
        ax = axes[1][i]
        ax.plot(x, pred, ls="--", color=INK2, lw=1.5, label="theory growth (scaled to first point)")
        ax.plot(x, t, marker="o", color=COLOR[a], label="measured time")
        ax.set_xscale("log")
        if a == "Hash table":                                      # constant theory: linear y-axis from 0
            ax.set_ylim(0, max(t) * 1.8)
            ax.set_ylabel("microseconds per search")
        else:
            ax.set_yscale("log")
            ax.set_ylim(top=max(max(t), max(pred)) * 6)
            ax.set_ylabel("microseconds per search (log)")
        ax.set_title(LABEL[a] + ": time", fontsize=10)
        ax.set_xlabel("n (log scale)")
        ax.legend(fontsize=8, loc="upper left")
    fig.suptitle(f"Theory vs experiment   ({who(rows)})", fontsize=11, color=INK)
    save(fig, "fig10_1_theory_vs_experiment.png")


def fig_breakeven(rows):
    """Task 11: total time to answer k searches on the largest n, using measured costs."""
    nmax = max(int(r["n"]) for r in rows)
    pick = {r["algorithm"]: r for r in rows if int(r["n"]) == nmax}
    ks = [10 ** (e / 10) for e in range(0, 61)]                     # 1 .. 1,000,000 searches
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    for a in ALGOS:
        pre = float(pick[a]["preprocess_ms"])
        us = float(pick[a]["us_per_search"])
        y = [pre + k * us / 1000.0 for k in ks]
        ax.plot(ks, y, color=COLOR[a], label=LABEL[a])
        end_label(ax, ks, y, LABEL[a], COLOR[a])
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel(f"Number of searches k on n = {nmax:,} records (log scale)")
    ax.set_ylabel("Total time = preprocessing + k searches (ms, log)")
    ax.set_title(f"Which design is cheapest for k searches?   ({who(rows)})", fontsize=10)
    ax.set_xlim(right=ks[-1] * 60)
    ax.legend(loc="upper left")
    save(fig, "fig11_1_breakeven.png")


def fig_task12(t12):
    if not t12:
        print("  (no results/task12.csv yet - run: daa task12)")
        return
    order = ["Hash table", "Binary search", "Linear search"]
    rows = {r["algorithm"]: r for r in t12}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    vals = [float(rows[a]["cpu_ms_per_hour"]) for a in order]
    bars = ax.barh([LABEL[a] for a in order], vals, color=[COLOR[a] for a in order], height=0.55)
    ax.set_xscale("log")
    ax.invert_yaxis()
    for b, v, a in zip(bars, vals, order):
        tag = " (scaled from sample)" if rows[a]["scaled_from_sample"] == "yes" else ""
        ax.annotate(f" {num(v)} ms{tag}", (v, b.get_y() + b.get_height() / 2), va="center", fontsize=9, color=INK)
    ax.set_xlabel("CPU time for 50,000 searches = one hour of load (ms, log scale)")
    ax.set_title("Hourly search load on 1,000,000 records", fontsize=10)
    ax.set_xlim(right=max(vals) * 40)

    ax = axes[1]
    algos = ["Hash table", "Binary search"]
    inc = [float(rows[a]["update_incremental_ms"]) for a in algos]
    full = [float(rows[a]["update_rebuild_ms"]) for a in algos]
    y = range(len(algos))
    h = 0.36
    b1 = ax.barh([i - h / 2 - 0.01 for i in y], inc, height=h, color=[COLOR[a] for a in algos],
                 label="incremental (insert / merge today's batch)")
    b2 = ax.barh([i + h / 2 + 0.01 for i in y], full, height=h, color="white",
                 edgecolor=[COLOR[a] for a in algos], linewidth=2, hatch="//", label="full rebuild")
    for bars, vals in ((b1, inc), (b2, full)):
        for b, v in zip(bars, vals):
            ax.annotate(f" {num(v)} ms", (v, b.get_y() + b.get_height() / 2), va="center", fontsize=9, color=INK)
    ax.set_yticks(list(y)); ax.set_yticklabels([LABEL[a] for a in algos])
    ax.invert_yaxis()
    ax.set_xlabel("Time to add one day's 10,000 new records (ms)")
    ax.set_title("Daily update cost", fontsize=10)
    ax.set_xlim(right=max(full) * 2.0)
    ax.legend(fontsize=8, loc="upper right")
    r0 = t12[0]
    fig.suptitle(f"Task 12 benchmark   (Reg No {r0['reg_no']} | {r0['name']})", fontsize=11, color=INK)
    save(fig, "fig12_1_task12.png")


def main():
    rows = read(os.path.join(RES, "results.csv"))
    if not rows:
        sys.exit("results/results.csv not found - run  daa bench  first (from the repo root).")
    os.makedirs(OUT, exist_ok=True)
    sizes = sorted({int(r["n"]) for r in rows})
    print("Sizes found in results.csv:", ", ".join(f"{s:,}" for s in sizes))
    fig_time_per_search(rows)
    fig_comparisons(rows)
    fig_preprocessing(rows)
    fig_total(rows)
    fig_theory_vs_experiment(rows)
    fig_breakeven(rows)
    fig_task12(read(os.path.join(RES, "task12.csv")))


if __name__ == "__main__":
    main()
