// =====================================================================
// BENCHMARK + TEST DRIVER  (this file contains main)
//
//   daa test                   Task 8  : correctness tests (all algorithms)
//   daa bench 1000             Task 9  : benchmark ONE size  -> one screenshot per size
//   daa bench                  Task 9  : all four sizes, one after another
//   daa task12                 Task 12 : 50,000 searches on 1,000,000 records
//   daa task12 --full-linear   same, but really runs all 50,000 linear searches (slow)
//   daa gen 1000               writes data/students_1000.csv (sample dataset)
//
// Every run prints your reg no, name and the current date/time first,
// as the screenshot rules require. Results go to results/ as CSV files;
// src/plot_results.py turns them into the graphs.
// =====================================================================
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <map>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

#include "common.h"
#include "config.h"

namespace fs = std::filesystem;
using Clock = std::chrono::steady_clock;

static const int SIZES[] = {1000, 10000, 100000, 1000000};
static const double TARGET_LOAD = 0.75;      // hash table load factor alpha = n / m

// ------------------------------------------------------------------ helpers
static volatile long long g_sink = 0;        // stops the compiler deleting "unused" work

static double ms_since(Clock::time_point t0) {
    return std::chrono::duration<double, std::milli>(Clock::now() - t0).count();
}

static unsigned long long personal_seed() { return (unsigned long long)(REG_NO % 10000); }

static std::string commas(long long v) {
    std::string s = std::to_string(v < 0 ? -v : v);
    for (int i = (int)s.size() - 3; i > 0; i -= 3) s.insert((size_t)i, ",");
    return v < 0 ? "-" + s : s;
}

static std::string fmt(const char* f, double x) {
    char b[64];
    std::snprintf(b, sizeof(b), f, x);
    return b;
}

static std::string now_string() {
    std::time_t t = std::time(nullptr);
    char buf[64];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", std::localtime(&t));
    return buf;
}

static void rule(char c = '=') { std::printf("%s\n", std::string(100, c).c_str()); }

static void banner(const std::string& title) {
    rule('=');
    std::printf(" DAA Assignment 1 (CO1)  |  %s\n", title.c_str());
    std::printf(" Reg No: %lld  |  Name: %s  |  Dataset seed: %04llu (last 4 digits of reg no)\n",
                REG_NO, NAME, personal_seed());
    std::printf(" Run at: %s (system local time)\n", now_string().c_str());
    rule('=');
}

static bool config_ok() {
    if (REG_NO <= 0 || std::strcmp(NAME, "YOUR NAME") == 0) {
        std::fprintf(stderr, "\n  First open src/config.h, set REG_NO and NAME, then rebuild.\n\n");
        return false;
    }
    return true;
}

static double lg(double x) { return std::log2(x); }

// ------------------------------------------------------------------ queries
struct Query { long long key; bool present; };

// Independent answer key: the C++ library's std::sort + std::binary_search.
// Used only to CHECK our three algorithms, never to time them.
struct Oracle {
    std::vector<long long> keys;
    explicit Oracle(const std::vector<Record>& db) {
        keys.reserve(db.size());
        for (const Record& r : db) keys.push_back(r.reg_no);
        std::sort(keys.begin(), keys.end());
    }
    bool contains(long long k) const { return std::binary_search(keys.begin(), keys.end(), k); }
};

static std::vector<Query> make_queries(const std::vector<Record>& db, const Oracle& oracle,
                                       int hits, int misses, unsigned long long seed) {
    std::mt19937_64 rng(seed);
    KeyRange r = key_range_for(REG_NO);
    std::vector<Query> q;
    q.reserve((size_t)(hits + misses));
    for (int i = 0; i < hits && !db.empty(); i++)
        q.push_back({db[rng() % db.size()].reg_no, true});
    for (int i = 0; i < misses; i++) {
        long long k;
        do { k = random_key(rng, r); } while (oracle.contains(k));
        q.push_back({k, false});
    }
    for (int i = (int)q.size() - 1; i > 0; i--) {             // mix found / not-found
        int j = (int)(rng() % (unsigned long long)(i + 1));
        std::swap(q[(size_t)i], q[(size_t)j]);
    }
    return q;
}

static bool result_ok(const std::vector<Record>& db, long long key, bool present, int r) {
    if (present) return r >= 0 && r < (int)db.size() && db[(size_t)r].reg_no == key;
    return r == -1;
}

// ------------------------------------------------------------------ measuring
struct SearchStats {
    double hit_avg = 0, miss_avg = 0, all_avg = 0;
    long long max_c = 0;
    int correct = 0, total = 0;
    double us = 0;                            // average microseconds per search
};

// Pass 1: run each query once, count comparisons, check every answer.
template <class F>
static SearchStats count_pass(const std::vector<Query>& qs, size_t count,
                              const std::vector<Record>& db, F search) {
    SearchStats s;
    long long hs = 0, ms = 0;
    int h = 0, m = 0;
    for (size_t i = 0; i < count; i++) {
        long long c = 0;
        int r = search(qs[i].key, c);
        if (result_ok(db, qs[i].key, qs[i].present, r)) s.correct++;
        if (qs[i].present) { hs += c; h++; } else { ms += c; m++; }
        s.max_c = std::max(s.max_c, c);
    }
    s.total = (int)count;
    s.hit_avg = h ? (double)hs / h : 0;
    s.miss_avg = m ? (double)ms / m : 0;
    s.all_avg = count ? (double)(hs + ms) / (double)count : 0;
    return s;
}

