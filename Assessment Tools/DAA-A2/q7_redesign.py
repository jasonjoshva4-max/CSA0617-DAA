"""Q7 - Diagnose, redesign and validate: the exhaustive airlift planner from Q6.

Original (Q6): generate all 2^n bitmasks, add up each subset from scratch (n item checks per
subset), and only then test the payload limit.

Redesign, built in three separate steps so the effect of each idea can be measured:
  V1 reuse      : build loads as a decision tree (package i: load it / leave it). A child load
                  differs from its parent by one package, so its weight and value are the
                  parent's sums + one addition, instead of a full re-summation.
  V2 + capacity : weights are positive, so once a partial load is over the limit every load that
                  extends it is also over -> never take the 'load it' branch that breaks the limit.
  V3 + bound    : preprocessing - sort packages by value per kg. At each partial load compute an
                  optimistic bound (fill the remaining payload greedily, allowing a fraction of the
                  last package). If even this bound cannot beat the best complete load found so
                  far, the whole subtree is skipped.

Counted: nodes visited (partial loads), leaves (complete candidate loads evaluated),
         bound steps (packages scanned inside the bound), elementary operations
         (original: item checks; redesign: nodes + bound steps), time.
"""
import random
import statistics
import sys

import common as C
import q6_knapsack_exhaustive as Q6

sys.setrecursionlimit(10000)
NODE_CAP = 2_000_000          # safety stop for the hard-instance experiment


class NodeCapReached(Exception):
    pass


# ---------------------------------------------------------------------------- redesigned search
def tree_search(packages, capacity, prune_weight=False, use_bound=False, node_cap=None):
    """Depth-first include/exclude search. Returns (best value, best weight, chosen ids, counters)."""
    items = list(packages)
    if use_bound:                                 # preprocessing for the bound: best value per kg first
        items.sort(key=lambda p: p[2] / p[1], reverse=True)
    n = len(items)
    W = [p[1] for p in items]
    V = [p[2] for p in items]
    st = {"nodes": 0, "leaves": 0, "bound_steps": 0, "cut_weight": 0, "cut_bound": 0, "capped": False}
    best = {"value": -1, "weight": 0, "chosen": []}
    chosen = []

    def bound(i, w, v):
        """Optimistic value: fill the remaining payload with packages i.. in value-per-kg order,
        taking a fraction of the first one that does not fit. No real load can do better."""
        room, b = capacity - w, v
        while i < n:
            st["bound_steps"] += 1
            if W[i] <= room:
                room -= W[i]
                b += V[i]
                i += 1
            else:
                return b + V[i] * room / W[i]
        return b

    def visit(i, w, v):
        st["nodes"] += 1
        if node_cap and st["nodes"] > node_cap:
            raise NodeCapReached
        if i == n:                                # a complete candidate load
            st["leaves"] += 1
            if w <= capacity and v > best["value"]:
                best.update(value=v, weight=w, chosen=list(chosen))
            return
        if use_bound and bound(i, w, v) <= best["value"]:
            st["cut_bound"] += 1                  # nothing below here can beat the best load
            return
        if not prune_weight or w + W[i] <= capacity:
            chosen.append(items[i][0])
            visit(i + 1, w + W[i], v + V[i])      # load package i: one addition, sums reused
            chosen.pop()
        else:
            st["cut_weight"] += 1                 # loading it would break the payload limit
        visit(i + 1, w, v)                        # leave package i

    try:
        visit(0, 0, 0)
    except NodeCapReached:
        st["capped"] = True
    return best["value"], best["weight"], best["chosen"], st


VARIANTS = [("V1 reuse sums", dict()),
            ("V2 + capacity pruning", dict(prune_weight=True)),
            ("V3 + sort & bound", dict(prune_weight=True, use_bound=True))]


def ops_of(st):
    return st["nodes"] + st["bound_steps"]


