"""
semiconductor.py
=================
Modelo físico del límite de eficiencia de una celda de silicio, implementado
íntegramente a partir de las ecuaciones de la Unidad 4 (ver PDF de la clase
"Límite de eficiencia de celdas fotovoltaicas"), sin invocar ningún solver de
dispositivo completo (no se usa solcore, según prohibición del enunciado).

Todas las funciones reciben y devuelven cantidades ya explícitas en unidades
físicas (V, mA/cm^2, K, etc.) y ninguna constante numérica está "suelta": se
importan desde constantes.py.
"""

import numpy as np

from constantes import (
    Q, KB_EV, EG_T_A, EG_T_B, CN_PLUS_CP_AUGER, NI_300K_REF,
    GAMMA_VOC_T, VG0_SI_V, P_AM1_5_W_M2,
)


# ---------------------------------------------------------------------------
# Banda prohibida y concentración intrínseca en función de la temperatura
# ---------------------------------------------------------------------------

def Eg_T_eV(T_K):
    """Eg(T) = 1.206 - 0.000273*T [eV], T en kelvin (Unidad 4, diapositiva 38)."""
    return EG_T_A - EG_T_B * T_K


def ni_T_cm3(T_K, ni_300K=NI_300K_REF):
    """
    Concentración intrínseca n_i(T), calibrada para reproducir exactamente
    n_i(300K) = ni_300K (valor de referencia del curso, Anexo B) y con la
    dependencia funcional correcta n_i^2 ~ T^3 * exp(-Eg(T)/kT) que se deduce
    de n_i^2 = Nc*Nv*exp(-Eg/kT) con Nc,Nv ~ T^{3/2} (aproximación de
    Boltzmann, Unidad 2).

    Aproximación explícita: se fija la amplitud con el valor de referencia a
    300 K y sólo se propaga la forma funcional del escalamiento con T; esto
    evita tener que fijar a mano las masas efectivas con precisión de %, que
    no cambian la física cualitativa pedida en este problema (ver discusión
    en la pestaña de Validación).
    """
    T_K = np.asarray(T_K, dtype=float)
    Eg = Eg_T_eV(T_K)
    Eg_300 = Eg_T_eV(300.0)
    factor_T = (T_K / 300.0) ** 1.5
    factor_exp = np.exp(-(Eg / (2 * KB_EV * T_K)) + (Eg_300 / (2 * KB_EV * 300.0)))
    return ni_300K * factor_T * factor_exp


# ---------------------------------------------------------------------------
# Límite de V_OC por recombinación de Auger (Unidad 4, diapositivas 21-23)
# ---------------------------------------------------------------------------

def Voc_limite_auger_V(JL_mA_cm2, T_K, W_cm, ni_cm3, cn_cp=CN_PLUS_CP_AUGER):
    """
    V_OC = (2kT / 3q) * ln[ (1/ni^3) * (JL/q) * (1/W) * (1/(cn+cp)) ]

    Derivado en clase (Unidad 4) asumiendo:
      - recombinación de Auger como único mecanismo (material de pureza
        perfecta, sin defectos SRH ni recombinación superficial),
      - condición de circuito abierto (niveles cuasi-Fermi planos),
      - dopaje tal que n = p ~ Delta_p (caso simétrico, el más favorable).
    """
    JL_A_cm2 = np.asarray(JL_mA_cm2, dtype=float) / 1000.0
    ni_cm3 = np.asarray(ni_cm3, dtype=float)
    arg = (1.0 / ni_cm3 ** 3) * (JL_A_cm2 / Q) * (1.0 / W_cm) * (1.0 / cn_cp)
    return (2.0 * KB_EV * T_K / 3.0) * np.log(arg)


# ---------------------------------------------------------------------------
# Factor de llenado (Unidad 4, diapositivas 25 y 33-35)
# ---------------------------------------------------------------------------

def FF0_ideal(Voc_V, T_K, n_idealidad=1.0):
    """FF0 = [v_oc - ln(v_oc+0.72)] / (v_oc+1),  v_oc = Voc / (n*kT/q). Válido para v_oc>10."""
    v_oc = Voc_V / (n_idealidad * KB_EV * T_K)
    return (v_oc - np.log(v_oc + 0.72)) / (v_oc + 1.0)


def FF_con_parasiticos(Voc_V, Jsc_mA_cm2, T_K, Rs_ohm_cm2, Rp_ohm_cm2, n_idealidad=1.0):
    """
    Factor de llenado real incluyendo resistencia serie Rs, resistencia
    paralelo Rp y factor de idealidad n, siguiendo la secuencia de 6 pasos
    de la Unidad 4 (diapositivas 33-35):

      R_CH = Voc / Jsc
      r_s = Rs / R_CH ,  r_p = Rp / R_CH
      FF_n  = FF0 evaluado con v_oc = Voc/(n*kT/q)
      FF_nS = FF_n * (1 - r_s)
      FF    = FF_nS * (1 - (v_oc+0.7)/v_oc * FF_nS / r_p)
    """
    R_CH = Voc_V / (Jsc_mA_cm2 / 1000.0)  # V*cm^2/A = Ohm*cm^2
    r_s = Rs_ohm_cm2 / R_CH
    r_p = Rp_ohm_cm2 / R_CH
    v_oc = Voc_V / (n_idealidad * KB_EV * T_K)
    FF_n = FF0_ideal(Voc_V, T_K, n_idealidad)
    FF_nS = FF_n * (1.0 - r_s)
    FF = FF_nS * (1.0 - (v_oc + 0.7) / v_oc * FF_nS / r_p)
    return FF, r_s, r_p


# ---------------------------------------------------------------------------
# Coeficiente de temperatura de V_OC (Unidad 4, diapositivas 39-42)
# ---------------------------------------------------------------------------

def dVoc_dT_analitico_V_K(Voc_V, T_K, gamma=GAMMA_VOC_T, Vg0_V=VG0_SI_V):
    """
    dVoc/dT = - (Vg0 - Voc + gamma*kT/q) / T   [V/K]

    Derivado suponiendo dJsc/dT ~ 0 (Unidad 4, diapositiva 41) a partir de
    Jsc = A*T^gamma*exp[(q*Voc - Eg0)/kT].
    """
    return -(Vg0_V - Voc_V + gamma * KB_EV * T_K) / T_K
