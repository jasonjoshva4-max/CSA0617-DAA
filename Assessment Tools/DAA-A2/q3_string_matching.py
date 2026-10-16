"""Q3 - Engineering the behaviour of brute-force string matching.

Context: a security operations centre screens system logs for known event signatures.
The matcher tries every alignment (window) i = 0 .. n-m and compares the pattern with the
text character by character, left to right, stopping at the first mismatch.
All occurrences are reported (a screening tool must find every hit, not just the first).

Counted: character comparisons text[i+j] vs pattern[j].
"""
import os
import random
from collections import Counter

import common as C


# ---------------------------------------------------------------------------- algorithm
def brute_force_match(text, pattern):
    """Return (list of match positions, character comparisons, windows tried)."""
    n, m = len(text), len(pattern)
    comps, found = 0, []
    windows = max(n - m + 1, 0)
    for i in range(windows):
        j = 0
        while j < m:
            comps += 1
            if text[i + j] != pattern[j]:
                break
            j += 1
        if j == m:
            found.append(i)
    return found, comps, windows


def reference_positions(text, pattern):
    """Independent check using Python's own str.startswith."""
    return [i for i in range(len(text) - len(pattern) + 1) if text.startswith(pattern, i)]


# ---------------------------------------------------------------------------- predictions
def frequency_model(text, pattern):
    """Prediction from character frequencies only (assumes characters are independent):
    a window reaches pattern[j] only if pattern[0..j-1] all matched, so
    expected comparisons per window = 1 + f(p0) + f(p0)f(p1) + ... """
    cnt, n = Counter(text), len(text)
    per_window, reach = 0.0, 1.0
    for ch in pattern:
        per_window += reach
        reach *= cnt[ch] / n
    return per_window * (n - len(pattern) + 1)


# ---------------------------------------------------------------------------- test texts
def log_text(n, rng, failed_invalid_share, plant_xss=0, root_share=0.01):
    """A realistic-looking system log of exactly n characters.
    failed_invalid_share: share of lines that are 'Failed password for invalid user ...'."""
    users = ["alice", "bob", "carol", "deepak", "priya", "ravi", "meena", "arun"]
    bad = ["admin", "test", "oracle", "guest", "ubuntu", "pi", "support", "ftpuser"]
    lines, t, xss_left, k = [], 8 * 3600, plant_xss, 0
    while sum(len(x) for x in lines) < n:
        t += rng.randint(0, 3)
        ts = f"2026-10-16 {t // 3600 % 24:02d}:{t // 60 % 60:02d}:{t % 60:02d} gw01 "
        ip = f"{rng.choice([10, 172, 192])}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
        pid, port = rng.randint(1000, 9999), rng.randint(30000, 65000)
        r = rng.random()
        k += 1
        if xss_left and k % 97 == 0:
            lines.append(ts + f"nginx[{pid}]: {ip} GET /search?q=<script>alert(1)</script> 403 0\n")
            xss_left -= 1
        elif r < failed_invalid_share:
            lines.append(ts + f"sshd[{pid}]: Failed password for invalid user {rng.choice(bad)} from {ip} port {port} ssh2\n")
        elif r < failed_invalid_share + root_share:
            lines.append(ts + f"sshd[{pid}]: Failed password for root from {ip} port {port} ssh2\n")
        elif r < 0.55 + failed_invalid_share / 2:
            lines.append(ts + f"sshd[{pid}]: Accepted password for {rng.choice(users)} from {ip} port {port} ssh2\n")
        elif r < 0.80 + failed_invalid_share / 5:
            lines.append(ts + f"nginx[{pid}]: {ip} GET /api/orders/{rng.randint(1, 99999)} 200 {rng.randint(200, 9000)}\n")
        elif r < 0.92:
            lines.append(ts + f"kernel: eth{rng.randint(0, 1)}: link is up {rng.choice([100, 1000])} Mbps\n")
        else:
            lines.append(ts + f"cron[{pid}]: (root) CMD (run-parts /etc/cron.hourly)\n")
    return "".join(lines)[:n]


def packet_dump(n, rng, malicious_share=0.35):
    """Hex dump of network packets, one packet per line, exactly n characters.
    Malicious packets carry a NOP sled (a long run of byte 90) before their shellcode,
    and some shellcode starts with 31 C0 (xor eax, eax)."""
    hexb = lambda: f"{rng.randrange(256):02X}"
    lines, k = [], 0
    while sum(len(x) for x in lines) < n:
        k += 1
        body = [hexb() for _ in range(20)]                       # header bytes
        if rng.random() < malicious_share:
            body += ["90"] * rng.randint(64, 256)                # NOP sled
            body += (["31", "C0"] if rng.random() < 0.3 else [hexb(), hexb()])
        body += [hexb() for _ in range(rng.randint(20, 120))]    # rest of payload
        ip = f"203.0.113.{rng.randint(1, 254)}"
        lines.append(f"pkt {k:04d} src {ip} len {len(body)}: " + " ".join(body) + "\n")
    return "".join(lines)[:n]


