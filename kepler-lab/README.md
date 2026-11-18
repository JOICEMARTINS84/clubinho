# Kepler Lab

Laboratório interativo de órbitas elípticas. Ajuste o semieixo maior, a excentricidade e os intervalos de tempo; compare áreas e velocidades.

## Executar

```bash
python -m pip install -r kepler-lab/requirements.txt
python -m streamlit run kepler-lab/app.py
```

O modelo utiliza a equação de Kepler, resolvida iterativamente, e a equação vis-viva para uma órbita ideal em torno do Sol. Não representa efemérides reais.

Para publicar separadamente no Streamlit, selecione `kepler-lab/app.py` como arquivo principal.
