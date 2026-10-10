// =====================================================================
// Algorithm 2 : BINARY SEARCH  (recursive, decrease-and-conquer)
//
// Idea: if the keys are in sorted order, compare the key with the middle
// one. Equal -> found. Smaller -> the key can only be in the left half.
// Larger -> only in the right half. Each call throws away half the range.
//
// Preprocessing: the database is unsorted, so we first build an index of
// (key, position) pairs and sort it with merge sort. The sort cost belongs
// to this algorithm's total cost.
// =====================================================================
#include "common.h"

// ---------------- Preprocessing: merge sort (recursive) ----------------
void merge_sort(std::vector<IndexEntry>& a, std::vector<IndexEntry>& tmp,
                int lo, int hi, long long& comparisons) {
    if (lo >= hi) return;                         // 0 or 1 element: already sorted
    int mid = lo + (hi - lo) / 2;
    merge_sort(a, tmp, lo, mid, comparisons);     // sort left half
    merge_sort(a, tmp, mid + 1, hi, comparisons); // sort right half

    // merge the two sorted halves into tmp, then copy back
    int i = lo, j = mid + 1, k = lo;
    while (i <= mid && j <= hi) {
        comparisons++;                            // basic operation of the sort
        if (a[i].key <= a[j].key) tmp[k++] = a[i++];
        else                      tmp[k++] = a[j++];
    }
    while (i <= mid) tmp[k++] = a[i++];
    while (j <= hi)  tmp[k++] = a[j++];
    for (k = lo; k <= hi; k++) a[k] = tmp[k];
}

std::vector<IndexEntry> build_sorted_index(const std::vector<Record>& db, long long& comparisons) {
    int n = (int)db.size();
    std::vector<IndexEntry> index(n), tmp(n);
    for (int i = 0; i < n; i++) index[i] = {db[i].reg_no, i};   // O(n) copy of keys
    if (n > 1) merge_sort(index, tmp, 0, n - 1, comparisons);    // O(n log n) sort
    return index;
}

// ---------------- Search: recursive binary search ----------------
int binary_search_recursive(const std::vector<IndexEntry>& index, long long key,
                            int lo, int hi, long long& comparisons) {
    if (lo > hi) return -1;                       // BASE CASE: empty range -> not found

    int mid = lo + (hi - lo) / 2;                 // middle position (no overflow)
    comparisons++;                                // one 3-way comparison of key with index[mid]
    if (key == index[mid].key)                    // <-- BASIC OPERATION (key comparison)
        return index[mid].pos;                    // found
    if (key < index[mid].key)
        return binary_search_recursive(index, key, lo, mid - 1, comparisons);  // left half
    return binary_search_recursive(index, key, mid + 1, hi, comparisons);      // right half
}

int binary_search(const std::vector<IndexEntry>& index, long long key, long long& comparisons) {
    return binary_search_recursive(index, key, 0, (int)index.size() - 1, comparisons);
}

// ---------------- Daily update (used in Task 12) ----------------
// Sort the small batch of new entries (k log k), then merge it with the
// already-sorted index in one linear pass (n + k).
void merge_batch_into_index(std::vector<IndexEntry>& index, std::vector<IndexEntry> batch,
                            long long& comparisons) {
    std::vector<IndexEntry> tmp(batch.size());
    if (batch.size() > 1) merge_sort(batch, tmp, 0, (int)batch.size() - 1, comparisons);

    std::vector<IndexEntry> out;
    out.reserve(index.size() + batch.size());
    size_t i = 0, j = 0;
    while (i < index.size() && j < batch.size()) {
        comparisons++;
        if (index[i].key <= batch[j].key) out.push_back(index[i++]);
        else                              out.push_back(batch[j++]);
    }
    while (i < index.size()) out.push_back(index[i++]);
    while (j < batch.size()) out.push_back(batch[j++]);
    index.swap(out);
}
