import sys
sys.path.insert(0, 'C:/Users/imadq/AIInvestment/scripts')
from aiinvest import capital_web
graph = capital_web.build_graph()
ids = sorted(n['id'] for n in graph['nodes'])
for i in ids:
    print(i)
