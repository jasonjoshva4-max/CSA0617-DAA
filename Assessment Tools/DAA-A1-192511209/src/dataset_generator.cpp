// =====================================================================
// DATASET GENERATOR
//
// Builds n unique student records from YOUR seed (last 4 digits of your
// reg no), so every student gets a different dataset.
//   * Keys have the same number of digits as your reg no.
//   * Your own reg no is always IN the dataset (test case: found).
//   * Your reg no + 1 is never in the dataset (test case: not found).
//   * Records are shuffled, so the database is NOT sorted (realistic).
//
// Only mt19937_64 is used, with our own mapping and shuffle, so the same
// seed gives exactly the same dataset on every compiler and OS.
// =====================================================================
#include "common.h"
#include <cstdio>
#include <fstream>
#include <stdexcept>
#include <unordered_set>

static const char* DEPTS[] = {"AIML", "CSE", "ECE", "EEE", "MECH", "IT", "AIDS", "CIVIL"};

KeyRange key_range_for(long long reg_no) {
    long long lo = 1;
    while (lo <= reg_no / 10) lo *= 10;        // e.g. 231801123 -> lo = 100000000
    return {lo, lo * 10 - 1};                  //                  hi = 999999999
}

long long random_key(std::mt19937_64& rng, KeyRange r) {
    unsigned long long span = (unsigned long long)(r.hi - r.lo + 1);
    return r.lo + (long long)(rng() % span);
}

Record make_record(long long key, const char* name, std::mt19937_64& rng) {
    Record rec{};
    rec.reg_no = key;
    std::snprintf(rec.name, sizeof(rec.name), "%s", name);
    std::snprintf(rec.dept, sizeof(rec.dept), "%s", DEPTS[rng() % 8]);
    rec.cgpa = 5.0f + (float)(rng() % 501) / 100.0f;   // 5.00 .. 10.00
    return rec;
}

std::vector<Record> generate_dataset(int n, long long own_reg_no, const char* own_name,
                                     unsigned long long seed) {
    std::vector<Record> db;
    if (n <= 0) return db;

    KeyRange r = key_range_for(own_reg_no);
    if (r.hi - r.lo + 1 < 10LL * n)
        throw std::runtime_error("reg no has too few digits to make this many unique keys");

    std::mt19937_64 rng(seed);
    std::unordered_set<long long> used;
    used.reserve((size_t)n * 2);
    db.reserve((size_t)n);

    used.insert(own_reg_no);                       // your own record is always present
    db.push_back(make_record(own_reg_no, own_name, rng));

    char name[20];
    long long serial = 1;
    while ((int)db.size() < n) {
        long long k = random_key(rng, r);
        if (k == own_reg_no + 1) continue;         // keep reg no + 1 ABSENT
        if (!used.insert(k).second) continue;      // duplicate -> draw again
        std::snprintf(name, sizeof(name), "Student_%lld", serial++);
        db.push_back(make_record(k, name, rng));
    }

    // Fisher-Yates shuffle: database order becomes random
    for (int i = n - 1; i > 0; i--) {
        int j = (int)(rng() % (unsigned long long)(i + 1));
        std::swap(db[i], db[j]);
    }
    return db;
}

void write_dataset_csv(const std::vector<Record>& db, const std::string& path) {
    std::ofstream out(path);
    out << "position,reg_no,name,dept,cgpa\n";
    for (size_t i = 0; i < db.size(); i++) {
        char cg[16];
        std::snprintf(cg, sizeof(cg), "%.2f", db[i].cgpa);
        out << i << ',' << db[i].reg_no << ',' << db[i].name << ',' << db[i].dept << ',' << cg << '\n';
    }
}
