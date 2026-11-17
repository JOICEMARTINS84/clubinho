# O Céu na Bandeira do Brasil

**Aplicativo independente** de astronomia educativa para o Streamlit Community Cloud.
Autoria: **Joice Souza Martins Santos**, projeto Matemática & Contexto.

## O que contém
- Atlas interativo da bandeira do Brasil com 27 estrelas, 26 estados e o Distrito Federal;
- Nove constelações, nomes e designações astronômicas;
- Busca por estado/estrela, filtro por constelação e seleção por clique;
- Texto histórico e referências institucionais;
- Ficha de cada estrela com navegação anterior/próxima, carta celeste com as demais estrelas da constelação clicáveis, magnitude aparente de catálogo e busca sem distinção de acentos;
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
- `index.html` — página final, autossuficiente (**gerada** por `build.py`; é o que o Streamlit exibe)
- `src/template.html`, `src/style.css`, `src/app.js` — o código-fonte da página, em peças separadas
- `estrelas.json` — catálogo auditável das 27 estrelas
- `cartas_celestes.json` — cartas das 9 constelações (dados do D3-Celestial)
- `build.py` — junta `src/` e os JSON em `index.html`
- `validar_estrelas.py` — conferência do catálogo, das cartas e do `index.html`
- `requirements.txt` — dependências deste app
- `.streamlit/config.toml` — tema deste app

## Como editar

Mexa sempre nos arquivos de `src/` ou nos JSON, **nunca direto no `index.html`**. Depois:

```bash
python bandeira-astronomica/build.py              # regenera o index.html
python bandeira-astronomica/validar_estrelas.py   # confere dados e HTML
```

Faça o commit do `index.html` junto com as alterações: é ele que o Streamlit Cloud lê.

## Fontes

- Lei nº 5.700/1971 — https://www2.camara.leg.br/legin/fed/lei/1970-1979/lei-5700-1-setembro-1971-357915-normaatualizada-pl.html
- D3-Celestial — catálogo estelar e cartas celestes (https://github.com/ofrohn/d3-celestial)
- Agência Espacial Brasileira — constelações e bandeira brasileira

## Etapas futuras

- Conferir visualmente a reconstituição vetorial com o Anexo nº 2 da Lei nº 8.421/1992.
- Acrescentar dados físicos astronômicos e referências por estrela com curadoria, e eventualmente uma API/catalogador como SIMBAD/VizieR.


## Revisão geométrica

Os centros das 27 estrelas foram organizados em coordenadas de SVG 2000×1400 com consulta ao estudo de construção vetorial de [Daniel Madeira](https://github.com/danmadeira/bandeira-nacional), realizado com base nas medidas legais. A implementação do HTML desenha as formas por comandos SVG próprios e calcula os pentagramas por funções trigonométricas. As correspondências astronômicas são conferidas com materiais do INPE e do Observatório Nacional.

O arquivo `estrelas.json` contém `cx`, `cy` e `grandeza`, além de estado, estrela e constelação. `x` e `y` guardam a posição percentual correspondente na bandeira.

## Melhorias desta revisão

- A ficha agora distingue **grandeza gráfica da bandeira** de **magnitude aparente de catálogo**, com explicação educativa.
- A altura do atlas dentro do iframe do Streamlit é ajustada por mensagem própria do Streamlit e por `ResizeObserver`, com fallback seguro.
- A busca usa normalização explícita de diacríticos e comparação compatível com português do Brasil.
- Checagens automatizadas verificam a disponibilidade das magnitudes das 27 estrelas.

## Identidade editorial (2026)

A versão **Atlas Editorial Científico** usa uma navegação por seções, prancha gráfica numerada,
registro estelar, carta celeste e bibliografia com notas de proveniência.
A apresentação foi simplificada para lembrar um catálogo de divulgação científica,
sem efeitos luminosos decorativos. Os pontos de dados e as associações das estrelas não foram alterados.
A bandeira abre inteira no celular; o botão **Ampliar disco** auxilia a seleção dos pontos.

O projeto permanece em desenvolvimento e a representação não deve ser tratada como uma
efeméride, observação em tempo real ou imagem oficial da bandeira.


## Interface — mesa de consulta (novembro de 2026)

A navegação principal deixou o formato de página promocional e passou a usar três
áreas contínuas: índice alfabético por UF, bandeira em prancha central e registro
astronômico com carta celeste. No celular, a ordem é bandeira, registro e índice;
o seletor por estado fica acima da prancha para acesso rápido.

A versão usa somente fontes nativas do sistema (sem dependências de fontes da web),
não adiciona dados estelares e mantém as fontes do catálogo. O índice acompanha
a seleção, a busca e os filtros. A consulta no Streamlit usa o mesmo `index.html`
proveniente de `build.py`.

## Revisão de legibilidade e apresentação

A interface usa duas famílias tipográficas e uma paleta neutra com azul-escuro.
Os totais são calculados a partir do catálogo. O marcador numérico da estrela
na bandeira remete à legenda externa. A distância, ausente dos dados, aparece
como travessão. Os arquivos `estrelas.json` e `cartas_celestes.json` permanecem
inalterados.

O CSS da página reside em `src/style.css`; os estilos do contêiner do Streamlit
são injetados em `streamlit_app.py`, pois o iframe tem um documento isolado.
