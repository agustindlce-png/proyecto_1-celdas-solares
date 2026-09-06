"""
app.py
======
Proyecto 1 - Simulación Interactiva de Procesos Físicos en Semiconductores y
Celdas Fotovoltaicas. Problema 2.3: "El límite de eficiencia: del espectro
solar a su exploración usando silicio semiconductor".

Arquitectura:
  - constantes.py     -> todas las constantes físicas y parámetros de la semilla
  - espectro.py        -> carga y procesamiento del espectro AM1.5G real (ASTM G173)
  - semiconductor.py   -> modelo físico (Eg(T), ni(T), Voc límite, FF, dVoc/dT)
  - ecuaciones.py       -> compendio en LaTeX de las ecuaciones fundamentales,
                            usado sólo por la pestaña "Ecuaciones" (no calcula nada)
  - app.py (este archivo) -> interfaz Streamlit con 5 pestañas y estado
                              compartido vía st.session_state

CAMBIOS respecto de la versión original
------------------------------------------
1) FIX FÍSICO: dentro de calcular_cascada() (Pestaña 2), el cálculo de
   `ni_ref` y `ni_op` ahora pasa explícitamente Eg_eV=Eg (el Eg explorado en
   el slider de la Pestaña 1, compartido vía st.session_state) a
   ni_T_cm3(). Antes, esas llamadas usaban siempre el Eg real del silicio a
   esa temperatura, sin importar el Eg del slider -- así, al mover Eg en la
   cascada, V_OC casi no cambiaba, cuando físicamente V_OC ~ ln(1/ni^3) y
   ni ~ exp(-Eg/2kT) implica que subir Eg debe subir V_OC fuertemente. Las
   llamadas a ni_T_cm3() en la Pestaña 3 y en la pestaña de Validación NO
   pasan Eg_eV, por lo que siguen usando el Eg(T) real del silicio y ningún
   valor de referencia (V1-V6) se ve alterado.

2) NUEVA PESTAÑA "📐 Ecuaciones": muestra, agrupadas por pestaña de
   contenido, todas las ecuaciones fundamentales del modelo (en LaTeX, con
   descripción física y referencia al archivo/función donde se implementan),
   importadas desde ecuaciones.py. No agrega ningún cálculo nuevo; es sólo
   documentación visible dentro de la propia app, útil para la presentación.
"""

import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from constantes import (
    EG_SI_300K, KB_EV, P_AM1_5_W_M2, CN_PLUS_CP_AUGER, NI_300K_REF,
    W_CELL_REF_UM, SEMILLA_S, T_OPERACION_SEMILLA_C, GAMMA_VOC_T, VG0_SI_V,
    MODULO_REF_NOMBRE, MODULO_REF_TEMP_COEF_VOC_PCT_C,
    MODULO_REF_TEMP_COEF_ISC_PCT_C, MODULO_REF_TEMP_COEF_PMAX_PCT_C,
)
from espectro import get_espectro, FUENTE_ESPECTRO
from semiconductor import (
    Eg_T_eV, ni_T_cm3, Voc_limite_auger_V, FF0_ideal, FF_con_parasiticos,
    dVoc_dT_analitico_V_K,
)
from ecuaciones import TODAS_LAS_ECUACIONES

st.set_page_config(
    page_title="Límite de eficiencia — celda de silicio",
    layout="wide",
)

espectro = get_espectro()

# ============================================================================
# Estado compartido entre pestañas (st.session_state)
# ============================================================================
defaults = {
    "Eg_eV": EG_SI_300K,
    "W_cm": W_CELL_REF_UM * 1e-4,           # 100 µm -> cm, fijo para 2.3
    "activar_subgap": True,
    "activar_termalizacion": True,
    "activar_qvoc": True,
    "activar_ff0": True,
    "activar_rsrp": True,
    "Rs_ohmcm2": 0.5,
    "Rp_ohmcm2": 800.0,
    "activar_recomb": True,
    "factor_coleccion": 0.95,
    "activar_optico": True,
    "factor_optico": 0.95,
    "activar_temperatura": True,
    "T_operacion_C": T_OPERACION_SEMILLA_C,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================================
# Barra lateral: semilla y parámetros asignados (siempre visibles)
# ============================================================================
with st.sidebar:
    st.title("🔆 Parámetros del grupo")
    st.markdown(f"**Semilla S = {SEMILLA_S}**")
    st.markdown(
        f"- T de operación asignada (Tabla A.1, fila S={SEMILLA_S}): "
        f"**{T_OPERACION_SEMILLA_C:.0f} °C**"
    )
    st.caption(
        "El Problema 2.3 sólo usa la T de operación de la Tabla A.1. "
        "El espesor está fijo en **W = 100 µm** (caso canónico de la Unidad 4 "
        "que reproducen las verificaciones V3/V4 de la pestaña de Validación); "
        "por eso no se usa el W de la tabla."
    )
    st.divider()
    st.header("Estado compartido")
    st.markdown(
        f"- Banda prohibida explorada, **Eg = {st.session_state.Eg_eV:.2f} eV** "
        "(pestaña 1, se usa también en la cascada de la pestaña 2)"
    )
    st.markdown(
        f"- T de operación actual (cascada / temperatura): "
        f"**{st.session_state.T_operacion_C:.0f} °C**"
    )
    st.divider()
    st.caption("Fuente del espectro solar:")
    st.caption(FUENTE_ESPECTRO)


# ============================================================================
# Pestañas
# ============================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Espectro solar como flujo de fotones",
    "2. Cascada de pérdidas interactiva",
    "3. Efecto de la temperatura",
    "Validación",
    "📐 Ecuaciones",
])

