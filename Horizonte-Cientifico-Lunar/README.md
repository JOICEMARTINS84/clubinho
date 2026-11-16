# Horizonte Científico / Lua — v1.0

Laboratório científico interativo em Python + Streamlit, do projeto **Matemática & Contexto**.
Autora: **Joice Souza Martins Santos**.

## O que faz

- Consulta **posições reais do Sol e da Terra vistas de um ponto lunar** usando a API NASA/JPL Horizons.
- Exibe gráficos das elevações sobre o horizonte geométrico (em UTC).
- Mostra um diagrama polar do céu local.
- Calcula **energia solar teórica**, comparando painéis horizontais, inclinados ou com rastreamento ideal.
- Exporta os resultados para CSV.

## Executar no computador com Python (recomendado: Python 3.11 ou 3.12)

No **Windows**, você também pode abrir `INICIAR_WINDOWS.bat` com dois cliques (é necessário ter Python instalado).

Como alternativa, abra o terminal dentro da pasta do projeto:

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Se o Windows usar o comando `py` em vez de `python`:

```powershell
py -m pip install -r requirements.txt
py -m streamlit run streamlit_app.py
```

O terminal mostra um endereço local (em geral `http://localhost:8501`). Abra-o no navegador.
Selecione local, período, orientação do painel e pressione **Consultar NASA / JPL**.
É necessário acesso à internet para consultar as efemérides.

## Publicar gratuitamente (Streamlit Community Cloud)

1. O código-fonte está no repositório `JOICEMARTINS84/clubinho`, na pasta `Horizonte-Cientifico-Lunar/`.
2. Entre em https://share.streamlit.io e conecte o GitHub.
3. Selecione repositório `JOICEMARTINS84/clubinho`, branch `main` e arquivo principal `Horizonte-Cientifico-Lunar/streamlit_app.py`.
4. Compartilhe o link público no WordPress, ou teste a incorporação conforme as permissões do tema/plano.

## Metodologia e limites

**Efemérides NASA/JPL:** `OBSERVER`, observador `coord@301` (ponto topocêntrico na Lua), alvos 10=Sol e 399=Terra, `QUANTITIES=4` para azimute e elevação, `TIME_TYPE=UT`, `CSV_FORMAT=YES`. Latitude geodética entre -90 e 90, longitude leste entre -180 e +180. Altitude do sítio fixada em **0 km** sobre o elipsoide lunar de referência.

**Visibilidade:** somente o centro do corpo acima de 0° em um horizonte geométrico plano. **Não** modela sombras de cristas, crateras, obstáculos, ângulo da antena ou comunicação de rádio. Um Sol geometricamente acima do horizonte pode estar bloqueado pelo terreno.

**Modelo energético:** potência teórica = 1361 W/m² × área × eficiência × fator de incidência solar, aplicada apenas com elevação solar positiva. Irradiância fixa convencional, não medida no ponto; perdas reais (temperatura, poeira, baterias, reguladores, degradação) não modeladas. O modo rastreamento ideal mantém a normal do painel alinhada à direção solar enquanto a elevação for positiva; é um limite superior, não uma sugestão de hardware real.

**Integração de energia:** método dos trapézios com dados a cada 3, 6 ou 12 horas, sem interpolação dos períodos de transição pelo horizonte. Precisão limitada pela resolução temporal e pelas hipóteses de cálculo.

**Próxima fase:** mapas reais de elevação LRO/LOLA e perfil do horizonte por azimute, para calcular sombras e iluminações do relevo, além de efeitos de perda energética.

## Links de documentação

- JPL Horizons API: https://ssd-api.jpl.nasa.gov/doc/horizons.html
- JPL Horizons manual: https://ssd.jpl.nasa.gov/horizons/manual.html
- Dados da missão LOLA/LRO: https://pds-geosciences.wustl.edu/missions/lro/lola.htm
- Streamlit Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud

## Testes locais (opcional)

```bash
python -m pip install pytest
python -m pytest -q
```

Não foram inventados dados JPL para preencher eventuais falhas de rede. Se a API estiver indisponível, o aplicativo apresenta o erro e não gera gráficos fictícios.
