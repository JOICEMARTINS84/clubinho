# O céu da Bandeira Brasileira — Matemática & Contexto

Autora: **Joice Souza Martins Santos**.

Programa educacional com Python, HTML, CSS e JavaScript: 27 estrelas interativas, nove constelações, estados brasileiros, história oficial da bandeira, fala em português e quiz.

## Executar localmente

~~~bash
python -m http.server 8000
~~~

Visite http://localhost:8000/Bandeira-Astronomica/ (se o servidor foi aberto na raiz do repositório) ou http://localhost:8000/ (se abriu dentro desta pasta).

## Python e API do SIMBAD/CDS

~~~bash
pip install -r requirements.txt
python catalogo.py --simbad
~~~

O arquivo dados.json registra o mapeamento oficial e serve mesmo sem API. O Python faz consultas por astroquery e adiciona somente coordenadas, tipo espectral e magnitude V realmente informados pelo SIMBAD. Se não houver resultado, nenhum dado numérico é inventado.

## GitHub Pages

Os arquivos HTML, CSS, JS e JSON são estáticos. GitHub Pages não executa Python; use Python para gerar ou atualizar o JSON antes da publicação.

## Referências oficiais

- https://plenarinho.leg.br/index.php/2018/10/bandeira-nacional/
- https://www2.camara.leg.br/legin/fed/lei/1992/lei-8421-11-maio-1992-362960-anexos-pl.pdf
- https://www2.camara.leg.br/legin/fed/lei/1970-1979/lei-5700-1-setembro-1971-357915-normaatualizada-pl.html
- https://simbad.cds.unistra.fr/

**Nota:** Posições x/y usadas no SVG são didáticas aproximadas, NÃO posições oficiais exatas ou coordenadas RA/Dec. Tamanho 1–5 na bandeira não é magnitude astronômica V.
