import sys
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import capital_web
graph = capital_web.build_graph()
node_ids = sorted(n['id'] for n in graph['nodes'])
print(node_ids)
