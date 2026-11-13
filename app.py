"""
SIMTELE-RISK | Prototipo Semana 1 (Streamlit)
Sistemas lineales + teoría de errores, con escenarios NORMAL / ESTRÉS / MAL CONDICIONADO.
Ejecutar:  streamlit run app.py
"""
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

import metodos_lineales as ml

st.set_page_config(page_title="SIMTELE-RISK", page_icon="🚡", layout="wide")

# ------------------------------------------------------------------ INICIO
st.title("🚡 SIMTELE-RISK")
st.caption("Proyecto final de Métodos Numéricos · datos sintéticos y educativos, "
           "sin conexión con equipos de control reales.")

tarjetas = st.columns(4)
modulos = ["1 · Detención", "2 · Deterioro", "3 · Oscilaciones", "4 · Sensores"]
for col, nombre in zip(tarjetas, modulos):
    col.info(f"**{nombre}**")

modulo = st.sidebar.radio("Módulo", modulos, index=1)

if modulo != "2 · Deterioro":
    st.warning(f"El módulo «{modulo}» se implementa en las próximas semanas. "
               "Por ahora está activo el bloque de **sistemas lineales** (módulo 2).")
    st.stop()

# ------------------------------------------------------------- PARÁMETROS
st.header("Módulo 2 · Calibración por sistemas lineales A x = b")
st.markdown("Se construye un sistema con solución conocida **x\\*** (b = A·x\\*) y matriz **SPD**, "
            "para comparar Jacobi, Gauss-Seidel, LU y Gradiente Conjugado contra la referencia directa.")

escenario = st.sidebar.selectbox("Escenario", ml.ESCENARIOS)
cfg = ml.config_escenario(escenario)
st.sidebar.markdown(f"**Tipo:** {cfg['tipo']}")

n = st.sidebar.number_input("Tamaño n (≥ 4)", min_value=4, max_value=30, value=cfg["n"], step=1)
tol = st.sidebar.number_input("Tolerancia (residual relativo)", min_value=1e-16, max_value=1e-2,
                              value=float(cfg["tol"]), format="%.1e")
max_iter = st.sidebar.number_input("Máx. iteraciones", min_value=10, max_value=50000,
                                   value=int(cfg["max_iter"]), step=10)
seed = st.sidebar.number_input("Semilla", min_value=0, max_value=9999, value=42, step=1)
delta = st.sidebar.number_input("Perturbación relativa de b", min_value=1e-12, max_value=1e-1,
                                value=float(cfg["delta"]), format="%.1e")

A, b, x_ref = ml.construir_sistema(escenario, n=int(n), seed=int(seed))

# ---------------------------------------------------------- DIAGNÓSTICO
diag = ml.diagnostico_matriz(A)
st.subheader("1. Diagnóstico de la matriz")
c1, c2, c3, c4 = st.columns(4)
c1.metric("κ∞(A)", f"{diag['kappa_inf']:.3e}")
c2.metric("SPD", "Sí" if diag["definida_positiva"] else "No")
c3.metric("ρ(Jacobi)", f"{diag['radio_espectral_jacobi']:.3f}")
c4.metric("ρ(Gauss-Seidel)", f"{diag['radio_espectral_gs']:.3f}")
st.write(
    f"Simétrica: **{diag['simetrica']}** · Diagonal dominante: **{diag['diag_dominante']}** · "
    f"λmín = {diag['autovalor_min']:.3e} · λmáx = {diag['autovalor_max']:.3e}"
)
st.caption("Convergencia: Jacobi y Gauss-Seidel convergen si ρ < 1 (garantizado con dominancia diagonal estricta; "
           "Gauss-Seidel también converge para toda matriz SPD). El Gradiente Conjugado estándar exige A SPD.")
if not diag["definida_positiva"]:
    st.error("A no es SPD: el Gradiente Conjugado estándar no es válido.")

with st.expander("Ver A, b y x* (solución exacta conocida)"):
    st.dataframe(pd.DataFrame(A, columns=[f"x{i+1}" for i in range(A.shape[0])]))
    st.write("b =", np.array2string(b, precision=6, separator=", "))
    st.write("x* =", np.array2string(x_ref, precision=6, separator=", "))

# -------------------------------------------------------------- EJECUCIÓN
resultados = ml.ejecutar_todos(A, b, x_ref, tol=tol, max_iter=int(max_iter))