// Pass 2: time the same queries. Repeats the whole batch until at least
// min_ms has passed, so even very fast searches are timed accurately.
template <class F>
static double time_us_per_search(const std::vector<Query>& qs, size_t count, F search,
                                 double min_ms = 200.0) {
    long long acc = 0, dummy = 0, reps = 0;
    auto t0 = Clock::now();
    double el;
    do {
        for (size_t i = 0; i < count; i++) acc += search(qs[i].key, dummy);
        reps++;
        el = ms_since(t0);
    } while (el < min_ms);
    g_sink = g_sink + acc;
    return el * 1000.0 / ((double)reps * (double)count);
}

// Average time of one call of work(), repeated until min_ms has passed.
template <class F>
static double time_ms_avg(F work, double min_ms = 200.0) {
    int reps = 0;
    auto t0 = Clock::now();
    double el;
    do { work(); reps++; el = ms_since(t0); } while (el < min_ms);
    return el / reps;
}

// Median time (ms) of `runs` timed runs of the whole batch.
template <class F>
static double median_batch_ms(const std::vector<Query>& qs, size_t count, F search, int runs) {
    std::vector<double> t;
    long long acc = 0, dummy = 0;
    for (int k = 0; k < runs; k++) {
        auto t0 = Clock::now();
        for (size_t i = 0; i < count; i++) acc += search(qs[i].key, dummy);
        t.push_back(ms_since(t0));
    }
    g_sink = g_sink + acc;
    std::sort(t.begin(), t.end());
    return t[t.size() / 2];
}

// ------------------------------------------------------------------ CSV merge
// results/raw/<prefix>_<n>.csv  ->  results/<out>   (sorted by n, one header)
static void merge_raw(const std::string& prefix, const std::string& out_path) {
    std::map<long long, std::string> files;
    if (!fs::exists("results/raw")) return;
    for (const auto& e : fs::directory_iterator("results/raw")) {
        std::string f = e.path().filename().string();
        if (f.rfind(prefix + "_", 0) == 0 && f.size() > 4 && f.substr(f.size() - 4) == ".csv") {
            std::string num = f.substr(prefix.size() + 1, f.size() - prefix.size() - 5);
            try { files[std::stoll(num)] = e.path().string(); } catch (...) {}
        }
    }
    std::ofstream out(out_path);
    bool header_done = false;
    for (const auto& kv : files) {
        std::ifstream in(kv.second);
        std::string line;
        bool first = true;
        while (std::getline(in, line)) {
            if (first) { first = false; if (header_done) continue; header_done = true; }
            out << line << '\n';
        }
    }
}

// =================================================================== TASK 9
struct CaseRow { std::string algo, kase; long long key; double measured; std::string theory; };

