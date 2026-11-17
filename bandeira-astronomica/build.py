"""Monta o index.html autossuficiente a partir das peças em src/.

Fontes de verdade:
  src/template.html        estrutura da página
  src/style.css            estilos
  src/app.js               lógica
  estrelas.json            catálogo das 27 estrelas
  cartas_celestes.json     cartas das 9 constelações

Uso (apenas biblioteca padrão):
  python build.py           gera/atualiza index.html
  python build.py --check   falha se o index.html estiver desatualizado

O Streamlit lê o index.html pronto, e ele também abre direto no navegador,
sem servidor, por isso tudo é incorporado em um único arquivo.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "index.html"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def inline_json(value) -> str:
    """JSON compacto, seguro para ficar dentro de uma tag <script>."""
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return text.replace("</", "<\\/")


def render() -> str:
    atlas = {
        "stars": json.loads(read("estrelas.json")),
        "charts": json.loads(read("cartas_celestes.json")),
    }
    html = read("src/template.html")
    for token, content in (
        ("{{STYLE}}", read("src/style.css")),
        ("{{DATA}}", "window.ATLAS=" + inline_json(atlas) + ";"),
        ("{{SCRIPT}}", read("src/app.js")),
    ):
        if token not in html:
            raise SystemExit(f"Marcador {token} não encontrado em src/template.html")
        html = html.replace(token, content)
    return html


def main() -> int:
    html = render()
    if "--check" in sys.argv:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
        if current != html:
            print("index.html está desatualizado. Rode: python build.py")
            return 1
        print("index.html está em dia com src/ e os JSON.")
        return 0
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"index.html gerado ({len(html.encode('utf-8')) / 1024:.1f} KB).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
