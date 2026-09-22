"""The Physical-AI / rare-earth-magnet value-chain universe (mirrors quantum_stack.py).

Scope (owner, 2026-09-22): every stock-market-listed player in the chain that turns ore
into a humanoid joint — US listings AND foreign listings (Shanghai, Shenzhen, Hong Kong,
Tokyo, Sydney, Toronto, London, Seoul, Frankfurt, Brussels). Tickers are TradingView
``EXCHANGE:SYMBOL`` form; the scanner market each exchange lives on is in
MARKET_OF_EXCHANGE, so the pull groups tickers by market (one POST per market).

Every ticker below resolved live on the TradingView scanner on 2026-09-22 (description,
close, market cap, currency). Each name lives in ONE primary layer (dominant exposure).
Diversified giants where the theme is a small slice (Tesla, Nvidia, TDK, Shin-Etsu,
Hitachi, Siemens, Magna, Samsung) are GRAPH-ONLY nodes, not screener members. Private
names (Figure, Unitree, Noveon, Vulcan, VAC, Proterial, maxon ...) are watch-list nodes.

Layer key -> what the layer is:
  P0-upstream   mine, feedstock, deposit developers (ore -> concentrate)
  P1-refining   separation, metal, recycling (concentrate -> oxide/metal)
  P2-magnets    sintered NdFeB / SmCo magnet makers
  P3-actuators  motors, reducers, screws, bearings, encoders/sensors, integrated actuators
  P4-robots     humanoid / robot integrators with a listed pure-ish exposure

Sources for the roster: the explainer doc + physics lesson research (FAI 2026, IEA,
CSIS, company pages), PhotonCap humanoid investment map, KraneShares KOID holdings,
Green Stocks Research rare-earth list, Rare Earth Exchanges China magnet ecosystem,
Core Matter actuator supplier map — see references/physical-ai-lesson and the doc.
Educational/research only — not investment advice. Many upstream names are pre-revenue
developers; the screener shows nulls, never fabricated numbers.
"""
from __future__ import annotations

SECTOR = "PhysicalAI"

# TradingView scanner market per exchange prefix.
MARKET_OF_EXCHANGE = {
    "NYSE": "america", "NASDAQ": "america", "AMEX": "america", "OTC": "america",
    "SSE": "china", "SZSE": "china",
    "HKEX": "hongkong",
    "TSE": "japan",
    "ASX": "australia",
    "TSX": "canada", "TSXV": "canada", "CSE": "canada",
    "LSE": "uk",
    "KRX": "korea",
    "XETR": "germany",
    "EURONEXT": "belgium",
}

COUNTRY_OF_EXCHANGE = {
    "NYSE": "US", "NASDAQ": "US", "AMEX": "US", "OTC": "US",
    "SSE": "CN", "SZSE": "CN", "HKEX": "HK", "TSE": "JP", "ASX": "AU",
    "TSX": "CA", "TSXV": "CA", "CSE": "CA", "LSE": "GB", "KRX": "KR",
    "XETR": "DE", "EURONEXT": "BE",
}

