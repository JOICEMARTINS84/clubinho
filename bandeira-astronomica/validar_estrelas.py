"""Auditoria dos dados do atlas da Bandeira Nacional.

Rodar: python validar_estrelas.py
Usa apenas a biblioteca padrão do Python.
"""
from pathlib import Path
import json
import math

data = json.loads(Path(__file__).with_name("estrelas.json").read_text(encoding="utf-8"))

assert len(data) == 27, "A bandeira tem 27 estrelas."
assert len({star["uf"] for star in data}) == 27, "Todas as 27 UFs devem ser distintas."
assert len({star["constelacao"] for star in data}) == 9, "O atlas deve ter 9 constelações."
assert {star["grandeza"] for star in data} == set(range(1, 6)), "Devem aparecer as 5 grandezas gráficas."
assert all(
    math.hypot(star["cx"] - 1000, star["cy"] - 700) < 350
    for star in data
), "Estrela fora do disco azul."
assert all(
    abs(star["cx"] / 20 - star["x"]) < 0.02 and
    abs(star["cy"] / 14 - star["y"]) < 0.02
    for star in data
), "Coordenadas absolutas e percentuais divergentes."
assert next(star for star in data if star["uf"] == "PA")["nome"] == "Spica"
assert next(star for star in data if star["uf"] == "RS")["grandeza"] == 2
print("Auditoria concluída: 27 estrelas, 9 constelações, 5 grandezas e coordenadas consistentes.")
