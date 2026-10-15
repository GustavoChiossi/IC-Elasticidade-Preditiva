from statsmodels.tsa.arima.model import ARIMA
from scipy.special import inv_boxcox
from scipy.stats import boxcox
import pmdarima as pm
import numpy as np

def aplicar_boxcox(serie):
    offset = 0
    if np.min(serie) <= 0:
        offset = abs(np.min(serie)) + 1
        serie = serie + offset

    if np.ptp(serie) < 1e-6:  
        return serie.astype(float), None, offset

    serie_box, lambda_box = boxcox(serie)
    return serie_box, lambda_box, offset

def transformar_boxcox(valor, lambda_box):
    if lambda_box is None:
        return valor
    if lambda_box == 0:
        return np.log(valor)
    return (valor ** lambda_box - 1) / lambda_box


def escolher_aarima(serie_box):
    modelo = pm.auto_arima(
        serie_box,
        start_p=0,
        start_q=0,
        max_p=5,
        max_q=5,
        max_d=2,
        seasonal=False,
        stepwise=True,
        trace=False,
        error_action="ignore",
        suppress_warnings=True,
    )
    return modelo.order

class AARIMA:
    def __init__(self, min_amostras: int = 120, piso_previsao: float = 0.0,
                 teto_previsao: float | None = None):
        self.min_amostras = min_amostras
        self.piso_previsao = piso_previsao
        self.teto_previsao = teto_previsao

        self.lambda_box = None
        self.offset = None
        self.ordem = None
        self.inicializado = False

    def inicializar(self, historico):
        historico = np.array(historico, dtype=float)
        serie_box, lambda_box, offset = aplicar_boxcox(historico)
        ordem = escolher_aarima(serie_box)

        self.lambda_box = lambda_box
        self.offset = offset
        self.ordem = ordem
        self.inicializado = True

        return ordem

    def prever_proximo_passo(self, historico, janela_deslizante: int | None = None):
        if len(historico) < self.min_amostras:
            return None

        historico = np.array(historico, dtype=float)

        if not self.inicializado:
            self.inicializar(historico)

        if janela_deslizante is not None and len(historico) > janela_deslizante:
            hist_fit = historico[-janela_deslizante:]
        else:
            hist_fit = historico

        hist_box = [transformar_boxcox(v + self.offset, self.lambda_box) for v in hist_fit]

        modelo = ARIMA(hist_box, order=self.ordem)
        modelo_fit = modelo.fit(method_kwargs={"maxiter": 1000})

        previsao_box = modelo_fit.forecast(steps=1)[0]
        p, d, q = self.ordem
        ajuste = 0

        if d == 0:
            if len(hist_box) >= 2:
                ajuste = 0.5 * (hist_box[-1] - hist_box[-2])
        else:
            if len(hist_box) >= 3:
                ajuste = 0.5 * (hist_box[-1] - 2 * hist_box[-2] + hist_box[-3])

        previsao_corrigida = previsao_box + ajuste

        if self.lambda_box is None:
            previsao_final = previsao_corrigida - self.offset
        else:
            previsao_final = inv_boxcox(previsao_corrigida, self.lambda_box) - self.offset

        previsao_final = max(self.piso_previsao, float(previsao_final))
        if self.teto_previsao is not None:
            previsao_final = min(previsao_final, self.teto_previsao)

        return previsao_final