LAYERS = {
    "P0-upstream": [
        # producers / integrated miners
        "SSE:600111",    # China Northern Rare Earth — largest light-RE producer (Bayan Obo)
        "SSE:600259",    # China Rare Earth Nonferrous (Guangsheng) — heavy-RE ionic clay mining
        "SSE:600392",    # Shenghe Resources — mining/processing; ~3% holder of MP
        # US
        "NASDAQ:NB",     # NioCorp — Elk Creek Nb/Sc/REE developer
        "NASDAQ:CRML",   # Critical Metals — Tanbreez (Greenland) REE developer
        "OTC:REEMF",     # Rare Element Resources — Bear Lodge developer
        "AMEX:IDR",      # Idaho Strategic Resources — gold + REE exploration
        "AMEX:REA",      # Rare Earths Americas — developer
        "NASDAQ:EMAT",   # Evolution Metals & Technologies — magnet/REE micro-cap
        # Australia
        "ASX:ARU",       # Arafura — Nolans NdPr project
        "ASX:HAS",       # Hastings Technology Metals — Yangibana
        "ASX:NTU",       # Northern Minerals — Browns Range heavy REE (xenotime)
        "ASX:ARR",       # American Rare Earths — Halleck Creek (US)
        "ASX:BRE",       # Brazilian Rare Earths — Rocha da Rocha
        "ASX:MEI",       # Meteoric Resources — Caldeira ionic clay (Brazil)
        "ASX:VML",       # Vital Metals — Nechalacho
        "ASX:IXR",       # Ionic Rare Earths — Makuutu ionic clay + recycling tech
        "ASX:LIN",       # Lindian Resources — Kangankunde
        "ASX:ETM",       # Energy Transition Minerals — Kvanefjeld
        "ASX:REE",       # RareX — Cummins Range
        "ASX:AR3",       # Australian Rare Earths — Koppamurra ionic clay
        "ASX:SGQ",       # St George Mining — Araxá (Brazil) Nb/REE
        "ASX:SRL",       # Sunrise Energy Metals
        "ASX:VMM",       # Viridis Mining — Colossus ionic clay (Brazil)
        "ASX:MRZ",       # Mont Royal Resources
        # Canada
        "TSX:ARA",       # Aclara Resources — ionic clay heavy REE (Brazil/Chile), SPREC process
        "TSXV:DEFN",     # Defense Metals — Wicheeda
        "TSX:AVL",       # Avalon Advanced Materials — Nechalacho
        "CSE:API",       # Appia Rare Earths & Uranium
        # UK
        "LSE:MKA",       # Mkango Resources — Songwe Hill + HyProMag recycling
        "LSE:PRE",       # Pensana — Longonjo (Angola) + Saltend
        "LSE:RBW",       # Rainbow Rare Earths — Phalaborwa (phosphogypsum)
    ],
    "P1-refining": [
        "NYSE:MP",       # MP Materials — Mountain Pass mine + separation + Independence/10X magnets
        "ASX:LYC",       # Lynas — Mt Weld + Malaysia separation; first ex-China Dy/Tb (2025)
        "AMEX:UUUU",     # Energy Fuels — White Mesa monazite -> NdPr, Dy, Tb oxides
        "ASX:ILU",       # Iluka — Eneabba refinery (2027)
        "SZSE:000831",   # China Rare Earth Resources & Technology — heavy-RE separation (China RE Group)
        "HKEX:769",      # China Rare Earth Holdings — separation
        "TSXV:UCU",      # Ucore — RapidSX separation (Louisiana)
        "TSXV:GMA",      # Geomega — magnet recycling
        "NASDAQ:AREC",   # American Resources — ReElement Technologies separation/recycling
        "EURONEXT:SOLB", # Solvay — La Rochelle separation (Europe)
    ],
    "P2-magnets": [
        "SZSE:300748",   # JL Mag — largest sintered NdFeB maker; 60,000 t target by 2027
        "HKEX:6680",     # JL Mag H-share (dual listing)
        "SSE:600366",    # Ningbo Yunsheng
        "SZSE:000970",   # Beijing Zhong Ke San Huan
        "SZSE:300224",   # Yantai Zhenghai Magnetic
        "SSE:688077",    # Earth-Panda Advanced Magnetic
        "SZSE:300127",   # Chengdu Galaxy Magnets
        "SZSE:000795",   # Innuovo Technology
        "SZSE:301141",   # Zhejiang Zhongke Magnetic
        "SSE:603072",    # Baotou Tianhe Magnetics
        "SZSE:000969",   # Advanced Technology & Materials (AT&M)
        "SSE:600549",    # Xiamen Tungsten — Golden Dragon Rare Earth magnets
        "TSX:NEO",       # Neo Performance Materials — Narva (Estonia) magnets + Dy/Tb line
        "NASDAQ:USAR",   # USA Rare Earth — Stillwater (OK) magnets; Round Top
        "TSE:5471",      # Daido Steel — NdFeB magnets (Japan)
    ],
    "P3-actuators": [
        # motors
        "TSE:6594",      # Nidec — BLDC / coreless motors; Nidec-Shimpo strain-wave reducers
        "NYSE:MOG.A",    # Moog — actuators
        "SZSE:300124",   # Inovance — servo motors
        "SSE:603728",    # Moons' Electric — motors
        "NASDAQ:NOVT",   # Novanta — motors/encoders
        "NYSE:RRX",      # Regal Rexnord — Kollmorgen motors
        "NASDAQ:ALNT",   # Allient — motion/motors
        "KRX:108490",    # ROBOTIS — Dynamixel servo actuators, cycloid gears
        "SZSE:003021",   # Zhaowei Machinery — micro drive systems
        "HKEX:2692",     # Zhaowei H-share (dual listing)
        # reducers
        "TSE:6324",      # Harmonic Drive Systems — strain-wave reducers
        "TSE:6268",      # Nabtesco — RV cycloidal reducers
        "SSE:688017",    # Leader Harmonious Drive (Leaderdrive) — strain-wave reducers, roller screws
        "SZSE:002472",   # Shuanghuan Driveline — RV + harmonic reducers (Huandong)
        "SZSE:002896",   # Zhongda Leader — planetary / RV reducers
        "KRX:058610",    # SPG — planetary, strain-wave, cycloidal reducers
        "XETR:SHA0",     # Schaeffler — bearings, planetary screws, rotary actuators (Ewellix)
        # screws / integrated actuators / thermal
        "SSE:601100",    # Jiangsu Hengli Hydraulic — roller screws, linear actuators
        "SZSE:002050",   # Sanhua Intelligent Controls — linear actuators, thermal
        "HKEX:2050",     # Sanhua H-share (dual listing)
        "SSE:601689",    # Tuopu Group — rotary actuators, dexterous hands
        # bearings
        "TSE:6481",      # THK — cross-roller bearings, linear motion
        "TSE:6480",      # Nippon Thompson (IKO) — cross-roller bearings
        # sensors / encoders
        "EURONEXT:MELE", # Melexis — magnetic position sensor ICs
        "NASDAQ:ALGM",   # Allegro MicroSystems — current / position sensors
        "LSE:RSW",       # Renishaw — encoders
    ],
    "P4-robots": [
        "HKEX:9880",     # UBTech — Walker S humanoids
        "KRX:454910",    # Doosan Robotics
        "KRX:277810",    # Rainbow Robotics — RB-Y1 / Hubo (Samsung-controlled)
    ],
}

