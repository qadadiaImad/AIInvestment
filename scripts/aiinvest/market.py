import datetime, json, urllib.request

YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"
INDEX_SYMBOLS = {"sp500": "^GSPC", "nasdaq": "^IXIC", "vix": "^VIX", "ten_year": "^TNX"}

def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

def _fetch_yahoo(sym):
    url = YAHOO.format(sym=sym)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        meta = json.load(r)["chart"]["result"][0]["meta"]
    price, prev = meta.get("regularMarketPrice"), meta.get("chartPreviousClose")
    if not isinstance(price, (int, float)) or not isinstance(prev, (int, float)) or not prev:
        raise ValueError(f"dirty quote for {sym}: price={price} prev={prev}")
    return float(price), float(prev)

def fetch_market_pulse(fetch=_fetch_yahoo):
    pulse = {}
    for key, sym in INDEX_SYMBOLS.items():
        price, prev = fetch(sym)
        if not isinstance(price, (int, float)) or not isinstance(prev, (int, float)) or not prev:
            raise ValueError(f"dirty quote for {sym}")
        # ^TNX from Yahoo is now quoted as the yield directly (e.g. 4.485 = 4.485%),
        # NOT the legacy yield*10. So do not divide. ten_year change stays a raw
        # point/bps move (yield diff); indices use percent change.
        disp = price
        change = price - prev if key == "ten_year" else (price - prev) / prev * 100
        pulse[key] = {"symbol": sym, "price": round(disp, 2),
                      "change_pct": round(change, 2),
                      "retrieved_at": _utcnow(), "source": f"yahoo:{sym}", "source_class": "xhr-json"}
    return pulse