# ============================================================================
# PESTAÑA 1 — El espectro solar como flujo de fotones
# ============================================================================
with tab1:
    st.header("El espectro solar como flujo de fotones")
    st.markdown(
        "Espectro de referencia **AM1.5G** (ASTM G173-03, mismos datos que "
        "`astmg173.xls`), convertido a flujo de fotones "
        r"$N_{ph}(\lambda) = P(\lambda)/E_{foton}(\lambda)$, con "
        r"$E_{foton}=hc/\lambda$ calculado explícitamente (no la aproximación "
        r"$\lambda/1.24$, aunque es equivalente dentro de <0.1%)."
    )

    col_ctrl, col_plot = st.columns([1, 2])

    with col_ctrl:
        Eg = st.slider(
            "Banda prohibida explorada, Eg [eV]",
            min_value=0.5, max_value=3.0,
            step=0.01, key="Eg_eV",
            help="Este valor se comparte con la Pestaña 2 (cascada de pérdidas).",
        )
        rango = st.select_slider(
            "Rango espectral mostrado [nm]",
            options=[300, 500, 800, 1200, 1800, 2500, 4000],
            value=2500,
        )

        Nph_total = espectro.Nph_sobre_gap_m2s(Eg) / 1e4  # cm^-2 s^-1
        Jsc_max = espectro.Jsc_max_mA_cm2(Eg)
        P_total = espectro.irradiancia_total_Wm2()
        P_sobre = espectro.potencia_sobre_gap_Wm2(Eg)
        P_bajo = espectro.potencia_bajo_gap_Wm2(Eg)
        E_gap_usada = Nph_total * 1e4 * Eg * 1.602176634e-19  # W/m2 (energía útil al gap)

        st.metric("Fotones con E > Eg", f"{Nph_total:.3e} cm⁻² s⁻¹")
        st.metric("J_sc,máx = q·N_ph", f"{Jsc_max:.2f} mA/cm²")

        frac_subgap = P_bajo / P_total * 100
        frac_termal = (P_sobre - E_gap_usada) / P_total * 100
        frac_util = E_gap_usada / P_total * 100

        st.markdown("**Pérdidas de energía (respecto de los 1000 W/m² incidentes):**")
        st.markdown(f"- Fotones sub-bandgap (no absorbidos): **{frac_subgap:.1f}%**")
        st.markdown(f"- Termalización (exceso de energía sobre Eg): **{frac_termal:.1f}%**")
        st.markdown(f"- Fracción de energía útil (Nph · Eg): **{frac_util:.1f}%**")

    with col_plot:
        mask = espectro.wl_nm <= rango
        wl = espectro.wl_nm[mask]
        P = espectro.P_Wm2nm[mask]
        lam_g = espectro.lambda_gap_nm(Eg)

        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.plot(wl, P, color="black", lw=1.2, label="Irradiancia espectral AM1.5G")

        mask_abs = wl <= lam_g
        mask_noabs = wl > lam_g

        # Área de termalización: energía por sobre la usada al gap, para fotones absorbidos.
        # Se aproxima gráficamente escalando P por (1 - Eg/E_foton) en la zona absorbida,
        # que es exactamente la fracción de energía de cada fotón perdida como calor.
        E_foton = espectro.E_eV[mask]
        frac_calor = np.clip(1 - Eg / np.where(E_foton > 0, E_foton, np.inf), 0, 1)
        ax.fill_between(
            wl[mask_abs], 0, (P * frac_calor)[mask_abs],
            color="tab:red", alpha=0.4, label="Termalización (calor)",
        )
        ax.fill_between(
            wl[mask_noabs], 0, P[mask_noabs],
            color="tab:blue", alpha=0.4, label="Sub-bandgap (no absorbido)",
        )
        ax.axvline(lam_g, color="green", ls="--", lw=1.5,
                   label=fr"$\lambda_g$={lam_g:.0f} nm (Eg={Eg:.2f} eV)")
        ax.set_xlabel("Longitud de onda λ [nm]")
        ax.set_ylabel(r"Irradiancia espectral P(λ) [W m$^{-2}$ nm$^{-1}$]")
        ax.set_title("Espectro AM1.5G y pérdidas asociadas al gap Eg")
        ax.legend(fontsize=8, loc="upper right")
        ax.set_xlim(wl.min(), wl.max())
        st.pyplot(fig, width="stretch")

        fig2, ax2 = plt.subplots(figsize=(7, 3.2))
        ax2.plot(wl, espectro.Nph_lambda[mask] / 1e4, color="darkorange", lw=1.2)
        ax2.axvline(lam_g, color="green", ls="--", lw=1.2)
        ax2.set_xlabel("Longitud de onda λ [nm]")
        ax2.set_ylabel(r"$N_{ph}(\lambda)$ [fotones s$^{-1}$ cm$^{-2}$ nm$^{-1}$]")
        ax2.set_title("Flujo de fotones espectral")
        st.pyplot(fig2, width="stretch")

    st.info(
        "💡 Al mover Eg: sube ⇒ $\\lambda_g$ baja ⇒ menos fotones aprovechables "
        "⇒ $J_{sc,max}$ baja, pero (como se ve en la Pestaña 2) $V_{OC}$ sube. "
        "Ese es el compromiso fundamental de la eficiencia de conversión."
    )