# Attempted on each pull; included automatically once they resolve live.
PENDING = []  # Unitree (pre-IPO), Mkango/Nasdaq SPAC (re-verify)

# Diversified bridges — GRAPH-ONLY (the theme is a small slice of the business).
GIANT_NODES = [
    {"id": "TSLA", "name": "Tesla (Optimus)", "layer": "P4-robots", "note": "Optimus humanoid; magnet-curb impact Apr 2025"},
    {"id": "NVDA", "name": "Nvidia", "layer": "P4-robots", "note": "Jetson edge compute, GR00T VLA"},
    {"id": "QCOM", "name": "Qualcomm", "layer": "P4-robots", "note": "RB6 robotics platform"},
    {"id": "AVGO", "name": "Broadcom", "layer": "P3-actuators", "note": "encoders"},
    {"id": "TDK", "name": "TDK", "layer": "P3-actuators", "note": "NdFeB magnets, magnetic sensors, IMUs"},
    {"id": "SHIN-ETSU", "name": "Shin-Etsu Chemical", "layer": "P2-magnets", "note": "NdFeB magnets (Japan)"},
    {"id": "MGA", "name": "Magna International", "layer": "P4-robots", "note": "Sanctuary AI partner"},
    {"id": "SAMSUNG", "name": "Samsung Electronics", "layer": "P4-robots", "note": "controls Rainbow Robotics"},
    {"id": "GM", "name": "General Motors", "layer": "P3-actuators", "note": "Noveon EV-magnet customer"},
    {"id": "BOSCH", "name": "Robert Bosch", "layer": "P3-actuators", "note": "Neo Narva magnet MoU; Bosch Rexroth roller screws"},
    {"id": "DOD", "name": "US Department of Defense", "layer": "P1-refining", "note": "MP preferred equity, $110/kg NdPr floor, 10X offtake"},
]

