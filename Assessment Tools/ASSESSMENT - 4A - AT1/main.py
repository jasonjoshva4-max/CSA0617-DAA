"""
DAA Assignment 4A - Python Practice Implementations
Run: python main.py

This code is for practice/testing. The assignment brief states that submission
must be language-independent pseudocode, not programming code.
"""

from math import inf


# ---------------------------------------------------------------------------
# TASK 1: Fractional Knapsack (packages may be divided)
# Package format: (package_id, weight, value)
# ---------------------------------------------------------------------------
def fractional_knapsack(packages, capacity):
    if capacity <= 0:
        return 0.0, []

    # Greedy rule: take the greatest value-per-unit-weight first.
    ordered = sorted(packages, key=lambda p: p[2] / p[1] if p[1] > 0 else inf,
                     reverse=True)
    remaining = capacity
    total_value = 0.0
    loaded = []

    for package_id, weight, value in ordered:
        if remaining <= 0:
            break
        if weight <= 0:
            continue

        amount = min(weight, remaining)
        fraction = amount / weight
        gained = value * fraction
        loaded.append((package_id, amount, gained, fraction))
        total_value += gained
        remaining -= amount

    return total_value, loaded


# ---------------------------------------------------------------------------
# TASK 2: Job Sequencing with Deadlines (each job takes one slot)
# Job format: (job_id, deadline, profit)
# ---------------------------------------------------------------------------
def job_sequencing(jobs):
    if not jobs:
        return [], 0

    max_deadline = max((deadline for _, deadline, _ in jobs), default=0)
    max_deadline = max(0, max_deadline)
    slots = [None] * (max_deadline + 1)  # slots 1..max_deadline

    ordered = sorted(jobs, key=lambda job: job[2], reverse=True)
    total_profit = 0

    for job_id, deadline, profit in ordered:
        if profit <= 0:
            continue
        latest = min(deadline, max_deadline)
        for slot in range(latest, 0, -1):
            if slots[slot] is None:
                slots[slot] = (job_id, profit)
                total_profit += profit
                break

    schedule = [(slot, slots[slot][0], slots[slot][1])
                for slot in range(1, len(slots)) if slots[slot] is not None]
    return schedule, total_profit


# ---------------------------------------------------------------------------
# TASK 3: 0/1 Knapsack using bottom-up dynamic programming
# Items: (item_id, weight, value)
# ---------------------------------------------------------------------------
def knapsack_01(items, capacity):
    n = len(items)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        item_id, weight, value = items[i - 1]
        for cap in range(capacity + 1):
            dp[i][cap] = dp[i - 1][cap]  # exclude item
            if weight <= cap:
                include = dp[i - 1][cap - weight] + value
                if include > dp[i][cap]:
                    dp[i][cap] = include

    selected = []
    cap = capacity
    for i in range(n, 0, -1):
        if dp[i][cap] != dp[i - 1][cap]:
            item_id, weight, value = items[i - 1]
            selected.append((item_id, weight, value))
            cap -= weight
    selected.reverse()
    return dp[n][capacity], selected, dp


# ---------------------------------------------------------------------------
# TASK 4: Word Break
# Correct condition requires both a valid prior prefix and dictionary word.
# ---------------------------------------------------------------------------
def word_break(text, dictionary):
    n = len(text)
    dp = [False] * (n + 1)
    previous = [-1] * (n + 1)
    dp[0] = True

    for end in range(1, n + 1):
        for start in range(0, end):
            if dp[start] and text[start:end] in dictionary:
                dp[end] = True
                previous[end] = start
                break

    if not dp[n]:
        return False, []
    words = []
    end = n
    while end > 0:
        start = previous[end]
        words.append(text[start:end])
        end = start
    words.reverse()
    return True, words


def faulty_word_break(text, dictionary):
    """Original defective logic, included only to demonstrate the bug."""
    n = len(text)
    dp = [False] * (n + 1)
    dp[0] = True
    for end in range(1, n + 1):
        dp[end] = False
        for start in range(end):
            if text[start:end] in dictionary:  # missing dp[start] check
                dp[end] = True
                break
    return dp[n], dp


