"""
ecuaciones.py
=============
Compendio de las ecuaciones fundamentales usadas por el modelo físico de la
aplicación (Problema 2.3 - "El límite de eficiencia: del espectro solar a su
exploración usando silicio semiconductor"), organizadas por pestaña.

Este módulo NO calcula nada: sólo centraliza, en formato LaTeX + texto
explicativo, las mismas ecuaciones que `semiconductor.py` y `espectro.py`
implementan numéricamente. Sirve para:
  - mostrarlas en la pestaña "Ecuaciones" de la interfaz (ver app.py), y
  - tenerlas a mano, ya redactadas, para citar durante la presentación oral.

Cada entrada es un diccionario con:
  - "nombre"        : título corto de la ecuación
  - "latex"         : cadena LaTeX (sin los símbolos $ ni $$; se pasa
                       directamente a st.latex)
  - "descripcion"   : explicación breve en texto, con las unidades de cada
                       símbolo y de dónde sale (Unidad y diapositiva del curso)
  - "donde_se_usa"  : en qué archivo/función del código se implementa,
                       para poder mostrar en pantalla la trazabilidad
                       ecuación -> código durante la defensa
"""

ECUACIONES_PESTANA_1 = [
    {
        "nombre": "Energía de un fotón",
        "latex": r"E_{foton}(\lambda) = \frac{hc}{\lambda}",
        "descripcion": (
            "h = 6.626×10⁻³⁴ J·s (Planck), c = 3×10⁸ m/s, λ en metros. "
            "El resultado en Joules se convierte a eV dividiendo por "
            "q = 1.602×10⁻¹⁹ C. Se usa la forma explícita hc/λ (no la "
            "aproximación λ/1.24 eV·nm) para evitar el redondeo de esa "
            "constante, aunque el resultado difiere en menos de 0.1%."
        ),
        "donde_se_usa": "espectro.py, propiedad E_eV",
    },
    {
        "nombre": "Flujo de fotones espectral",
        "latex": r"N_{ph}(\lambda) = \frac{P(\lambda)}{E_{foton}(\lambda)}",
        "descripcion": (
            "P(λ) es la irradiancia espectral AM1.5G en W·m⁻²·nm⁻¹, cargada "
            "desde el archivo astmg173.xls (ASTM G173-03). N_ph(λ) resulta "
            "en fotones·s⁻¹·m⁻²·nm⁻¹."
        ),
        "donde_se_usa": "espectro.py, propiedad Nph_lambda",
    },
    {
        "nombre": "Fotones aprovechables sobre el gap",
        "latex": (
            r"N_{ph}(E>E_g) = \int_{0}^{\lambda_g} N_{ph}(\lambda)\, d\lambda,"
            r"\qquad \lambda_g = \frac{hc}{E_g}"
        ),
        "descripcion": (
            "Sólo los fotones con energía mayor a Eg (equivalente a longitud "
            "de onda menor a λ_g) tienen energía suficiente para generar un "
            "par electrón-hueco en un material de banda prohibida Eg."
        ),
        "donde_se_usa": "espectro.py, método Nph_sobre_gap_m2s",
    },
    {
        "nombre": "Corriente de cortocircuito máxima",
        "latex": r"J_{SC,\,m\acute{a}x} = q \cdot N_{ph}(E>E_g)",
        "descripcion": (
            "Límite superior teórico de Jsc para un Eg dado: supone que "
            "TODOS los fotones absorbidos con E>Eg generan exactamente un "
            "par colectado (eficiencia cuántica externa EQE = 100%)."
        ),
        "donde_se_usa": "espectro.py, método Jsc_max_mA_cm2",
    },
]

