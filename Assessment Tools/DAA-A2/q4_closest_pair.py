"""Q4 - Brute-force closest pair: drone collision-risk monitoring.

Each drone reports D_i = (x_i, y_i) in metres (to the centimetre) inside a 10 km x 10 km delivery zone.
Only pairs (i, j) with i < j are examined, so every unordered pair is seen exactly once:
pairs = (n-1) + (n-2) + ... + 1 = n(n-1)/2.
Squared distances are compared (no square root inside the loop); one sqrt at the end.

Counted: pairs examined, distance calculations.
"""
import bisect
import math
import random

import common as C

AREA_M = 10_000            # side of the delivery zone in metres
RESPONSE_BUDGET_S = 0.1    # acceptable response time, see README (10 % of a 1 s position-update cycle)


# ---------------------------------------------------------------------------- algorithm
def closest_pair_bf(points):
    """Return (i, j, distance, pairs examined, distance calculations)."""
    n = len(points)
    best, bi, bj = math.inf, -1, -1
    pairs = dist_calcs = 0
    for i in range(n - 1):
        xi, yi = points[i]
        for j in range(i + 1, n):              # j > i: (j, i) is never examined again
            pairs += 1
            dx = xi - points[j][0]
            dy = yi - points[j][1]
            d2 = dx * dx + dy * dy             # squared distance is enough for comparing
            dist_calcs += 1
            if d2 < best:
                best, bi, bj = d2, i, j
    return bi, bj, math.sqrt(best), pairs, dist_calcs


def avoidable_pairs(points, d):
    """Pairs whose x-coordinates already differ by at least d (the final closest distance).
    Such a pair can never be the closest pair, yet brute force computed its full distance.
    Counted separately with sorting + binary search, so it does not affect the measurement."""
    xs = sorted(p[0] for p in points)
    n = len(xs)
    near = 0
    for i, x in enumerate(xs):
        near += bisect.bisect_left(xs, x + d, lo=i + 1) - (i + 1)
    return n * (n - 1) // 2 - near


# ---------------------------------------------------------------------------- data
def uniform(n, rng):
    return [(round(rng.uniform(0, AREA_M), 2), round(rng.uniform(0, AREA_M), 2)) for _ in range(n)]


def clustered(n, rng, depots=5):
    centres = [(rng.uniform(1000, 9000), rng.uniform(1000, 9000)) for _ in range(depots)]
    out = []
    for _ in range(n):
        cx, cy = rng.choice(centres)
        out.append((round(min(max(rng.gauss(cx, 300), 0), AREA_M), 2), round(min(max(rng.gauss(cy, 300), 0), AREA_M), 2)))
    return out


def corridor(n, rng):
    """All drones flying along one straight corridor (y = 5000)."""
    return [(round(rng.uniform(0, AREA_M), 2), 5000.0) for _ in range(n)]