def strongly_correlated(n, rng):
    """Hard class: every package has almost the same value per kg (value = weight + 10)."""
    pk = []
    for i in range(n):
        w = rng.randint(5, 60)
        pk.append((f"P{i + 1:02d}", w, w + 10))
    return pk, int(Q6.CAPACITY_SHARE * sum(p[1] for p in pk))


def uncorrelated(n, rng):
    pk = [(f"P{i + 1:02d}", rng.randint(5, 60), rng.randint(10, 100)) for i in range(n)]
    return pk, int(Q6.CAPACITY_SHARE * sum(p[1] for p in pk))


# ---------------------------------------------------------------------------- experiments
def main():
    C.banner("Q7 Diagnose, redesign and validate - airlift planner (from Q6)")
    manifest = Q6.master_manifest()
    sizes = [8, 10, 12, 14, 16] if C.QUICK else [8, 10, 12, 14, 16, 18, 20]

    # ---- A. diagnosis, from the original implementation
    C.section("A. Diagnosis: where the original exhaustive search spends its effort")
    orig = {}
    diag = []
    for n in sizes:
        pk, cap = Q6.instance(n, manifest)
        t, res = C.time_it(lambda: Q6.exhaustive_knapsack(pk, cap), min_seconds=0.1)
        orig[n] = (res, t)
        st = res[3]
        infeasible = st["subsets"] - st["feasible"]
        diag.append([n, st["subsets"], st["feasible"], infeasible, 100 * infeasible / st["subsets"],
                     st["item_checks"], st["additions"], st["additions"] / st["subsets"], 2 ** n - 1,
                     st["additions"] / (2 ** n - 1)])
    C.table(["n", "subsets", "feasible", "infeasible", "infeasible %", "item checks", "additions",
             "additions/subset", "additions if reused", "repeat factor"], diag)
    C.save_csv("q7_diagnosis.csv", ["n", "subsets", "feasible", "infeasible", "infeasible_percent", "item_checks",
                                    "additions", "additions_per_subset", "additions_with_reuse",
                                    "repeat_factor"], diag)
    d = diag[-1]
    print(f"\n  at n = {d[0]}: {d[4]:.1f}% of all generated loads break the payload limit (all their work is wasted),")
    print(f"  every subset is re-summed from scratch ({d[7]:.1f} additions each, x{d[9]:.1f} more than needed),")
    print("  and the limit is only checked after the subset is complete (generate first, test later).")

    # ---- B. objective
    C.section("B. Design objective (measurable)")
    print("  O1  return the same optimum as the original (and as an independent DP check) on every instance")
    print(f"  O2  at n = {sizes[-1]}: at least 90% fewer elementary operations than the original")
    print(f"  O3  plan a 40-package airlift within the {Q6.DEADLINE_S:g} s deadline (original limit: about 18)")

    # ---- D. prediction
    C.section("D. Prediction written before running the redesign")
    n = sizes[-1]
    feas = orig[n][0][3]["feasible"]
    print(f"  V1: same 2^n = {2 ** n:,} candidates; nodes = 2^(n+1)-1 = {2 ** (n + 1) - 1:,} instead of "
          f"n x 2^n = {n * 2 ** n:,} item checks -> about n/2 = {n / 2:g}x fewer operations")
    print(f"  V2: candidates (leaves) drop to exactly the feasible loads = {feas:,} ({100 * feas / 2 ** n:.1f}%)")
    print("  V3: candidates drop far below the feasible count, but the gain depends on the data")
    print("      (expected to be weak when all packages have a similar value per kg)")

    # ---- E. validation on the same instances as Q6
    C.section("E. Original vs redesign on the same instances as Q6")
    comp = []
    for n in sizes:
        pk, cap = Q6.instance(n, manifest)
        (bv0, bw0, ch0, st0), t0 = orig[n]
        dp = Q6.dp_best_value(pk, cap)
        comp.append([n, "V0 original exhaustive", st0["subsets"], st0["subsets"], st0["item_checks"], 0,
                     st0["item_checks"], bv0, "PASS" if bv0 == dp else "FAIL", t0 * 1000, 1.0, 1.0])
        for name, kw in VARIANTS:
            t, (bv, bw, ch, st) = C.time_it(lambda: tree_search(pk, cap, **kw), min_seconds=0.05)
            comp.append([n, name, st["leaves"], st["nodes"], st["nodes"], st["bound_steps"], ops_of(st), bv,
                         "PASS" if bv == bv0 == dp else "FAIL", t * 1000, st0["item_checks"] / ops_of(st),
                         t0 / t])
    C.table(["n", "variant", "candidates", "nodes", "item steps", "bound steps", "total ops", "best value",
             "same optimum", "time ms", "ops gain x", "time gain x"], comp)
    C.save_csv("q7_comparison.csv", ["n", "variant", "candidates_evaluated", "nodes_or_subsets", "item_steps",
                                     "bound_steps", "total_ops", "best_value", "same_optimum", "time_ms",
                                     "ops_gain", "time_gain"], comp)

    # ---- E2. larger airlifts (only the redesign can attempt them)
    big_sizes = [20, 25, 30, 40] if C.QUICK else [20, 25, 30, 40, 50, 60, 80]
    c0 = orig[sizes[-1]][1] / (sizes[-1] * 2 ** sizes[-1])       # original: seconds per item check
    C.section("E2. Larger airlifts with V3 (same manifest, more packages)")
    big = []
    for n in big_sizes:
        pk, cap = Q6.instance(n, manifest)
        t, (bv, bw, ch, st) = C.time_it(lambda: tree_search(pk, cap, prune_weight=True, use_bound=True),
                                        min_seconds=0.05)
        dp = Q6.dp_best_value(pk, cap)
        big.append([n, cap, 2 ** n, st["leaves"], st["nodes"], st["bound_steps"], ops_of(st), bv,
                    "PASS" if bv == dp else "FAIL", t * 1000, Q6.human(c0 * n * 2 ** n),
                    "yes" if t <= Q6.DEADLINE_S else "NO"])
    C.table(["n", "limit kg", "2^n", "candidates", "nodes", "bound steps", "total ops", "best value", "DP check",
             "V3 time ms", "original would need", f"within {Q6.DEADLINE_S:g} s"], big)
    C.save_csv("q7_large.csv", ["n", "capacity_kg", "subsets_2n", "candidates_evaluated", "nodes", "bound_steps",
                                "total_ops", "best_value", "dp_check", "time_ms", "original_predicted",
                                "within_deadline"], big)

    # ---- F. limitation: instances where the bound is weak
    lim_sizes = [10, 20, 30, 40] if C.QUICK else [10, 20, 30, 40, 50, 60]
    C.section(f"F. Limitation test: 5 instances per size, uncorrelated vs strongly correlated (node cap {NODE_CAP:,})")
    lim = []
    for kind, gen in (("uncorrelated", uncorrelated), ("strongly correlated", strongly_correlated)):
        for n in lim_sizes:
            nodes, times, capped, ok = [], [], 0, True
            for s in range(5):
                pk, cap = gen(n, random.Random(C.seed(700 + 100 * s + n)))
                t, (bv, bw, ch, st) = C.time_it(
                    lambda: tree_search(pk, cap, prune_weight=True, use_bound=True, node_cap=NODE_CAP),
                    min_seconds=0.0, max_reps=1)
                nodes.append(st["nodes"])
                times.append(t)
                if st["capped"]:
                    capped += 1
                else:
                    ok = ok and bv == Q6.dp_best_value(pk, cap)
            lim.append([kind, n, int(statistics.median(nodes)), max(nodes), capped, max(times) * 1000,
                        "PASS" if ok else "FAIL"])
    C.table(["instance class", "n", "median nodes", "max nodes", "hit cap", "max time ms", "DP check"], lim)
    print("  (a run that hits the node cap is stopped without an answer; the DP check covers the finished runs)")
    C.save_csv("q7_limitation.csv", ["instance_class", "n", "median_nodes", "max_nodes", "instances_hitting_cap",
                                     "max_time_ms", "dp_check"], lim)

    # ---- objective check
    C.section("Objective check")
    o1 = all(r[8] == "PASS" for r in comp) and all(r[8] == "PASS" for r in big)
    v0 = next(r for r in comp if r[0] == sizes[-1] and r[1].startswith("V0"))
    v3 = next(r for r in comp if r[0] == sizes[-1] and r[1].startswith("V3"))
    red = 100 * (1 - v3[6] / v0[6])
    r40 = next((r for r in big if r[0] == 40), None)
    print(f"  O1 same optimum on every instance                : {'MET' if o1 else 'NOT MET'}")
    print(f"  O2 operations at n = {sizes[-1]}: {v0[6]:,} -> {v3[6]:,} ({red:.3f}% fewer) : "
          f"{'MET' if red >= 90 else 'NOT MET'}")
    if r40:
        print(f"  O3 40 packages in {r40[9]:.2f} ms (deadline {Q6.DEADLINE_S * 1000:g} ms)        : "
              f"{'MET' if r40[11] == 'yes' else 'NOT MET'}")
    hard = [r for r in lim if r[0] == "strongly correlated"]
    print(f"  limitation: strongly correlated, n = {hard[-1][1]}: median {hard[-1][2]:,} nodes, max {hard[-1][3]:,}, "
          f"{hard[-1][4]} of 5 hit the node cap")

    plots(comp, big, lim, sizes)