# Private / pre-IPO watch-list nodes.
PRIVATE_NODES = [
    {"id": "figure", "name": "Figure AI", "layer": "P4-robots"},
    {"id": "agility", "name": "Agility Robotics", "layer": "P4-robots"},
    {"id": "apptronik", "name": "Apptronik", "layer": "P4-robots"},
    {"id": "1x", "name": "1X Technologies", "layer": "P4-robots"},
    {"id": "unitree", "name": "Unitree Robotics", "layer": "P4-robots"},
    {"id": "boston_dynamics", "name": "Boston Dynamics (Hyundai)", "layer": "P4-robots"},
    {"id": "noveon", "name": "Noveon Magnetics", "layer": "P2-magnets"},
    {"id": "vulcan", "name": "Vulcan Elements", "layer": "P2-magnets"},
    {"id": "evac", "name": "e-VAC / Vacuumschmelze", "layer": "P2-magnets"},
    {"id": "proterial", "name": "Proterial (ex Hitachi Metals)", "layer": "P2-magnets"},
    {"id": "serra_verde", "name": "Serra Verde", "layer": "P0-upstream"},
    {"id": "maxon", "name": "maxon", "layer": "P3-actuators"},
    {"id": "laifual", "name": "Laifual", "layer": "P3-actuators"},
    {"id": "rollvis", "name": "Rollvis / GSA", "layer": "P3-actuators"},
]


def _exchange(ticker):
    return ticker.split(":")[0]


def market_of(ticker):
    """Scanner market for an EXCHANGE:SYMBOL ticker (KeyError if the exchange is unmapped)."""
    return MARKET_OF_EXCHANGE[_exchange(ticker)]


def country_of(ticker):
    return COUNTRY_OF_EXCHANGE[_exchange(ticker)]


def all_tickers():
    """Flat, de-duplicated list of every screener ticker across the layers."""
    seen, out = set(), []
    for tickers in LAYERS.values():
        for t in tickers:
            if t not in seen:
                seen.add(t)
                out.append(t)
    return out


def layer_of(ticker):
    for layer, tickers in LAYERS.items():
        if ticker in tickers:
            return layer
    return None


def by_market(tickers=None):
    """Group tickers by scanner market: {market: [tickers]} (insertion-ordered)."""
    out = {}
    for t in (tickers if tickers is not None else all_tickers()):
        out.setdefault(market_of(t), []).append(t)
    return out


# GuruFocus symbol spelling per exchange (verified live 2026-09-22 against the chart API:
# SHSE not SSE, HKSE with 5-digit zero padding, XKRX/XTER/XBRU/OTCPK; US bare symbol).
_GF_EXCHANGE = {
    "NYSE": None, "NASDAQ": None, "AMEX": None, "OTC": "OTCPK",
    "SSE": "SHSE", "SZSE": "SZSE", "HKEX": "HKSE", "TSE": "TSE", "ASX": "ASX",
    "TSX": "TSX", "TSXV": "TSXV", "CSE": "CSE", "LSE": "LSE", "KRX": "XKRX",
    "XETR": "XTER", "EURONEXT": "XBRU",
}


def gf_symbol(ticker):
    """TradingView EXCHANGE:SYMBOL -> the symbol GuruFocus's chart API accepts."""
    exch, sym = ticker.split(":", 1)
    gx = _GF_EXCHANGE[exch]
    if exch == "HKEX":
        sym = sym.zfill(5)
    return sym if gx is None else f"{gx}:{sym}"


def fundamental_key(ticker):
    """Key for data/fundamental/<key>.json. US listings keep the bare symbol (shared with the
    AI/quantum universes); foreign listings are namespaced EXCH_SYMBOL so that ASX:LIN can
    never collide with Linde (NYSE:LIN) or ASX:HAS with Hasbro."""
    exch, sym = ticker.split(":", 1)
    return sym if COUNTRY_OF_EXCHANGE[exch] == "US" else f"{exch}_{sym}"