# ---------------------------------------------------------------------------- experiments
def main():
    C.banner("Q4 Brute-force closest pair - drone collision-risk monitoring")

    # ---- small hand-checkable test
    C.section("Correctness: small instance that can be checked by hand")
    small = [(0, 0), (3, 4), (7, 1), (6, 5), (2, 9)]
    print("  drones: " + ", ".join(f"D{i + 1}{p}" for i, p in enumerate(small)))
    rows = []
    for i in range(len(small)):
        for j in range(i + 1, len(small)):
            dx, dy = small[i][0] - small[j][0], small[i][1] - small[j][1]
            rows.append([f"D{i + 1}-D{j + 1}", dx * dx + dy * dy, round(math.sqrt(dx * dx + dy * dy), 4)])
    C.table(["pair", "squared distance", "distance"], rows)
    bi, bj, d, pairs, calcs = closest_pair_bf(small)
    print(f"  algorithm: D{bi + 1}-D{bj + 1}, distance {d:.4f}, pairs examined {pairs} (= 5*4/2 = 10)")
    same = [(100.0, 100.0), (2500.0, 40.0), (100.0, 100.0)]
    bi, bj, d, pairs, _ = closest_pair_bf(same)
    print(f"  edge case, two drones report the same position: D{bi + 1}-D{bj + 1}, distance {d} -> flagged")
    _, _, d2, p2, _ = closest_pair_bf([(0.0, 0.0), (30.0, 40.0)])
    print(f"  edge case, n = 2: distance {d2}, pairs examined {p2}")

    # ---- growth
    sizes = [125, 250, 500, 1000] if C.QUICK else [125, 250, 500, 1000, 2000, 4000]
    C.section("Experiment 1: growth with the number of drones (uniform positions)")
    grow = []
    sample = None
    for n in sizes:
        pts = uniform(n, random.Random(C.seed(400 + n)))
        if n == 500:
            sample = pts
            C.save_data("q4_drones_n500.csv", ["drone", "x_m", "y_m"], [[f"D{i + 1}", x, y] for i, (x, y) in enumerate(pts)])
        t, (bi, bj, d, pairs, calcs) = C.time_it(lambda: closest_pair_bf(pts), min_seconds=0.2)
        avoid = avoidable_pairs(pts, d)
        grow.append([n, n * (n - 1) // 2, pairs, calcs, f"D{bi + 1}-D{bj + 1}", round(d, 2), t * 1000,
                     t / pairs * 1e9, 100 * avoid / pairs])
    C.table(["n", "theory n(n-1)/2", "pairs examined", "distance calcs", "closest pair", "distance m",
             "time ms", "ns per pair", "% pairs avoidable"], grow)
    C.save_csv("q4_growth.csv", ["n", "theory_pairs", "pairs_examined", "distance_calculations", "closest_pair",
                                 "distance_m", "time_ms", "ns_per_pair", "percent_pairs_dx_ge_dmin"], grow)
    print("\n  ratio check when n doubles (theory: pairs about x4):")
    for a, b in zip(grow, grow[1:]):
        print(f"    n {a[0]:>5} -> {b[0]:>5}: pairs x{b[2] / a[2]:.2f}, time x{b[6] / a[6]:.2f}")

    # ---- same n, different arrangements
    n = 1000
    C.section(f"Experiment 2: same n = {n}, different arrangements (is the work input-sensitive?)")
    arr = []
    for name, gen in (("uniform", uniform), ("clustered (5 depots)", clustered), ("one corridor", corridor)):
        pts = gen(n, random.Random(C.seed(450)))
        t, (bi, bj, d, pairs, calcs) = C.time_it(lambda: closest_pair_bf(pts), min_seconds=0.2)
        arr.append([name, n, pairs, calcs, round(d, 2), t * 1000])
    C.table(["arrangement", "n", "pairs examined", "distance calcs", "closest distance m", "time ms"], arr)
    C.save_csv("q4_arrangements.csv", ["arrangement", "n", "pairs_examined", "distance_calculations",
                                       "closest_distance_m", "time_ms"], arr)

    # ---- scalability boundary
    C.section(f"Scalability: acceptable response time = {RESPONSE_BUDGET_S * 1000:g} ms")
    t_pair = grow[-1][6] / 1000 / grow[-1][2]
    n_max = int((1 + math.sqrt(1 + 8 * RESPONSE_BUDGET_S / t_pair)) / 2)
    print(f"  measured time per pair (largest run, n = {grow[-1][0]:,}) : {t_pair * 1e9:.1f} ns")
    print(f"  n(n-1)/2 x {t_pair * 1e9:.1f} ns <= {RESPONSE_BUDGET_S:g} s  ->  n_max = about {n_max:,} drones")
    pred = []
    for nn in sorted(set([n_max] + [500, 1000, 2000, 5000, 10000, 50000])):
        p = nn * (nn - 1) // 2
        pred.append([nn, p, p * t_pair * 1000, "yes" if p * t_pair <= RESPONSE_BUDGET_S else "NO"])
    C.table(["drones", "pairs", "predicted ms", f"within {RESPONSE_BUDGET_S * 1000:g} ms?"], pred)
    C.save_csv("q4_boundary.csv", ["drones", "pairs", "predicted_ms", "within_budget"], pred)

    plots(grow, sample, t_pair, n_max)


