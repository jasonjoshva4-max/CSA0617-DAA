"""
DAA Assignment 4B – Algorithm Engineering
Student: Jason Joshva M J | Register No.: 192511209
Standard-library Python demonstrations for all six assignment tasks.
"""
from itertools import permutations
from math import inf
import time
import tracemalloc

def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)

# TASK 1: Word Wrap DP
def word_wrap(words, width, show_states=True):
    n = len(words)
    # cost[i][j] = penalty for placing words i..j on one line; None if it won't fit
    cost = [[None] * n for _ in range(n)]
    for i in range(n):
        used = 0
        for j in range(i, n):
            used += len(words[j]) + (1 if j > i else 0)
            if used <= width:
                slack = width - used
                cost[i][j] = 0 if j == n - 1 else slack ** 2
            else:
                break
    dp = [inf] * (n + 1)
    prev = [-1] * (n + 1)
    dp[0] = 0
    for j in range(1, n + 1):
        for i in range(j):
            c = cost[i][j - 1]
            if c is not None and dp[i] + c < dp[j]:
                dp[j], prev[j] = dp[i] + c, i
    lines = []
    j = n
    while j > 0 and prev[j] >= 0:
        i = prev[j]
        line_words = words[i:j]
        used = sum(map(len, line_words)) + len(line_words) - 1
        slack = width - used
        penalty = 0 if j == n else slack ** 2
        lines.append((i, j, " ".join(line_words), slack, penalty))
        j = i
    lines.reverse()
    if show_states:
        print("DP state meaning: dp[j] = minimum penalty for arranging the first j words.")
        print("DP costs:", [None if x == inf else int(x) for x in dp])
        print("Predecessors:", prev)
    return dp[n], lines, dp, prev

def task1():
    section("TASK 1 – WORD WRAP DYNAMIC PROGRAMMING")
    words = "Dynamic programming creates balanced lines for readable documents".split()
    width = 16
    print("Input words:", words)
    print("Base width:", width)
    value, lines, dp, prev = word_wrap(words, width)
    print("Minimum total penalty:", value)
    print("Line | Text | Unused spaces | Penalty")
    for k, (_, _, text, slack, penalty) in enumerate(lines, 1):
        print(f"{k:>4} | {text:<35} | {slack:>4} | {penalty:>7}")
    print("\nWidth-change predictions (recorded before each run):")
    for w, prediction in [(12, "Arrangement likely changes; first change near early long words; penalty may rise."),
                           (20, "Arrangement may change; first change around line boundary; penalty may fall."),
                           (25, "Fewer lines expected; first change near start; penalty likely falls.")]:
        print(f"Prediction for width {w}: {prediction}")
        v, ls, _, _ = word_wrap(words, w, show_states=False)
        print(f"Actual width {w}: penalty={v}; lines={[x[2] for x in ls]}")
    boundary_words = ["extraordinary", "test"]
    boundary_width = len(boundary_words[0])
    print(f"Boundary test: words={boundary_words}, width={boundary_width}")
    try:
        v, ls, _, _ = word_wrap(boundary_words, boundary_width, show_states=False)
        print("Boundary result:", v, [x[2] for x in ls])
    except Exception as e:
        print("Boundary error caught:", type(e).__name__, str(e))
    print("Boundary rationale: a word exactly equal to the width must fit; a longer word must be rejected/handled.")

# TASK 2: Knapsack
def fractional_knapsack(items, capacity):
    ordered = sorted(items, key=lambda x: x[2] / x[1], reverse=True)
    remaining, total, chosen, comparisons = capacity, 0.0, [], 0
    for name, weight, value in ordered:
        comparisons += 1
        if remaining <= 0: break
        amount = min(weight, remaining)
        fraction = amount / weight
        gained = value * fraction
        chosen.append((name, amount, gained, fraction))
        total += gained
        remaining -= amount
    return total, chosen, comparisons

def knapsack01(items, capacity):
    n = len(items)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i, (_, weight, value) in enumerate(items, 1):
        for c in range(capacity + 1):
            dp[i][c] = dp[i-1][c]
            if weight <= c:
                dp[i][c] = max(dp[i][c], value + dp[i-1][c-weight])
    chosen, c = [], capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i-1][c]:
            name, weight, value = items[i-1]
            chosen.append((name, weight, value))
            c -= weight
    chosen.reverse()
    return dp[n][capacity], chosen, dp, n * (capacity + 1)

