// =====================================================================
// Algorithm 1 : LINEAR SEARCH  (iterative, brute force)
//
// Idea: the database is stored in arbitrary (insertion) order, so check
// the records one by one from the first to the last until the key is
// found or the records run out.
// Preprocessing: none.
// =====================================================================
#include "common.h"

int linear_search(const std::vector<Record>& db, long long key, long long& comparisons) {
    int n = (int)db.size();
    for (int i = 0; i < n; i++) {
        comparisons++;                    // count one key comparison
        if (db[i].reg_no == key) {        // <-- BASIC OPERATION (key comparison)
            return i;                     // found: return its position
        }
    }
    return -1;                            // checked all n records: not found
}
