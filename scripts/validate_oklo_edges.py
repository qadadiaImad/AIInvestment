import sys
import json
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import capital_web

# Load the edges
with open('C:/Users/imadq/AIInvestment/data/enrich/OKLO_edges.json', 'r', encoding='utf-8') as f:
    edges = json.load(f)

print(f"Total edges: {len(edges)}")

# Get allowed node IDs
graph = capital_web.build_graph()
node_ids = set(n['id'] for n in graph['nodes'])

print(f"\nAllowed node count: {len(node_ids)}")
print(f"OKLO in nodes: {'OKLO' in node_ids}")
print(f"META in nodes: {'META' in node_ids}")
print(f"EQIX in nodes: {'EQIX' in node_ids}")
print(f"LEU in nodes: {'LEU' in node_ids}")

# Validate each edge
print("\n--- Edge validation ---")
valid_certainty = {"filed", "reported", "rumored"}
valid_types = {"equity_stake", "compute_commitment", "customer", "infra_partner", "voting_power", "subsidiary"}

for i, e in enumerate(edges):
    issues = []
    if e['src'] not in node_ids:
        issues.append(f"src '{e['src']}' not in node_ids")
    if e['dst'] not in node_ids:
        issues.append(f"dst '{e['dst']}' not in node_ids")
    if e.get('certainty') not in valid_certainty:
        issues.append(f"invalid certainty: {e.get('certainty')}")
    if e.get('type') not in valid_types:
        issues.append(f"invalid type: {e.get('type')}")
    if not e.get('source_url'):
        issues.append("missing source_url")
    if not e.get('quote'):
        issues.append("missing quote")
    if not e.get('retrieved_at'):
        issues.append("missing retrieved_at")

    status = "OK" if not issues else f"ISSUES: {issues}"
    print(f"  Edge {i+1}: {e['src']} -> {e['dst']} ({e['type']}, {e['certainty']}) => {status}")

# Count by certainty
by_certainty = {}
for e in edges:
    c = e.get('certainty', 'unknown')
    by_certainty[c] = by_certainty.get(c, 0) + 1

print(f"\n--- Summary ---")
print(f"Total edges: {len(edges)}")
for c, n in sorted(by_certainty.items()):
    print(f"  {c}: {n}")
