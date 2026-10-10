#pragma once
// Shared types and function declarations used by every .cpp file.
#include <random>
#include <string>
#include <vector>

// ---------------------------------------------------------------------
// One student record. Fixed-size fields, like a row in a database table.
// reg_no is the unique key we search for.
// ---------------------------------------------------------------------
struct Record {
    long long reg_no;
    char      name[20];
    char      dept[6];
    float     cgpa;
};

// One entry of the sorted index used by binary search:
// the key, plus the position of the full record inside the database.
struct IndexEntry {
    long long key;
    int       pos;
};

// =====================================================================
// Algorithm 1 : Linear search (iterative, brute force)      algo1_linear.cpp
// Returns the record's position in db, or -1 if not found.
// `comparisons` is increased by the number of key comparisons made.
// =====================================================================
int linear_search(const std::vector<Record>& db, long long key, long long& comparisons);

// =====================================================================
// Algorithm 2 : Binary search (recursive, decrease-and-conquer)
//               + merge sort preprocessing                    algo2_binary.cpp
// =====================================================================
std::vector<IndexEntry> build_sorted_index(const std::vector<Record>& db, long long& comparisons);
void merge_sort(std::vector<IndexEntry>& a, std::vector<IndexEntry>& tmp,
                int lo, int hi, long long& comparisons);
int  binary_search_recursive(const std::vector<IndexEntry>& index, long long key,
                             int lo, int hi, long long& comparisons);
int  binary_search(const std::vector<IndexEntry>& index, long long key, long long& comparisons);
// Daily update: sort a small batch of new entries and merge it into the index.
void merge_batch_into_index(std::vector<IndexEntry>& index, std::vector<IndexEntry> batch,
                            long long& comparisons);

// =====================================================================
// Algorithm 3 : Hash table with separate chaining (iterative lookup)
//               h(k) = k mod m, m prime                       algo3_hash.cpp
// =====================================================================
struct HashTable {
    std::vector<int>       head;  // head[b] = first entry in bucket b (-1 = empty)
    std::vector<int>       next;  // next[e] = next entry in the same bucket (-1 = end)
    std::vector<long long> keys;  // keys[e] = registration number of entry e
    std::vector<int>       pos;   // pos[e]  = position of that record in the database
    long long              m = 0; // number of buckets

    long long size() const { return (long long)keys.size(); }
    double load_factor() const { return m ? (double)keys.size() / (double)m : 0.0; }
    // Make room for `cap` entries in advance, so later inserts never copy the arrays.
    void reserve(size_t cap) { next.reserve(cap); keys.reserve(cap); pos.reserve(cap); }
    // Memory used: 4 bytes per bucket + 16 bytes per entry (next, key, pos).
    long long bytes() const { return m * 4 + (long long)keys.size() * 16; }
};

long long next_prime(long long x);
void hash_build(HashTable& h, const std::vector<Record>& db, double target_load);
void hash_insert(HashTable& h, long long key, int pos);
int  hash_search(const HashTable& h, long long key, long long& comparisons);
int  hash_longest_chain(const HashTable& h);
std::vector<int> hash_chain_lengths(const HashTable& h);

// =====================================================================
// Dataset generator                                     dataset_generator.cpp
// =====================================================================
struct KeyRange { long long lo, hi; };

KeyRange  key_range_for(long long reg_no);
long long random_key(std::mt19937_64& rng, KeyRange r);
Record    make_record(long long key, const char* name, std::mt19937_64& rng);
std::vector<Record> generate_dataset(int n, long long own_reg_no, const char* own_name,
                                     unsigned long long seed);
void write_dataset_csv(const std::vector<Record>& db, const std::string& path);
