__author__ = 'vlad'
import warnings
import math

from statsmodels.tsa.arima_model import ARIMA
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brute


def choose_arima_order(endog):
    def objfunc(order, *params):
        series = params

        try:
            mod = ARIMA(series, order, exog=None)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = mod.fit(disp=0, solver='bfgs', maxiter=5000)
        except:
            return float('inf')
        if math.isnan(res.aic):
            return float('inf')
        return res.aic

    grid = (slice(1, 5, 1), slice(0, 3, 1), slice(0, 5, 1))

    t = brute(objfunc, grid, args=endog, finish=None).astype(int)

    return ARIMA(endog, t, exog=None).fit()


def forecast(x, steps):
    mod = choose_arima_order(x[:-steps])

    t = mod.forecast(steps)[0]

    axis = np.arange(1, x.shape[0] + 1)
    forecast_res = np.zeros(x.shape[0])
    for k in xrange(x.shape[0] - steps):
        forecast_res[k] = x[k]
    for k in xrange(x.shape[0] - steps, x.shape[0]):
        forecast_res[k] = t[k - x.shape[0] + steps]
    return forecast_res