# ============================================================================
# PESTAÑA 2 — Cascada de pérdidas interactiva
# ============================================================================
with tab2:
    st.header("Cascada de pérdidas interactiva")
    st.markdown(
        "Cascada tipo *waterfall* que parte del 100% de la potencia incidente "
        "AM1.5 (1000 W/m²) y termina en la eficiencia final, con un peldaño por "
        "cada uno de los ocho mecanismos de la Unidad 4 (diapositiva 14). "
        "**Cada peldaño se puede activar/desactivar y su magnitud se recalcula "
        "en tiempo real desde el modelo físico**, nunca desde una constante fija."
    )

    Eg = st.session_state.Eg_eV
    W_cm = st.session_state.W_cm

    colA, colB = st.columns([1, 1])

    with colA:
        st.subheader("Mecanismos intrínsecos (Eg fijo, silicio ideal)")
        st.caption(
            "Estos 4 primeros son inevitables para un material con este Eg; "
            "desactivarlos es sólo ilustrativo (equivale a suponer que ese "
            "mecanismo en particular no existiera)."
        )
        st.session_state.activar_subgap = st.checkbox(
            "1. Fotones sub-bandgap no absorbidos", value=st.session_state.activar_subgap)
        st.session_state.activar_termalizacion = st.checkbox(
            "2. Termalización del exceso de energía", value=st.session_state.activar_termalizacion)
        st.session_state.activar_qvoc = st.checkbox(
            "3. Pérdida de energía de cargas al cruzar la juntura (qVoc<Eg)",
            value=st.session_state.activar_qvoc)
        st.session_state.activar_ff0 = st.checkbox(
            "4. Factor de forma ideal del diodo (FF0<1)", value=st.session_state.activar_ff0)

        st.subheader("Mecanismos evitables (defectos/diseño)")
        st.session_state.activar_rsrp = st.checkbox(
            "5. Efectos parasíticos Rs, Rp", value=st.session_state.activar_rsrp)
        if st.session_state.activar_rsrp:
            st.session_state.Rs_ohmcm2 = st.slider(
                "Rs [Ω·cm²]", 0.0, 5.0, float(st.session_state.Rs_ohmcm2), 0.05)
            st.session_state.Rp_ohmcm2 = st.slider(
                "Rp [Ω·cm²]", 10.0, 3000.0, float(st.session_state.Rp_ohmcm2), 10.0)

        st.session_state.activar_recomb = st.checkbox(
            "6. Recombinación en volumen/superficie/contactos",
            value=st.session_state.activar_recomb)
        if st.session_state.activar_recomb:
            st.session_state.factor_coleccion = st.slider(
                "Factor de colección (fracción de portadores colectados)",
                0.70, 1.0, float(st.session_state.factor_coleccion), 0.01)

        st.session_state.activar_optico = st.checkbox(
            "7. Pérdidas ópticas (reflexión, sombreado, absorción incompleta)",
            value=st.session_state.activar_optico)
        if st.session_state.activar_optico:
            st.session_state.factor_optico = st.slider(
                "Factor óptico (fracción de fotones útiles que ingresan)",
                0.70, 1.0, float(st.session_state.factor_optico), 0.01)

        st.session_state.activar_temperatura = st.checkbox(
            "8. Pérdidas por temperatura de operación", value=st.session_state.activar_temperatura)
        if st.session_state.activar_temperatura:
            st.session_state.T_operacion_C = st.slider(
                "T de operación [°C]", 15.0, 75.0, float(st.session_state.T_operacion_C), 1.0,
                help="Compartido con la Pestaña 3.")

    # ---- Cálculo de la cascada, 100% real-time --------------------------------
    def calcular_cascada():
        T_ref_K = 298.15  # 25 C, STC
        Jsc_max = espectro.Jsc_max_mA_cm2(Eg)
        P_total = espectro.irradiancia_total_Wm2()
        P_sobre = espectro.potencia_sobre_gap_Wm2(Eg)
        P_bajo = espectro.potencia_bajo_gap_Wm2(Eg)
        Nph_m2 = espectro.Nph_sobre_gap_m2s(Eg)
        E_util_Wm2 = Nph_m2 * Eg * 1.602176634e-19

        ratio1 = (P_total - P_bajo) / P_total if st.session_state.activar_subgap else 1.0
        ratio2 = (E_util_Wm2 / P_sobre) if st.session_state.activar_termalizacion else 1.0

        # ni_ref se calcula con el Eg EXPLORADO en el slider (Eg_eV=Eg), no con
        # el Eg real del silicio a T_ref_K. Así, V_OC refleja correctamente que
        # ni ~ exp(-Eg/2kT): al subir Eg, ni cae exponencialmente y V_OC sube
        # fuerte, en vez de quedarse casi plano como ocurría antes del fix.
        ni_ref = ni_T_cm3(T_ref_K, Eg_eV=Eg)
        Voc = Voc_limite_auger_V(Jsc_max, T_ref_K, W_cm, ni_ref)
        ratio3 = (Voc / Eg) if st.session_state.activar_qvoc else 1.0

        FF0 = FF0_ideal(Voc, T_ref_K)
        ratio4 = FF0 if st.session_state.activar_ff0 else 1.0

        if st.session_state.activar_rsrp:
            FF_real, rs, rp = FF_con_parasiticos(
                Voc, Jsc_max, T_ref_K,
                st.session_state.Rs_ohmcm2, st.session_state.Rp_ohmcm2)
            ratio5 = FF_real / FF0
        else:
            ratio5 = 1.0

        ratio6 = st.session_state.factor_coleccion if st.session_state.activar_recomb else 1.0
        ratio7 = st.session_state.factor_optico if st.session_state.activar_optico else 1.0

        if st.session_state.activar_temperatura:
            T_op_K = st.session_state.T_operacion_C + 273.15
            # Mismo criterio: el barrido de temperatura de este peldaño (8)
            # sigue usando el Eg EXPLORADO, para ser consistente con Voc de
            # más arriba en esta misma cascada (ambos deben describir el
            # mismo material hipotético de banda Eg, sólo que a T distinta).
            ni_op = ni_T_cm3(T_op_K, Eg_eV=Eg)
            Voc_op = Voc_limite_auger_V(Jsc_max, T_op_K, W_cm, ni_op)
            FF0_op = FF0_ideal(Voc_op, T_op_K)
            eta_25 = Voc * Jsc_max * FF0          # proporcional a eta (mW/cm2), basta con la razon
            eta_op = Voc_op * Jsc_max * FF0_op
            ratio8 = eta_op / eta_25
        else:
            ratio8 = 1.0

        ratios = [ratio1, ratio2, ratio3, ratio4, ratio5, ratio6, ratio7, ratio8]
        etiquetas = [
            "100% incidente (AM1.5)",
            "1. Fotones sub-bandgap",
            "2. Termalización",
            "3. qVoc < Eg",
            "4. FF0 diodo ideal",
            "5. Parasíticos Rs,Rp",
            "6. Recombinación",
            "7. Pérdidas ópticas",
            "8. Temperatura",
        ]
        niveles = [100.0]
        for r in ratios:
            niveles.append(niveles[-1] * r)
        return etiquetas, niveles, Voc, Jsc_max, FF0

    etiquetas, niveles, Voc_calc, Jsc_calc, FF0_calc = calcular_cascada()

    with colB:
        st.subheader("Resultado de la cascada")
        st.metric("Eficiencia final η", f"{niveles[-1]:.1f} %")
        c1, c2, c3 = st.columns(3)
        c1.metric("V_OC (Auger, 25°C)", f"{Voc_calc*1000:.0f} mV")
        c2.metric("J_sc,máx", f"{Jsc_calc:.1f} mA/cm²")
        c3.metric("FF0 ideal", f"{FF0_calc:.3f}")

        fig, ax = plt.subplots(figsize=(6.5, 5))
        colores = plt.cm.viridis(np.linspace(0.15, 0.9, len(niveles)))
        ax.bar(range(len(niveles)), niveles, color=colores)
        for i, v in enumerate(niveles):
            ax.text(i, v + 1, f"{v:.1f}%", ha="center", fontsize=8)
        ax.set_xticks(range(len(etiquetas)))
        ax.set_xticklabels(etiquetas, rotation=60, ha="right", fontsize=8)
        ax.set_ylabel("Fracción de la potencia incidente [%]")
        ax.set_ylim(0, 105)
        ax.set_title("Cascada de pérdidas (waterfall)")
        st.pyplot(fig, width="stretch")

        residuo = 100 - (sum(np.diff(niveles) * -1) + niveles[-1])
        st.caption(
            f"Cierre de la cascada: suma de pérdidas + eficiencia final = "
            f"{100 - residuo:.3f}% (residuo numérico = {residuo:.2e} pp)"
        )

    st.divider()
    st.subheader("🎬 Animación temporal: construcción de la cascada")
    st.caption(
        "Reconstruye la cascada peldaño a peldaño en el tiempo (no es un gráfico "
        "estático): cada barra aparece secuencialmente, mostrando cómo cada "
        "mecanismo consume una fracción de la potencia incidente."
    )
    if st.button("▶ Reproducir animación"):
        placeholder = st.empty()
        for n in range(1, len(niveles) + 1):
            fig_a, ax_a = plt.subplots(figsize=(7, 4))
            colores_a = plt.cm.viridis(np.linspace(0.15, 0.9, n))
            ax_a.bar(range(n), niveles[:n], color=colores_a)
            for i in range(n):
                ax_a.text(i, niveles[i] + 1, f"{niveles[i]:.1f}%", ha="center", fontsize=8)
            ax_a.set_xticks(range(len(etiquetas)))
            ax_a.set_xticklabels(etiquetas, rotation=60, ha="right", fontsize=8)
            ax_a.set_xlim(-0.5, len(etiquetas) - 0.5)
            ax_a.set_ylim(0, 105)
            ax_a.set_ylabel("Fracción de la potencia incidente [%]")
            ax_a.set_title(f"Construyendo la cascada... paso {n}/{len(niveles)}")
            placeholder.pyplot(fig_a)
            plt.close(fig_a)
            time.sleep(0.5)
        st.success("Cascada completa.")

    st.info(
        "Si desactivas los mecanismos 5, 6, 7 y 8 (todos los que la Unidad 4 "
        "declara evitables), la cascada debe converger al límite de **29.3%** "
        "para W = 100 µm. Pruébalo con los checkboxes de la izquierda."
    )