def plots(comp, big, lim, sizes):
    plt = C.pyplot()
    if not plt:
        return
    colours = {"V0": C.RED, "V1": C.BLUE, "V2": C.YELLOW, "V3": C.AQUA}
    names = list(dict.fromkeys(r[1] for r in comp))
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2))
    for ax, col, label in ((axes[0], 6, "elementary operations"), (axes[1], 2, "candidate loads evaluated")):
        for name in names:
            pts = [(r[0], r[col]) for r in comp if r[1] == name]
            ax.plot([p[0] for p in pts], [max(p[1], 1) for p in pts], "o-", color=colours[name[:2]], label=name)
        ext = [(r[0], r[6] if col == 6 else r[3]) for r in big if r[0] > sizes[-1]]
        if ext:
            ax.plot([sizes[-1]] + [p[0] for p in ext],
                    [next(r[col] for r in comp if r[0] == sizes[-1] and r[1].startswith("V3"))] + [p[1] for p in ext],
                    "o--", color=C.AQUA, alpha=0.6, label="V3, larger airlifts")
        ax.set_yscale("log")
        ax.set_xlabel("number of packages n")
        ax.set_ylabel(f"{label} (log)")
        ax.set_title(label, fontsize=10)
    axes[0].legend(fontsize=8)
    fig.suptitle(f"Q7: original vs redesign (same instances as Q6)   [{C.who()}]", fontsize=10)
    C.save_fig(plt, fig, "q7_comparison.png")

    fig, ax = plt.subplots(figsize=(7, 4.2))
    for kind, col in (("uncorrelated", C.AQUA), ("strongly correlated", C.RED)):
        rows = [r for r in lim if r[0] == kind]
        ax.plot([r[1] for r in rows], [r[2] for r in rows], "o-", color=col, label=f"{kind}: median")
        ax.plot([r[1] for r in rows], [r[3] for r in rows], "v:", color=col, label=f"{kind}: max")
    ax.axhline(NODE_CAP, color=C.GREY, ls="--", lw=1, label="node cap (search stopped)")
    ax.set_yscale("log")
    ax.set_ylim(20, NODE_CAP * 150)
    ax.set_xlabel("number of packages n")
    ax.set_ylabel("nodes visited by V3 (log)")
    ax.set_title(f"Q7: where the redesign is weak   [{C.who()}]", fontsize=10)
    ax.legend(fontsize=8, ncol=2, loc="upper left")
    C.save_fig(plt, fig, "q7_limitation.png")


if __name__ == "__main__":
    C.run(main, "q7")
