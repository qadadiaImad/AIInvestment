from aiinvest.daily_brief import pick_movers

def test_news_weight_breaks_ties_toward_mentioned():
    ai = [{"ticker": "AAA", "perf_1y": 30.0}, {"ticker": "BBB", "perf_1y": 25.0}]
    q  = [{"ticker": "QQQ", "perf_1y": 70.0}]
    news = [{"tickers": ["BBB"]}, {"tickers": ["BBB"]}]  # BBB mentioned twice
    picks = pick_movers(ai, q, news)
    assert picks["ai"]["ticker"] == "BBB"   # 25*(1+2)=75 > 30*(1+0)=30
    assert picks["quantum"]["ticker"] == "QQQ"
