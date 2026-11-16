# Horizonte Científico / Lua — v2.0

Laboratório científico interativo em Python + Streamlit, do projeto **Matemática & Contexto**.
Autora: **Joice Souza Martins Santos**.

## O que faz

- Consulta **azimute, elevação e distância ao centro do Sol e da Terra** de um ponto lunar pela API NASA/JPL Horizons.
- Exibe gráficos das distâncias e elevações em UTC e a separação angular Sol–Terra.
- Calcula tempo de propagação aproximado Terra–observador lunar (distância / velocidade da luz).
- Apresenta um diagrama polar das direções do céu local.
- Calcula **irradiância e energia solar teóricas** com fluxo solar variável pela lei do inverso do quadrado da distância. Simula painéis horizontais, inclinados ou com rastreamento ideal.
- Permite escolher sítios Apollo 11, 15 e 17 com coordenadas publicadas pela NASA.
- Indica o acesso externo ao mapa real **NASA Moon Trek** e exporta os dados do JPL junto às colunas calculadas em CSV.

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

**Efemérides NASA/JPL:** `OBSERVER`, observador `coord@301` (ponto topocêntrico na Lua), alvos 10=Sol e 399=Terra, `QUANTITIES=4,20` para azimute, elevação e distância aparente, `RANGE_UNITS=KM`, `SUPPRESS_RANGE_RATE=YES`, `TIME_TYPE=UT`, `CSV_FORMAT=YES`. Latitude geodética entre -90 e 90, longitude leste entre -180 e +180. Altitude do sítio fixada em **0 km** sobre o elipsoide lunar de referência.

**Visibilidade:** somente o centro do corpo acima de 0° em um horizonte geométrico plano. **Não** modela sombras de cristas, crateras, obstáculos, ângulo da antena ou comunicação de rádio. Um Sol geometricamente acima do horizonte pode estar bloqueado pelo terreno.

**Modelo energético:** irradiância teórica \(S(r)=1361\times(1\,UA/r)^2\) W/m², com a distância `r` do Sol fornecida pelo JPL (não uma medição radiométrica na Lua). A potência combina irradiância, área, eficiência e fator de incidência. Perdas por temperatura, poeira, baterias, reguladores e degradação não são modeladas. Rastreamento ideal mantém o painel alinhado ao Sol e é limite superior idealizado, não sugestão de hardware real.

**Distância e comunicação:** a distância aparente Terra–observador lunar vem da quantidade 20 do JPL. O tempo de propagação aproximado de um sinal em um sentido é \(t = d/c\). Não são avaliadas perdas de enlace, antenas, obstruções ou processamento de telecomunicação.

**Sítios Apollo:** coordenadas NASA/NSSDC são planetocêntricas e usadas como aproximação de latitude geodética; essa limitação deve ser considerada em análises de precisão.

**Integração de energia:** método dos trapézios com dados a cada 1, 3, 6 ou 12 horas, sem interpolação dos períodos de transição pelo horizonte. Precisão limitada pela resolução temporal e pelas hipóteses de cálculo.

**Próxima fase:** mapas reais de elevação LRO/LOLA e perfil do horizonte por azimute, para calcular sombras e iluminações do relevo, além de efeitos de perda energética.

## Links de documentação

- JPL Horizons API: https://ssd-api.jpl.nasa.gov/doc/horizons.html
- JPL Horizons manual: https://ssd.jpl.nasa.gov/horizons/manual.html
- Dados da missão LOLA/LRO: https://pds-geosciences.wustl.edu/missions/lro/lola.htm
- NASA Moon Trek: https://trek.nasa.gov/moon/
- Locais históricos Apollo (NASA/NSSDC): https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_sites.html
- Streamlit Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud

## Testes locais (opcional)

```bash
python -m pip install pytest
python -m pytest -q
```

Não foram inventados dados JPL para preencher eventuais falhas de rede. Se a API estiver indisponível, o aplicativo apresenta o erro e não gera gráficos fictícios.
