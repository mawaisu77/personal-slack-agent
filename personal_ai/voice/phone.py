"""Resolve outbound phone numbers to E.164 (T-030)."""

from __future__ import annotations

import re
from typing import Any

_E164 = re.compile(r"^\+[1-9]\d{1,14}$")


def resolve_phone_e164(payload: dict[str, Any]) -> str:
    """
    Prefer explicit E.164; otherwise normalize US-style 10/11 digit strings.
    Raises ``ValueError`` when no usable number is present.
    """
    for key in ("phone_e164", "e164", "to", "phone", "phone_number"):
        raw = payload.get(key)
        if not isinstance(raw, str):
            continue
        s = raw.strip()
        if not s:
            continue
        if s.startswith("+") and _E164.match(s):
            return s
        digits = re.sub(r"\D", "", s)
        if len(digits) == 10:
            return "+1" + digits
        if len(digits) == 11 and digits.startswith("1"):
            return "+" + digits
    msg = "No valid phone number in payload (expected E.164 or US digits)"
    raise ValueError(msg)
