# Controlador de Elasticidade Preditivo para Containers Docker

## Gerar dataset sintético
Pode ser feito com o seguinte [script](gerar_dataset.py).

## Testar estacionariedade
Pode-se testar o [dataset](dataset.csv) usando o script [ADF](teste-stationary.py). 

## Plotar os gráficos ACF e PACF
Pode ser feito com o script [plot.py](plot.py).

## Escolha dos parâmetros
Para escolher os parâmetros *p*, *d* e *q*, além de analisar os gráficos de ACF e PACF, é possível usar o script [auto_arima](auto-arima.py).

## ARIMA
Após escolha dos parâmetros, o ARIMA foi desenvolvido com o *split* de 80% treino e 20% teste.

## Resultados
[Gráfico de CPU com predição do ARIMA](CPU.png)

[Gráfico de RAM com predição do ARIMA](RAM.png)

## Próximas etapas
- Desenvolver um gerador de carga para memória RAM;
- Testar o ARIMA com diferentes padrões de carga (exponencial, ondas, aleatório, etc).