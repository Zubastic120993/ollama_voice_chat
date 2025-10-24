"""
logic_tool.py
Interprets user messages and calls the right function from scientific_tool.py
"""

from tools import scientific_tool as sci
import re

UNIT_ALIASES = {
    "farengheit": "fahrenheit",
    "farenheit": "fahrenheit",
    "celcius": "celsius",
    "centigrade": "celsius",
    "kelvins": "kelvin",
    "bars": "bar",
    "mpascal": "MPa",
    "mpsa": "MPa",
    "ton": "tonne",
    "tons": "tonne",
    "m3h": "m³/h",
    "m3": "m³",
    "litre": "liter",
    "litres": "liter",
    "meters": "meter",
    "metres": "meter",
}

def normalize_unit(u: str) -> str:
    """Normalize common misspellings and aliases for units."""
    u = u.strip().lower().replace("°", "")
    return UNIT_ALIASES.get(u, u)


def call_engineering_tool(message: str):
    msg = message
    msg_lower = msg.lower()

    # Steam properties
    if "steam" in msg_lower and ("enthalpy" in msg_lower or "entropy" in msg_lower):
        T = re.search(r"(\d+)\s*(?:c|°c)", msg_lower)
        P = re.search(r"(\d+)\s*(?:bar)", msg_lower)
        if T and P:
            result = sci.steam_props(float(T.group(1)), float(P.group(1)))
            return (
                f"Steam at {T.group(1)}°C & {P.group(1)} bar:\n"
                f"h = {result['h_kJkg']:.2f} kJ/kg, "
                f"s = {result['s_kJkgK']:.3f} kJ/kg·K, "
                f"ρ = {result['rho']:.2f} kg/m³"
            )
        return "Please specify temperature (°C) and pressure (bar)."

    # Fuel properties
    if "fuel" in msg_lower or "octane" in msg_lower or "diesel" in msg_lower:
        fuel = "n-octane" if "octane" in msg_lower else "n-heptane"
        result = sci.fuel_props(fuel)
        return (
            f"{fuel.capitalize()} → MW: {result['MW']:.2f}, "
            f"ρ_liq: {result['rho_liq']:.1f} kg/m³, "
            f"Cp: {result['cp_liq']:.0f} J/kg·K"
        )

    # Unit conversion
    if "convert" in msg_lower and "to" in msg_lower:
        try:
            val_match = re.search(r"(\d+(\.\d+)?)", msg)
            if not val_match:
                return "Please provide a numeric value to convert."

            val = float(val_match.group(1))
            parts = msg.split("to")
            from_u = normalize_unit(parts[0].split()[-1])
            to_u = normalize_unit(parts[1])
            result = sci.convert(val, from_u, to_u)

            return f"{val} {from_u} = {result:.4g} {to_u}"
        except Exception as e:
            return f"Conversion error: {e}"

    # Combustion
    if "combustion" in msg_lower or "flame" in msg_lower:
        result = sci.combustion("CH4")
        return f"Methane combustion → Flame T = {result['T_flame_K']:.0f} K"

    return None