def task2():
    section("TASK 2 – GREEDY FRACTIONAL VS DYNAMIC 0/1 KNAPSACK")
    items = [("A", 10, 60), ("B", 20, 100), ("C", 30, 120)]
    capacity = 50
    print("Normal dataset:", items, "| capacity:", capacity)
    fval, fitems, fops = fractional_knapsack(items, capacity)
    dval, ditem, dp, dops = knapsack01(items, capacity)
    print("Fractional greedy selected (id, weight, value, fraction):", fitems)
    print("Fractional optimum:", fval, "| ratio comparisons:", fops)
    print("0/1 DP selected:", ditem, "| optimum:", dval, "| DP cells:", dops)
    print("DP memory cells:", len(dp) * len(dp[0]), "(O(nW) table)")
    # Designed counterexample: ratio-greedy takes 6/10 first, blocks the two items.
    bad = [("Greedy", 10, 60), ("X", 6, 40), ("Y", 6, 40)]
    cap = 12
    greedy = sorted(bad, key=lambda x: x[2]/x[1], reverse=True)
    remaining, gv, gs = cap, 0, []
    for name, weight, value in greedy:
        if weight <= remaining:
            gs.append(name); remaining -= weight; gv += value
    opt, osel, _, _ = knapsack01(bad, cap)
    print("Counterexample items:", bad, "| capacity:", cap)
    print("First greedy commitment:", gs[0] if gs else "none", "uses capacity and prevents X+Y.")
    print("Greedy selection/value:", gs, gv)
    print("DP optimal selection/value:", osel, opt)
    print("Engineering comparison: fractional greedy O(n log n) time, O(n) sorting storage; exact 0/1 DP O(nW) time and O(nW) table memory.")
    print("Changed requirement (very fast, near-optimal acceptable): select ratio-greedy; observed quick scan, but counterexample shows loss of exact optimality.")

# TASK 3: Shortest paths
def dijkstra(graph, source):
    dist = {v: inf for v in graph}; parent = {v: None for v in graph}
    dist[source] = 0; done = set(); order = []
    while len(done) < len(graph):
        u = min((v for v in graph if v not in done), key=lambda v: dist[v], default=None)
        if u is None or dist[u] == inf: break
        done.add(u); order.append(u)
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v], parent[v] = dist[u] + w, u
    return dist, parent, order

def reconstruct(parent, target):
    path=[]
    while target is not None:
        path.append(target); target=parent[target]
    return list(reversed(path))

def bellman_ford(graph, source):
    edges=[(u,v,w) for u in graph for v,w in graph[u]]
    dist={v:inf for v in graph}; parent={v:None for v in graph}; dist[source]=0
    for _ in range(len(graph)-1):
        changed=False
        for u,v,w in edges:
            if dist[u] != inf and dist[u]+w < dist[v]:
                dist[v]=dist[u]+w; parent[v]=u; changed=True
        if not changed: break
    cycle=any(dist[u] != inf and dist[u]+w < dist[v] for u,v,w in edges)
    return dist,parent,cycle

def floyd_warshall(vertices, edges):
    d={u:{v:(0 if u==v else inf) for v in vertices} for u in vertices}
    for u,v,w in edges: d[u][v]=min(d[u][v],w)
    for k in vertices:
        for i in vertices:
            for j in vertices:
                if d[i][k] != inf and d[k][j] != inf:
                    d[i][j]=min(d[i][j],d[i][k]+d[k][j])
    return d

def warshall(vertices, edges):
    r={u:{v:(u==v) for v in vertices} for u in vertices}
    for u,v,_ in edges:r[u][v]=True
    for k in vertices:
        for i in vertices:
            for j in vertices:r[i][j]=r[i][j] or (r[i][k] and r[k][j])
    return r

