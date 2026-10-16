"""Shared helpers: banner, seeded random numbers, timing, tables, CSV files and plotting."""
import csv
import datetime
import os
import sys
import time

from config import NAME, REG_NO

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
GRAPHS = os.path.join(RESULTS, "graphs")
QUICK = "--quick" in sys.argv          # smaller sizes, for a fast trial run

# one fixed colour per series, used in every graph
BLUE, ORANGE, AQUA, YELLOW, GREY, RED = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#8a8984", "#e34948"


def check_config():
    if REG_NO == 0 or NAME == "YOUR NAME":
        print("\n  Open config.py, set REG_NO and NAME, save, and run again.\n")
        sys.exit(1)


def seed(offset=0):
    """Personal seed: last 4 digits of the reg no, plus an offset per experiment."""
    return (REG_NO % 10000) * 1000 + offset


def banner(title):
    check_config()
    line = "=" * 96
    print(line)
    print(f" DAA Assignment 2 (CO2)  |  {title}")
    print(f" Reg No: {REG_NO}  |  Name: {NAME}  |  Seed: {REG_NO % 10000:04d} (last 4 digits of reg no)")
    print(f" Run at: {datetime.datetime.now():%Y-%m-%d %H:%M:%S} (system local time)  |  Python {sys.version.split()[0]}")
    print(line)


def section(title):
    print(f"\n--- {title} " + "-" * max(4, 90 - len(title)))


def fmt(v):
    if isinstance(v, float):
        if v == 0:
            return "0"
        if abs(v) >= 1000:
            return f"{v:,.1f}"
        if abs(v) >= 1:
            return f"{v:.3f}"
        return f"{v:.4g}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


def table(headers, rows):
    cells = [[fmt(c) for c in r] for r in rows]
    widths = [max(len(str(h)), *(len(r[i]) for r in cells)) if cells else len(str(h)) for i, h in enumerate(headers)]
    print("  " + "  ".join(str(h).ljust(w) for h, w in zip(headers, widths)))
    print("  " + "  ".join("-" * w for w in widths))
    for r in cells:
        print("  " + "  ".join(c.rjust(w) if _num(c) else c.ljust(w) for c, w in zip(r, widths)))


def _num(s):
    s = s.lstrip("~")
    return s.replace(",", "").replace(".", "", 1).replace("-", "", 1).replace("e", "", 1).replace("+", "").isdigit()


def save_csv(name, headers, rows):
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, name)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["reg_no", "name"] + list(headers))
        for r in rows:
            w.writerow([REG_NO, NAME] + list(r))
    print(f"  [saved {os.path.relpath(path, HERE)}]")


def time_it(fn, min_seconds=0.1, max_reps=1000):
    """Run fn() repeatedly until min_seconds have passed (at least once).
    Returns (average seconds per run, result of the last run)."""
    reps, start = 0, time.perf_counter()
    while True:
        result = fn()
        reps += 1
        el = time.perf_counter() - start
        if el >= min_seconds or reps >= max_reps:
            return el / reps, result


class _Tee:
    """Writes everything printed to the screen into a text file as well."""
    def __init__(self, screen, path):
        self.screen, self.file = screen, open(path, "w", encoding="utf-8")

    def write(self, s):
        self.screen.write(s)
        self.file.write(s)

    def flush(self):
        self.screen.flush()
        self.file.flush()


def run(main, log_name):
    """Run one question's main(), saving the console output to results/<log_name>_console.txt."""
    os.makedirs(RESULTS, exist_ok=True)
    screen = sys.stdout
    sys.stdout = _Tee(screen, os.path.join(RESULTS, f"{log_name}_console.txt"))
    t0 = time.perf_counter()
    try:
        main()
        print(f"\n  [{log_name} finished in {time.perf_counter() - t0:.1f} s]\n")
    finally:
        sys.stdout.file.close()
        sys.stdout = screen


def save_data(name, headers, rows):
    """Save an input dataset (so the raw test data is part of the submission)."""
    d = os.path.join(RESULTS, "data")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def pyplot():
    """matplotlib if installed (graphs are skipped with a note if it is not)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [matplotlib not installed - graphs skipped. Install with:  pip install matplotlib]")
        return None
    plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 160, "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.grid": True, "grid.color": "#e4e3df", "axes.axisbelow": True,
                         "legend.frameon": False, "lines.linewidth": 2, "lines.markersize": 6})
    return plt


def save_fig(plt, fig, name, rect=None):
    os.makedirs(GRAPHS, exist_ok=True)
    path = os.path.join(GRAPHS, name)
    fig.tight_layout(rect=rect) if rect else fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print(f"  [graph {os.path.relpath(path, HERE)}]")


def log_xticks(ax, values):
    """Log x-axis with plain tick labels exactly at the measured sizes (no overlapping 10^x labels)."""
    ax.set_xscale("log")
    ax.set_xticks(values)
    ax.set_xticklabels([f"{v:,}" for v in values])
    ax.xaxis.set_minor_locator(__import__("matplotlib").ticker.NullLocator())


def who():
    return f"Reg No {REG_NO} | {NAME}"
