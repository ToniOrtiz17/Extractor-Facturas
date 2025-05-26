
import streamlit as st
import fitz  # PyMuPDF
import re
import os
import tempfile
import pandas as pd

st.set_page_config(page_title="Extractor de datos")
st.image("assets/logo_asesor.png", width=150)
st.title("Extractor de datos")
st.write("Tu herramienta profesional para comparar facturas de luz en segundos.")

def extraer_datos(texto):
    datos = {
        "Titular": "",
        "Dirección de suministro": "",
        "CUPS": "",
        "Mercado": "",
        "Peaje de acceso a la red": "",
        "Potencia Punta (kW)": "",
        "Potencia Valle (kW)": "",
        "Periodo Facturación": "",
        "Días Facturados": "",
        "Consumo Total (kWh)": "",
        "IVA (€)": "",
        "Total Factura": "",
        "Fecha Fin Contrato": "",
        "Permanencia": ""
    }

    patrones = {
        "Titular": r"(?i)Titular(?: del contrato)?:\s*([A-ZÑÁÉÍÓÚ ]{5,})",
        "Dirección de suministro": r"(?i)Dirección de suministro:\s*(.*)",
        "CUPS": r"(?i)CUPS[:\s]+(ES\d{20,})",
        "Mercado": r"(?i)Mercado[:\s]+(Libre|Regulado)",
        "Peaje de acceso a la red": r"(?i)Peaje de acceso a la red.*?:?\s*(\d\.\dTD)",
        "Potencia Punta (kW)": r"(?i)Potencia punta[:\s]+([\d,.]+)",
        "Potencia Valle (kW)": r"(?i)Potencia valle[:\s]+([\d,.]+)",
        "Periodo Facturación": r"(?i)Periodo de facturación[:\s]*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})",
        "Días Facturados": r"(?i)D[ií]as facturados[:\s]+(\d+)",
        "Consumo Total (kWh)": r"(?i)consumo total.*?[:\s]+(\d+)\s*kWh",
        "IVA (€)": r"(?i)IVA.*?[:\s]+([\d,.]+)\s?€",
        "Total Factura": r"(?i)total factura.*?[:\s]+([\d,.]+)\s?€",
        "Fecha Fin Contrato": r"(?i)fecha final del contrato[:\s]+(\d{2}/\d{2}/\d{4})",
        "Permanencia": r"(?i)permanencia[:\s]+(Sí|No)"
    }

    for campo, patron in patrones.items():
        coincidencia = re.search(patron, texto)
        if coincidencia:
            if campo == "Periodo Facturación":
                datos[campo] = f"{coincidencia.group(1)} - {coincidencia.group(2)}"
            else:
                datos[campo] = coincidencia.group(1).strip()

    return datos

uploaded_file = st.file_uploader("Sube tu factura (PDF o imagen)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    texto_completo = ""
    with fitz.open(tmp_path) as doc:
        for page in doc:
            texto_completo += page.get_text()

    os.unlink(tmp_path)

    datos_extraidos = extraer_datos(texto_completo)

    st.subheader(f"📄 Datos extraídos de {uploaded_file.name}")
    for campo, valor in datos_extraidos.items():
        st.markdown(f"**{campo}**: {valor}")

    if st.button("💾 Guardar en Excel"):
        df = pd.DataFrame([datos_extraidos])
        excel_path = f"/mnt/data/{uploaded_file.name.replace('.pdf','')}_extraido.xlsx"
        df.to_excel(excel_path, index=False)
        st.success(f"Archivo guardado en: {excel_path}")