st.subheader("2. Comparación de métodos")
filas = []
for r in resultados:
    h = r["historial"][-1]
    filas.append({
        "Método": r["metodo"],
        "Convergió": "Sí" if r["convergio"] else "No",
        "Iteraciones": r["iteraciones"],
        "Residual rel.": f"{h['residual_rel']:.3e}",
        "Error abs. (∞)": f"{h['error_abs']:.3e}",
        "Error rel.": f"{h['error_rel']:.3e}",
        "Error %": f"{h['error_pct']:.3e}",
        "Tiempo (ms)": f"{r['tiempo_ms']:.3f}",
        "Criterio / motivo": r["motivo"],
    })
st.dataframe(pd.DataFrame(filas), hide_index=True)

# ---- distinción pedida por la consigna: mal condicionado ≠ no converge
if escenario == "MAL_CONDICIONADO" or diag["kappa_inf"] > 1e6:
    st.info(
        "**Mal condicionamiento ≠ fallo de convergencia.** Con κ(A) enorme, incluso el método directo "
        "pierde dígitos (error ≈ κ·ε_máquina), aunque el residual sea diminuto. "
        "Un método iterativo que diverge o se estanca (Jacobi, Gauss-Seidel) es un problema "
        "distinto: depende de ρ(T) y no solo de κ."
    )

# ----------------------------------------------------------------- GRÁFICOS
st.subheader("3. Gráficos")
g1, g2 = st.columns(2)

with g1:
    fig, ax = plt.subplots(figsize=(6, 4))
    for r in resultados:
        if len(r["historial"]) > 1:
            ks = [h["iter"] for h in r["historial"]]
            rs = [max(h["residual_rel"], 1e-18) for h in r["historial"]]
            ax.semilogy(ks, rs, label=r["metodo"])
    ax.set_xlabel("Iteración")
    ax.set_ylabel("Residual relativo")
    ax.set_title("Convergencia del residual")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    st.pyplot(fig)

with g2:
    fig, ax = plt.subplots(figsize=(6, 4))
    nombres = [r["metodo"] for r in resultados]
    errores = [max(r["historial"][-1]["error_abs"], 1e-18) for r in resultados]
    ax.bar(range(len(nombres)), errores)
    ax.set_yscale("log")
    ax.set_xticks(range(len(nombres)))
    ax.set_xticklabels(nombres, rotation=25, ha="right")
    ax.set_ylabel("Error absoluto final (∞)")
    ax.set_title("Error final por método")
    ax.grid(True, axis="y", which="both", alpha=0.3)
    st.pyplot(fig)

# ------------------------------------------------- TABLAS DE ITERACIONES
st.subheader("4. Tablas de iteraciones")
for r in resultados:
    with st.expander(f"{r['metodo']} · {r['iteraciones']} iteración(es)"):
        if r["metodo"].startswith("LU"):
            st.write("**L**")
            st.dataframe(pd.DataFrame(r["L"]))
            st.write("**U**")
            st.dataframe(pd.DataFrame(r["U"]))
        tabla = pd.DataFrame([
            {"k": h["iter"],
             **{f"x{i+1}": v for i, v in enumerate(h["x"])},
             "residual": h["residual"], "error_abs": h["error_abs"], "error_rel": h["error_rel"]}
            for h in r["historial"]
        ])
        st.dataframe(tabla, hide_index=True)

# ------------------------------------------------------------ SENSIBILIDAD
st.subheader("5. Sensibilidad ante perturbaciones")
s = ml.sensibilidad(A, b, delta=delta, seed=int(seed))
st.table(pd.DataFrame({
    "Perturbación relativa de b": [f"{s['delta_b_rel']:.3e}"],
    "Cambio relativo en x": [f"{s['cambio_x_rel']:.3e}"],
    "Amplificación observada": [f"{s['amplificacion']:.3e}"],
    "Cota teórica κ(A)": [f"{s['cota_kappa']:.3e}"],
}))
st.caption("Se cumple: amplificación observada ≤ κ(A). Cuanto mayor es κ, más se amplifica una perturbación pequeña.")

# ------------------------------------------------------------ INTERPRETACIÓN
st.subheader("6. Interpretación (borrador)")
mejor = min((r for r in resultados if r["convergio"] and r["metodo"] != "Directa (referencia)"),
            key=lambda r: r["historial"][-1]["error_abs"], default=None)
st.markdown("**Conclusión numérica:** " + (
    f"en este escenario el método más preciso fue **{mejor['metodo']}** "
    f"(error abs. {mejor['historial'][-1]['error_abs']:.2e})." if mejor else
    "ningún método convergió con la configuración dada."))
st.markdown("**Conclusión del problema:** _(redáctenla ustedes: qué significa calibrar los coeficientes del "
            "modelo de deterioro con este sistema, y qué no puede inferirse de datos sintéticos)._")
