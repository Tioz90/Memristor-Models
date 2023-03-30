import numpy as np
from scipy.stats import truncnorm


def mimd(v, g_p, b_p, g_n, b_n):
    return np.where(v >= 0, g_p * np.sinh(b_p * v), g_n * np.sinh(b_n * v))


def mim_iv(v, g, b):
    return g * np.sinh(b * v)


def h1(v, g_p, b_p, g_n, b_n):
    return np.where(v >= 0, g_p * np.sinh(b_p * v), g_n * (1 - np.exp(-b_n * v)))


def h2(v, g_p, b_p, g_n, b_n):
    return np.where(v >= 0, g_p * (1 - np.exp(-b_p * v)), g_n * np.sinh(b_n * v))


def h2_2(v, g_p, b_p, g_n, b_n):
    return np.where(v >= 0, g_p * np.sinh(b_p * v), g_n * (1 - np.exp(-b_n * v)))


def h2_3(v, g_p, b_p, g_n, b_n):
    return np.where(v >= 0, g_p * np.sinh(b_p * v), g_n * (((b_n + 1) * v) / (b_n * v + 1)))


# def current(v, x, gmax_p, bmax_p, gmax_n, bmax_n, gmin_p, bmin_p, gmin_n, bmin_n):  # First implementation
#    return mimd(v, gmax_p, bmax_p, gmax_n, bmax_n) * x + mimd(v, gmin_p, bmin_p, gmin_n, bmin_n) * (1 - x)


# Implemented with Dima (2022)
def current(v, x, gmax_p, bmax_p, gmax_n, bmax_n, gmin_p, bmin_p, gmin_n, bmin_n):
    # -- during simulation: if x is close to 0, set it to 0 to avoid numerical issues with high levels of noise
    if hasattr(x, 'flags') and x.flags['WRITEABLE']:
        x[np.isclose(x, 0, atol=1e-200)] = 0
    return h1(v, gmax_p, bmax_p, gmax_n, bmax_n) * x + h2(v, gmin_p, bmin_p, gmin_n, bmin_n) * (1 - x)


def g(v, Ap, An, Vp, Vn):
    return np.select([v > Vp, v < Vn], [Ap * (np.exp(v) - np.exp(Vp)), -An * (np.exp(-v) - np.exp(Vn))], default=0)


def wp(x, xp):
    return (xp - x) / (1 - xp) + 1


def wn(x, xn):
    return x / xn


def f(v, x, xp, xn, alphap, alphan, eta):
    return np.select([eta * v >= 0, eta * v < 0],
                     [np.select([x >= xp, x < xp],
                                [np.exp(-alphap * (x - xp)) * wp(x, xp),
                                 1]),
                      np.select([x <= xn, x > xn],
                                [np.exp(alphan * (x - xn)) * wn(x, xn),
                                 1])
                      ])


def dxdt(v, x, Ap, An, Vp, Vn, xp, xn, alphap, alphan, eta):
    return eta * g(v, Ap, An, Vp, Vn) * f(v, x, xp, xn, alphap, alphan, eta)


def get_truncated_normal(mean, sd, low, upp, out_size, in_size):
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            res = truncnorm((low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd) \
                .rvs(out_size * in_size) \
                .reshape((out_size, in_size))
        except (ZeroDivisionError, ValueError):
            res = np.full((out_size, in_size), mean)

        if out_size == 1 and in_size == 1:
            res = res[0, 0]

        return res
