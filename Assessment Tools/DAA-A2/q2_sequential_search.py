"""Q2 - When is Sequential Search an appropriate engineering choice?

Context: the list of specialised tools currently issued to technicians in an aircraft
maintenance hangar. Record = (Tool ID, Technician ID, Issue Time, Work Bay).
The list is kept in issue order (new issues are appended, returns are deleted), so it is
NOT ordered by Tool ID - that is why the system scans it sequentially.

Counted: key comparisons = number of records whose Tool ID is compared with the target.
"""
import random
import time

import common as C

# ---- operating parameters used for the boundary (change them if you justify other values)
LATENCY_BUDGET_S = 0.001   # worst-case search time allowed for one lookup (1 ms, see README)
CPU_SHARE = 0.05           # share of one CPU core the lookup service may use (5 %)
HIT_RATE = 0.9             # 90 % of "who has tool X?" questions are about tools that ARE issued

HANGAR_ACTIVE_TOOLS = 300          # one hangar: tools issued at a busy moment
HANGAR_LOOKUPS_PER_HOUR = 120      # one hangar: lookups per hour at peak (2 per minute)
FACILITIES = 20                    # changed condition


# ---------------------------------------------------------------------------- algorithm
def sequential_search(records, tool_id):
    """Return (index of the record or -1, number of key comparisons)."""
    comps = 0
    for i in range(len(records)):
        comps += 1
        if records[i][0] == tool_id:
            return i, comps
    return -1, comps


# ---------------------------------------------------------------------------- data
def make_records(n, rng):
    """n issued tools in issue order. Tool numbers are distinct and unrelated to list order."""
    numbers = rng.sample(range(1, max(20 * n, 2000)), n)
    t = 7 * 60                                            # first issue at 07:00
    recs = []
    for num in numbers:
        t += rng.randint(0, 2)
        recs.append((f"T-{num}", f"TECH-{rng.randint(100, 999)}",
                     f"{(t // 60) % 24:02d}:{t % 60:02d}", f"BAY-{rng.randint(1, 12):02d}"))
    return recs


def missing_ids(records, k, rng):
    """k Tool IDs that are NOT in the list (tool already returned / wrong ID)."""
    present = {r[0] for r in records}
    out = []
    while len(out) < k:
        tid = f"T-{rng.randint(1, 50 * len(records) + 5000)}"
        if tid not in present:
            out.append(tid)
    return out