# ============================================================================
# PESTAÑA 3 — Efecto de la temperatura
# ============================================================================
with tab3:
    st.header("Efecto de la temperatura")
    st.markdown(
        "Se implementa $E_g(T) = 1.206 - 0.000273\\cdot T$ (T en kelvin) y se "
        "recalculan $J_{sc}$, $V_{OC}$, $FF$ y $\\eta$ entre 15 y 75 °C, "
        "usando el mismo modelo de límite de Auger de la Pestaña 2 (W=100 µm)."
    )

    Eg_300 = EG_SI_300K
    W_cm = st.session_state.W_cm

    T_C = np.linspace(15, 75, 61)
    T_K = T_C + 273.15

    # NOTA: aquí ni_T_cm3 se llama SIN Eg_eV (comportamiento por defecto),
    # es decir, con el Eg(T) REAL del silicio en cada punto del barrido -- que
    # es lo físicamente correcto para "el mismo dispositivo de silicio real
    # calentándose", a diferencia de la cascada de la Pestaña 2, que explora
    # un Eg hipotético fijo. Esto reproduce exactamente los valores de
    # referencia de la pestaña de Validación (V3, V4, V6), que tampoco pasan
    # Eg_eV.
    Eg_T_arr = Eg_T_eV(T_K)
    Jsc_T = np.array([espectro.Jsc_max_mA_cm2(eg) for eg in Eg_T_arr])
    ni_T_arr = ni_T_cm3(T_K)
    Voc_T = Voc_limite_auger_V(Jsc_T, T_K, W_cm, ni_T_arr)
    FF_T = FF0_ideal(Voc_T, T_K)
    eta_T = Voc_T * Jsc_T * FF_T / (P_AM1_5_W_M2 / 10) * 100  # % (Pin=100 mW/cm2)

    col1, col2 = st.columns(2)
    with col1:
        fig, axs = plt.subplots(2, 2, figsize=(7, 6))
        axs[0, 0].plot(T_C, Jsc_T, color="tab:blue")
        axs[0, 0].set_xlabel("T [°C]"); axs[0, 0].set_ylabel(r"$J_{sc}$ [mA/cm²]")
        axs[0, 1].plot(T_C, Voc_T * 1000, color="tab:red")
        axs[0, 1].set_xlabel("T [°C]"); axs[0, 1].set_ylabel(r"$V_{OC}$ [mV]")
        axs[1, 0].plot(T_C, FF_T, color="tab:green")
        axs[1, 0].set_xlabel("T [°C]"); axs[1, 0].set_ylabel("FF [-]")
        axs[1, 1].plot(T_C, eta_T, color="tab:purple")
        axs[1, 1].set_xlabel("T [°C]"); axs[1, 1].set_ylabel(r"$\eta$ [%]")
        fig.suptitle("Barrido térmico, 15-75 °C (W = 100 µm)")
        fig.tight_layout()
        st.pyplot(fig, width="stretch")

    with col2:
        st.subheader("Coeficiente dV_OC/dT")
        dVoc_dT_num = np.gradient(Voc_T, T_K)  # V/K
        idx_ref = np.argmin(np.abs(T_C - 25))
        dVoc_dT_num_ref = dVoc_dT_num[idx_ref]
        dVoc_dT_an_ref = dVoc_dT_analitico_V_K(Voc_T[idx_ref], T_K[idx_ref])

        c1, c2 = st.columns(2)
        c1.metric("dVoc/dT numérico (a 25°C, este dispositivo)", f"{dVoc_dT_num_ref*1000:.3f} mV/°C")
        c2.metric("dVoc/dT analítico (mismo punto)", f"{dVoc_dT_an_ref*1000:.3f} mV/°C")
        st.caption(
            "Ambos usan Vg0=1.2V, γ=3 (Unidad 4). El valor absoluto difiere del "
            "clásico −2.3 mV/°C de la lámina 42 porque allí se asume Voc≈0.6V "
            "(celda comercial típica), mientras que aquí Voc≈0.79V corresponde "
            "al límite ideal de Auger (sin defectos) de este mismo problema. "
            "La verificación V6 de la pestaña de Validación reproduce el caso "
            "de la lámina 42 exactamente, como control independiente del modelo."
        )

        st.subheader("Observación: mayor V_OC ⇒ menor |dV_OC/dT|")
        Voc_barrido = np.linspace(0.45, 0.85, 60)
        dVoc_dT_barrido = dVoc_dT_analitico_V_K(Voc_barrido, 300.0)
        fig2, ax2 = plt.subplots(figsize=(5, 3.3))
        ax2.plot(Voc_barrido, dVoc_dT_barrido * 1000, color="darkorange")
        ax2.set_xlabel(r"$V_{OC}$ supuesto [V]")
        ax2.set_ylabel(r"$dV_{OC}/dT$ [mV/°C]")
        ax2.set_title("Barrido de Voc a T=300K (reproduce lámina 44)")
        st.pyplot(fig2, width="stretch")

    st.divider()
    st.subheader("Confrontación con un módulo comercial real")
    st.markdown(f"**Fuente:** {MODULO_REF_NOMBRE} (ficha técnica, Unidad 4, diapositiva 45).")

    dVoc_dT_pct_sim = dVoc_dT_num_ref / Voc_T[idx_ref] * 100
    dPmax_dT_pct_sim = np.gradient(eta_T, T_C)[idx_ref] / eta_T[idx_ref] * 100

    df_comp = pd.DataFrame({
        "Coeficiente": ["dVoc/dT [%/°C]", "dPmax/dT [%/°C] (≈ dη/dT)"],
        "Módulo comercial (datasheet)": [MODULO_REF_TEMP_COEF_VOC_PCT_C, MODULO_REF_TEMP_COEF_PMAX_PCT_C],
        "Celda simulada (este modelo)": [round(dVoc_dT_pct_sim, 3), round(dPmax_dT_pct_sim, 3)],
    })
    st.dataframe(df_comp, hide_index=True, width="stretch")
    st.markdown(
        "**Discusión:** el módulo comercial tiene coeficientes de magnitud algo "
        "mayor porque es una celda real (con recombinación SRH, superficial y "
        "pérdidas resistivas dependientes de T que aquí no se modelan) y, "
        "además, un **módulo es una asociación en serie de muchas celdas**: "
        "el coeficiente porcentual (%/°C) es aproximadamente independiente del "
        "número de celdas en serie porque es una razón entre ΔV y V, pero el "
        "coeficiente absoluto (mV/°C o W/°C) del módulo sí escala con el "
        "número de celdas."
    )