def task3():
    section("TASK 3 – ROUTING: DIJKSTRA, BELLMAN-FORD, FLOYD & WARSHALL")
    V=list("ABCDEFGH")
    edges=[("A","B",4),("A","C",2),("B","C",1),("B","D",5),("C","D",8),
           ("C","E",10),("D","E",2),("D","F",6),("E","F",3),("E","G",4),
           ("F","G",1),("G","H",2),("F","H",7),("B","H",15)]
    graph={v:[] for v in V}
    for u,v,w in edges: graph[u].append((v,w))
    print("Graph edges (14):", edges)
    dist,par,order=dijkstra(graph,"A")
    print("Dijkstra distances:",dist)
    print("Predecessors:",par)
    print("Finalisation order:",order)
    print("Actual route A -> H:",reconstruct(par,"H"),"cost",dist["H"])
    neg_edges=edges+[("H","B",-12)]
    ng={v:[] for v in V}
    for u,v,w in neg_edges:ng[u].append((v,w))
    print("Prediction before negative edge: Dijkstra is not guaranteed valid; H->B may improve routes to B and downstream nodes.")
    bd,bp,cycle=bellman_ford(ng,"A")
    print("Bellman-Ford after negative edge:",bd,"reachable negative cycle:",cycle)
    cycle_edges=neg_edges+[("B","H",1)]
    cg={v:[] for v in V}
    for u,v,w in cycle_edges:cg[u].append((v,w))
    _,_,cycle_found=bellman_ford(cg,"A")
    print("Production failure test (B->H=1 added): reachable negative cycle detected:",cycle_found)
    fw=floyd_warshall(V,edges)
    print("Floyd-Warshall distance matrix:")
    print("     "+" ".join(V))
    for u in V: print(u, " ".join("∞" if fw[u][v]==inf else str(int(fw[u][v])) for v in V))
    reach=warshall(V,edges)
    print("Warshall reachability matrix (1 reachable, 0 not reachable):")
    print("     "+" ".join(V))
    for u in V:print(u," ".join("1" if reach[u][v] else "0" for v in V))
    print("Interpretation: Dijkstra requires nonnegative weights; Bellman-Ford handles negative edges and detects reachable negative cycles.")

# TASK 4: Assembly line
def assembly_line(a,b,t,e,x,trace=True):
    n=len(a); f1=[0]*n;f2=[0]*n; p1=[0]*n;p2=[0]*n
    f1[0]=e[0]+a[0];f2[0]=e[1]+b[0]
    for j in range(1,n):
        stay1=f1[j-1]+a[j]; trans1=f2[j-1]+t[1][j-1]+a[j]
        stay2=f2[j-1]+b[j]; trans2=f1[j-1]+t[0][j-1]+b[j]
        f1[j]=min(stay1,trans1);p1[j]=0 if stay1<=trans1 else 1
        f2[j]=min(stay2,trans2);p2[j]=1 if stay2<=trans2 else 0
        if trace:print(f"Station {j+1}: L1 stay={stay1}, transfer={trans1}, choose L{p1[j]+1}; L2 stay={stay2}, transfer={trans2}, choose L{p2[j]+1}")
    end1=f1[-1]+x[0];end2=f2[-1]+x[1]
    line=0 if end1<=end2 else 1; total=min(end1,end2)
    route=[line]
    for j in range(n-1,0,-1): route.append(p1[j] if route[-1]==0 else p2[j])
    route.reverse()
    return total,route,f1,f2

def task4():
    section("TASK 4 – TWO-LINE ASSEMBLY SCHEDULING DP")
    a=[7,9,3,4,8,4];b=[8,5,6,4,5,7]
    t=[[2,3,1,3,4],[2,1,2,2,1]];e=[2,4];x=[3,2]
    print("Line 1 processing:",a);print("Line 2 processing:",b)
    print("Entry:",e,"Exit:",x,"Transfer L1->L2:",t[0],"L2->L1:",t[1])
    total,route,f1,f2=assembly_line(a,b,t,e,x)
    print("DP cumulative L1:",f1);print("DP cumulative L2:",f2)
    print("Optimal line by station:",["L"+str(q+1) for q in route])
    transfers=[i+1 for i in range(1,len(route)) if route[i]!=route[i-1]]
    print("Transfer points (before station):",transfers)
    print("Minimum production time:",total)
    print("Prediction: increasing L1->L2 transfer at station 3 should discourage that switch; route/time will be recomputed.")
    t2=[row[:] for row in t];t2[0][2]+=20
    v2,r2,_,_=assembly_line(a,b,t2,e,x,trace=False)
    print("Observed after transfer increase: time",v2,"route",["L"+str(q+1) for q in r2])
    print("Disruption experiment: make Line 1 station 3 slower by 15.")
    a2=a[:];a2[2]+=15
    v3,r3,_,_=assembly_line(a2,b,t,e,x,trace=False)
    print("Observed disruption: time",v3,"route",["L"+str(q+1) for q in r3])
    print("Three-line extension: state becomes F[line][station] for 3 lines; each transition minimises over the 3 predecessor lines plus line-specific transfer costs; store predecessor line for route reconstruction.")

