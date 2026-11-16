"""Auditoria simples do conjunto de 27 estrelas do atlas.
Execute: python validar_estrelas.py
Não usa API nem gera efemérides.
"""
import json
from pathlib import Path
data = json.loads(Path(__file__).with_name("estrelas.json").read_text(encoding="utf-8"))
assert len(data) == 27, "São necessárias 27 estrelas."
assert len({s["uf"] for s in data}) == 27, "UF duplicada."
assert len({s["constelacao"] for s in data}) == 9, "São esperadas nove constelações."
assert all(0 <= s["x"] <= 100 and 0 <= s["y"] <= 100 for s in data)
print(f"Auditoria OK: {len(data)} estrelas, {len(set(s['constelacao'] for s in data))} constelações.")