static void run_bench(int n) {
    banner("Task 9 benchmark  |  n = " + commas(n) + " records");
    const unsigned long long seed = personal_seed();
    const int HITS = 500, MISSES = 500, Q = HITS + MISSES;

    auto t0 = Clock::now();
    std::vector<Record> db = generate_dataset(n, REG_NO, NAME, seed);
    double gen_ms = ms_since(t0);
    Oracle oracle(db);
    std::vector<Query> qs = make_queries(db, oracle, HITS, MISSES, seed * 7919ULL + (unsigned long long)n);

    std::printf("[1] Dataset : %s unique records, generated in %.1f ms, stored in random order\n",
                commas(n).c_str(), gen_ms);
    std::printf("    Queries : %d present + %d absent keys - the SAME %d queries for all three algorithms\n\n",
                HITS, MISSES, Q);

    // ---------------- preprocessing
    long long sort_comps = 0;
    std::vector<IndexEntry> index = build_sorted_index(db, sort_comps);
    double sort_ms = time_ms_avg([&] {
        long long c = 0;
        std::vector<IndexEntry> ix = build_sorted_index(db, c);
        g_sink = g_sink + (long long)ix.size();
    });
    HashTable ht;
    hash_build(ht, db, TARGET_LOAD);
    double hash_ms = time_ms_avg([&] {
        HashTable t;
        hash_build(t, db, TARGET_LOAD);
        g_sink = g_sink + t.m;
    });
    const double alpha = ht.load_factor();
    const int longest = hash_longest_chain(ht);
    const double th_sort = n > 1 ? n * lg(n) : 0;

    std::printf("[2] Preprocessing (done once, before any search)\n");
    std::printf("    %-20s %-46s %15s %11s\n", "Algorithm", "Work", "Basic ops", "Time (ms)");
    std::printf("    %-20s %-46s %15s %11.3f\n", "Linear (iterative)", "none - searches the raw records", "0", 0.0);
    std::printf("    %-20s %-46s %15s %11.3f\n", "Binary (recursive)",
                ("merge sort; theory n*log2(n) = " + commas((long long)th_sort)).c_str(),
                (commas(sort_comps) + " cmp").c_str(), sort_ms);
    std::printf("    %-20s %-46s %15s %11.3f\n", "Hash table",
                ("m = " + commas(ht.m) + ", alpha = " + fmt("%.3f", alpha) +
                 ", max chain = " + std::to_string(longest)).c_str(),
                (commas(n) + " ins").c_str(), hash_ms);
    std::printf("\n");

    // ---------------- searching
    auto lin = [&](long long k, long long& c) { return linear_search(db, k, c); };
    auto bin = [&](long long k, long long& c) { return binary_search(index, k, c); };
    auto hsh = [&](long long k, long long& c) { return hash_search(ht, k, c); };

    SearchStats sl = count_pass(qs, qs.size(), db, lin);
    SearchStats sb = count_pass(qs, qs.size(), db, bin);
    SearchStats sh = count_pass(qs, qs.size(), db, hsh);
    sl.us = time_us_per_search(qs, qs.size(), lin);
    sb.us = time_us_per_search(qs, qs.size(), bin);
    sh.us = time_us_per_search(qs, qs.size(), hsh);

    const double thl_h = (n + 1) / 2.0, thl_m = n;
    const double thb_h = lg(n + 1.0) - 1.0, thb_m = lg(n + 1.0);
    const double thh_h = 1.0 + alpha / 2.0 - alpha / (2.0 * n), thh_m = alpha;

    std::printf("[3] Searching: %d queries per algorithm  (comparisons = key comparisons per search;\n"
                "    us/search = average over repeated passes of the same queries, at least 200 ms)\n", Q);
    std::printf("    %-20s %12s %10s %13s %10s %9s %11s %10s\n", "Algorithm", "found: meas", "theory",
                "absent: meas", "theory", "max seen", "us/search", "correct");
    auto row = [&](const char* name, const SearchStats& s, double th_h, double th_m) {
        std::printf("    %-20s %12.2f %10.2f %13.2f %10.2f %9lld %11.4f %10s\n", name, s.hit_avg, th_h,
                    s.miss_avg, th_m, s.max_c, s.us,
                    (std::to_string(s.correct) + "/" + std::to_string(s.total)).c_str());
    };
    row("Linear (iterative)", sl, thl_h, thl_m);
    row("Binary (recursive)", sb, thb_h, thb_m);
    row("Hash table", sh, thh_h, thh_m);
    std::printf("    theory: linear (n+1)/2 and n | binary log2(n+1)-1 and log2(n+1) | hash 1+alpha/2 and alpha\n\n");

    // ---------------- case analysis (Task 4 evidence)
    std::vector<CaseRow> cases;
    auto one = [&](auto f, long long key) { long long c = 0; f(key, c); return (double)c; };
    const int floor_lg = n > 0 ? (int)std::floor(lg(n)) : 0;
    long long own_lin = (long long)one(lin, REG_NO);

    cases.push_back({"Linear", "Best: key is 1st record", db.front().reg_no, one(lin, db.front().reg_no), "1"});
    cases.push_back({"Linear", "Worst: key is last record", db.back().reg_no, one(lin, db.back().reg_no), "n = " + commas(n)});
    cases.push_back({"Linear", "Worst: absent (reg no + 1)", REG_NO + 1, one(lin, REG_NO + 1), "n = " + commas(n)});
    cases.push_back({"Linear", "Own reg no (found)", REG_NO, (double)own_lin, "its position = " + commas(own_lin)});
    cases.push_back({"Linear", "Average: 500 random present", -1, sl.hit_avg, "(n+1)/2 = " + fmt("%.1f", thl_h)});

    const long long mid_key = index[(size_t)(n - 1) / 2].key;
    const long long above_max = index.back().key + 1;
    cases.push_back({"Binary", "Best: key at middle of index", mid_key, one(bin, mid_key), "1"});
    cases.push_back({"Binary", "Worst: key > largest key", above_max, one(bin, above_max),
                     "floor(log2 n)+1 = " + std::to_string(floor_lg + 1)});
    cases.push_back({"Binary", "Absent: reg no + 1", REG_NO + 1, one(bin, REG_NO + 1), "~log2(n+1) = " + fmt("%.2f", thb_m)});
    cases.push_back({"Binary", "Own reg no (found)", REG_NO, one(bin, REG_NO), "<= " + std::to_string(floor_lg + 1)});
    cases.push_back({"Binary", "Average: 500 random present", -1, sb.hit_avg, "~log2(n+1)-1 = " + fmt("%.2f", thb_h)});

    std::vector<int> len = hash_chain_lengths(ht);
    long long b_best = -1, b_empty = -1, b_long = 0;
    for (long long b = 0; b < ht.m; b++) {
        if (len[(size_t)b] > 0 && b_best < 0) b_best = b;
        if (len[(size_t)b] == 0 && b_empty < 0) b_empty = b;
        if (len[(size_t)b] > len[(size_t)b_long]) b_long = b;
    }
    long long best_key = ht.keys[(size_t)ht.head[(size_t)b_best]];
    int e = ht.head[(size_t)b_long];
    while (ht.next[(size_t)e] != -1) e = ht.next[(size_t)e];
    long long worst_key = ht.keys[(size_t)e];
    KeyRange kr = key_range_for(REG_NO);
    long long empty_key = -1;
    if (b_empty >= 0) {
        long long t = (kr.lo - b_empty + ht.m - 1) / ht.m;
        empty_key = b_empty + t * ht.m;
    }
    cases.push_back({"Hash", "Best: key at head of a chain", best_key, one(hsh, best_key), "1"});
    if (empty_key > 0)
        cases.push_back({"Hash", "Best absent: empty bucket", empty_key, one(hsh, empty_key), "0"});
    cases.push_back({"Hash", "Worst: end of longest chain", worst_key, one(hsh, worst_key),
                     "longest chain = " + std::to_string(longest)});
    cases.push_back({"Hash", "Absent: reg no + 1", REG_NO + 1, one(hsh, REG_NO + 1),
                     "its chain length = " + std::to_string(len[(size_t)((REG_NO + 1) % ht.m)])});
    cases.push_back({"Hash", "Own reg no (found)", REG_NO, one(hsh, REG_NO), "its place in its chain"});
    cases.push_back({"Hash", "Average: 500 random present", -1, sh.hit_avg, "1+alpha/2 = " + fmt("%.3f", thh_h)});

    std::printf("[4] Case analysis (Task 4): the input that triggers each case, and its comparison count\n");
    std::printf("    %-8s %-30s %16s %12s   %s\n", "Algo", "Case", "Search key", "Comparisons", "Theory");
    for (const CaseRow& c : cases) {
        std::string key = c.key < 0 ? "-" : std::to_string(c.key);
        std::printf("    %-8s %-30s %16s %12.2f   %s\n", c.algo.c_str(), c.kase.c_str(), key.c_str(),
                    c.measured, c.theory.c_str());
    }
    std::printf("\n");

    // ---------------- total cost
    const double search_l = sl.us * Q / 1000.0, search_b = sb.us * Q / 1000.0, search_h = sh.us * Q / 1000.0;
    std::printf("[5] Total cost = preprocessing + %d searches\n", Q);
    std::printf("    %-20s %16s %20s %14s\n", "Algorithm", "Preprocess (ms)", "Searching (ms)", "Total (ms)");
    std::printf("    %-20s %16.3f %20.3f %14.3f\n", "Linear (iterative)", 0.0, search_l, search_l);
    std::printf("    %-20s %16.3f %20.3f %14.3f\n", "Binary (recursive)", sort_ms, search_b, sort_ms + search_b);
    std::printf("    %-20s %16.3f %20.3f %14.3f\n", "Hash table", hash_ms, search_h, hash_ms + search_h);
    auto breakeven = [&](double pre_ms, double us) -> std::string {
        double gain_ms = (sl.us - us) / 1000.0;
        if (gain_ms <= 0) return "never";
        return commas((long long)std::ceil(pre_ms / gain_ms));
    };
    std::printf("    Break-even vs linear: sorted index pays off after %s searches, hash table after %s searches\n\n",
                breakeven(sort_ms, sb.us).c_str(), breakeven(hash_ms, sh.us).c_str());

    // ---------------- CSV
    fs::create_directories("results/raw");
    {
        std::ofstream f("results/raw/bench_" + std::to_string(n) + ".csv");
        f.precision(12);                                   // keep every digit in the CSV
        f << "reg_no,name,n,algorithm,preprocess_ms,preprocess_basic_ops,theory_preprocess_ops,queries,"
             "avg_comp_found,theory_comp_found,avg_comp_absent,theory_comp_absent,avg_comp_all,max_comp,"
             "us_per_search,search_ms_total,total_ms,correct,load_factor,longest_chain\n";
        auto w = [&](const char* a, double pre, long long pre_ops, double th_pre, const SearchStats& s,
                     double th_h, double th_m, double search_ms) {
            f << REG_NO << ",\"" << NAME << "\"," << n << ',' << a << ',' << pre << ',' << pre_ops << ','
              << (long long)th_pre << ',' << Q << ',' << s.hit_avg << ',' << th_h << ',' << s.miss_avg << ','
              << th_m << ',' << s.all_avg << ',' << s.max_c << ',' << s.us << ',' << search_ms << ','
              << pre + search_ms << ',' << s.correct << ',' << alpha << ',' << longest << '\n';
        };
        w("Linear search", 0.0, 0, 0, sl, thl_h, thl_m, search_l);
        w("Binary search", sort_ms, sort_comps, th_sort, sb, thb_h, thb_m, search_b);
        w("Hash table", hash_ms, n, n, sh, thh_h, thh_m, search_h);
    }
    {
        std::ofstream f("results/raw/cases_" + std::to_string(n) + ".csv");
        f.precision(12);                                   // keep every digit in the CSV
        f << "n,algorithm,case,search_key,comparisons,theory\n";
        for (const CaseRow& c : cases)
            f << n << ',' << c.algo << ",\"" << c.kase << "\"," << (c.key < 0 ? std::string("") : std::to_string(c.key))
              << ',' << c.measured << ",\"" << c.theory << "\"\n";
    }
    merge_raw("bench", "results/results.csv");
    merge_raw("cases", "results/cases.csv");
    std::printf("[6] Saved results/raw/bench_%d.csv -> merged into results/results.csv (and results/cases.csv)\n", n);
    rule('-');
}

