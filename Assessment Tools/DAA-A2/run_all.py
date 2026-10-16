"""Run every question in order:   python run_all.py        (full run, about 1-2 minutes)
                                  python run_all.py --quick (smaller sizes, for a trial run)"""
import os

import common as C
import q1_sorting
import q2_sequential_search
import q3_string_matching
import q4_closest_pair
import q5_convex_hull
import q6_knapsack_exhaustive
import q7_redesign

C.check_config()
for name, module in (("q1", q1_sorting), ("q2", q2_sequential_search), ("q3", q3_string_matching),
                     ("q4", q4_closest_pair), ("q5", q5_convex_hull), ("q6", q6_knapsack_exhaustive),
                     ("q7", q7_redesign)):
    C.run(module.main, name)

print("=" * 96)
print(f" All done for {C.who()}.  Everything is in the results folder:")
for sub in ("", "data", "graphs"):
    d = os.path.join(C.RESULTS, sub)
    files = sorted(f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)))
    print(f"   results/{sub + '/' if sub else ''}  ({len(files)} files)")
print("=" * 96)
