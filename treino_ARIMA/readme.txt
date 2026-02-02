Os códigos usam o arquivo CSV que está em gerador_ram/dataset-gerador.csv

auto-arima.py ajuda a escolher os melhores parâmetros (p,d,q). arima.py é o ARIMA em si.

1. Executar primeiro o auto-arima.py
2. Usar os parâmetros dados na ultima linha de arima.py
3. Executar arima.py

NOTA: nem sempre o auto-arima vai acertar os parâmetros. Nesse caso, os parâmetros escolhidos por ele foram (4,1,0). Após alguns testes, observei que o melhores parâmetros são (4,0,0).