// =================================================================== TASK 8
static int g_pass = 0, g_fail = 0;

static std::string cell(int r, long long c) {
    return (r >= 0 ? std::string("FOUND") : std::string("NOT FOUND")) + " (" + std::to_string(c) + ")";
}

static void run_cases(const std::vector<Record>& db, const char* label) {
    std::vector<IndexEntry> index;
    long long sc = 0;
    index = build_sorted_index(db, sc);
    HashTable ht;
    hash_build(ht, db, TARGET_LOAD);
    Oracle oracle(db);
    const int n = (int)db.size();

    struct T { std::string name; long long key; };
    std::vector<T> tests;
    tests.push_back({"Own reg no", REG_NO});
    tests.push_back({"Own reg no + 1", REG_NO + 1});
    if (n == 1) {
        tests.push_back({"Below the only key", db.front().reg_no - 1});
    }
    if (n >= 2) {
        std::mt19937_64 rng(personal_seed() + 99);
        KeyRange r = key_range_for(REG_NO);
        long long absent;
        do { absent = random_key(rng, r); } while (oracle.contains(absent));
        tests.push_back({"First record (DB order)", db.front().reg_no});
        tests.push_back({"Last record (DB order)", db.back().reg_no});
        tests.push_back({"Smallest reg no", index.front().key});
        tests.push_back({"Largest reg no", index.back().key});
        tests.push_back({"Below smallest (min - 1)", index.front().key - 1});
        tests.push_back({"Above largest (max + 1)", index.back().key + 1});
        tests.push_back({"Random present key", db[rng() % (unsigned long long)n].reg_no});
        tests.push_back({"Random absent key", absent});
    }

    std::printf("%s\n", label);
    std::printf("    %-2s %-26s %14s %-10s %-17s %-15s %-15s %s\n", "#", "Test case", "Key", "Expected",
                "Linear (comps)", "Binary (comps)", "Hash (comps)", "Result");
    int idx = 1;
    for (const T& t : tests) {
        bool expect = oracle.contains(t.key);
        long long cl = 0, cb = 0, ch = 0;
        int rl = linear_search(db, t.key, cl);
        int rb = binary_search(index, t.key, cb);
        int rh = hash_search(ht, t.key, ch);
        bool ok = result_ok(db, t.key, expect, rl) && result_ok(db, t.key, expect, rb) &&
                  result_ok(db, t.key, expect, rh) && rl == rb && rb == rh;
        ok ? g_pass++ : g_fail++;
        std::printf("    %-2d %-26s %14lld %-10s %-17s %-15s %-15s %s\n", idx++, t.name.c_str(), t.key,
                    expect ? "FOUND" : "NOT FOUND", cell(rl, cl).c_str(), cell(rb, cb).c_str(),
                    cell(rh, ch).c_str(), ok ? "PASS" : "FAIL");
    }
    long long c = 0;
    int r = hash_search(ht, REG_NO, c);
    if (r >= 0)
        std::printf("    Record retrieved for %lld -> position %d | %s | %s | CGPA %.2f (all three agree)\n",
                    REG_NO, r, db[(size_t)r].name, db[(size_t)r].dept, db[(size_t)r].cgpa);
    std::printf("\n");
}

