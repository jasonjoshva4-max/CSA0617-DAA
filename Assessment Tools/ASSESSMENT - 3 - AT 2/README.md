# KartIQ — Divide-and-Conquer Engine (Python)

Course: CSA06 – Design and Analysis of Algorithms, CO3 Case Study

This beginner-friendly project demonstrates the four algorithm modules in the provided assignment:

1. **Stable Merge Sort** — sorts sample orders by timestamp and preserves arrival order for equal timestamps.
2. **Quick Sort** — sorts seller scores using a median-of-three pivot to reduce the poor behavior of a first-element pivot on nearly sorted data.
3. **Binary Search** — searches the sorted order list and returns the *first* order with the requested timestamp.
4. **Strassen Matrix Multiplication** — uses the seven Strassen products on the assignment's 2×2 matrices and checks the result against conventional multiplication.

## Requirements

- Python 3.9 or newer
- No third-party packages required

## Run

Open a terminal in this folder and run:

```bash
python main.py
```

On Windows, if `python` is not recognized, try:

```bash
py main.py
```

## Suggested screenshots

Capture screenshots of:
1. The terminal showing Module 1's original and sorted orders (equal timestamps remain in original order).
2. The terminal showing Module 2's sorted seller scores.
3. The terminal showing Module 3's first matching order for timestamp `102`.
4. The terminal showing Strassen's result and `Verification: True`.
5. The complete terminal output showing all four modules completed.

## Notes

- The program is a demonstration using the exact sample inputs from the case study.
- The assignment's theoretical analysis (recurrences, comparison estimates, memory discussion, and design justification) is separate from this executable demonstration.
