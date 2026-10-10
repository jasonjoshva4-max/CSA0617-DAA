// =====================================================================
// Algorithm 3 : HASH TABLE with SEPARATE CHAINING  (iterative lookup)
//
// Idea: instead of searching through the records, compute WHERE a key
// must be. A hash function h(k) = k mod m maps every registration number
// to one of m buckets. Each bucket holds a short chain (linked list) of
// the keys that map to it. To search, compute h(k) and scan only that
// chain.
//
// Preprocessing: build the table once - insert all n records.
// m is chosen as the smallest PRIME >= n / target_load, so the load
// factor alpha = n / m stays near the target (0.75 here) and keys that
// share a pattern (e.g. consecutive reg nos) still spread out evenly.
// =====================================================================
#include "common.h"
#include <algorithm>
#include <cmath>

static const double MAX_LOAD = 1.0;   // grow the table if alpha would go above this

static bool is_prime(long long x) {
    if (x < 2) return false;
    if (x % 2 == 0) return x == 2;
    for (long long d = 3; d * d <= x; d += 2)
        if (x % d == 0) return false;
    return true;
}

long long next_prime(long long x) {
    if (x <= 2) return 2;
    while (!is_prime(x)) x++;
    return x;
}

// h(k) = k mod m
static inline long long bucket_of(long long key, long long m) { return key % m; }

// Re-link every existing entry into a new bucket array of size new_m.
static void rehash(HashTable& h, long long new_m) {
    h.m = new_m;
    h.head.assign((size_t)new_m, -1);
    for (int e = 0; e < (int)h.keys.size(); e++) {
        long long b = bucket_of(h.keys[e], h.m);
        h.next[e] = h.head[b];
        h.head[b] = e;
    }
}

void hash_build(HashTable& h, const std::vector<Record>& db, double target_load) {
    long long n = (long long)db.size();
    long long m = next_prime((long long)std::ceil((double)std::max(n, 1LL) / target_load));
    h.m = m;
    h.head.assign((size_t)m, -1);
    h.next.assign((size_t)n, -1);
    h.keys.resize((size_t)n);
    h.pos.resize((size_t)n);
    for (int e = 0; e < (int)n; e++) {          // n insertions, O(1) each
        h.keys[e] = db[e].reg_no;
        h.pos[e]  = e;
        long long b = bucket_of(h.keys[e], m);  // compute the bucket
        h.next[e] = h.head[b];                  // insert at the front of its chain
        h.head[b] = e;
    }
}

void hash_insert(HashTable& h, long long key, int pos) {
    if ((double)(h.keys.size() + 1) > MAX_LOAD * (double)h.m)
        rehash(h, next_prime(2 * h.m + 1));     // rare: double the buckets
    int e = (int)h.keys.size();
    h.keys.push_back(key);
    h.pos.push_back(pos);
    long long b = bucket_of(key, h.m);
    h.next.push_back(h.head[b]);
    h.head[b] = e;
}

int hash_search(const HashTable& h, long long key, long long& comparisons) {
    long long b = bucket_of(key, h.m);          // 1. jump straight to the bucket
    for (int e = h.head[b]; e != -1; e = h.next[e]) {   // 2. walk its chain
        comparisons++;                          // count one key comparison
        if (h.keys[e] == key)                   // <-- BASIC OPERATION (key comparison)
            return h.pos[e];                    // found
    }
    return -1;                                  // end of chain: not found
}

std::vector<int> hash_chain_lengths(const HashTable& h) {
    std::vector<int> len((size_t)h.m, 0);
    for (long long b = 0; b < h.m; b++)
        for (int e = h.head[b]; e != -1; e = h.next[e]) len[b]++;
    return len;
}

int hash_longest_chain(const HashTable& h) {
    std::vector<int> len = hash_chain_lengths(h);
    return len.empty() ? 0 : *std::max_element(len.begin(), len.end());
}