static int run_test() {
    banner("Task 8 correctness tests  |  linear, binary (recursive), hash table");
    const unsigned long long seed = personal_seed();

    std::vector<Record> db = generate_dataset(1000, REG_NO, NAME, seed);
    run_cases(db, "[A] Fixed test cases on the n = 1,000 dataset  (FOUND/NOT FOUND, key comparisons in brackets)");

    std::vector<Record> empty;
    run_cases(empty, "[B1] Edge case: empty database (n = 0)");
    std::vector<Record> single = generate_dataset(1, REG_NO, NAME, seed);
    run_cases(single, "[B2] Edge case: database with one record (n = 1)");

    std::printf("[C] Random cross-check against an independent answer key (std::sort + std::binary_search)\n");
    std::printf("    %-11s %9s %14s %14s %14s %12s %13s %7s\n", "n", "queries", "linear ok", "binary ok",
                "hash ok", "own found", "own+1 absent", "result");
    for (int n : SIZES) {
        std::vector<Record> d = generate_dataset(n, REG_NO, NAME, seed);
        Oracle o(d);
        std::vector<Query> qs = make_queries(d, o, 500, 500, seed * 7919ULL + (unsigned long long)n);
        long long sc = 0;
        std::vector<IndexEntry> ix = build_sorted_index(d, sc);
        HashTable ht;
        hash_build(ht, d, TARGET_LOAD);
        auto lin = [&](long long k, long long& c) { return linear_search(d, k, c); };
        auto bin = [&](long long k, long long& c) { return binary_search(ix, k, c); };
        auto hsh = [&](long long k, long long& c) { return hash_search(ht, k, c); };
        SearchStats a = count_pass(qs, qs.size(), d, lin);
        SearchStats b = count_pass(qs, qs.size(), d, bin);
        SearchStats h = count_pass(qs, qs.size(), d, hsh);
        long long c = 0;
        bool own = linear_search(d, REG_NO, c) >= 0 && binary_search(ix, REG_NO, c) >= 0 && hash_search(ht, REG_NO, c) >= 0;
        bool own1 = linear_search(d, REG_NO + 1, c) < 0 && binary_search(ix, REG_NO + 1, c) < 0 && hash_search(ht, REG_NO + 1, c) < 0;
        bool ok = a.correct == a.total && b.correct == b.total && h.correct == h.total && own && own1;
        ok ? g_pass++ : g_fail++;
        auto frac = [](const SearchStats& s) { return std::to_string(s.correct) + "/" + std::to_string(s.total); };
        std::printf("    %-11s %9zu %14s %14s %14s %12s %13s %7s\n", commas(n).c_str(), qs.size(),
                    frac(a).c_str(), frac(b).c_str(), frac(h).c_str(), own ? "yes" : "NO",
                    own1 ? "yes" : "NO", ok ? "PASS" : "FAIL");
    }
    std::printf("\n");
    rule('-');
    std::printf(" SUMMARY: %d passed, %d failed  ->  %s\n", g_pass, g_fail,
                g_fail == 0 ? "ALL TESTS PASSED" : "SOME TESTS FAILED");
    rule('-');
    return g_fail == 0 ? 0 : 1;
}

