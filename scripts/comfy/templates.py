"""Load and parameterize API-format ComfyUI workflow templates.

Templates are the JSON shape POST /prompt expects:
{node_id: {"class_type": …, "inputs": {…}}, …}. PARAM_MAPS names the
logical knobs a template exposes and where each lands (node_id, input);
entries are added as templates are authored against the live server.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

PARAM_MAPS: dict[str, dict[str, tuple[str, str]]] = {}


def apply_params(workflow: dict, param_map: dict, params: dict) -> dict:
    unknown = set(params) - set(param_map)
    if unknown:
        raise KeyError(f"unknown params {sorted(unknown)}; "
                       f"template exposes {sorted(param_map)}")
    wf = copy.deepcopy(workflow)
    for name, value in params.items():
        node_id, input_name = param_map[name]
        wf[node_id]["inputs"][input_name] = value
    return wf


def load_template(name: str, **params) -> dict:
    wf = json.loads((TEMPLATES_DIR / f"{name}.json").read_text("utf-8"))
    return apply_params(wf, PARAM_MAPS[name], params)