# ---------------------------------------------------------------------------
# TASK 5: Shortest paths
# Graph is an adjacency dictionary: node -> [(neighbor, weight), ...]
# ---------------------------------------------------------------------------
def dijkstra(graph, source):
    nodes = list(graph)
    for edges in graph.values():
        for neighbor, _ in edges:
            if neighbor not in nodes:
                nodes.append(neighbor)

    dist = {node: inf for node in nodes}
    prev = {node: None for node in nodes}
    visited = set()
    dist[source] = 0

    while len(visited) < len(nodes):
        current = None
        best = inf
        for node in nodes:
            if node not in visited and dist[node] < best:
                best = dist[node]
                current = node

        if current is None:
            break
        visited.add(current)

        for neighbor, weight in graph.get(current, []):
            if weight < 0:
                raise ValueError("Dijkstra requires non-negative edge weights.")
            candidate = dist[current] + weight
            if candidate < dist[neighbor]:
                dist[neighbor] = candidate
                prev[neighbor] = current

    return dist, prev


def bellman_ford(graph, source):
    nodes = list(graph)
    edges = []
    for u, neighbors in graph.items():
        for v, weight in neighbors:
            edges.append((u, v, weight))
            if v not in nodes:
                nodes.append(v)

    dist = {node: inf for node in nodes}
    prev = {node: None for node in nodes}
    dist[source] = 0

    for _ in range(max(0, len(nodes) - 1)):
        changed = False
        for u, v, weight in edges:
            if dist[u] != inf and dist[u] + weight < dist[v]:
                dist[v] = dist[u] + weight
                prev[v] = u
                changed = True
        if not changed:
            break

    # A reachable negative-weight cycle can still relax an edge.
    for u, v, weight in edges:
        if dist[u] != inf and dist[u] + weight < dist[v]:
            return dist, prev, True
    return dist, prev, False


def floyd_warshall(graph):
    nodes = list(graph)
    for neighbors in graph.values():
        for v, _ in neighbors:
            if v not in nodes:
                nodes.append(v)

    dist = {u: {v: (0 if u == v else inf) for v in nodes} for u in nodes}
    for u, neighbors in graph.items():
        for v, weight in neighbors:
            if weight < dist[u][v]:
                dist[u][v] = weight

    for k in nodes:
        for i in nodes:
            for j in nodes:
                if dist[i][k] != inf and dist[k][j] != inf:
                    candidate = dist[i][k] + dist[k][j]
                    if candidate < dist[i][j]:
                        dist[i][j] = candidate
    return nodes, dist


# ---------------------------------------------------------------------------
# TASK 6: Weighted interval scheduling (energy-saving job selection)
# Job format: (job_id, start, finish, energy_saving)
# Touching intervals are compatible: previous_finish <= next_start.
# ---------------------------------------------------------------------------
def energy_aware_schedule(jobs):
    if not jobs:
        return 0, []

    ordered = sorted(jobs, key=lambda job: job[2])  # finish time
    n = len(ordered)

    # p[i] = rightmost earlier job compatible with job i (1-based DP indexing)
    p = [0] * (n + 1)
    for i in range(1, n + 1):
        start = ordered[i - 1][1]
        compatible = 0
        for j in range(1, i):
            if ordered[j - 1][2] <= start:
                compatible = j
        p[i] = compatible

    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        energy = ordered[i - 1][3]
        take = energy + dp[p[i]]
        skip = dp[i - 1]
        dp[i] = max(skip, take)

    selected = []
    i = n
    while i > 0:
        energy = ordered[i - 1][3]
        if energy + dp[p[i]] > dp[i - 1]:
            selected.append(ordered[i - 1])
            i = p[i]
        else:
            i -= 1
    selected.reverse()
    return dp[n], selected