def random_text(n, alphabet, rng):
    return "".join(rng.choice(alphabet) for _ in range(n))


def short(s, k=28):
    s = s.replace("\n", "\\n")
    return s if len(s) <= k else s[:k - 3] + "..."


# ---------------------------------------------------------------------------- experiments
def run_test(tag, purpose, text, pattern, structure_prediction=None, note=""):
    n, m = len(text), len(pattern)
    pred = frequency_model(text, pattern)
    print(f"\n  {tag}: {purpose}")
    print(f"    text n = {n:,}   pattern m = {m}  '{short(pattern, 40)}'   windows n-m+1 = {n - m + 1:,}")
    print(f"    PREDICTION (character-frequency model) : about {pred:,.0f} comparisons"
          f"  ({pred / (n - m + 1):.3f} per window)")
    if structure_prediction is not None:
        print(f"    PREDICTION (structure-aware)           : about {structure_prediction:,.0f} comparisons  {note}")
    found, comps, windows = brute_force_match(text, pattern)
    assert found == reference_positions(text, pattern), "matcher disagrees with str.startswith"
    print(f"    OBSERVED                               : {comps:,} comparisons ({comps / windows:.3f} per window), "
          f"{len(found)} match(es), positions verified")
    worst = windows * m
    return [tag, purpose, n, m, short(pattern), windows, len(found), round(pred),
            round(structure_prediction) if structure_prediction is not None else "-",
            comps, comps / windows, worst, 100 * comps / worst]


