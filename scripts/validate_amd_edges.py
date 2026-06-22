"""Validate AMD_edges.json against capital_web node list and schema rules."""
import json
import sys
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import capital_web

# Load allowed node IDs
graph = capital_web.build_graph()
allowed = {n['id'] for n in graph['nodes']}

# Load AMD edges
with open('C:/Users/imadq/AIInvestment/data/enrich/AMD_edges.json', encoding='utf-8') as f:
    edges = json.load(f)

print(f"Total edges: {len(edges)}")
print(f"Allowed node count: {len(allowed)}")

issues = []
for e in edges:
    if e['src'] not in allowed:
        issues.append(f"INVALID src: {e['src']}")
    if e['dst'] not in allowed:
        issues.append(f"INVALID dst: {e['dst']}")
    if e.get('certainty') not in capital_web.VALID_CERTAINTY:
        issues.append(f"INVALID certainty: {e.get('certainty')} ({e['src']}->{e['dst']})")
    if e.get('type') not in capital_web.VALID_EDGE_TYPES:
        issues.append(f"INVALID type: {e.get('type')} ({e['src']}->{e['dst']})")
    if not e.get('quote'):
        issues.append(f"MISSING quote: {e['src']}->{e['dst']}")
    if not e.get('source_url'):
        issues.append(f"MISSING source_url: {e['src']}->{e['dst']}")
    if not e.get('certainty'):
        issues.append(f"MISSING certainty: {e['src']}->{e['dst']}")

if issues:
    print("\nVALIDATION ISSUES:")
    for i in issues:
        print(f"  {i}")
else:
    print("\nAll edges VALID")

# Count by certainty
from collections import Counter
counts = Counter(e['certainty'] for e in edges)
print(f"\nCounts by certainty: {dict(counts)}")

# Print summary
print("\nEdge summary:")
for e in edges:
    print(f"  {e['src']} -> {e['dst']} [{e['type']}] ({e['certainty']})")
