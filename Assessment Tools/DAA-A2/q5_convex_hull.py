"""Q5 - Brute-force convex hull derived from the geometric principle.

Context: monitoring stations in a wildlife reserve, P_i = (x_i, y_i) in metres (integers).

Decision rule used (derived in the report):
  For every pair (Pi, Pj), i < j, look at every other point Pk and compute
      cross(Pi, Pj, Pk) = (xj - xi)(yk - yi) - (yj - yi)(xk - xi)
  > 0 : Pk is left of the directed line Pi -> Pj
  < 0 : Pk is right of it
  = 0 : Pk is on the line (collinear)
  Pi-Pj is accepted as a hull edge if no point is strictly left while another is strictly
  right, AND every collinear point lies between Pi and Pj (otherwise Pi-Pj is only part of a
  longer edge and the longer one is kept instead).
Duplicate stations are removed first. Integer coordinates keep the cross product exact.

Counted: pairs examined and orientation (cross-product) tests.
"""
import random
from collections import defaultdict

import common as C


# ---------------------------------------------------------------------------- geometry
def cross(o, a, b):
    """> 0 if b is left of the directed line o -> a, < 0 if right, 0 if collinear."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def between(p, q, r):
    """For a point r already known to be collinear with p and q: is r on the segment p-q?"""
    return min(p[0], q[0]) <= r[0] <= max(p[0], q[0]) and min(p[1], q[1]) <= r[1] <= max(p[1], q[1])


# ---------------------------------------------------------------------------- algorithm
def brute_force_hull_edges(stations, early_exit=False, collinear_rule=True):
    """Return (distinct points, accepted edges as index pairs, counters)."""
    pts = sorted(set(stations))                 # remove duplicate stations
    n = len(pts)
    st = {"input": len(stations), "distinct": n, "pairs": 0, "tests": 0}
    edges = []
    for i in range(n - 1):
        for j in range(i + 1, n):
            st["pairs"] += 1
            left = right = beyond = 0
            for k in range(n):
                if k == i or k == j:
                    continue
                st["tests"] += 1
                c = cross(pts[i], pts[j], pts[k])
                if c > 0:
                    left += 1
                elif c < 0:
                    right += 1
                elif collinear_rule and not between(pts[i], pts[j], pts[k]):
                    beyond += 1
                if early_exit and ((left and right) or beyond):
                    break                       # this pair can no longer be an edge
            if not (left and right) and not beyond:
                edges.append((i, j))
    st["edges"] = len(edges)
    return pts, edges, st


def build_boundary(pts, edges):
    """Join the accepted edges into one closed boundary, listed counter-clockwise."""
    if len(pts) <= 1:
        return list(pts)
    if len(edges) == 1:                          # all stations on one line: hull is a segment
        return [pts[edges[0][0]], pts[edges[0][1]]]
    adj = defaultdict(list)
    for i, j in edges:
        adj[i].append(j)
        adj[j].append(i)
    if any(len(v) != 2 for v in adj.values()):
        raise ValueError("accepted edges do not form a single closed boundary "
                         f"(vertex degrees {sorted(set(len(v) for v in adj.values()))})")
    start = min(adj)
    order, prev, cur = [start], None, start
    while True:
        a, b = adj[cur]
        nxt = a if a != prev else b
        if nxt == start:
            break
        order.append(nxt)
        prev, cur = cur, nxt
    if len(order) != len(adj):
        raise ValueError("accepted edges form more than one cycle")
    area2 = sum(cross((0, 0), pts[order[t]], pts[order[(t + 1) % len(order)]]) for t in range(len(order)))
    if area2 < 0:
        order.reverse()
    return [pts[i] for i in order]


def boundary_stations(pts, hull):
    """Stations lying on the boundary: the corners plus collinear stations on an edge."""
    if len(hull) < 2:
        return set(hull)
    edges = [(hull[t], hull[(t + 1) % len(hull)]) for t in range(len(hull))] if len(hull) > 2 else [(hull[0], hull[1])]
    return {p for p in pts if any(cross(a, b, p) == 0 and between(a, b, p) for a, b in edges)}


def monotone_chain(points):
    """Independent reference hull (Andrew's monotone chain), used only to check the result."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def solve(stations, **kw):
    pts, edges, st = brute_force_hull_edges(stations, **kw)
    hull = build_boundary(pts, edges)
    ok = set(hull) == set(monotone_chain(stations))
    return pts, hull, st, ok


# ---------------------------------------------------------------------------- test data
def random_stations(n, rng, w=20000, h=15000):
    return [(rng.randint(0, w), rng.randint(0, h)) for _ in range(n)]


def challenge_stations():
    s = [(0, 0), (12000, 0), (12000, 8000), (0, 8000)]                   # rectangular reserve fence
    s += [(3000, 0), (6000, 0), (9000, 0), (12000, 4000),                # stations ON the fence (collinear)
          (4000, 8000), (8000, 8000), (0, 2000), (0, 6000)]
    s += [(6000, 0), (12000, 8000)]                                      # duplicate reports
    s += [(2000, 1000), (4000, 2000), (6000, 3000), (8000, 4000)]        # collinear line inside
    s += [(6000, 4000), (3000, 6000), (10000, 2500)]                     # ordinary interior points
    s += [(12001, 6000)]                                                 # 1 m outside the right fence
    return s


def river_stations():
    return [(1000 + 1500 * t, 2000 + 1000 * t) for t in (0, 3, 1, 7, 4, 2, 9, 5, 11, 6, 8, 10)]


# ---------------------------------------------------------------------------- experiments
def describe(name, stations):
    pts, hull, st, ok = solve(stations)
    on_b = boundary_stations(pts, hull)
    print(f"\n  {name}")
    print(f"    stations {st['input']} (distinct {st['distinct']}), pairs examined {st['pairs']:,}, "
          f"orientation tests {st['tests']:,}, accepted edges {st['edges']}")
    print(f"    hull corners ({len(hull)}, counter-clockwise): {hull}")
    print(f"    stations on the boundary: {len(on_b)}  (corners + stations lying on an edge)")
    print(f"    interior stations: {st['distinct'] - len(on_b)}   check against monotone chain: {'PASS' if ok else 'FAIL'}")
    return pts, hull, on_b, st, ok


def main():
    C.banner("Q5 Brute-force convex hull - wildlife reserve boundary")
    rng = random.Random(C.seed(5))

    C.section("Test configurations")
    test_a = random_stations(30, rng)
    test_b = challenge_stations()
    test_c = river_stations()
    for fname, data in (("q5_testA_random.csv", test_a), ("q5_testB_challenge.csv", test_b),
                        ("q5_testC_collinear.csv", test_c)):
        C.save_data(fname, ["station", "x_m", "y_m"], [[f"S{i + 1}", x, y] for i, (x, y) in enumerate(data)])
    results = {}
    results["A"] = describe("Test A: 30 random stations (boundary and interior points)", test_a)
    results["B"] = describe("Test B (designed challenge): rectangle with stations on the fence, duplicates, "
                            "an interior collinear line, one station 1 m outside", test_b)
    results["C"] = describe("Test C (degenerate): all 12 stations along a straight river bank", test_c)

    # what goes wrong on test B with the simple 'all points on one side' rule
    _, naive_edges, _ = brute_force_hull_edges(test_b, collinear_rule=False)
    try:
        build_boundary(sorted(set(test_b)), naive_edges)
        naive_msg = "boundary built"
    except ValueError as e:
        naive_msg = f"boundary FAILS: {e}"
    print(f"\n  Same test B with the naive rule (collinear points ignored): {len(naive_edges)} edges accepted "
          f"instead of {results['B'][3]['edges']} -> {naive_msg}")

    C.section("Edge cases")
    edge_rows = []
    for label, s in (("1 station", [(500, 500)]), ("2 stations", [(0, 0), (900, 300)]),
                     ("3 stations, triangle", [(0, 0), (900, 0), (400, 700)]),
                     ("3 stations, collinear", [(0, 0), (500, 500), (1000, 1000)]),
                     ("4 stations, one inside", [(0, 0), (900, 0), (400, 700), (400, 200)]),
                     ("5 copies of one station", [(7, 7)] * 5)):
        pts, hull, st, ok = solve(s)
        edge_rows.append([label, st["input"], st["distinct"], st["pairs"], st["tests"], len(hull), str(hull),
                          "PASS" if ok else "FAIL"])
    C.table(["case", "input", "distinct", "pairs", "tests", "corners", "hull", "check"], edge_rows)

    summary = []
    for key, name in (("A", "A random"), ("B", "B challenge"), ("C", "C collinear")):
        pts, hull, on_b, st, ok = results[key]
        summary.append([name, st["input"], st["distinct"], st["pairs"], st["tests"], st["edges"], len(hull),
                        len(on_b), st["distinct"] - len(on_b), "PASS" if ok else "FAIL"])
    summary.append(["B with naive rule", len(test_b), len(set(test_b)), "-", "-", len(naive_edges), "-", "-", "-",
                    "FAIL"])
    C.save_csv("q5_tests.csv", ["test", "stations", "distinct", "pairs", "orientation_tests", "accepted_edges",
                                "hull_corners", "boundary_stations", "interior_stations", "check"], summary)

    # ---- growth
    sizes = [10, 20, 40, 80] if C.QUICK else [10, 20, 40, 80, 160, 320]
    C.section("Growth: random stations, full test vs early exit")
    grow = []
    for n in sizes:
        pts_n = random_stations(n, random.Random(C.seed(500 + n)))
        t, (pts, hull, st, ok) = C.time_it(lambda: solve(pts_n), min_seconds=0.1)
        _, _, st_e = brute_force_hull_edges(pts_n, early_exit=True)
        m = st["distinct"]
        grow.append([n, m, m * (m - 1) // 2, st["pairs"], m * (m - 1) * (m - 2) // 2, st["tests"], st_e["tests"],
                     len(hull), t * 1000, "PASS" if ok else "FAIL"])
    C.table(["n", "distinct", "theory pairs", "pairs", "theory tests n(n-1)(n-2)/2", "tests (full)",
             "tests (early exit)", "corners h", "time ms", "check"], grow)
    C.save_csv("q5_growth.csv", ["n", "distinct", "theory_pairs", "pairs", "theory_tests", "tests_full",
                                 "tests_early_exit", "hull_corners", "time_ms", "check"], grow)
    print("\n  ratio check when n doubles (theory: tests about x8):")
    for a, b in zip(grow, grow[1:]):
        print(f"    n {a[0]:>4} -> {b[0]:>4}: tests x{b[5] / a[5]:.2f}, time x{b[8] / a[8]:.2f}")

    plots(results, grow)


def plots(results, grow):
    plt = C.pyplot()
    if not plt:
        return
    titles = {"A": "Test A: random stations", "B": "Test B: designed challenge", "C": "Test C: all collinear"}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    for ax, key in zip(axes, "ABC"):
        pts, hull, on_b, st, ok = results[key]
        inner = [p for p in pts if p not in on_b]
        edge_pts = [p for p in on_b if p not in hull]
        ring = hull + hull[:1] if len(hull) > 2 else hull
        ax.fill([p[0] for p in ring], [p[1] for p in ring], color=C.BLUE, alpha=0.08)
        ax.plot([p[0] for p in ring], [p[1] for p in ring], "-", color=C.BLUE, lw=1.8, label="outer boundary")
        ax.scatter([p[0] for p in inner], [p[1] for p in inner], s=22, color=C.GREY, label="interior station", zorder=3)
        ax.scatter([p[0] for p in edge_pts], [p[1] for p in edge_pts], s=36, color=C.ORANGE, marker="s",
                   label="station on an edge", zorder=4)
        ax.scatter([p[0] for p in hull], [p[1] for p in hull], s=46, color=C.RED, label="hull corner", zorder=5)
        ax.set_title(f"{titles[key]} ({st['distinct']} distinct, {len(hull)} corners)", fontsize=10)
        ax.set_xlabel("x (m)")
        ax.set_aspect("equal", adjustable="datalim")
    axes[0].set_ylabel("y (m)")
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=9)
    fig.suptitle(f"Q5: brute-force convex hull   [{C.who()}]", fontsize=10)
    C.save_fig(plt, fig, "q5_hulls.png", rect=(0, 0.07, 1, 1))

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ns = [r[1] for r in grow]
    ax.plot(ns, [r[5] for r in grow], "o-", color=C.BLUE, label="orientation tests, full")
    ax.plot(ns, [r[6] for r in grow], "s-", color=C.AQUA, label="orientation tests, early exit")
    ax.plot(ns, [r[4] for r in grow], ":", color="black", label="theory n(n-1)(n-2)/2")
    C.log_xticks(ax, ns)
    ax.set_yscale("log")
    ax.set_xlabel("number of stations n (log)")
    ax.set_ylabel("orientation tests (log)")
    ax.set_title(f"Q5: work vs n   [{C.who()}]", fontsize=10)
    ax.legend(fontsize=8)
    C.save_fig(plt, fig, "q5_growth.png")


if __name__ == "__main__":
    C.run(main, "q5")