// =================================================================== TASK 12
static int run_task12(bool full_linear) {
    banner("Task 12  |  50,000 searches/hour on 1,000,000 records, new records once a day");
    const int N = 1000000, Q = 50000, PRESENT = 45000, ABSENT = 5000;
    const int LIN_SAMPLE = full_linear ? Q : 2000;
    const int DAILY_NEW = 10000;
    const double PER_DAY = 24.0 * Q;
    const unsigned long long seed = personal_seed();

    auto t0 = Clock::now();
    std::vector<Record> db = generate_dataset(N, REG_NO, NAME, seed);
    double gen_ms = ms_since(t0);
    Oracle oracle(db);
    std::vector<Query> qs = make_queries(db, oracle, PRESENT, ABSENT, seed * 104729ULL + 12);

    std::printf("[1] Workload: %s records (generated in %.0f ms). %s searches per hour = %.1f per second.\n",
                commas(N).c_str(), gen_ms, commas(Q).c_str(), Q / 3600.0);
    std::printf("    Query mix: %s present + %s absent (most lookups are for students who exist).\n",
                commas(PRESENT).c_str(), commas(ABSENT).c_str());
    std::printf("    Per day: %s searches, but only ONE batch of new records -> index built once per day.\n\n",
                commas((long long)PER_DAY).c_str());

    // ---------------- preprocessing (once per day)
    long long sort_comps = 0;
    std::vector<IndexEntry> index = build_sorted_index(db, sort_comps);
    double sort_ms = time_ms_avg([&] {
        long long c = 0;
        std::vector<IndexEntry> ix = build_sorted_index(db, c);
        g_sink = g_sink + (long long)ix.size();
    }, 300.0);
    HashTable ht;
    hash_build(ht, db, TARGET_LOAD);
    double hash_ms = time_ms_avg([&] {
        HashTable t;
        hash_build(t, db, TARGET_LOAD);
        g_sink = g_sink + t.m;
    }, 300.0);
    std::printf("[2] Preprocessing, done once per day\n");
    std::printf("    Binary search : merge sort of the index   %10.2f ms  (%s comparisons)\n", sort_ms, commas(sort_comps).c_str());
    std::printf("    Hash table    : build %s buckets       %10.2f ms  (alpha = %.3f, longest chain = %d)\n",
                commas(ht.m).c_str(), hash_ms, ht.load_factor(), hash_longest_chain(ht));
    std::printf("    Extra memory  : sorted index %.1f MB (+%.1f MB temporary while sorting), hash table %.1f MB,"
                " records %.1f MB\n\n", index.size() * sizeof(IndexEntry) / 1e6, index.size() * sizeof(IndexEntry) / 1e6,
                ht.bytes() / 1e6, db.size() * sizeof(Record) / 1e6);

    // ---------------- 50,000 searches
    auto lin = [&](long long k, long long& c) { return linear_search(db, k, c); };
    auto bin = [&](long long k, long long& c) { return binary_search(index, k, c); };
    auto hsh = [&](long long k, long long& c) { return hash_search(ht, k, c); };

    SearchStats sh = count_pass(qs, (size_t)Q, db, hsh);
    double hash_q_ms = median_batch_ms(qs, (size_t)Q, hsh, 5);
    SearchStats sb = count_pass(qs, (size_t)Q, db, bin);
    double bin_q_ms = median_batch_ms(qs, (size_t)Q, bin, 5);
    t0 = Clock::now();
    SearchStats sl = count_pass(qs, (size_t)LIN_SAMPLE, db, lin);   // linear is slow: time this one pass
    double lin_sample_ms = ms_since(t0);
    double lin_q_ms = lin_sample_ms * Q / LIN_SAMPLE;

    std::printf("[3] Running the hourly load: %s searches\n", commas(Q).c_str());
    std::printf("    %-20s %15s %18s %13s %11s %10s %14s\n", "Algorithm", "searches run", "time for 50,000",
                "us/search", "avg comps", "max comps", "correct");
    auto row = [&](const char* name, int run, double ms, const SearchStats& s, const char* note) {
        std::printf("    %-20s %15s %15.2f ms %13.4f %11.2f %10lld %14s %s\n", name, commas(run).c_str(), ms,
                    ms * 1000.0 / Q, s.all_avg, s.max_c,
                    (commas(s.correct) + "/" + commas(s.total)).c_str(), note);
    };
    row("Hash table", Q, hash_q_ms, sh, "");
    row("Binary (recursive)", Q, bin_q_ms, sb, "");
    row("Linear (iterative)", LIN_SAMPLE, lin_q_ms, sl,
        full_linear ? "" : "<- measured on 2,000, scaled x25");
    std::printf("\n");

    // ---------------- cost per hour / day
    std::printf("[4] Cost of the new operating conditions\n");
    std::printf("    %-20s %16s %15s %12s %17s %20s\n", "Algorithm", "build/day (ms)", "CPU/hour (ms)",
                "% of 1 hour", "CPU/day (ms)", "build per search(us)");
    auto cost = [&](const char* name, double build, double hour_ms) {
        std::printf("    %-20s %16.2f %15.2f %11.4f%% %17.1f %20.4f\n", name, build, hour_ms,
                    hour_ms / 3600000.0 * 100.0, build + 24.0 * hour_ms, build * 1000.0 / PER_DAY);
    };
    cost("Hash table", hash_ms, hash_q_ms);
    cost("Binary (recursive)", sort_ms, bin_q_ms);
    cost("Linear (iterative)", 0.0, lin_q_ms);
    std::printf("\n");

    // ---------------- daily update: 10,000 new records
    std::mt19937_64 rng(seed * 31ULL + 5);
    KeyRange kr = key_range_for(REG_NO);
    std::vector<Record> fresh;
    {
        std::unordered_set<long long> taken;                 // keys already in today's batch
        while ((int)fresh.size() < DAILY_NEW) {
            long long k = random_key(rng, kr);
            if (k == REG_NO + 1 || oracle.contains(k)) continue;   // must be a NEW student
            if (!taken.insert(k).second) continue;                 // no duplicates in the batch
            char nm[20];
            std::snprintf(nm, sizeof(nm), "New_%d", (int)fresh.size() + 1);
            fresh.push_back(make_record(k, nm, rng));
        }
    }

    std::vector<Record> db_new = db;
    db_new.reserve((size_t)(N + DAILY_NEW));          // space reserved up front, as a real table would
    t0 = Clock::now();
    for (const Record& r : fresh) db_new.push_back(r);                       // linear: just append
    double lin_upd_ms = ms_since(t0);

    std::vector<IndexEntry> batch;
    for (int i = 0; i < DAILY_NEW; i++) batch.push_back({fresh[(size_t)i].reg_no, N + i});
    std::vector<IndexEntry> index_inc = index;
    long long merge_comps = 0;
    t0 = Clock::now();
    merge_batch_into_index(index_inc, batch, merge_comps);                   // sort batch + merge
    double bin_inc_ms = ms_since(t0);

    long long full_comps = 0;
    t0 = Clock::now();
    std::vector<IndexEntry> index_full = build_sorted_index(db_new, full_comps);   // full re-sort
    double bin_full_ms = ms_since(t0);

    ht.reserve((size_t)(N + DAILY_NEW));              // spare capacity reserved before the update
    t0 = Clock::now();
    for (int i = 0; i < DAILY_NEW; i++) hash_insert(ht, fresh[(size_t)i].reg_no, N + i);   // incremental
    double hash_inc_ms = ms_since(t0);

    HashTable ht_full;
    t0 = Clock::now();
    hash_build(ht_full, db_new, TARGET_LOAD);                                // full rebuild
    double hash_full_ms = ms_since(t0);

    // verify the updated structures
    int upd_ok = 0, upd_total = 0;
    for (int i = 0; i < DAILY_NEW; i += 10) {
        long long c = 0, key = fresh[(size_t)i].reg_no;
        int rb = binary_search(index_inc, key, c), rh = hash_search(ht, key, c);
        bool ok = rb == N + i && rh == N + i && db_new[(size_t)rb].reg_no == key;
        if (i % 50 == 0) ok = ok && linear_search(db_new, key, c) == N + i;
        upd_ok += ok; upd_total++;
    }
    for (int i = 0; i < 1000; i++) {
        const Query& q = qs[(size_t)i];
        long long c = 0;
        int rb = binary_search(index_inc, q.key, c), rh = hash_search(ht, q.key, c);
        upd_ok += (rb == rh) && result_ok(db_new, q.key, q.present, rh);
        upd_total++;
    }

    std::printf("[5] Daily update: %s new records added (database grows to %s)\n", commas(DAILY_NEW).c_str(),
                commas(N + DAILY_NEW).c_str());
    std::printf("    %-19s %-40s %10s  %-23s %10s\n", "Algorithm", "Incremental update", "time (ms)",
                "Full rebuild", "time (ms)");
    std::printf("    %-19s %-40s %10.3f  %-23s %10s\n", "Linear (iterative)", "append records, no index", lin_upd_ms, "-", "-");
    std::printf("    %-19s %-40s %10.3f  %-23s %10.3f\n", "Binary (recursive)",
                ("sort batch + merge (" + commas(merge_comps) + " comps)").c_str(), bin_inc_ms,
                "merge sort all records", bin_full_ms);
    std::printf("    %-19s %-40s %10.3f  %-23s %10.3f\n", "Hash table",
                ("insert 10,000 keys; alpha now " + fmt("%.3f", ht.load_factor())).c_str(), hash_inc_ms,
                "rebuild whole table", hash_full_ms);
    std::printf("    Check after update: %d/%d lookups correct (new keys found, old answers unchanged)\n\n",
                upd_ok, upd_total);
    g_sink = g_sink + (long long)index_full.size() + ht_full.m + full_comps;

    // ---------------- summary
    std::printf("[6] Summary (from the numbers above)\n");
    std::printf("    Hash table is %.1fx faster per search than binary search and %.0fx faster than linear search.\n",
                bin_q_ms / hash_q_ms, lin_q_ms / hash_q_ms);
    std::printf("    Building the hash table once a day costs %.4f us per search when spread over %s searches.\n",
                hash_ms * 1000.0 / PER_DAY, commas((long long)PER_DAY).c_str());
    std::printf("    Linear search would need %.1f s of CPU every hour; the hash table needs %.2f ms.\n",
                lin_q_ms / 1000.0, hash_q_ms);

    fs::create_directories("results");
    std::ofstream f("results/task12.csv");
    f.precision(12);                                   // keep every digit in the CSV
    f << "reg_no,name,algorithm,build_ms_per_day,searches_run,ms_for_50000,us_per_search,avg_comps,max_comps,"
         "cpu_ms_per_hour,pct_of_hour,cpu_ms_per_day,build_us_per_search,update_incremental_ms,update_rebuild_ms,"
         "correct,scaled_from_sample\n";
    auto w = [&](const char* a, double build, int run, double qms, const SearchStats& s, double inc, double full,
                 bool scaled) {
        f << REG_NO << ",\"" << NAME << "\"," << a << ',' << build << ',' << run << ',' << qms << ','
          << qms * 1000.0 / Q << ',' << s.all_avg << ',' << s.max_c << ',' << qms << ','
          << qms / 3600000.0 * 100.0 << ',' << build + 24.0 * qms << ',' << build * 1000.0 / PER_DAY << ','
          << inc << ',' << full << ',' << s.correct << ',' << (scaled ? "yes" : "no") << '\n';
    };
    w("Hash table", hash_ms, Q, hash_q_ms, sh, hash_inc_ms, hash_full_ms, false);
    w("Binary search", sort_ms, Q, bin_q_ms, sb, bin_inc_ms, bin_full_ms, false);
    w("Linear search", 0.0, LIN_SAMPLE, lin_q_ms, sl, lin_upd_ms, 0.0, !full_linear);
    std::printf("[7] Saved results/task12.csv\n");
    rule('-');
    return 0;
}