def main():
    C.banner("Q3 Brute-force string matching - cybersecurity log screening")
    rng = random.Random(C.seed(3))
    n = 15_000 if C.QUICK else 60_000

    normal_log = log_text(n, rng, failed_invalid_share=0.03, plant_xss=3)
    attack_log = log_text(n, rng, failed_invalid_share=0.60)
    dump = packet_dump(n, rng)
    all_a = "A" * n
    rand26 = random_text(n, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", rng)
    d = os.path.join(C.RESULTS, "data")
    os.makedirs(d, exist_ok=True)
    for name, txt in (("q3_normal_log.txt", normal_log), ("q3_attack_log.txt", attack_log),
                      ("q3_packet_dump.txt", dump)):
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(txt)

    C.section("Designed tests (prediction printed before each run)")
    rows = []
    xss = "<script>alert("
    rows.append(run_test("T1", "little work: rare first character in a normal log", normal_log, xss))
    worst_p = "A" * (len(xss) - 1) + "B"
    w = n - len(worst_p) + 1
    rows.append(run_test("T2", "engineered worst case: text AAAA..., pattern AAA...AB", all_a, worst_p,
                         w * len(worst_p), "= (n-m+1) x m, every window fails at the last character"))
    sled_sig = "90 " * 8 + "31 C0"
    run8 = "90 " * 8
    starts = sum(1 for i in range(len(dump) - len(run8) + 1) if dump.startswith(run8, i))
    sw = len(dump) - len(sled_sig) + 1
    rows.append(run_test("T3", "own test: NOP-sled signature in a packet hex dump (long runs of '90 ')", dump,
                         sled_sig, sw + starts * len(run8),
                         f"= windows + {starts:,} sled positions x {len(run8)} matched characters"))
    root = "Failed password for root"
    prefix = "Failed password for "
    for tag, purpose, txt in (("S1", "near-miss prefix: attack log, 60% 'Failed password for invalid user'", attack_log),
                              ("S2", "same pattern, normal log (3% failed logins) for contrast", normal_log)):
        near = txt.count(prefix) - txt.count(root)
        hits = txt.count(root)
        sp = (len(txt) - len(root) + 1) + near * len(prefix) + hits * (len(root) - 1)
        rows.append(run_test(tag, purpose, txt, root, sp,
                             f"= windows + {near:,} near misses x {len(prefix)} + {hits} hits x {len(root) - 1}"))
    rnd_p = random_text(len(xss), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", random.Random(C.seed(31)))
    rows.append(run_test("S3", "same n and m as T2, but random A-Z text", rand26, rnd_p))

    print()
    hdr = ["test", "purpose", "n", "m", "pattern", "windows", "matches", "pred (freq)", "pred (structure)",
           "observed comps", "comps/window", "worst (n-m+1)m", "% of worst"]
    C.table([h for i, h in enumerate(hdr) if i != 1], [[c for i, c in enumerate(r) if i != 1] for r in rows])
    C.save_csv("q3_tests.csv", ["test", "purpose", "n", "m", "pattern", "windows", "matches", "predicted_frequency_model",
                                "predicted_structure_aware", "observed_comparisons", "comparisons_per_window",
                                "worst_case_bound", "percent_of_worst"], rows)

    # ---- sweep 1: pattern length in the worst case
    n2 = 5_000 if C.QUICK else 20_000
    C.section(f"Sweep 1: worst-case text 'A' x {n2:,}, pattern 'A'x(m-1)+'B', vary m")
    sweep_m = []
    for m in (2, 5, 10, 20, 40, 80):
        _, comps, windows = brute_force_match("A" * n2, "A" * (m - 1) + "B")
        sweep_m.append([n2, m, windows, windows * m, comps, comps / n2])
    C.table(["n", "m", "windows", "predicted (n-m+1)m", "observed", "comps per text char"], sweep_m)
    C.save_csv("q3_sweep_pattern_length.csv", ["n", "m", "windows", "predicted", "observed", "comps_per_text_char"],
               sweep_m)

    # ---- sweep 2: alphabet size of random text (same n, same m)
    C.section(f"Sweep 2: random text, n = {n:,}, m = {len(xss)}, vary alphabet size")
    sweep_a = []
    for sigma in (2, 4, 26):
        alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:sigma]
        r3 = random.Random(C.seed(40 + sigma))
        txt, pat = random_text(n, alpha, r3), random_text(len(xss), alpha, r3)
        theory = (1 - (1 / sigma) ** len(pat)) / (1 - 1 / sigma)
        found, comps, windows = brute_force_match(txt, pat)
        assert found == reference_positions(txt, pat)
        sweep_a.append([sigma, alpha if sigma < 26 else "A-Z", windows, theory, comps / windows, comps, len(found)])
    C.table(["alphabet size", "letters", "windows", "theory per window", "observed per window", "observed comps",
             "matches"], sweep_a)
    C.save_csv("q3_sweep_alphabet.csv", ["alphabet_size", "letters", "windows", "theory_per_window",
                                         "observed_per_window", "observed_comparisons", "matches"], sweep_a)

    plots(rows, sweep_m, sweep_a)


def plots(rows, sweep_m, sweep_a):
    plt = C.pyplot()
    if not plt:
        return
    fig, ax = plt.subplots(figsize=(9, 4.3))
    labels = [r[0] for r in rows]
    obs = [r[9] for r in rows]
    cols = [C.AQUA, C.RED, C.ORANGE, C.BLUE, C.BLUE, C.GREY]
    ax.bar(labels, obs, color=cols[:len(rows)], width=0.55)
    for i, r in enumerate(rows):
        ax.text(i, r[9] * 1.12, f"{r[9]:,}\n({r[10]:.2f}/window)", ha="center", fontsize=8)
        ax.plot([i - 0.32, i + 0.32], [r[11]] * 2, color="black", lw=1)
    ax.plot([], [], color="black", lw=1, label="worst-case bound (n-m+1) x m for that test")
    ax.set_yscale("log")
    ax.set_ylim(min(obs) / 3, max(r[11] for r in rows) * 6)
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels([f"{r[0]}\nn={r[2]:,}, m={r[3]}" for r in rows], fontsize=8)
    ax.set_ylabel("character comparisons (log)")
    ax.set_title(f"Q3: character comparisons per designed test   [{C.who()}]", fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    C.save_fig(plt, fig, "q3_tests.png")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    ax = axes[0]
    ax.plot([r[1] for r in sweep_m], [r[4] for r in sweep_m], "o-", color=C.RED, label="observed")
    ax.plot([r[1] for r in sweep_m], [r[3] for r in sweep_m], ":", color="black", label="(n-m+1) x m")
    ax.set_xlabel("pattern length m")
    ax.set_ylabel("character comparisons")
    ax.set_title(f"worst-case text, n = {sweep_m[0][0]:,}: work grows with m", fontsize=10)
    ax.legend(fontsize=8)
    ax = axes[1]
    ax.bar([str(r[0]) for r in sweep_a], [r[4] for r in sweep_a], color=C.BLUE, width=0.5, label="observed")
    ax.plot([str(r[0]) for r in sweep_a], [r[3] for r in sweep_a], "D", color=C.ORANGE, label="theory")
    for i, r in enumerate(sweep_a):
        ax.text(i, r[4] + 0.04, f"{r[4]:.3f}", ha="center", fontsize=8)
    ax.set_xlabel("alphabet size of random text")
    ax.set_ylabel("comparisons per window")
    ax.set_title("random text: smaller alphabet = more partial matches", fontsize=10)
    ax.legend(fontsize=8)
    fig.suptitle(f"Q3: sweeps   [{C.who()}]", fontsize=10)
    C.save_fig(plt, fig, "q3_sweeps.png")


if __name__ == "__main__":
    C.run(main, "q3")
