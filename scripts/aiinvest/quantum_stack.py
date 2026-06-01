"""The quantum-sector value-chain universe (mirrors ai_stack.py).

Tickers are TradingView ``EXCHANGE:SYMBOL`` form for the *america* scanner. Each
US-listed name lives in ONE primary screener layer. Diversified giants (where quantum
is a small slice) are GRAPH-ONLY nodes — not screener members. Foreign listings and
private / pre-IPO names are watch-list graph nodes only (can't be pulled from the
america scanner). See GIANT_NODES / PRIVATE_NODES / FOREIGN_NODES below.

Universe sourced from 2026-06-01-quantum-universe-research.md. Educational/research
only — not investment advice. Pure-plays are largely pre-revenue/speculative; recent
SPAC/IPO names (INFQ/XNDU/HQ/BTQ/QNT) must be re-verified live before a pull treats
them as fact.
"""
from __future__ import annotations

SECTOR = "Quantum"

LAYERS = {
    # Q1 — Qubit hardware / quantum computers (the pure-plays)
    "Q1-hardware": [
        "NYSE:IONQ", "NASDAQ:RGTI", "NYSE:QBTS", "NASDAQ:QUBT", "NYSE:INFQ", "NASDAQ:XNDU",
    ],
    # Q3 — Software / algorithms / compilers / middleware (pure-play)
    "Q3-software": [
        "NASDAQ:HQ",
    ],
    # Q4 — Networking & post-quantum security (QKD, PQC, QRNG)
    "Q4-security": [
        "NASDAQ:ARQQ", "NASDAQ:LAES", "NASDAQ:WKEY", "AMEX:QNC", "NASDAQ:BTQ",
    ],
    # Q5 — Applications / demand-side (pharma, finance — customers, not quantum businesses)
    "Q5-applications": [
        "NYSE:AZN", "NYSE:GSK", "NASDAQ:MRNA", "NYSE:JPM", "NYSE:GS",
        "NYSE:BCS", "NYSE:BBVA", "NYSE:HSBC",
    ],
}

# Attempted on each pull; included automatically once it resolves live.
PENDING = []  # Quantinuum (QNT) IPO ~Jun 4 2026 — NOT yet trading; "QNT" maps to a
# different issuer on Yahoo/the data source, so do not pull it as the quantum pure-play
# until it lists. Quantinuum remains a private watch-list node below.

# Diversified bridges/suppliers — GRAPH-ONLY (quantum is a small slice; not screener
# members). id is the bare symbol so the combined graph can bridge AI<->Quantum.
GIANT_NODES = [
    {"id": "IBM", "name": "IBM", "layer": "Q1-hardware", "note": "superconducting qubits; IBM Quantum cloud"},
    {"id": "GOOGL", "name": "Alphabet (Google Quantum AI)", "layer": "Q1-hardware", "note": "Willow chip; quantum cloud"},
    {"id": "MSFT", "name": "Microsoft", "layer": "Q1-hardware", "note": "Majorana / topological; Azure Quantum"},
    {"id": "AMZN", "name": "Amazon", "layer": "Q2-cloud", "note": "AWS Braket QaaS; Ocelot chip"},
    {"id": "NVDA", "name": "Nvidia", "layer": "Q2-cloud", "note": "CUDA-Q / NVQLink; quantum-classical bridge"},
    {"id": "INTC", "name": "Intel", "layer": "Q1-hardware", "note": "silicon spin qubits (Tunnel Falls)"},
    {"id": "HON", "name": "Honeywell", "layer": "Q1-hardware", "note": "majority owner of Quantinuum"},
    {"id": "AMAT", "name": "Applied Materials", "layer": "Q0-enabling", "note": "fab / materials for qubit devices"},
    {"id": "TSM", "name": "TSMC", "layer": "Q0-enabling", "note": "foundry for control chips"},
    {"id": "COHR", "name": "Coherent", "layer": "Q0-enabling", "note": "lasers / photonics / optics"},
    {"id": "CSCO", "name": "Cisco", "layer": "Q4-security", "note": "quantum networking research"},
    {"id": "AMD", "name": "AMD", "layer": "Q2-cloud", "note": "classical co-processing / FPGA control (Xilinx)"},
    {"id": "NOK", "name": "Nokia", "layer": "Q4-security", "note": "quantum-safe networking / Bell Labs"},
    {"id": "BAH", "name": "Booz Allen Hamilton", "layer": "Q2-cloud", "note": "quantum services prime; SEEQC investor"},
    {"id": "LDOS", "name": "Leidos", "layer": "Q2-cloud", "note": "quantum services prime"},
    {"id": "NOC", "name": "Northrop Grumman", "layer": "Q2-cloud", "note": "defense quantum programs"},
    {"id": "LMT", "name": "Lockheed Martin", "layer": "Q2-cloud", "note": "defense quantum programs"},
    {"id": "ACN", "name": "Accenture", "layer": "Q2-cloud", "note": "quantum services / integration"},
    {"id": "FORM", "name": "FormFactor", "layer": "Q0-enabling", "note": "cryogenic probe / test systems"},
    {"id": "KEYS", "name": "Keysight", "layer": "Q0-enabling", "note": "quantum control & test instruments"},
    {"id": "MKSI", "name": "MKS Instruments", "layer": "Q0-enabling", "note": "vacuum / photonics / RF subsystems"},
    {"id": "IPGP", "name": "IPG Photonics", "layer": "Q0-enabling", "note": "lasers"},
    {"id": "LITE", "name": "Lumentum", "layer": "Q0-enabling", "note": "photonics / lasers"},
    {"id": "APH", "name": "Amphenol", "layer": "Q0-enabling", "note": "RF / cryo interconnect"},
    {"id": "STM", "name": "STMicroelectronics", "layer": "Q0-enabling", "note": "control / cryo-CMOS electronics"},
]

