"""Q6 - Exhaustive search for the humanitarian airlift (0/1 knapsack).

Representation : a candidate load is an n-bit number (mask); bit i = 1 means package i is loaded.
Generation     : mask = 0, 1, 2, ..., 2^n - 1 lists every subset exactly once.
Feasibility    : total weight of the chosen packages <= payload limit.
Evaluation     : total humanitarian value of the chosen packages.
Retention      : keep the feasible load with the highest value seen so far.

Counted: subsets generated, feasible subsets, item checks (bit tests, n per subset),
         additions (weight/value sums), time.
"""
import random

import common as C

DEADLINE_S = 1.0           # loading decision must be ready within 1 s (see README)
CAPACITY_SHARE = 0.4       # payload limit = 40 % of the total weight of the available packages


# ---------------------------------------------------------------------------- algorithm
def exhaustive_knapsack(packages, capacity):
    """packages: list of (id, weight, value). Returns (best value, best weight, chosen ids, counters)."""
    n = len(packages)
    best_value, best_weight, best_mask = -1, 0, 0
    st = {"subsets": 0, "feasible": 0, "item_checks": 0, "additions": 0}
    for mask in range(1 << n):                  # generate every candidate subset
        st["subsets"] += 1
        w = v = 0
        for i in range(n):                      # evaluate it from scratch
            st["item_checks"] += 1
            if mask >> i & 1:
                w += packages[i][1]
                v += packages[i][2]
                st["additions"] += 1
        if w <= capacity:                       # feasibility check
            st["feasible"] += 1
            if v > best_value:                  # retain the best feasible subset
                best_value, best_weight, best_mask = v, w, mask
    chosen = [packages[i][0] for i in range(n) if best_mask >> i & 1]
    return best_value, best_weight, chosen, st


def dp_best_value(packages, capacity):
    """Independent check (dynamic programming over capacities) - used only to verify the optimum."""
    best = [0] * (capacity + 1)
    for _, w, v in packages:
        for c in range(capacity, w - 1, -1):
            if best[c - w] + v > best[c]:
                best[c] = best[c - w] + v
    return best[capacity]


# ---------------------------------------------------------------------------- data
def master_manifest(count=80):
    """All packages that could become available, in arrival order. An instance of size n uses
    the first n of them, so a bigger instance = the same manifest plus extra packages."""
    rng = random.Random(C.seed(6))
    return [(f"P{i + 1:02d}", rng.randint(5, 60), rng.randint(10, 100)) for i in range(count)]


def instance(n, manifest=None):
    pk = (manifest or master_manifest())[:n]
    return pk, int(CAPACITY_SHARE * sum(p[1] for p in pk))


SMALL = [("P1 medical kits", 20, 90), ("P2 drinking water", 25, 70), ("P3 food rations", 15, 50),
         ("P4 shelter tents", 30, 80)]
SMALL_CAP = 50


