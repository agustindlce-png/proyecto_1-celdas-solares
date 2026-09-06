"""
constantes.py
=============
Único módulo donde se declaran constantes físicas y parámetros de material.
Cada constante indica su unidad y su fuente en un comentario, tal como exige
la Sección 1.4 del enunciado del Proyecto 1 ("no se aceptan números
arbitrarios dispersos en el código").
"""

# ---------------------------------------------------------------------------
# Constantes físicas universales (CODATA 2018)
# ---------------------------------------------------------------------------
Q = 1.602176634e-19          # Carga elemental [C]                 (CODATA 2018)
H_PLANCK = 6.62607015e-34    # Constante de Planck [J*s]           (CODATA 2018)
C_LUZ = 2.99792458e8         # Velocidad de la luz en el vacío [m/s] (CODATA 2018, exacta)
KB_J = 1.380649e-23          # Constante de Boltzmann [J/K]        (CODATA 2018, exacta)
KB_EV = 8.617333262e-5       # Constante de Boltzmann [eV/K]       (CODATA 2018, = KB_J/Q)
M0_ELECTRON = 9.1093837015e-31  # Masa en reposo del electrón [kg] (CODATA 2018)

# ---------------------------------------------------------------------------
# Parámetros del silicio cristalino, usados en la Unidad 4 del curso
# ---------------------------------------------------------------------------
EG_SI_300K = 1.12             # Banda prohibida del silicio a 300 K [eV]
                               # (Valor canónico del curso, Anexo B / Unidad 4)

# Dependencia de Eg con la temperatura (ajuste lineal usado explícitamente
# en la Unidad 4, diapositiva 38, válido en el rango 15-75 °C del problema):
EG_T_A = 1.206                 # Término constante [eV]  (Unidad 4, diap. 38)
EG_T_B = 0.000273               # Pendiente [eV/K]        (Unidad 4, diap. 38)
# Eg(T) = EG_T_A - EG_T_B * T,  con T en kelvin

CN_PLUS_CP_AUGER = 4e-31       # Suma de coeficientes de recombinación Auger
                               # (electrones + huecos) del silicio [cm^6/s]
                               # (Unidad 4, usado en la derivación de V_OC límite
                               #  y en el Problema 2.1 del enunciado)

B_RADIATIVO_SI = 4.73e-15      # Coeficiente de recombinación radiativa del
                               # silicio [cm^3/s]   (Unidad 4)

NI_300K_REF = 1.0e10           # Concentración intrínseca de referencia del
                               # silicio a 300 K [cm^-3]  (Anexo B / Unidad 2 y 4)

W_CELL_REF_UM = 100.0          # Espesor canónico de la celda para el límite
                               # de 29.3% de la Unidad 4 [µm]  (Unidad 4)

# Densidades efectivas de estados de silicio a 300 K (usadas para construir
# n_i(T) de forma físicamente consistente, ver semiconductor.py). Se derivan
# de las masas efectivas de densidad de estados reportadas para silicio
# (Green, M.A. (1990), "Intrinsic concentration, effective densities of
# states, and effective mass in silicon", J. Appl. Phys. 67, 2944), que dan
# Nc(300K) ~ 2.8e19 cm^-3 y Nv(300K) ~ 1.04e19 cm^-3. Se usan aquí sólo como
# valores de referencia a 300 K para calibrar la ley de escala T^3 * exp(-Eg/kT).
NC_300K_SI = 2.8e19            # Densidad efectiva de estados, banda de conducción [cm^-3]
NV_300K_SI = 1.04e19           # Densidad efectiva de estados, banda de valencia [cm^-3]

# ---------------------------------------------------------------------------
# Condiciones de referencia estándar de ensayo (STC) para celdas solares
# ---------------------------------------------------------------------------
P_AM1_5_W_M2 = 1000.0          # Irradiancia total del espectro AM1.5G global
                               # bajo condiciones STC [W/m^2]
                               # (= 100 mW/cm^2, Unidad 3 y ASTM G173-03)
T_STC_K = 298.15                # Temperatura de referencia STC, 25 °C [K]

# ---------------------------------------------------------------------------
# Parámetros del modelo de V_OC(T) de la Unidad 4 (diapositivas 39-42)
# ---------------------------------------------------------------------------
GAMMA_VOC_T = 3                 # Exponente adimensional de T en I0 ~ A*T^gamma*exp(-Eg0/kT)
                               # (Unidad 4, diapositiva 40; valor típico usado en el curso)
VG0_SI_V = 1.2                  # Banda prohibida extrapolada a T->0, en volts [V]
                               # (Unidad 4, diapositiva 42, para silicio)

# ---------------------------------------------------------------------------
# Semilla y parámetros asignados por RUT (Anexo A, Tabla A.1)
# ---------------------------------------------------------------------------
# S = (suma de los últimos 3 dígitos de los RUT de los integrantes, sin
#      dígito verificador) mod 10  =  (025 + 219 + 319) mod 10 = 3
SEMILLA_S = 3
# Fila S=3 de la Tabla A.1. Para el Problema 2.3, la nota del Anexo A indica
# que este problema *sólo* usa la temperatura de operación como punto de
# partida del barrido térmico de la Pestaña 3; no usa NA, ND, tau_SRH,
# S_frontal ni el espesor W de esta tabla (W se fija en 100 µm, caso
# canónico de la Unidad 4 que reproducen las verificaciones V3 y V4).
T_OPERACION_SEMILLA_C = 25.0     # [°C]  (Tabla A.1, fila S=3)

# ---------------------------------------------------------------------------
# Datasheet de módulo comercial real, usado en la Pestaña 3 para comparar
# coeficientes de temperatura simulados vs. medidos (Sección 2.3.b, Pestaña 3)
# ---------------------------------------------------------------------------
# Fuente: JinkoSolar, ficha técnica módulo 66QL6-BDV (650-670 W, bifacial),
# mostrada en Unidad 4, diapositiva 45 del curso.
MODULO_REF_NOMBRE = "JinkoSolar 66QL6-BDV (650-670 W)"
MODULO_REF_TEMP_COEF_VOC_PCT_C = -0.24   # [%/°C]
MODULO_REF_TEMP_COEF_ISC_PCT_C = 0.046   # [%/°C]
MODULO_REF_TEMP_COEF_PMAX_PCT_C = -0.26  # [%/°C]