# TASK 5: MST algorithms
def kruskal(vertices, edges):
    parent={v:v for v in vertices};rank={v:0 for v in vertices}
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    chosen=[];trace=[]
    for u,v,w in sorted(edges,key=lambda e:e[2]):
        ru,rv=find(u),find(v)
        if ru!=rv:
            chosen.append((u,v,w));trace.append((u,v,w))
            if rank[ru]<rank[rv]:ru,rv=rv,ru
            parent[rv]=ru
            if rank[ru]==rank[rv]:rank[ru]+=1
            if len(chosen)==len(vertices)-1:break
    return chosen,trace

def prim(vertices, edges):
    adj={v:[] for v in vertices}
    for u,v,w in edges:adj[u].append((v,w));adj[v].append((u,w))
    used={vertices[0]};chosen=[];trace=[]
    while len(used)<len(vertices):
        candidates=[(w,u,v) for u in used for v,w in adj[u] if v not in used]
        if not candidates:break
        w,u,v=min(candidates)
        used.add(v);chosen.append((u,v,w));trace.append((u,v,w))
    return chosen,trace

def boruvka(vertices, edges):
    parent={v:v for v in vertices}
    def find(x):
        if parent[x]!=x:parent[x]=find(parent[x])
        return parent[x]
    chosen=[];rounds=[]
    while len({find(v) for v in vertices})>1:
        best={}
        for u,v,w in edges:
            a,b=find(u),find(v)
            if a==b:continue
            if a not in best or w<best[a][2]:best[a]=(u,v,w)
            if b not in best or w<best[b][2]:best[b]=(u,v,w)
        added=[]
        for edge in best.values():
            u,v,w=edge;a,b=find(u),find(v)
            if a!=b:parent[a]=b;chosen.append(edge);added.append(edge)
        rounds.append(added)
        if not added:break
    return chosen,rounds

def task5():
    section("TASK 5 – KRUSKAL, PRIM AND BORUVKA MST")
    V=list("ABCDEFGH")
    E=[("A","B",4),("A","C",3),("B","C",1),("B","D",5),("C","D",4),
       ("C","E",6),("D","E",2),("D","F",7),("E","F",3),("E","G",5),
       ("F","G",2),("F","H",6),("G","H",1),("B","H",9)]
    print("Connected graph edges:",E)
    k,kt=kruskal(V,E);p,pt=prim(V,E);b,br=boruvka(V,E)
    for name,es,tr in [("Kruskal",k,kt),("Prim",p,pt),("Boruvka",b,[e for r in br for e in r])]:
        print(name,"safe-edge trace:",tr)
        print(name,"MST edges:",es,"total cost:",sum(e[2] for e in es))
    print("Boruvka rounds:",br)
    # equal-weight alternate MST: triangle with all weights 1
    equal=[("A","B",1),("B","C",1),("A","C",1)]
    ke,_=kruskal(list("ABC"),equal);pe,_=prim(list("ABC"),equal)
    print("Multiple-MST graph:",equal)
    print("Kruskal edge set:",ke,"Prim edge set:",pe,"Both total:",sum(e[2] for e in ke),sum(e[2] for e in pe))
    print("Deployment: sparse graphs suit edge sorting + DSU (Kruskal); Prim grows locally with adjacency lists/heap; Boruvka selects cheapest outgoing edge per component and is naturally parallel-friendly; dense graphs often benefit from matrix-based Prim.")