# Private / pre-IPO watch-list — GRAPH-ONLY nodes (not on the america scanner).
PRIVATE_NODES = [
    {"id": "quantinuum", "name": "Quantinuum", "layer": "Q1-hardware", "note": "trapped-ion; HON majority; IPO imminent (QNT)"},
    {"id": "psiquantum", "name": "PsiQuantum", "layer": "Q1-hardware", "note": "photonic; private"},
    {"id": "iqm", "name": "IQM", "layer": "Q1-hardware", "note": "superconducting; SPAC pending"},
    {"id": "pasqal", "name": "Pasqal", "layer": "Q1-hardware", "note": "neutral-atom; SPAC pending"},
    {"id": "quera", "name": "QuEra", "layer": "Q1-hardware", "note": "neutral-atom; private"},
    {"id": "atom_computing", "name": "Atom Computing", "layer": "Q1-hardware", "note": "neutral-atom; MSFT partner"},
    {"id": "alice_bob", "name": "Alice & Bob", "layer": "Q1-hardware", "note": "cat-qubit; NVDA NVentures-backed"},
    {"id": "quandela", "name": "Quandela", "layer": "Q1-hardware", "note": "photonic; private"},
    {"id": "oqc", "name": "Oxford Quantum Circuits", "layer": "Q1-hardware", "note": "superconducting; private"},
    {"id": "seeqc", "name": "SEEQC", "layer": "Q1-hardware", "note": "digital SFQ; SPAC pending; BAH investor"},
    {"id": "nord_quantique", "name": "Nord Quantique", "layer": "Q1-hardware", "note": "bosonic-code; private"},
    {"id": "bluefors", "name": "Bluefors", "layer": "Q0-enabling", "note": "dilution refrigerators (cryo)"},
    {"id": "quantum_machines", "name": "Quantum Machines", "layer": "Q0-enabling", "note": "quantum control hardware"},
    {"id": "qblox", "name": "Qblox", "layer": "Q0-enabling", "note": "qubit control electronics"},
    {"id": "classiq", "name": "Classiq", "layer": "Q3-software", "note": "quantum software / synthesis"},
    {"id": "q_ctrl", "name": "Q-CTRL", "layer": "Q3-software", "note": "quantum control / error-suppression SW"},
    {"id": "riverlane", "name": "Riverlane", "layer": "Q3-software", "note": "quantum error-correction stack"},
    {"id": "sandboxaq", "name": "SandboxAQ", "layer": "Q3-software", "note": "AI+quantum; Alphabet spinout"},
    {"id": "id_quantique", "name": "ID Quantique", "layer": "Q4-security", "note": "QKD/QRNG; IonQ-owned"},
    {"id": "qunnect", "name": "Qunnect", "layer": "Q4-security", "note": "quantum networking; private"},
    {"id": "aliro", "name": "Aliro Quantum", "layer": "Q4-security", "note": "entanglement networks; private"},
    {"id": "pqshield", "name": "PQShield", "layer": "Q4-security", "note": "post-quantum cryptography; private"},
    {"id": "oxford_ionics", "name": "Oxford Ionics", "layer": "Q1-hardware", "note": "trapped-ion; acquired by IONQ Sep'25"},
    {"id": "quantum_circuits", "name": "Quantum Circuits Inc", "layer": "Q1-hardware", "note": "dual-rail; acquired by QBTS Jan'26"},
    {"id": "lightsynq", "name": "Lightsynq", "layer": "Q4-security", "note": "quantum networking; IonQ-owned"},
]

# Foreign-listed / non-america names — GRAPH-ONLY nodes (not on the america scanner).
FOREIGN_NODES = [
    {"id": "oxig", "name": "Oxford Instruments", "layer": "Q0-enabling", "note": "LSE:OXIG — cryogenics"},
    {"id": "hamamatsu", "name": "Hamamatsu Photonics", "layer": "Q0-enabling", "note": "TSE:6965 — detectors/photonics"},
    {"id": "toshiba", "name": "Toshiba", "layer": "Q4-security", "note": "TSE:6502 — QKD"},
    {"id": "fujitsu", "name": "Fujitsu", "layer": "Q1-hardware", "note": "TSE:6702 — superconducting program"},
    {"id": "nec", "name": "NEC", "layer": "Q1-hardware", "note": "TSE:6701 — annealing/quantum program"},
    {"id": "quantumctek", "name": "QuantumCTek", "layer": "Q4-security", "note": "SHA:688027 — QKD networks"},
    {"id": "exail", "name": "Exail", "layer": "Q0-enabling", "note": "EPA:EXA — quantum sensing"},
    {"id": "thales", "name": "Thales", "layer": "Q4-security", "note": "EPA:HO — quantum/PQC"},
    {"id": "ntt", "name": "NTT", "layer": "Q4-security", "note": "TSE:9432 — quantum networking research"},
    {"id": "soitec", "name": "Soitec", "layer": "Q0-enabling", "note": "EPA:SOI — substrates"},
]


def all_tickers():
    """Flat, de-duplicated list of every tradeable screener ticker across the stack."""
    seen, out = set(), []
    for tickers in LAYERS.values():
        for t in tickers:
            if t not in seen:
                seen.add(t)
                out.append(t)
    return out


def layer_of(ticker):
    """Return the stack-layer key for a screener ticker, or None if not in the universe."""
    for layer, tickers in LAYERS.items():
        if ticker in tickers:
            return layer
    return None
