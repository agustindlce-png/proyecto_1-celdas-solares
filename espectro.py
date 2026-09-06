"""
espectro.py
===========
Carga el espectro solar de referencia AM1.5G (ASTM G173-03) y calcula, en
tiempo real (integración numérica, nunca datos precalculados a mano):

  - la irradiancia espectral P(lambda)                [W m^-2 nm^-1]
  - el flujo de fotones N_ph(lambda)                   [fotones s^-1 m^-2 nm^-1]
  - integrales sobre un umbral de energía E > Eg        (fotocorriente máxima)

Fuente de los datos: ASTM G173-03 "Standard Tables for Reference Solar
Spectral Irradiances", derivados de SMARTS v2.9.2 (mismo archivo que
astmg173.xls provisto en Webcursos). Descargados de una copia pública y
citable del dataset oficial de NREL/ASTM, usada ampliamente en la literatura
de eficiencia de celdas solares (ver Shockley-Queisser-limit, marcus-cmc,
GitHub; también reproducido en rredc.nrel.gov/solar/spectra/am1.5/astmg173).
Rango cubierto: 280 nm - 4000 nm (cubre completamente los 300-1200 nm
mínimos exigidos y bastante más).
"""

import numpy as np
import pandas as pd
import os

from constantes import H_PLANCK, C_LUZ, Q

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "ASTMG173.csv")

FUENTE_ESPECTRO = (
    "ASTM G173-03 Reference Spectra Derived from SMARTS v2.9.2 "
    "(NREL Renewable Resource Data Center, rredc.nrel.gov/solar/spectra/am1.5/astmg173). "
    "Rango de datos: 280-4000 nm."
)


def _trapz(y, x):
    """Integración trapezoidal, compatible con versiones nuevas y viejas de numpy."""
    if hasattr(np, "trapezoid"):
        return np.trapezoid(y, x)
    return np.trapz(y, x)


class EspectroAM15G:
    """Encapsula el espectro AM1.5G y las magnitudes derivadas de él."""

    def __init__(self):
        df = pd.read_csv(_DATA_PATH, skiprows=1)
        df.columns = [c.strip() for c in df.columns]
        self.wl_nm = df["Wvlgth nm"].to_numpy(dtype=float)
        self.P_Wm2nm = df["Global tilt  W*m-2*nm-1"].to_numpy(dtype=float)

        # Energía de fotón por longitud de onda: E = h*c/lambda  [J] -> [eV]
        E_J = H_PLANCK * C_LUZ / (self.wl_nm * 1e-9)
        self.E_eV = E_J / Q

        # Flujo de fotones N_ph(lambda) = P(lambda) / E_foton(lambda)
        # [W m^-2 nm^-1] / [J]  =  [fotones s^-1 m^-2 nm^-1]
        self.Nph_lambda = self.P_Wm2nm / E_J

    # -- Magnitudes integradas ------------------------------------------------

    def irradiancia_total_Wm2(self, wl_min=None, wl_max=None):
        """Integral de P(lambda) dlambda -> potencia total incidente [W/m^2]."""
        wl, P = self._recortar(self.wl_nm, self.P_Wm2nm, wl_min, wl_max)
        return _trapz(P, wl)

    def lambda_gap_nm(self, Eg_eV):
        """Longitud de onda de corte correspondiente a un gap Eg [eV] -> [nm]."""
        return H_PLANCK * C_LUZ / (Eg_eV * Q) * 1e9

    def Nph_sobre_gap_m2s(self, Eg_eV, wl_min=None, wl_max=None):
        """
        Integral de N_ph(lambda) dlambda para fotones con E > Eg
        (equivalente a lambda < lambda_gap).  Devuelve [fotones s^-1 m^-2].
        """
        lam_g = self.lambda_gap_nm(Eg_eV)
        wl, Nph = self._recortar(self.wl_nm, self.Nph_lambda, wl_min, wl_max)
        mask = wl <= lam_g
        if mask.sum() < 2:
            return 0.0
        return _trapz(Nph[mask], wl[mask])

    def potencia_sobre_gap_Wm2(self, Eg_eV):
        """Integral de P(lambda) dlambda para fotones con E > Eg (lambda < lambda_gap)."""
        lam_g = self.lambda_gap_nm(Eg_eV)
        mask = self.wl_nm <= lam_g
        if mask.sum() < 2:
            return 0.0
        return _trapz(self.P_Wm2nm[mask], self.wl_nm[mask])

    def potencia_bajo_gap_Wm2(self, Eg_eV):
        """Integral de P(lambda) dlambda para fotones con E < Eg (lambda > lambda_gap), no absorbidos."""
        lam_g = self.lambda_gap_nm(Eg_eV)
        mask = self.wl_nm > lam_g
        if mask.sum() < 2:
            return 0.0
        return _trapz(self.P_Wm2nm[mask], self.wl_nm[mask])

    def Jsc_max_mA_cm2(self, Eg_eV, wl_min=None, wl_max=None):
        """
        Densidad de corriente de cortocircuito máxima (fotón -> par e-h con
        eficiencia cuántica unitaria), integrando el espectro real.
        J_sc,max = q * N_ph(E>Eg)   [A/m^2] -> [mA/cm^2]
        """
        Nph_m2 = self.Nph_sobre_gap_m2s(Eg_eV, wl_min, wl_max)
        J_A_m2 = Q * Nph_m2
        return J_A_m2 * 1e-4 * 1e3  # A/m^2 -> A/cm^2 -> mA/cm^2

    @staticmethod
    def _recortar(wl, y, wl_min, wl_max):
        if wl_min is None and wl_max is None:
            return wl, y
        mask = np.ones_like(wl, dtype=bool)
        if wl_min is not None:
            mask &= wl >= wl_min
        if wl_max is not None:
            mask &= wl <= wl_max
        return wl[mask], y[mask]


_espectro_singleton = None


def get_espectro():
    """Devuelve una única instancia cacheada del espectro (carga perezosa)."""
    global _espectro_singleton
    if _espectro_singleton is None:
        _espectro_singleton = EspectroAM15G()
    return _espectro_singleton
