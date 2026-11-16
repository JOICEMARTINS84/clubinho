# O Céu na Bandeira do Brasil

**Aplicativo independente** de astronomia educativa para o Streamlit Community Cloud.
Autoria: **Joice Souza Martins Santos**, projeto Matemática & Contexto.

## O que contém
- Atlas interativo da bandeira do Brasil com 27 estrelas, 26 estados e o Distrito Federal;
- Nove constelações, nomes e designações astronômicas;
- Busca por estado/estrela, filtro por constelação e seleção por clique;
- Texto histórico e referências institucionais;
- Interface responsiva em HTML, CSS e JavaScript incorporada a uma aplicação Python + Streamlit.

**Nota científica (versão revisada):** a bandeira foi reconstruída em SVG com proporção 20:14, círculo de raio 3,5 módulos, losango e arco segundo a Lei nº 5.700/1971, e centros das 27 estrelas baseados em estudo da geometria do desenho modular. As estrelas têm as cinco grandezas gráficas previstas na lei. A interface permite ampliar o círculo azul. Este desenho vetorial é uma reconstituição didática baseada na legislação; não é uma imagem oficial fornecida pelo governo, nem uma projeção astronômica de dados observacionais. Não há API astronômica ativa nesta versão.

## Publicar como aplicativo SEPARADO do Horizonte Lunar

1. Entre em **https://share.streamlit.io** com seu GitHub.
2. Clique em **Create app** → **Yup, I have an app**.
3. Use estes três campos:
   - Repository: `JOICEMARTINS84/clubinho`
   - Branch: `main`
   - Main file path: `bandeira-astronomica/streamlit_app.py`
4. Escolha um subdomínio como `ceu-na-bandeira-brasil` **se estiver disponível**.
5. Clique em **Deploy**. O Streamlit criará um endereço próprio para este app. Este procedimento não modifica nem substitui o Horizonte Lunar.

## Rodar no seu computador

No terminal, na raiz do repositório:

```bash
pip install -r bandeira-astronomica/requirements.txt
streamlit run bandeira-astronomica/streamlit_app.py
```

Também é possível abrir `bandeira-astronomica/index.html` diretamente no navegador, sem Python.

## Estrutura

- `streamlit_app.py` — arquivo de entrada de **seu próprio aplicativo Streamlit**
- `requirements.txt` — dependências deste app
- `.streamlit/config.toml` — tema deste app
- `index.html` — interface HTML/CSS/JS
- `estrelas.json` — catálogo auditável das 27 estrelas
- `validar_estrelas.py` — conferência do catálogo

## Fontes

- Lei nº 5.700/1971 — https://www2.camara.leg.br/legin/fed/lei/1970-1979/lei-5700-1-setembro-1971-357915-normaatualizada-pl.html
- INPE — material didático sobre bandeira e astronomia
- Agência Espacial Brasileira — constelações e bandeira brasileira

## Etapas futuras

- Conferir visualmente a reconstituição vetorial com o Anexo nº 2 da Lei nº 8.421/1992.
- Acrescentar dados físicos astronômicos e referências por estrela com curadoria, e eventualmente uma API/catalogador como SIMBAD/VizieR.


## Revisão geométrica

Os centros das 27 estrelas foram organizados em coordenadas de SVG 2000×1400 com consulta ao estudo de construção vetorial de [Daniel Madeira](https://github.com/danmadeira/bandeira-nacional), realizado com base nas medidas legais. A implementação do HTML desenha as formas por comandos SVG próprios e calcula os pentagramas por funções trigonométricas. As correspondências astronômicas são conferidas com materiais do INPE e do Observatório Nacional.

O arquivo `estrelas.json` contém `cx`, `cy` e `grandeza`, além de estado, estrela e constelação. `x` e `y` guardam a posição percentual correspondente na bandeira.