def plots(grow, sample, t_pair, n_max):
    plt = C.pyplot()
    if not plt:
        return
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    ns = [r[0] for r in grow]
    ax = axes[0]
    ax.plot(ns, [r[2] for r in grow], "o", color=C.BLUE, ms=8, label="pairs examined (observed)")
    xs = list(range(ns[0], ns[-1] + 1, max(1, (ns[-1] - ns[0]) // 200)))
    ax.plot(xs, [x * (x - 1) / 2 for x in xs], "-", color=C.GREY, lw=1.2, label="theory n(n-1)/2")
    ax.set_xlabel("number of drones n")
    ax.set_ylabel("pairs examined")
    ax.set_title("pairs examined vs n", fontsize=10)
    ax.legend(fontsize=8)
    ax = axes[1]
    ax.plot(ns, [r[6] for r in grow], "o-", color=C.ORANGE, label="measured time")
    ax.plot(ns, [x * (x - 1) / 2 * t_pair * 1000 for x in ns], ":", color="black", label="n(n-1)/2 x time per pair")
    ax.axhline(RESPONSE_BUDGET_S * 1000, color=C.RED, ls="--", label=f"budget {RESPONSE_BUDGET_S * 1000:g} ms")
    ax.axvline(n_max, color=C.RED, ls=":", lw=1)
    ax.text(n_max, RESPONSE_BUDGET_S * 1000 * 1.3, f" n_max ~ {n_max:,}", color=C.RED, fontsize=8)
    C.log_xticks(ax, ns)
    ax.set_yscale("log")
    ax.set_xlabel("number of drones n (log)")
    ax.set_ylabel("time ms (log)")
    ax.set_title("execution time vs n", fontsize=10)
    ax.legend(fontsize=8)
    fig.suptitle(f"Q4: brute-force closest pair   [{C.who()}]", fontsize=10)
    C.save_fig(plt, fig, "q4_growth.png")

    if sample:
        bi, bj, d, _, _ = closest_pair_bf(sample)
        fig, ax = plt.subplots(figsize=(5.6, 5.6))
        ax.scatter([p[0] for p in sample], [p[1] for p in sample], s=8, color=C.BLUE, label="drone")
        ax.plot([sample[bi][0], sample[bj][0]], [sample[bi][1], sample[bj][1]], "o-", color=C.RED, ms=7,
                label=f"closest pair D{bi + 1}-D{bj + 1}: {d:.1f} m")
        ax.set_xlim(0, AREA_M); ax.set_ylim(0, AREA_M)
        ax.set_aspect("equal")
        cx, cy = (sample[bi][0] + sample[bj][0]) / 2, (sample[bi][1] + sample[bj][1]) / 2
        r = max(60.0, 4 * d)
        ax.add_patch(plt.Circle((cx, cy), 250, fill=False, color=C.RED, lw=1.2))
        ins = ax.inset_axes([0.03, 0.03, 0.3, 0.3])
        ins.scatter([p[0] for p in sample], [p[1] for p in sample], s=14, color=C.BLUE)
        ins.plot([sample[bi][0], sample[bj][0]], [sample[bi][1], sample[bj][1]], "o-", color=C.RED, ms=6)
        ins.set_xlim(cx - r, cx + r); ins.set_ylim(cy - r, cy + r)
        ins.set_aspect("equal")
        ins.set_xticks([]); ins.set_yticks([])
        ins.set_title(f"zoom: {2 * r:.0f} m wide", fontsize=7)
        ins.set_facecolor("white")
        for sp in ins.spines.values():
            sp.set_visible(True); sp.set_color(C.RED)
        ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
        ax.set_title(f"Q4: {len(sample)} drones   [{C.who()}]", fontsize=10)
        ax.legend(fontsize=8, loc="upper right", frameon=True)
        C.save_fig(plt, fig, "q4_drones_n500.png")


if __name__ == "__main__":
    C.run(main, "q4")
