"""Auditoria dos dados e do HTML do atlas da Bandeira Nacional.

Rodar: python validar_estrelas.py
Usa apenas a biblioteca padrão do Python.
"""
from pathlib import Path
import json
import math

import build

ROOT = Path(__file__).resolve().parent


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


stars = load("estrelas.json")
charts = load("cartas_celestes.json")

# --- Catálogo de estrelas ----------------------------------------------------
assert len(stars) == 27, "A bandeira tem 27 estrelas."
assert len({s["uf"] for s in stars}) == 27, "Todas as 27 UFs devem ser distintas."
assert len({s["constelacao"] for s in stars}) == 9, "O atlas deve ter 9 constelações."
assert {s["grandeza"] for s in stars} == set(range(1, 6)), "Devem aparecer as 5 grandezas gráficas."
assert all(
    math.hypot(s["cx"] - 1000, s["cy"] - 700) < 350 for s in stars
), "Estrela fora do disco azul."
assert all(
    abs(s["cx"] / 20 - s["x"]) < 0.02 and abs(s["cy"] / 14 - s["y"]) < 0.02 for s in stars
), "Coordenadas absolutas e percentuais divergentes."
assert next(s for s in stars if s["uf"] == "PA")["nome"] == "Spica"
assert next(s for s in stars if s["uf"] == "RS")["grandeza"] == 2

# --- Cartas celestes ---------------------------------------------------------
assert set(charts) == {s["constelacao"] for s in stars}, "Cada constelação precisa de uma carta."
for s in stars:
    assert s["uf"] in charts[s["constelacao"]]["highlights"], f"{s['uf']} sem destaque na carta."
assert sum(len(c["highlights"]) for c in charts.values()) == 27, "A soma dos destaques deve ser 27."
assert all(
    math.isfinite(charts[s["constelacao"]]["highlights"][s["uf"]]["m"])
    for s in stars
), "Cada estrela deve ter magnitude aparente numérica de catálogo."

# --- index.html gerado -------------------------------------------------------
assert (ROOT / "index.html").read_text(encoding="utf-8") == build.render(), (
    "index.html está desatualizado em relação a src/ e aos JSON. Rode: python build.py"
)

print("Auditoria concluída: 27 estrelas, 9 constelações com carta, 5 grandezas, "
      "coordenadas consistentes e index.html em dia.")
