from aiinvest import capital_web
graph = capital_web.build_graph()
ids = sorted(n['id'] for n in graph['nodes'])
print(ids)