# ---------------------------------------------------------------------------- experiments
def main():
    C.banner("Q6 Exhaustive search - humanitarian airlift (0/1 knapsack)")

    # ---- correctness on a hand-checkable instance
    C.section(f"Correctness check: 4 packages, payload limit {SMALL_CAP} kg -> 2^4 = 16 subsets")
    for p in SMALL:
        print(f"    {p[0]:<18} weight {p[1]:>3} kg   value {p[2]:>3}   value/kg {p[2] / p[1]:.2f}")
    rows, best_so_far = [], -1
    for mask in range(16):
        ids = [SMALL[i][0].split()[0] for i in range(4) if mask >> i & 1]
        w = sum(SMALL[i][1] for i in range(4) if mask >> i & 1)
        v = sum(SMALL[i][2] for i in range(4) if mask >> i & 1)
        feas = w <= SMALL_CAP
        if feas and v > best_so_far:
            best_so_far = v
        rows.append([format(mask, "04b")[::-1], "{" + ",".join(ids) + "}", w, v, "yes" if feas else "no",
                     best_so_far])
    C.table(["mask (P1..P4)", "packages", "weight", "value", "feasible", "best so far"], rows)
    C.save_csv("q6_small_instance.csv", ["mask_P1_to_P4", "packages", "weight", "value", "feasible", "best_so_far"],
               rows)
    bv, bw, chosen, st = exhaustive_knapsack(SMALL, SMALL_CAP)
    print(f"\n  exhaustive search: value {bv}, weight {bw} kg, load {chosen}, subsets {st['subsets']}, "
          f"feasible {st['feasible']}")
    print(f"  dynamic-programming check: value {dp_best_value(SMALL, SMALL_CAP)} -> "
          f"{'PASS' if dp_best_value(SMALL, SMALL_CAP) == bv else 'FAIL'}")
    room, gv, gl = SMALL_CAP, 0, []
    for p in sorted(SMALL, key=lambda p: p[2] / p[1], reverse=True):
        if p[1] <= room:
            room -= p[1]; gv += p[2]; gl.append(p[0].split()[0])
    print(f"  for comparison, 'best value per kg first' gives {gl} = value {gv} (not optimal)")

    # ---- growth
    sizes = [8, 10, 12, 14, 16] if C.QUICK else [8, 10, 12, 14, 16, 18, 20]
    manifest = master_manifest()
    C.save_data("q6_master_manifest.csv", ["package_id", "weight_kg", "value"], manifest)
    C.section("Prediction before running: candidates = 2^n, item checks = n x 2^n")
    C.table(["n", "2^n subsets", "n x 2^n item checks", "vs previous size"],
            [[n, 2 ** n, n * 2 ** n, "-" if k == 0 else f"x{2 ** (n - sizes[k - 1])} subsets"]
             for k, n in enumerate(sizes)])

    C.section("Experiment: growth with the number of packages (same manifest, extra packages added)")
    grow = []
    for n in sizes:
        pk, cap = instance(n, manifest)
        t, (bv, bw, chosen, st) = C.time_it(lambda: exhaustive_knapsack(pk, cap), min_seconds=0.1)
        ok = dp_best_value(pk, cap) == bv
        grow.append([n, cap, 2 ** n, st["subsets"], st["feasible"], 100 * st["feasible"] / st["subsets"],
                     st["item_checks"], st["additions"], bv, bw, len(chosen), t * 1000, t / st["subsets"] * 1e9,
                     "PASS" if ok else "FAIL"])
    C.table(["n", "limit kg", "2^n", "subsets", "feasible", "feasible %", "item checks", "additions",
             "best value", "weight", "packages", "time ms", "ns/subset", "DP check"], grow)
    C.save_csv("q6_growth.csv", ["n", "capacity_kg", "theory_subsets", "subsets", "feasible", "feasible_percent",
                                 "item_checks", "additions", "best_value", "best_weight", "packages_loaded",
                                 "time_ms", "ns_per_subset", "dp_check"], grow)
    print("\n  ratio check (n + 2 -> theory x4 subsets):")
    for a, b in zip(grow, grow[1:]):
        print(f"    n {a[0]:>2} -> {b[0]:>2}: subsets x{b[3] / a[3]:.2f}, item checks x{b[6] / a[6]:.2f}, "
              f"time x{b[11] / a[11]:.2f}")

    # ---- deployment boundary
    C.section(f"Deployment decision: loading plan must be ready within {DEADLINE_S:g} s")
    last = grow[-1]
    c = last[11] / 1000 / (last[0] * 2 ** last[0])       # seconds per item check, from the largest run
    print(f"  measured cost per item check (n = {last[0]}): {c * 1e9:.1f} ns  ->  time(n) ~ {c * 1e9:.1f} ns x n x 2^n")
    pred, n_max = [], 0
    for n in list(range(16, 31)) + [32, 40, 50]:
        tp = c * n * 2 ** n
        if tp <= DEADLINE_S:
            n_max = n
        measured = next((r[11] / 1000 for r in grow if r[0] == n), None)
        pred.append([n, 2 ** n, tp, "-" if measured is None else round(measured, 3),
                     "yes" if tp <= DEADLINE_S else "NO", human(tp)])
    C.table(["n", "subsets", "predicted s", "measured s", f"within {DEADLINE_S:g} s?", "predicted (readable)"], pred)
    C.save_csv("q6_deployment.csv", ["n", "subsets", "predicted_s", "measured_s", "within_deadline", "readable"], pred)
    print(f"\n  largest n within the deadline: n = {n_max} packages")

    plots(grow, pred, n_max)


def human(s):
    for unit, k in (("years", 31_557_600), ("days", 86_400), ("hours", 3600), ("minutes", 60)):
        if s >= k:
            return f"{s / k:,.1f} {unit}"
    return f"{s:.2f} s" if s >= 1 else f"{s * 1000:.0f} ms"


def plots(grow, pred, n_max):
    plt = C.pyplot()
    if not plt:
        return
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    ns = [r[0] for r in grow]
    ax = axes[0]
    ax.plot(ns, [r[3] for r in grow], "o-", color=C.BLUE, label="subsets generated (observed)")
    ax.plot(ns, [r[4] for r in grow], "s-", color=C.AQUA, label="feasible subsets")
    ax.plot(ns, [2 ** n for n in ns], ":", color="black", label="theory 2^n")
    ax.set_yscale("log")
    ax.set_xlabel("number of packages n")
    ax.set_ylabel("count (log)")
    ax.set_title("solution space vs n", fontsize=10)
    ax.legend(fontsize=8)
    ax = axes[1]
    ax.plot([r[0] for r in pred], [r[2] for r in pred], ":", color="black", label="predicted c x n x 2^n")
    ax.plot(ns, [r[11] / 1000 for r in grow], "o", color=C.ORANGE, ms=7, label="measured")
    ax.axhline(DEADLINE_S, color=C.RED, ls="--", label=f"deadline {DEADLINE_S:g} s")
    ax.axvline(n_max, color=C.RED, ls=":", lw=1)
    ax.text(n_max - 0.5, DEADLINE_S * 30, f"n_max = {n_max}", color=C.RED, fontsize=8, ha="right")
    ax.set_yscale("log")
    ax.set_xlabel("number of packages n")
    ax.set_ylabel("time s (log)")
    ax.set_title("time vs n and the deployment boundary", fontsize=10)
    ax.legend(fontsize=8)
    fig.suptitle(f"Q6: exhaustive search   [{C.who()}]", fontsize=10)
    C.save_fig(plt, fig, "q6_growth.png")


if __name__ == "__main__":
    C.run(main, "q6")
