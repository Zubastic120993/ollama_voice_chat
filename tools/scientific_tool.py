
"""
scientific_tool.py
==================
Thermodynamics & unit conversion helper module
Uses Pint, CoolProp, thermo, and Cantera.
"""

import pint
import CoolProp.CoolProp as CP
import thermo
import cantera as ct

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity

# =====================================================
# 🌡️ Steam / Water properties
# =====================================================
def steam_props(T_C, P_bar):
    T = Q_(T_C, ureg.degC).to("K").magnitude
    P = Q_(P_bar, ureg.bar).to("Pa").magnitude
    return {
        "h_kJkg": CP.PropsSI("H", "T", T, "P", P, "Water") / 1000,
        "s_kJkgK": CP.PropsSI("S", "T", T, "P", P, "Water") / 1000,
        "rho": CP.PropsSI("D", "T", T, "P", P, "Water"),
        "v_m3kg": 1 / CP.PropsSI("D", "T", T, "P", P, "Water"),
    }

# =====================================================
# ⛽ Fuel properties
# =====================================================
def fuel_props(fuel="n-octane"):
    f = thermo.Chemical(fuel)
    return {
        "formula": f.formula,
        "MW": f.MW,
        "rho_liq": f.rhol,
        "cp_liq": f.Cpl,
        "hvap": f.Hvap,
    }

# =====================================================
# 🔥 Combustion (simple equilibrium)
# =====================================================
def combustion(fuel="CH4", phi=1.0, P_bar=1.0, T_K=300):
    gas = ct.Solution("gri30.yaml")
    gas.TP = T_K, P_bar * 1e5
    gas.set_equivalence_ratio(phi=phi, fuel=fuel, oxidizer="O2:1.0, N2:3.76")
    gas.equilibrate("HP")
    return {"T_flame_K": gas.T, "products": gas.mole_fraction_dict()}

# =====================================================
# 🧮 Quick unit converter
# =====================================================
def convert(value, from_unit, to_unit):
    return Q_(value, from_unit).to(to_unit).magnitude