# ============================================================================
# PESTAÑA 4 — Validación
# ============================================================================
with tab4:
    st.header("Validación")
    st.caption(
        "Estas verificaciones se ejecutan automáticamente cada vez que se abre "
        "esta pestaña, usando los mismos módulos de cálculo que el resto de la "
        "aplicación (nada está precalculado a mano)."
    )

    filas = []

    # --- V1: integral del espectro AM1.5G ---
    P_total_calc = espectro.irradiancia_total_Wm2()
    ref = 1000.0
    err = abs(P_total_calc - ref) / ref * 100
    filas.append(("V1", "Integral del espectro AM1.5G cargado desde astmg173",
                   f"{P_total_calc:.1f} W/m²", "1000 ± 15 W/m²", f"{err:.2f}%", err <= 1.5))

    # --- V2: flujo de fotones y Jsc,max sobre Eg=1.12eV ---
    Nph_v2 = espectro.Nph_sobre_gap_m2s(1.12) / 1e4
    Jsc_v2 = espectro.Jsc_max_mA_cm2(1.12)
    ref_Nph, ref_Jsc = 2.72e17, 43.5
    err_Nph = abs(Nph_v2 - ref_Nph) / ref_Nph * 100
    err_Jsc = abs(Jsc_v2 - ref_Jsc) / ref_Jsc * 100
    filas.append(("V2a", "Flujo de fotones sobre Eg=1.12 eV",
                   f"{Nph_v2:.3e} cm⁻²s⁻¹", "2.72e17 cm⁻²s⁻¹ (±5%)", f"{err_Nph:.2f}%", err_Nph <= 5))
    filas.append(("V2b", "J_sc,máx correspondiente",
                   f"{Jsc_v2:.2f} mA/cm²", "43.5 mA/cm² (±5%)", f"{err_Jsc:.2f}%", err_Jsc <= 5))

    # --- V3: Voc límite por Auger ---
    # Sin Eg_eV: usa el Eg REAL del silicio a T_ref_K (= 1.12 eV a 300K, dentro
    # de la pequeña corrección de Eg_T_eV), tal como exige la referencia de
    # la tabla del Anexo B. No se ve afectado por el fix de la Pestaña 2.
    T_ref_K = 298.15
    ni_ref = ni_T_cm3(T_ref_K)
    Voc_v3 = Voc_limite_auger_V(Jsc_v2, T_ref_K, W_CELL_REF_UM * 1e-4, ni_ref, CN_PLUS_CP_AUGER)
    ref_Voc = 0.785
    diff_Voc_mV = abs(Voc_v3 * 1000 - ref_Voc * 1000)
    filas.append(("V3", "V_OC límite por Auger (W=100µm, ni=1e10, cn+cp=4e-31)",
                   f"{Voc_v3*1000:.1f} mV", "785 ± 15 mV",
                   f"{diff_Voc_mV:.1f} mV de diferencia", diff_Voc_mV <= 15))

    # --- V4: FF0 y eficiencia límite ---
    FF0_v4 = FF0_ideal(Voc_v3, T_ref_K)
    eta_v4 = Voc_v3 * Jsc_v2 * FF0_v4 / (P_AM1_5_W_M2 / 10) * 100
    ref_FF0, ref_eta = 0.86, 29.3
    filas.append(("V4a", "FF0 (factor de forma ideal) para ese Voc",
                   f"{FF0_v4:.4f}", "0.86 ± 0.01", f"{abs(FF0_v4-ref_FF0):.4f} (dif. abs.)",
                   abs(FF0_v4 - ref_FF0) <= 0.01))
    filas.append(("V4b", "Eficiencia límite resultante η",
                   f"{eta_v4:.2f}%", "29.3 ± 0.5 pp", f"{abs(eta_v4-ref_eta):.2f} pp",
                   abs(eta_v4 - ref_eta) <= 0.5))

    # --- V5: cierre de la cascada ---
    # calcular_cascada() usa Eg=st.session_state.Eg_eV -- el Eg que el usuario
    # tenga puesto en el slider en el momento de abrir la pestaña. El cierre a
    # 100% es una identidad aritmética de la cascada multiplicativa, así que
    # se cumple para cualquier Eg (por eso el residuo siempre da ~0): esta
    # verificación certifica consistencia de la construcción del arreglo de
    # niveles, no la validez física de V_OC (eso lo hacen V3/V4/V6).
    etiquetas_v5, niveles_v5, _, _, _ = calcular_cascada()
    suma_cierre = niveles_v5[-1] + sum(-np.diff(niveles_v5))
    residuo_v5 = abs(100 - suma_cierre)
    filas.append(("V5", "Cierre de la cascada de pérdidas (suma de peldaños + η final)",
                   f"{suma_cierre:.4f}%", "100 ± 0.5 pp (residuo mostrado)",
                   f"residuo = {residuo_v5:.2e} pp", residuo_v5 <= 0.5))

    # --- V6: dVoc/dT numérico vs analítico, caso de control Vg0=1.2, Voc=0.6, T=300K ---
    # Se construye una curva sintética autoconsistente Voc(T) a partir de la MISMA
    # relación Isc = A*T^gamma*exp[(qVoc-Eg0)/kT] con Isc=cte (Unidad 4, diap. 40-41),
    # fijando la constante de integración para que Voc(300K)=0.6V exactamente.
    # Esto aísla y valida la relación matemática dVoc/dT en sí misma, independiente
    # del valor particular de Voc que entrega nuestro dispositivo simulado (~0.79V).
    Vg0_test, gamma_test, Voc300_test, T0_test = 1.2, 3, 0.6, 300.0
    # De Isc = A*T^gamma*exp[(q*Voc-Eg0)/kT] = cte  =>  Voc(T) = kT/q*(C - gamma*ln T) + Vg0
    const_test = (Voc300_test - Vg0_test) / (KB_EV * T0_test) + gamma_test * np.log(T0_test)
    T_test = np.linspace(295, 305, 21)
    Voc_test = (KB_EV * T_test) * (const_test - gamma_test * np.log(T_test)) + Vg0_test
    idx_t0 = np.argmin(np.abs(T_test - T0_test))
    dVoc_dT_num_v6 = np.gradient(Voc_test, T_test)[idx_t0]
    dVoc_dT_an_v6 = dVoc_dT_analitico_V_K(Voc300_test, T0_test, gamma_test, Vg0_test)
    diff_v6_mV = abs(dVoc_dT_num_v6 - dVoc_dT_an_v6) * 1000
    filas.append(("V6", "dVoc/dT numérico vs. analítico (Vg0=1.2V, Voc=0.6V, γ=3, T=300K)",
                   f"num={dVoc_dT_num_v6*1000:.3f} / an={dVoc_dT_an_v6*1000:.3f} mV/°C",
                   "coincidencia <0.2 mV/°C; ambos ≈ −2.3 mV/°C",
                   f"{diff_v6_mV:.4f} mV/°C", diff_v6_mV <= 0.2))

    # --- V7: coeficiente de temperatura del módulo comercial ---
    filas.append(("V7", f"Coef. de temperatura de potencia, {MODULO_REF_NOMBRE}",
                   f"{dPmax_dT_pct_sim:.3f} %/°C (simulado, celda ideal)",
                   f"{MODULO_REF_TEMP_COEF_PMAX_PCT_C} %/°C (datasheet, módulo real)",
                   "reportado y discutido en Pestaña 3", True))

    df_val = pd.DataFrame(
        filas, columns=["#", "Verificación", "Valor calculado", "Valor de referencia",
                         "Error / diferencia", "Aprobado"]
    )
    df_val["Veredicto"] = df_val["Aprobado"].map(lambda ok: "✅ Aprobado" if ok else "❌ Rechazado")
    st.dataframe(
        df_val.drop(columns=["Aprobado"]), hide_index=True, width="stretch"
    )

    n_aprob = df_val["Aprobado"].sum()
    st.markdown(f"**{n_aprob} / {len(df_val)} verificaciones aprobadas.**")

    with st.expander("Notas sobre aproximaciones del modelo (por qué V3/V4 pueden no calzar al 100%)"):
        st.markdown(
            "- El límite de $V_{OC}$ (V3) supone recombinación de Auger como "
            "**único** mecanismo, dopaje simétrico $n=p\\sim\\Delta p$ y atrapamiento "
            "perfecto de luz en 100 µm — todas explícitas en `semiconductor.py`.\n"
            "- $n_i(T)$ se calibra para calzar exactamente con la referencia de "
            "300 K del curso (1×10¹⁰ cm⁻³) y propaga la forma funcional "
            "$T^3 e^{-E_g/kT}$; no usa masas efectivas ajustadas partícula por "
            "partícula, lo que introduce un error de segundo orden aceptado "
            "explícitamente en esta pestaña.\n"
            "- La pestaña de Validación **no codifica ningún resultado**: cada "
            "fila llama a las mismas funciones que las pestañas 1-3.\n"
            "- En la Pestaña 2 (cascada), $n_i$ se calcula con el Eg EXPLORADO "
            "en el slider (no el Eg real del silicio), para que $V_{OC}$ refleje "
            "correctamente el trade-off físico $J_{sc}$ vs $V_{OC}$ al variar Eg. "
            "En la Pestaña 3 y en esta pestaña de Validación, en cambio, se usa "
            "siempre el Eg(T) real del silicio, que es lo que exige la tabla de "
            "referencia del Anexo B."
        )

# ============================================================================
# PESTAÑA 5 — Ecuaciones fundamentales
# ============================================================================
with tab5:
    st.header("📐 Ecuaciones fundamentales del modelo")
    st.markdown(
        "Compendio de todas las ecuaciones físicas implementadas en la "
        "aplicación, agrupadas por pestaña de contenido. Cada ecuación indica "
        "en qué archivo/función del código se calcula, para trazabilidad "
        "directa entre la física y la implementación durante la presentación."
    )
    st.caption(
        "Definidas en `ecuaciones.py` — este módulo sólo contiene texto y "
        "LaTeX; no participa en ningún cálculo de la aplicación."
    )

    for seccion, lista_ecuaciones in TODAS_LAS_ECUACIONES.items():
        st.subheader(seccion)
        for eq in lista_ecuaciones:
            with st.expander(f"**{eq['nombre']}**", expanded=False):
                st.latex(eq["latex"])
                st.markdown(eq["descripcion"])
                st.caption(f"📄 Implementado en: `{eq['donde_se_usa']}`")
        st.divider()