def print_section(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main():
    print("DAA Assignment 4A - Python Practice Implementations")

    print_section("TASK 1 - Fractional Knapsack")
    packages = [("BoxA", 10, 60), ("BoxB", 20, 100), ("BoxC", 30, 120)]
    value, loaded = fractional_knapsack(packages, 50)
    print("Packages (id, weight, value):", packages)
    print("Capacity: 50")
    print("Loaded (id, amount, value gained, fraction):", loaded)
    print("Maximum value:", value)

    print_section("TASK 2 - Job Sequencing with Deadlines")
    jobs = [("A", 2, 80), ("B", 1, 35), ("C", 2, 60),
            ("D", 3, 40), ("E", 1, 25)]
    schedule, profit = job_sequencing(jobs)
    print("Given jobs:", jobs)
    print("Schedule (slot, job, profit):", schedule)
    print("Total profit:", profit)

    changed_jobs = [("A", 2, 30), ("B", 1, 35), ("C", 2, 60),
                    ("D", 3, 40), ("E", 1, 25)]
    changed_schedule, changed_profit = job_sequencing(changed_jobs)
    print("Changed case (A profit changed 80 -> 30):", changed_schedule)
    print("Changed total profit:", changed_profit)

    print_section("TASK 3 - 0/1 Knapsack")
    items = [("P", 2, 12), ("Q", 3, 20), ("R", 4, 25), ("S", 5, 30)]
    best_value, chosen, table = knapsack_01(items, 7)
    print("Items:", items, "| Capacity: 7")
    print("Selected items:", chosen)
    print("Maximum value:", best_value)

    print_section("TASK 4 - Word Break")
    text = "xcat"
    dictionary = {"cat"}
    print("Failing case for original logic:", text, dictionary)
    print("Faulty result and DP states:", faulty_word_break(text, dictionary))
    print("Corrected result:", word_break(text, dictionary))
    print("Regression case catdog / {cat, dog}:", word_break("catdog", {"cat", "dog"}))

    print_section("TASK 5 - Dijkstra, Bellman-Ford and Floyd-Warshall")
    graph = {
        "A": [("B", 4), ("C", 7)],
        "B": [("C", 2), ("D", 6)],
        "C": [("D", 1), ("E", 8)],
        "D": [("E", 3)],
        "E": []
    }
    print("Dijkstra from A:", dijkstra(graph, "A")[0])
    print("Bellman-Ford from A:", bellman_ford(graph, "A")[0:3:2])
    nodes, all_pairs = floyd_warshall(graph)
    print("Floyd-Warshall all-pairs distances:")
    for node in nodes:
        print(node, all_pairs[node])

    negative_graph = {
        "A": [("B", 1)],
        "B": [("C", -2)],
        "C": [("B", -2)]
    }
    print("Reachable negative cycle detected:",
          bellman_ford(negative_graph, "A")[2])

    print_section("TASK 6 - Energy-Aware Weighted Job Scheduling")
    energy_jobs = [
        ("J1", 1, 3, 20), ("J2", 2, 5, 50),
        ("J3", 4, 6, 30), ("J4", 6, 8, 40),
        ("J5", 5, 9, 60), ("J6", 8, 10, 30),
        ("J7", 9, 11, 50), ("J8", 11, 13, 40)
    ]
    energy, selected_jobs = energy_aware_schedule(energy_jobs)
    print("Selected jobs:", selected_jobs)
    print("Maximum energy-saving value:", energy)

    adversarial = [
        ("Long", 1, 10, 100),
        ("A", 1, 2, 30), ("B", 2, 3, 30), ("C", 3, 4, 30),
        ("D", 4, 5, 30), ("E", 5, 6, 30)
    ]
    adv_energy, adv_selected = energy_aware_schedule(adversarial)
    print("Adversarial input selected jobs:", adv_selected)
    print("Adversarial optimum:", adv_energy,
          "(chooses five compatible short jobs, value 150)")

    print("\nAll six task demonstrations completed.")


if __name__ == "__main__":
    main()