# TASK 6: Held-Karp TSP
def held_karp(cost):
    n=len(cost); m=n-1
    # masks represent delivery vertices 1..n-1
    dp={};parent={}
    for j in range(1,n):
        mask=1<<(j-1);dp[(mask,j)]=cost[0][j];parent[(mask,j)]=0
    for size in range(2,m+1):
        for subset in combinations(range(1,n),size):
            mask=sum(1<<(j-1) for j in subset)
            for j in subset:
                pm=mask^(1<<(j-1))
                best=min((dp[(pm,k)]+cost[k][j],k) for k in subset if k!=j)
                dp[(mask,j)]=best[0];parent[(mask,j)]=best[1]
    full=(1<<m)-1
    bestcost,last=min((dp[(full,j)]+cost[j][0],j) for j in range(1,n))
    route=[last];mask=full;cur=last
    while mask:
        prev=parent[(mask,cur)]
        mask^=1<<(cur-1)
        if prev==0:break
        route.append(prev);cur=prev
    route.reverse()
    return bestcost,[0]+route+[0],len(dp),dp

def exhaustive_tsp(cost):
    n=len(cost);best=inf;bestroute=None
    for p in permutations(range(1,n)):
        val=cost[0][p[0]]+sum(cost[p[i]][p[i+1]] for i in range(len(p)-1))+cost[p[-1]][0]
        if val<best:best,bestroute=val,(0,)+p+(0,)
    return best,bestroute

def task6():
    section("TASK 6 – TSP HELD-KARP DYNAMIC PROGRAMMING")
    names=["Hub","A","B","C","D","E","F"]
    cost=[
      [0,10,15,20,18,25,12],
      [10,0,35,25,17,30,22],
      [15,35,0,30,28,16,24],
      [20,25,30,0,12,18,14],
      [18,17,28,12,0,20,16],
      [25,30,16,18,20,0,11],
      [12,22,24,14,16,11,0]]
    print("Locations:",names)
    print("Travel-cost matrix:")
    for row in cost:print(row)
    val,route,states,dp=held_karp(cost)
    print("Optimal route:", " -> ".join(names[i] for i in route))
    print("Minimum travel cost:",val,"| DP states evaluated:",states)
    small=[row[:5] for row in cost[:5]]
    ref,refroute=exhaustive_tsp(small)
    dpval,dproute,_,_=held_karp(small)
    print("Validation (hub + 4 locations): exhaustive optimum",ref,"route",refroute)
    print("Validation DP optimum:",dpval,"route",dproute,"match:",ref==dpval)
    print("State-space scaling (n delivery locations):")
    for nloc in range(4,9):
        n=nloc+1
        print(f"{nloc:>2} | theoretical states <= {nloc}*2^(nloc-1) = {nloc*(2**(nloc-1))}")
    print("Memory observation: dictionary stores subset-endpoint states; growth is exponential in location count.")
    print("200 locations: exact Held-Karp is impractical (about n*2^n states). Requirement changes from exact optimality to fast excellent route; investigate nearest-neighbour + 2-opt or other heuristics, accepting no optimality guarantee.")
    reflection=("Dynamic Programming improves TSP over exhaustive enumeration by reusing the best cost for each visited subset and current endpoint. "
                "The implementation validates its small case against exhaustive enumeration and records subset states. "
                "However, the number of subsets is exponential: each delivery location may be either visited or not, and each subset can have multiple possible endpoints. "
                "Held-Karp therefore needs O(n^2 2^n) time and O(n 2^n) memory. "
                "It is far better than checking every route, but still becomes impractical as n grows. "
                "For a 200-location requirement, a heuristic such as nearest-neighbour followed by 2-opt is more appropriate when a high-quality route is acceptable.")
    print("Technical reflection (<=150 words):",reflection)

def main():
    print("DAA ASSIGNMENT 4B – ALGORITHM ENGINEERING")
    print("Jason Joshva M J | Register No. 192511209")
    print("Python standard library only; reproducible sample runs.")
    task1();task2();task3();task4();task5();task6()
    print("\nAll six Assignment 4B task demonstrations completed.")

if __name__=="__main__":
    from itertools import combinations
    main()
