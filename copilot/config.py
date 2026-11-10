"""Load config.yaml (paths are resolved relative to the repo root)."""
from pathlib import Path
import copy
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_config(path: str | Path | None = None, overrides: dict | None = None) -> dict:
    cfg = yaml.safe_load(open(path or ROOT / "config.yaml"))
    if overrides:
        cfg = copy.deepcopy(cfg)
        for dotted, value in overrides.items():
            node = cfg
            *parents, leaf = dotted.split(".")
            for p in parents:
                node = node[p]
            node[leaf] = value
    return cfg


def p(rel: str) -> Path:
    return ROOT / rel
