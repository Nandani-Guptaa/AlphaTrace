"""Validation and normalization for user-provided, non-executing portfolios."""

from collections import defaultdict
import csv
from io import StringIO
from math import isfinite
from typing import Any, Dict, List


def parse_csv_positions(csv_text: str) -> List[Dict[str, Any]]:
    """Parse the documented CSV shape before applying position validation."""
    if not csv_text or not csv_text.strip():
        raise ValueError("Portfolio CSV is empty.")
    reader = csv.DictReader(StringIO(csv_text))
    required = {"symbol", "quantity", "price"}
    if not reader.fieldnames or not required.issubset({name.strip() for name in reader.fieldnames if name}):
        raise ValueError("Portfolio CSV requires headers: symbol, quantity, price.")
    return normalize_positions(list(reader))


def normalize_positions(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate rows and aggregate only exactly equivalent duplicate positions.

    A duplicate is aggregateable only when symbol, price, asset type, and sector
    match.  Conflicting duplicates are rejected rather than silently applying an
    arbitrary price or metadata choice.  Quantity is signed; notional is quantity
    times price, with gross exposure calculated later as ``abs(notional)``.
    """
    if not rows:
        raise ValueError("Portfolio must contain at least one position.")

    grouped: Dict[tuple, float] = defaultdict(float)
    normalized: Dict[tuple, Dict[str, Any]] = {}
    symbols: Dict[str, tuple] = {}
    for index, row in enumerate(rows, start=1):
        symbol = str(row.get("symbol", "")).strip().upper()
        if not symbol:
            raise ValueError(f"Row {index}: symbol is required.")
        try:
            quantity = float(row.get("quantity"))
            price = float(row.get("price"))
        except (TypeError, ValueError):
            raise ValueError(f"Row {index}: quantity and price must be numbers.")
        if not isfinite(quantity) or not isfinite(price):
            raise ValueError(f"Row {index}: quantity and price must be finite numbers.")
        if quantity == 0:
            raise ValueError(f"Row {index}: quantity cannot be zero.")
        if price <= 0:
            raise ValueError(f"Row {index}: price must be greater than zero.")

        asset_type = str(row.get("asset_type") or "Unknown").strip() or "Unknown"
        sector = str(row.get("sector") or "Unknown").strip() or "Unknown"
        key = (symbol, price, asset_type, sector)
        previous_key = symbols.get(symbol)
        if previous_key is not None and previous_key != key:
            raise ValueError(
                f"Row {index}: duplicate symbol '{symbol}' has conflicting price or metadata; submit one consolidated row."
            )
        symbols[symbol] = key
        grouped[key] += quantity
        normalized[key] = {"symbol": symbol, "price": price, "asset_type": asset_type, "sector": sector}

    result = []
    for key, quantity in grouped.items():
        if quantity == 0:
            raise ValueError(f"Duplicate rows for '{key[0]}' net to zero and cannot form a position.")
        row = normalized[key]
        result.append({**row, "quantity": quantity, "exposure": round(quantity * row["price"], 2)})
    return sorted(result, key=lambda item: item["symbol"])