// =================================================================== main
static void help() {
    std::printf(
        "Usage:\n"
        "  daa test                   Task 8  correctness tests\n"
        "  daa bench <n>              Task 9  benchmark one size (1000, 10000, 100000, 1000000)\n"
        "  daa bench                  Task 9  all four sizes\n"
        "  daa task12 [--full-linear] Task 12 50,000 searches on 1,000,000 records\n"
        "  daa gen <n>                write data/students_<n>.csv\n"
        "Then: python src/plot_results.py   (draws the graphs into results/graphs/)\n");
}

int main(int argc, char** argv) {
    std::string cmd = argc > 1 ? argv[1] : "help";
    if (cmd == "help" || cmd == "-h" || cmd == "--help") { help(); return 0; }
    if (!config_ok()) return 1;
    try {
        if (cmd == "test") return run_test();
        if (cmd == "bench") {
            if (argc > 2) run_bench(std::stoi(argv[2]));
            else for (int n : SIZES) run_bench(n);
            return 0;
        }
        if (cmd == "task12") return run_task12(argc > 2 && std::string(argv[2]) == "--full-linear");
        if (cmd == "gen") {
            int n = argc > 2 ? std::stoi(argv[2]) : 1000;
            fs::create_directories("data");
            std::string path = "data/students_" + std::to_string(n) + ".csv";
            write_dataset_csv(generate_dataset(n, REG_NO, NAME, personal_seed()), path);
            banner("Dataset generator");
            std::printf(" Wrote %s records to %s\n", commas(n).c_str(), path.c_str());
            return 0;
        }
    } catch (const std::exception& e) {
        std::fprintf(stderr, "Error: %s\n", e.what());
        return 1;
    }
    help();
    return 1;
}
