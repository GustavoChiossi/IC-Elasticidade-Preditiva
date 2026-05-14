# implementacao do aarima

from statsmodels.tsa.arima.model import ARIMA
from scipy.stats import boxcox
import pmdarima as pm
import numpy as np
import warnings
warnings.filterwarnings("ignore")

PREVISAO_PONTOS = 5
ordem = None

def atualizar_parametros(historico):
    global ordem
    serie = np.array(historico)

    modelo = pm.auto_arima(
        serie,
        start_p=0,
        start_q=0,
        max_p=15,
        max_q=15,
        max_d=3,
        d=None,
        seasonal=False,
        stepwise=False,
        trace=False,
        test="kpss",
        information_criterion="aic",
        error_action="ignore",
        suppress_warnings=True,
        with_intercept="auto"
    )
    ordem = modelo.order
    print(f"Ordem escolhida: {ordem}")

def transformar_boxcox(valor, lmbda):
    if lmbda == 0:
        return np.log(valor)
    return (valor ** lmbda - 1) / lmbda

def prever(historico):
    global ordem
    P, D, Q = ordem
    
    historico = list(historico)
    historicoBox, lambdaBox = boxcox(np.array(historico) + 1)
    modelo = ARIMA(historicoBox,order=ordem)
    modeloFit = modelo.fit(method_kwargs={"maxiter":10000})
    previsao = modeloFit.forecast(steps=1)[0]

    if D == 0:
        if len(historico) >= 2:
            y_t = historico[-1]
            y_t1 = historico[-2]
            ajuste = 0.5 * (y_t - y_t1)
        else:
            ajuste = 0
    else:
        if len(historico) >= 3:
            y_t = historico[-1]
            y_t1 = historico[-2]
            y_t2 = historico[-3]
            ajuste = 0.5 * (y_t - 2*y_t1 + y_t2)
        else:
            ajuste = 0

    previsaoCorrigida = (previsao + ajuste)
    
    return previsaoCorrigida