"""Pure normalization and control handling for ecosystem configuration."""

from __future__ import annotations

import copy
import math
from collections.abc import Mapping
from typing import Any


DEFAULT_ECOSYSTEM_CONFIG = {
    "enabled": True,
    "simulationSpeed": 1.0,
    "startingSeed": 7,
    "foodAbundance": 1.0,
    "mutationRate": 0.08,
    "predatorPressure": 1.0,
    "foodDrops": True,
    "shrimpEnabled": True,
    "currentsEnabled": True,
    "huntsEnabled": True,
    "diagnosticAccelerated": False,
}
CONTROL_KEYS = frozenset(DEFAULT_ECOSYSTEM_CONFIG)


def _number(value: Any, fallback: float, low: float, high: float) -> float:
    if isinstance(value, bool):
        return fallback
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    if not math.isfinite(number):
        return fallback
    return max(low, min(high, number))


def _seed(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return DEFAULT_ECOSYSTEM_CONFIG["startingSeed"]
    return max(-(2**31), min(2**31 - 1, value))


def normalise_ecosystem_config(raw: Any) -> dict[str, Any]:
    incoming = raw if isinstance(raw, Mapping) else {}
    return {
        "enabled": incoming.get("enabled", True) is True,
        "simulationSpeed": round(_number(incoming.get("simulationSpeed"), 1.0, 0.1, 4.0), 2),
        "startingSeed": _seed(incoming.get("startingSeed")),
        "foodAbundance": round(_number(incoming.get("foodAbundance"), 1.0, 0.0, 2.0), 4),
        "mutationRate": round(_number(incoming.get("mutationRate"), 0.08, 0.0, 1.0), 4),
        "predatorPressure": round(_number(incoming.get("predatorPressure"), 1.0, 0.0, 2.0), 4),
        "foodDrops": incoming.get("foodDrops", True) is True,
        "shrimpEnabled": incoming.get("shrimpEnabled", True) is True,
        "currentsEnabled": incoming.get("currentsEnabled", True) is True,
        "huntsEnabled": incoming.get("huntsEnabled", True) is True,
        "diagnosticAccelerated": incoming.get("diagnosticAccelerated", False) is True,
    }


def apply_ecosystem_control(config: Mapping[str, Any], key: str, value: Any) -> dict[str, Any]:
    """Return a normalized copy after changing one ecosystem control only."""

    if key not in CONTROL_KEYS:
        raise KeyError(f"unknown ecosystem control: {key}")
    next_config = normalise_ecosystem_config(config)
    next_config[key] = value
    return normalise_ecosystem_config(next_config)


def reset_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Reset ecosystem controls while preserving all unrelated configuration."""

    preserved = copy.deepcopy(dict(config))
    preserved["ecosystem"] = copy.deepcopy(DEFAULT_ECOSYSTEM_CONFIG)
    return preserved


def model_settings(config: Mapping[str, Any]) -> dict[str, Any]:
    ecosystem = normalise_ecosystem_config(config.get("ecosystem", config))
    result = {
        "food_abundance": ecosystem["foodAbundance"],
        "mutation_rate": ecosystem["mutationRate"],
        "predator_pressure": ecosystem["predatorPressure"],
        "food_drops": ecosystem["foodDrops"],
        "shrimp_enabled": ecosystem["shrimpEnabled"],
        "currents_enabled": ecosystem["currentsEnabled"],
        "hunts_enabled": ecosystem["huntsEnabled"],
    }
    if isinstance(config.get("species"), Mapping):
        try:
            from scripts.ecosystem_model import DEFAULT_POPULATION, MAX_POPULATION
        except ModuleNotFoundError:
            from ecosystem_model import DEFAULT_POPULATION, MAX_POPULATION
        result["species"] = {
            key: max(0, min(MAX_POPULATION[key], value))
            if isinstance(value := config["species"].get(key, default), int) and not isinstance(value, bool)
            else default for key, default in DEFAULT_POPULATION.items()
        }
    return result


__all__ = [
    "CONTROL_KEYS",
    "DEFAULT_ECOSYSTEM_CONFIG",
    "apply_ecosystem_control",
    "model_settings",
    "normalise_ecosystem_config",
    "reset_config",
]
