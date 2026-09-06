# Proyecto 1 — Problema 2.3
## El límite de eficiencia: del espectro solar a su exploración usando silicio semiconductor

Aplicación Streamlit para el curso *Celdas Solares Fotovoltaicas*, Semestre 2026-2
(Prof. Felipe A. Larraín, PhD).

- **Semilla del grupo:** S = 3 (RUT: ...025, ...219, ...319 → suma=563 → 563 mod 10 = 3)
- **Parámetro asignado usado por este problema:** T de operación = 25 °C (Tabla A.1, fila S=3)

---

## 1. Arquitectura de la aplicación

```
proyecto/
├── constantes.py     # Único módulo con TODAS las constantes físicas.
│                      # Cada constante declara su unidad y su fuente en un
│                      # comentario (CODATA, Unidad 2/3/4 del curso, ASTM G173,
│                      # datasheet JinkoSolar). Nada de "números mágicos"
│                      # sueltos en el resto del código.
│
├── espectro.py        # Carga data/ASTMG173.csv (espectro AM1.5G real, mismos
│                      # datos que astmg173.xls) y calcula en tiempo real,
│                      # por integración numérica (trapezoidal):
│                      #   - irradiancia total P(λ) integrada
│                      #   - flujo de fotones N_ph(λ) = P(λ) / E_fotón(λ)
│                      #   - N_ph y J_sc,máx sobre cualquier umbral Eg
│
├── semiconductor.py   # Modelo físico de la Unidad 4, sin usar ningún solver
│                      # de dispositivo completo (no se usa solcore):
│                      #   - Eg(T), n_i(T)
│                      #   - V_OC límite por recombinación de Auger
│                      #   - FF0 ideal y FF con parásitos (Rs, Rp)
│                      #   - dV_OC/dT analítico
│
├── data/
│   └── ASTMG173.csv   # ASTM G173-03 Reference Spectra (SMARTS v2.9.2),
│                      # descargado de una copia pública citable en GitHub
│                      # (equivalente exacto a astmg173.xls de Webcursos)
│
├── app.py             # Interfaz Streamlit: 4 pestañas (st.tabs) + estado
│                      # compartido vía st.session_state (Eg, T de operación)
│
└── requirements.txt   # Dependencias para Streamlit Community Cloud
```

### Flujo de datos y estado compartido

- **Pestaña 1 → Pestaña 2:** el deslizador de banda prohibida `Eg` vive en
  `st.session_state["Eg_eV"]`. La Pestaña 2 lee ese mismo valor para calcular
  los primeros 4 peldaños de la cascada (intrínsecos al gap elegido).
- **Pestaña 2 ↔ Pestaña 3:** la temperatura de operación
  `st.session_state["T_operacion_C"]` se fija en la Pestaña 2 (peldaño 8) y
  se usa como punto de referencia marcado en las curvas de la Pestaña 3.
- **Pestaña 4 (Validación):** no repite ningún número; llama exactamente a
  las mismas funciones (`espectro.py`, `semiconductor.py`,
  `calcular_cascada()`) que usan las pestañas 1-3, evaluadas en los puntos de
  operación que pide el enunciado (Eg=1.12 eV, T=300 K, etc.).

### Principio de diseño

Ningún valor mostrado en pantalla está "hardcodeado": todos se recalculan en
cada re-ejecución del script a partir de datos reales (espectro AM1.5G) y de
las ecuaciones cerradas de la Unidad 4. Las únicas excepciones son las
constantes físicas y los datos de una única ficha técnica comercial citada
(JinkoSolar 66QL6-BDV, usada como punto de comparación en la Pestaña 3), que
están declaradas explícitamente en `constantes.py` con su fuente.

---

## 2. Fichas de librerías utilizadas

### Streamlit
- **Qué es:** framework de despliegue web para aplicaciones de datos en Python.
- **Rol en esta app:** capa de interfaz (widgets, pestañas `st.tabs`, estado
  compartido `st.session_state`, animación con `st.empty()`). No implementa
  ningún modelo físico ni realiza cálculos.
- **Entradas:** interacciones del usuario (sliders, checkboxes, botones).
- **Salidas:** re-renderizado de la interfaz y de las figuras.

### NumPy
- **Qué es:** librería de arreglos numéricos y álgebra vectorizada.
- **Rol en esta app:** integración numérica (`np.trapezoid`), evaluación
  vectorizada de las ecuaciones de `semiconductor.py` sobre arreglos de
  temperatura/longitud de onda, derivadas numéricas (`np.gradient`).
- **Supuestos:** ninguno físico; es álgebra numérica de propósito general.
- **Entradas/salidas:** arreglos numéricos (longitudes de onda, temperaturas,
  irradiancias) → arreglos numéricos derivados (flujos de fotones, Voc(T), etc.).

### pandas
- **Qué es:** librería de manejo de datos tabulares.
- **Rol en esta app:** lectura del archivo `ASTMG173.csv` (espectro AM1.5G) y
  construcción de la tabla comparativa de coeficientes de temperatura y de
  la tabla de la pestaña de Validación.
- **Entradas/salidas:** CSV → DataFrame; listas de resultados → DataFrame
  mostrado con `st.dataframe`.

### Matplotlib
- **Qué es:** librería de visualización científica 2D.
- **Rol en esta app:** todas las figuras (espectro, flujo de fotones, cascada
  de pérdidas, barridos de temperatura). Se usa explícitamente en modo
  "figura + ejes" (`plt.subplots`) para poder fijar unidades en cada eje,
  como exige el enunciado.
- **Entradas/salidas:** arreglos NumPy → objetos `Figure` renderizados con
  `st.pyplot`.

### Nota sobre librerías especializadas de PV (tmm, pvlib)

Este problema (2.3) se resolvió **sin** `pvlib` ni `tmm`: todo el modelo
óptico-eléctrico (integración del espectro, balance de fotones,
recombinación de Auger, factor de forma) se implementó explícitamente en
`espectro.py` y `semiconductor.py` a partir de las ecuaciones deducidas en
clase (Unidad 4), lo que permite que cada verificación de la pestaña de
Validación pueda auditarse línea por línea contra el PDF de la clase.
`solcore` no se usó en ningún momento (está prohibido por el enunciado).

---

## 3. Cómo correr localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```