ECUACIONES_PESTANA_2 = [
    {
        "nombre": "Concentración intrínseca n_i(T)",
        "latex": (
            r"n_i(T) = n_{i,300K}\left(\frac{T}{300}\right)^{3/2}"
            r"\exp\!\left[-\frac{E_g(T)}{2k_BT} + \frac{E_g(300)}{2k_B\cdot 300}\right]"
        ),
        "descripcion": (
            "Forma funcional derivada de n_i² = N_c·N_v·exp(-Eg/k_BT) con "
            "N_c, N_v ~ T^(3/2) (aproximación de Boltzmann, Unidad 2), "
            "calibrada para reproducir n_i(300K) = 1×10¹⁰ cm⁻³ exactamente "
            "(Anexo B). En la Pestaña 2 (cascada de pérdidas), Eg es el "
            "valor EXPLORADO en el slider de la Pestaña 1 -- no "
            "necesariamente el Eg real del silicio -- de modo que n_i cae "
            "exponencialmente al subir Eg y V_OC sube en consecuencia."
        ),
        "donde_se_usa": "semiconductor.py, función ni_T_cm3",
    },
    {
        "nombre": "V_OC límite por recombinación de Auger",
        "latex": (
            r"V_{OC} = \frac{2k_BT}{3q}\,"
            r"\ln\!\left[\frac{1}{n_i^{3}}\cdot\frac{J_L}{q}\cdot\frac{1}{W}"
            r"\cdot\frac{1}{c_n+c_p}\right]"
        ),
        "descripcion": (
            "Supone recombinación de Auger como único mecanismo (material "
            "de pureza perfecta, sin SRH ni recombinación superficial), "
            "condición de circuito abierto (niveles cuasi-Fermi planos) y "
            "dopaje simétrico n≈p≈Δp. c_n+c_p = 4×10⁻³¹ cm⁶/s (Unidad 4)."
        ),
        "donde_se_usa": "semiconductor.py, función Voc_limite_auger_V",
    },
    {
        "nombre": "Factor de forma ideal (diodo puro)",
        "latex": (
            r"FF_0 = \frac{v_{OC} - \ln(v_{OC}+0.72)}{v_{OC}+1},"
            r"\qquad v_{OC} = \frac{V_{OC}}{n\,k_BT/q}"
        ),
        "descripcion": (
            "Expresión empírica de Green (1981), válida para v_OC > 10. "
            "n es el factor de idealidad del diodo (n=1 en el caso ideal)."
        ),
        "donde_se_usa": "semiconductor.py, función FF0_ideal",
    },
    {
        "nombre": "Factor de forma real (con R_s, R_p)",
        "latex": (
            r"FF = FF_0\,(1-r_s)\left[1-\frac{v_{OC}+0.7}{v_{OC}}"
            r"\cdot\frac{FF_0(1-r_s)}{r_p}\right],"
            r"\qquad r_s=\frac{R_s}{V_{OC}/J_{SC}},\ \ r_p=\frac{R_p}{V_{OC}/J_{SC}}"
        ),
        "descripcion": (
            "Secuencia de pasos de la Unidad 4 (diapositivas 33-35) para "
            "incorporar resistencia serie R_s y resistencia paralelo R_p "
            "al factor de forma ideal FF_0."
        ),
        "donde_se_usa": "semiconductor.py, función FF_con_parasiticos",
    },
    {
        "nombre": "Eficiencia de conversión",
        "latex": r"\eta = \frac{V_{OC}\cdot J_{SC}\cdot FF}{P_{in}}",
        "descripcion": (
            "P_in = 100 mW/cm² (irradiancia de 1 sol, AM1.5G, condición "
            "estándar STC). η es el producto de los tres parámetros de la "
            "celda dividido por la potencia incidente."
        ),
        "donde_se_usa": "app.py, dentro de calcular_cascada() y en la Pestaña 3",
    },
]

ECUACIONES_PESTANA_3 = [
    {
        "nombre": "Banda prohibida en función de la temperatura",
        "latex": r"E_g(T) = 1.206 - 0.000273\cdot T \qquad [\text{eV, } T \text{ en K}]",
        "descripcion": (
            "Relación empírica del silicio (Unidad 4, diapositiva 38). "
            "A 300 K entrega Eg ≈ 1.124 eV, ligeramente distinto del valor "
            "canónico de 1.12 eV usado como punto de referencia puntual en "
            "el Anexo B."
        ),
        "donde_se_usa": "semiconductor.py, función Eg_T_eV",
    },
    {
        "nombre": "Coeficiente de temperatura de V_OC (analítico)",
        "latex": r"\frac{dV_{OC}}{dT} = -\frac{V_{g0}-V_{OC}+\gamma\,k_BT/q}{T}",
        "descripcion": (
            "Derivado suponiendo dJ_SC/dT ≈ 0, a partir de "
            r"$J_{SC}=A\,T^{\gamma}\exp[(qV_{OC}-E_{g0})/k_BT]=\text{cte}$ "
            "(Unidad 4, diapositivas 39-41). Para silicio: V_g0 = 1.2 V, "
            "γ = 3."
        ),
        "donde_se_usa": "semiconductor.py, función dVoc_dT_analitico_V_K",
    },
]

# Diccionario maestro: clave = título de sección mostrado en la pestaña,
# valor = lista de ecuaciones de esa sección (mismo formato de arriba).
TODAS_LAS_ECUACIONES = {
    "Pestaña 1 — Espectro solar como flujo de fotones": ECUACIONES_PESTANA_1,
    "Pestaña 2 — Cascada de pérdidas (V_OC, FF, η)": ECUACIONES_PESTANA_2,
    "Pestaña 3 — Efecto de la temperatura": ECUACIONES_PESTANA_3,
}
