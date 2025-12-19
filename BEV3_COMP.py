import streamlit as st
import pandas as pd
import numpy as np
import io
from collections import OrderedDict
import openpyxl

# =================================================
# CONFIG STREAMLIT
# =================================================
st.set_page_config(page_title="Rear vs Rear Comparacion Perceptron", layout="wide")
st.title("📐 Comparación Rear vs Rear – Diferencia por Punto")

# =================================================
# LECTOR PERCEPTRON – EXPORT FORMAT A
# =================================================
def leer_perceptron_exportA(file):
    lines = file.read().decode("latin-1").splitlines()

    header = None
    rows = []

    for line in lines:
        cols = line.split("\t")

        if len(cols) > 5 and cols[0] == "JSN" and cols[1] == "PSN":
            header = cols
            continue

        if header is None:
            continue

        if cols[0] in ["USL", "LSL", "UTL", "LTL", "URL", "LRL", "NOMINAL"]:
            continue

        if cols[0].isdigit():
            row = OrderedDict()
            for i, col in enumerate(header):
                val = cols[i] if i < len(cols) else ""
                row[col] = str(val).replace(",", "")
            rows.append(row)

    df = pd.DataFrame(rows)

    for c in df.columns[5:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    ejes = df.columns[5:].tolist()
    return df, ejes

# =================================================
# UI – CARGA
# =================================================
archivo_a = st.file_uploader("📤 Rear Archivo A (Primera medición)", type="txt")
archivo_b = st.file_uploader("📤 Rear Archivo B (Segunda medición)", type="txt")

if archivo_a and archivo_b:

    # =================================================
    # LECTURA
    # =================================================
    df_a, ejes_a = leer_perceptron_exportA(archivo_a)
    df_b, ejes_b = leer_perceptron_exportA(archivo_b)

    if df_a.empty or df_b.empty:
        st.error("❌ No se pudieron leer mediciones reales")
        st.stop()

    # Tomamos el JSN como nombre de columna
    jsn_a = df_a["JSN"].iloc[0]
    jsn_b = df_b["JSN"].iloc[0]

    # =================================================
    # MATCH PSN
    # =================================================
    df_a["PSN"] = df_a["PSN"].astype(str).str.strip()
    df_b["PSN"] = df_b["PSN"].astype(str).str.strip()

    psn_comunes = sorted(set(df_a["PSN"]).intersection(set(df_b["PSN"])))

    if not psn_comunes:
        st.error("❌ No hay PSN comunes")
        st.stop()

    df_match = pd.DataFrame({"PSN": psn_comunes})

    df_a = df_a[df_a["PSN"].isin(psn_comunes)]
    df_b = df_b[df_b["PSN"].isin(psn_comunes)]

    # =================================================
    # EJES COMUNES
    # =================================================
    ejes_comunes = sorted(set(ejes_a).intersection(set(ejes_b)))

    if not ejes_comunes:
        st.error("❌ No hay ejes comunes")
        st.stop()

    # =================================================
    # COMPARATIVO
    # =================================================
    comparativo = []

    for eje in ejes_comunes:
        for psn in psn_comunes:
            val_a = df_a.loc[df_a["PSN"] == psn, eje].values
            val_b = df_b.loc[df_b["PSN"] == psn, eje].values

            if len(val_a) == 0 or len(val_b) == 0:
                continue
            if pd.isna(val_a[0]) or pd.isna(val_b[0]):
                continue

            comparativo.append([
                psn,
                eje,
                round(val_a[0], 3),
                round(val_b[0], 3),
                round(val_a[0] - val_b[0], 3)  # 🔥 A - B
            ])

    df_comparativo = pd.DataFrame(
        comparativo,
        columns=[
            "PSN",
            "Axis",
            str(jsn_a),
            str(jsn_b),
            "Correlacion"
        ]
    )

    # =================================================
    # CORRELACION PROMEDIO POR EJE
    # =================================================
    df_correlacion = (
        df_comparativo
        .groupby("Axis", as_index=False)["Correlacion"]
        .mean()
        .round(3)
    )

    # =================================================
    # VISUALIZACIÓN
    # =================================================
    st.subheader("📋 Match PSN")
    st.dataframe(df_match, use_container_width=True)

    st.subheader("📊 Comparativo por Punto")
    st.dataframe(df_comparativo, use_container_width=True)

    st.subheader("📐 Correlación Promedio por Punto")
    st.dataframe(df_correlacion, use_container_width=True)

    # =================================================
    # EXPORT EXCEL
    # =================================================
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_a.to_excel(writer, index=False, sheet_name="Rear_A")
        df_b.to_excel(writer, index=False, sheet_name="Rear_B")
        df_match.to_excel(writer, index=False, sheet_name="Match_PSN")
        df_comparativo.to_excel(writer, index=False, sheet_name="Comparativo")
        df_correlacion.to_excel(writer, index=False, sheet_name="Correlacion")

    output.seek(0)

    st.download_button(
        label="📥 Descargar Excel Comparativo Rear",
        data=output,
        file_name="Rear_vs_Rear_Comparacion_Percepton.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )