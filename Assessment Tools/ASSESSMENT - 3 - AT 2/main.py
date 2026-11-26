"""
KartIQ - Divide-and-Conquer Engine
CSA06 CO3 Case Study

Run:
    python main.py

Implements:
1. Stable Merge Sort for orders by timestamp
2. Quick Sort for seller scores (median-of-three pivot)
3. Binary Search returning the first matching timestamp
4. Strassen matrix multiplication for 2x2 sample matrices
"""

def merge_sort_orders(orders):
    """Stable merge sort. Each order is (timestamp, order_id)."""
    if len(orders) <= 1:
        return orders[:]

    mid = len(orders) // 2
    left = merge_sort_orders(orders[:mid])
    right = merge_sort_orders(orders[mid:])
    merged = []
    i = j = 0

    while i < len(left) and j < len(right):
        # <= preserves original arrival order when timestamps are equal.
        if left[i][0] <= right[j][0]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def quick_sort_scores(values):
    """Quick sort using median-of-three pivot selection."""
    arr = values[:]

    def sort(low, high):
        if low >= high:
            return

        mid = (low + high) // 2
        candidates = [arr[low], arr[mid], arr[high]]
        candidates.sort()
        pivot = candidates[1]

        i, j = low, high
        while i <= j:
            while arr[i] < pivot:
                i += 1
            while arr[j] > pivot:
                j -= 1
            if i <= j:
                arr[i], arr[j] = arr[j], arr[i]
                i += 1
                j -= 1

        if low < j:
            sort(low, j)
        if i < high:
            sort(i, high)

    if arr:
        sort(0, len(arr) - 1)
    return arr


def binary_search_first(items, target_timestamp):
    """Return the index of the first order with target timestamp, else -1."""
    low, high = 0, len(items) - 1
    answer = -1

    while low <= high:
        mid = (low + high) // 2
        timestamp = items[mid][0]

        if timestamp >= target_timestamp:
            if timestamp == target_timestamp:
                answer = mid
            high = mid - 1
        else:
            low = mid + 1

    return answer


def add_matrix(A, B):
    n = len(A)
    return [[A[i][j] + B[i][j] for j in range(n)] for i in range(n)]


def subtract_matrix(A, B):
    n = len(A)
    return [[A[i][j] - B[i][j] for j in range(n)] for i in range(n)]


def strassen_2x2(A, B):
    """Strassen multiplication for 2x2 matrices."""
    a, b = A[0]
    c, d = A[1]
    e, f = B[0]
    g, h = B[1]

    # Seven Strassen products
    m1 = (a + d) * (e + h)
    m2 = (c + d) * e
    m3 = a * (f - h)
    m4 = d * (g - e)
    m5 = (a + b) * h
    m6 = (c - a) * (e + f)
    m7 = (b - d) * (g + h)

    return [
        [m1 + m4 - m5 + m7, m3 + m5],
        [m2 + m4, m1 - m2 + m3 + m6]
    ]


def conventional_multiply(A, B):
    n = len(A)
    result = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result[i][j] += A[i][k] * B[k][j]
    return result


def main():
    print("=" * 60)
    print("KartIQ: Divide-and-Conquer Algorithm Demonstration")
    print("=" * 60)

    print("\nMODULE 1 - Stable Merge Sort")
    orders = [(105, "O1"), (102, "O2"), (105, "O3"),
              (101, "O4"), (102, "O5"), (103, "O6")]
    sorted_orders = merge_sort_orders(orders)
    print("Original orders:", orders)
    print("Sorted orders:  ", sorted_orders)
    print("Stable equal-time order: timestamp 102 -> O2, O5; timestamp 105 -> O1, O3")

    print("\nMODULE 2 - Quick Sort (median-of-three pivot)")
    scores = [42, 17, 63, 8, 55, 29]
    print("Original scores:", scores)
    print("Sorted scores:  ", quick_sort_scores(scores))

    print("\nMODULE 3 - Binary Search (first matching timestamp)")
    target = 102
    index = binary_search_first(sorted_orders, target)
    if index != -1:
        print(f"First order at timestamp {target}: index {index}, order {sorted_orders[index]}")
    else:
        print(f"No order found at timestamp {target}")

    print("\nMODULE 4 - Strassen Matrix Multiplication")
    A = [[1, 7], [3, 5]]
    B = [[1, 3], [7, 5]]
    product = strassen_2x2(A, B)
    print("Matrix A:", A)
    print("Matrix B:", B)
    print("Strassen A x B:", product)
    print("Conventional A x B:", conventional_multiply(A, B))
    print("Verification:", product == conventional_multiply(A, B))

    print("\nAll four modules completed successfully.")


if __name__ == "__main__":
    main()
