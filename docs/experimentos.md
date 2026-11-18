# Guia de experimentos

Os scripts avulsos originais não têm extensão. Baixe cada arquivo e salve com o nome sugerido abaixo para executá-lo. Use um ambiente Python separado dos laboratórios.

| Arquivo original | Nome local sugerido | Dependências |
| --- | --- | --- |
| Calculadora tk | calculadora.py | customtkinter |
| Segunda lei de Kepler | kepler.py | numpy, matplotlib |
| forca Astronomia | forca.py | tkinter (biblioteca padrão) |
| pedra-papel-tesoura-opencv | jogo.py | opencv-python, numpy |
| sistema solar | sistema_solar.py | turtle (biblioteca padrão) |

No Windows, instale somente as dependências necessárias com `py -m pip install nome-do-pacote` e execute, por exemplo, `py kepler.py`.

## Propostas de investigação

- **Kepler:** compare as áreas varridas em intervalos iguais e investigue como a excentricidade altera a velocidade orbital.
- **Sistema Solar:** compare os períodos visuais; distâncias, tamanhos, velocidades e satélites são representações didáticas, não medidas físicas.
- **Forca:** explique cada conceito após descobrir a palavra e consulte fontes astronômicas.
- **Visão computacional:** altere a iluminação e investigue como a segmentação por cor muda os resultados; o script usa câmera local, com configuração voltada ao Windows.
- **Calculadora:** teste operações válidas e entradas incorretas.

Os códigos são experimentos educacionais e não possuem garantia de compatibilidade com todos os sistemas ou versões do Python.
