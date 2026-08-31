from __future__ import annotations

from dataclasses import dataclass


class UnitConversionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class UnitDefinition:
    symbol: str
    dimension: str
    factor: float
    canonical: str


_UNITS = {
    "one": UnitDefinition("one", "dimensionless", 1.0, "one"),
    "mm": UnitDefinition("mm", "length", 0.001, "m"),
    "cm": UnitDefinition("cm", "length", 0.01, "m"),
    "dm": UnitDefinition("dm", "length", 0.1, "m"),
    "m": UnitDefinition("m", "length", 1.0, "m"),
    "km": UnitDefinition("km", "length", 1000.0, "m"),
    "g": UnitDefinition("g", "mass", 0.001, "kg"),
    "kg": UnitDefinition("kg", "mass", 1.0, "kg"),
    "second": UnitDefinition("second", "time", 1.0, "second"),
    "minute": UnitDefinition("minute", "time", 60.0, "second"),
    "hour": UnitDefinition("hour", "time", 3600.0, "second"),
    "day": UnitDefinition("day", "time", 86400.0, "second"),
    "cm2": UnitDefinition("cm2", "area", 0.0001, "m2"),
    "m2": UnitDefinition("m2", "area", 1.0, "m2"),
    "cm3": UnitDefinition("cm3", "volume", 0.000001, "m3"),
    "m3": UnitDefinition("m3", "volume", 1.0, "m3"),
    "ml": UnitDefinition("ml", "volume", 0.000001, "m3"),
    "liter": UnitDefinition("liter", "volume", 0.001, "m3"),
    "m/s": UnitDefinition("m/s", "speed", 1.0, "m/s"),
    "km/h": UnitDefinition("km/h", "speed", 1.0 / 3.6, "m/s"),
    "degree": UnitDefinition("degree", "angle", 1.0, "degree"),
}

_ALIASES = {
    "": "one",
    "1": "one",
    "s": "second",
    "sec": "second",
    "seconds": "second",
    "phút": "minute",
    "min": "minute",
    "minutes": "minute",
    "h": "hour",
    "hr": "hour",
    "hours": "hour",
    "ngày": "day",
    "days": "day",
    "cm²": "cm2",
    "m²": "m2",
    "cm³": "cm3",
    "m³": "m3",
    "l": "liter",
    "litre": "liter",
    "litres": "liter",
    "milliliter": "ml",
    "millilitre": "ml",
    "°": "degree",
    "deg": "degree",
    "degrees": "degree",
    "độ": "degree",
}


def normalize_unit(unit: str | None) -> str:
    raw = str(unit or "one").strip().lower()
    normalized = _ALIASES.get(raw, raw)
    if normalized not in _UNITS:
        raise UnitConversionError(f"Unsupported math unit: {unit}")
    return normalized


def unit_definition(unit: str | None) -> UnitDefinition:
    return _UNITS[normalize_unit(unit)]


def canonicalize(value: float, unit: str | None) -> tuple[float, str]:
    definition = unit_definition(unit)
    return value * definition.factor, definition.canonical


def convert(value: float, source: str, target: str) -> float:
    source_definition = unit_definition(source)
    target_definition = unit_definition(target)
    if source_definition.dimension != target_definition.dimension:
        raise UnitConversionError(
            f"Cannot convert {source_definition.dimension} to {target_definition.dimension}"
        )
    canonical = value * source_definition.factor
    return canonical / target_definition.factor


def supported_units() -> tuple[str, ...]:
    return tuple(_UNITS)