# ---------------------------------------------------------------------------- experiments
def main():
    C.banner("Q2 Sequential search - aircraft maintenance tool tracking")
    rng = random.Random(C.seed(2))

    # ---- the question from the brief
    C.section(f'Demo: "Who currently has Tool T-184?"  (one hangar, {HANGAR_ACTIVE_TOOLS} issued tools)')
    hangar = make_records(HANGAR_ACTIVE_TOOLS, rng)
    hangar = [r for r in hangar if r[0] != "T-184"]
    pos = rng.randint(0, len(hangar) - 1)
    hangar.insert(pos, ("T-184", "TECH-417", "09:12", "BAY-03"))
    hangar = hangar[:HANGAR_ACTIVE_TOOLS]
    C.save_data("q2_hangar_records.csv", ["tool_id", "technician_id", "issue_time", "work_bay"], hangar)
    idx, comps = sequential_search(hangar, "T-184")
    print(f"  Found at list position {idx + 1}: {hangar[idx]}  ->  {comps} comparisons")

    # ---- Experiment 1: successful searches at chosen positions + unsuccessful search
    n = 1000
    recs = make_records(n, rng)
    C.section(f"Experiment 1: target position vs comparisons (n = {n})")
    rows = []
    for label, p in (("first", 1), ("25%", n // 4), ("middle", n // 2), ("75%", 3 * n // 4), ("last", n)):
        i, c = sequential_search(recs, recs[p - 1][0])
        assert i == p - 1
        rows.append([f"successful - {label}", p, p, c])
    for tid in missing_ids(recs, 3, rng):
        i, c = sequential_search(recs, tid)
        assert i == -1
        rows.append([f"unsuccessful ({tid})", "-", n, c])
    C.table(["search", "position", "predicted comps", "observed comps"], rows)
    C.save_csv("q2_positions.csv", ["search", "position", "predicted_comparisons", "observed_comparisons"], rows)

    # ---- Experiment 2: different list sizes, many random lookups
    sizes = [100, 1000, 10000] if C.QUICK else [100, 1000, 10000, 100000]
    C.section("Experiment 2: list size vs comparisons (averaged over many random lookups)")
    size_rows = []
    for size in sizes:
        r2 = random.Random(C.seed(20 + len(str(size))))
        recs = make_records(size, r2)
        trials = max(100, min(1000, 5_000_000 // size))
        hits = [recs[r2.randrange(size)][0] for _ in range(trials)]
        misses = missing_ids(recs, trials, r2)
        t0 = time.perf_counter()
        hc = [sequential_search(recs, t)[1] for t in hits]
        t_hit = (time.perf_counter() - t0) / trials
        t0 = time.perf_counter()
        mc = [sequential_search(recs, t)[1] for t in misses]
        t_miss = (time.perf_counter() - t0) / trials
        size_rows.append([size, trials, (size + 1) / 2, sum(hc) / trials, min(hc), max(hc), size, sum(mc) / trials,
                          t_hit * 1e6, t_miss * 1e6, t_miss / size * 1e9])
    C.table(["n", "lookups", "pred avg hit", "obs avg hit", "min", "max", "pred miss", "obs miss",
             "us/hit", "us/miss", "ns/comparison"], size_rows)
    C.save_csv("q2_sizes.csv", ["n", "lookups_each", "predicted_avg_successful", "observed_avg_successful",
                                "min_successful", "max_successful", "predicted_unsuccessful",
                                "observed_avg_unsuccessful", "us_per_successful", "us_per_unsuccessful",
                                "ns_per_comparison"], size_rows)

    # ---- Experiment 3: operating boundary (size AND frequency)
    t_comp = size_rows[-1][-1] / 1e9            # seconds per comparison, measured on the largest list
    avg_factor = HIT_RATE * 0.5 + (1 - HIT_RATE) * 1.0        # average comparisons per lookup = factor * n
    n_lat = int(LATENCY_BUDGET_S / t_comp)
    C.section("Experiment 3: operating boundary")
    print(f"  measured cost of one comparison      : {t_comp * 1e9:.1f} ns (from n = {size_rows[-1][0]:,})")
    print(f"  latency rule : unsuccessful search (n comparisons) <= {LATENCY_BUDGET_S * 1000:g} ms"
          f"  ->  n <= {n_lat:,}")
    print(f"  load rule    : lookups/s x {avg_factor:.2f} n x {t_comp * 1e9:.1f} ns <= {CPU_SHARE:.0%} of one core")
    bound_rows = []
    for label, rate in (("1 per minute", 1 / 60), ("1 per second", 1), ("10 per second", 10),
                        ("100 per second", 100), ("1,000 per second", 1000), ("10,000 per second", 10000)):
        n_load = int(CPU_SHARE / (rate * avg_factor * t_comp))
        n_max = min(n_lat, n_load)
        bound_rows.append([label, rate, n_lat, n_load, n_max, "latency" if n_lat <= n_load else "load"])
    C.table(["lookup rate", "lookups/s", "n max (latency)", "n max (load)", "n max", "limited by"], bound_rows)
    C.save_csv("q2_boundary.csv", ["lookup_rate", "lookups_per_s", "n_max_latency", "n_max_load", "n_max",
                                   "limited_by"], bound_rows)

    # ---- Changed condition: 20 facilities
    C.section(f"Changed condition: one hangar -> {FACILITIES} facilities")
    big = make_records(HANGAR_ACTIVE_TOOLS * FACILITIES, random.Random(C.seed(29)))
    index = {r[0]: r for r in big}                   # alternative: hash index keyed by Tool ID
    probe = [big[i][0] for i in random.Random(C.seed(30)).sample(range(len(big)), 500)]
    t_dict, _ = C.time_it(lambda: [index.get(t) for t in probe], min_seconds=0.05)
    t_dict /= len(probe)
    scen = []
    for label, recs_n, per_hour in (("1 hangar", HANGAR_ACTIVE_TOOLS, HANGAR_LOOKUPS_PER_HOUR),
                                    (f"{FACILITIES} facilities, one list", HANGAR_ACTIVE_TOOLS * FACILITIES,
                                     HANGAR_LOOKUPS_PER_HOUR * FACILITIES)):
        avg_c = avg_factor * recs_n
        scen.append([label, recs_n, per_hour, round(avg_c), recs_n, round(per_hour * avg_c),
                     recs_n * t_comp * 1e3, per_hour * avg_c * t_comp, per_hour / 3600 * avg_c * t_comp * 100])
    C.table(["scenario", "records", "lookups/hour", "avg comps/lookup", "worst comps", "comps/hour",
             "worst ms", "CPU s/hour", "CPU %"], scen)
    C.save_csv("q2_scenarios.csv", ["scenario", "records", "lookups_per_hour", "avg_comparisons_per_lookup",
                                    "worst_comparisons", "comparisons_per_hour", "worst_case_ms",
                                    "cpu_seconds_per_hour", "cpu_percent"], scen)
    print(f"\n  growth from 1 hangar to {FACILITIES} facilities: comparisons per lookup x{FACILITIES}, lookups x"
          f"{FACILITIES}, total work x{FACILITIES * FACILITIES}")
    k_lat = LATENCY_BUDGET_S / (HANGAR_ACTIVE_TOOLS * t_comp)
    k_load = (CPU_SHARE / ((HANGAR_LOOKUPS_PER_HOUR / 3600) * avg_factor * HANGAR_ACTIVE_TOOLS * t_comp)) ** 0.5
    print(f"  facilities before the latency rule fails : about {k_lat:,.0f} (worst case grows like k)")
    print(f"  facilities before the load rule fails    : about {k_load:,.0f} (total work grows like k^2)")
    print(f"  hash index alternative: {t_dict * 1e6:.3f} us per lookup (about 1 probe), "
          f"but it must be updated on every issue and return")

    plots(rows, size_rows, bound_rows, scen, n)


def plots(rows, size_rows, bound_rows, scen, n):
    plt = C.pyplot()
    if not plt:
        return
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    ax = axes[0]
    succ = [r for r in rows if r[0].startswith("successful")]
    ax.plot([r[1] for r in succ], [r[3] for r in succ], "o-", color=C.BLUE, label="successful (observed)")
    ax.plot([1, n], [1, n], ":", color=C.GREY, label="prediction: comps = position")
    ax.axhline(n, color=C.RED, ls="--", label=f"unsuccessful: always n = {n}")
    for r in succ:
        ax.annotate(r[0].split(" - ")[1], (r[1], r[3]), textcoords="offset points",
                    xytext=(6, 4) if r[1] == 1 else (4, -13), fontsize=8)
    ax.set_xlabel("position of the target tool in the list")
    ax.set_ylabel("key comparisons")
    ax.set_title(f"comparisons vs target position (n = {n})", fontsize=10)
    ax.legend(fontsize=8)
    ax = axes[1]
    ns = [r[0] for r in size_rows]
    ax.plot(ns, [r[3] for r in size_rows], "o-", color=C.BLUE, label="successful, average (observed)")
    ax.plot(ns, [r[7] for r in size_rows], "s-", color=C.ORANGE, label="unsuccessful (observed)")
    ax.plot(ns, [(x + 1) / 2 for x in ns], ":", color=C.GREY, label="theory (n+1)/2 and n")
    ax.plot(ns, ns, ":", color=C.GREY)
    C.log_xticks(ax, ns)
    ax.set_yscale("log")
    ax.set_xlabel("number of active records n (log)")
    ax.set_ylabel("comparisons per lookup (log)")
    ax.set_title("comparisons vs list size", fontsize=10)
    ax.legend(fontsize=8)
    fig.suptitle(f"Q2: sequential search   [{C.who()}]", fontsize=10)
    C.save_fig(plt, fig, "q2_comparisons.png")

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    rates = [r[1] for r in bound_rows]
    nmax = [r[4] for r in bound_rows]
    ax.plot(rates, nmax, "o-", color=C.BLUE, label="largest n that meets both rules")
    ax.fill_between(rates, 1, nmax, color=C.BLUE, alpha=0.12, label="sequential search acceptable")
    for s, mk, col in zip(scen, ("o", "s"), (C.AQUA, C.ORANGE)):
        ax.plot(s[2] / 3600, s[1], mk, color=col, ms=9, label=f"{s[0]}: {s[1]:,} records, {s[2]:,}/h")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_ylim(10, max(nmax) * 5)
    ax.set_xlabel("lookup requests per second (log)")
    ax.set_ylabel("active records n (log)")
    ax.set_title(f"Q2: operating boundary (latency <= {LATENCY_BUDGET_S * 1000:g} ms, CPU <= {CPU_SHARE:.0%})"
                 f"   [{C.who()}]", fontsize=9)
    ax.legend(fontsize=8, loc="lower left")
    C.save_fig(plt, fig, "q2_boundary.png")


if __name__ == "__main__":
    C.run(main, "q2")
