
import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
import tempfile
import os
import re
import fitz  # PyMuPDF

st.set_page_config(page_title="Factura Luz App v11", layout="centered")
st.title("Factura Luz App - Toni Ortiz")
st.write("Extrae automáticamente los datos estandarizados de tus facturas de Iberdrola, Repsol o Endesa.")

EXCEL_PATH = os.path.expanduser("~/OneDrive/FacturasComparadas/facturas_comparadas.xlsx")
os.makedirs(os.path.dirname(EXCEL_PATH), exist_ok=True)

def extraer_datos(texto):
    campos = {
        "Titular": [
            r"(?i)Titular(?:.*?)?:\s*([A-ZÁÉÍÓÚÑ\s]+)",
            r"(?i)Cliente(?:.*?)?:\s*([A-ZÁÉÍÓÚÑ\s]+)"
        ],
        "Dirección de suministro": [
            r"Dirección de suministro:\s*(C.*?)\n",
            r"Suministro:\s*(.*?)\n",
            r"Domicilio:\s*(.*?)\n"
        ],
        "CUPS": [
            r"(ES\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?[A-Z0-9]{2})"
        ],
        "Mercado": [
            r"Mercado[:\s]*(Libre|Regulado)"
        ],
        "Peaje de acceso a la red": [
            r"Peaje[s]? de acceso a la red[^:]*[:\s]*(\d\.\dTD)",
            r"Tarifa de acceso[^:]*[:\s]*(\d\.\dTD)"
        ],
        "Potencia Punta (kW)": [
            r"Potencia punta[:\s]*(\d+[\.,]?\d*)\s*kW"
        ],
        "Potencia Valle (kW)": [
            r"Potencia valle[:\s]*(\d+[\.,]?\d*)\s*kW"
        ],
        "Periodo Facturación": [
            r"PERIODO DE FACTURACI[ÓO]N[:\s\n]*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})",
            r"Desde el\s*(\d{2}/\d{2}/\d{4})\s*hasta el\s*(\d{2}/\d{2}/\d{4})"
        ],
        "Días Facturados": [
            r"D[ÍI]AS FACTURADOS[:\s\n]*(\d+)",
            r"Número de días.*?(\d+)"
        ],
        "Consumo Total (kWh)": [
            r"consumida[^\d]*(\d+[\.,]?\d*)\s*kWh",
            r"Energia activa total\s*:\s*(\d+[\.,]?\d*)"
        ],
        "IVA (€)": [
            r"IVA[^\d]*(\d+[\.,]\d{2})[^\d]*(\d+[\.,]\d{2})"
        ],
        "Total Factura": [
            r"TOTAL IMPORTE FACTURA[^\d]*(\d+[\.,]\d{2})",
            r"TOTAL FACTURA[^\d]*(\d+[\.,]\d{2})"
        ],
        "Fecha Fin Contrato": [
            r"Fecha final del contrato[:\s]*(\d{2}/\d{2}/\d{4})",
            r"Fecha fin contrato.*?(\d{2}/\d{2}/\d{4})"
        ],
        "Permanencia": [
            r"Permanencia[:\s]*(Sí|Si|No)"
        ],
        "Tipo Tarifa TD": [
            r"\b(2\.0TD|3\.0TD|6\.1TD|6\.0TD|3\.1TD)\b"
        ]
    }

    resultado = {}

    for campo, patrones in campos.items():
        valor = "-"
        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                if campo == "Periodo Facturación":
                    valor = f"{match.group(1)} - {match.group(2)}"
                elif campo == "IVA (€)":
                    valor = f"{match.group(2).replace(',', '.')}€"
                elif campo == "Total Factura":
                    valor = f"{match.group(1).replace(',', '.')}€"
                elif campo == "CUPS":
                    valor = match.group(1).replace(" ", "")
                else:
                    valor = match.group(1).strip().replace(",", ".")
                break
        resultado[campo] = valor
    return resultado

st.subheader("📤 Sube tu factura (PDF o imagen)")
archivo = st.file_uploader("Selecciona una factura", type=["pdf", "jpg", "jpeg", "png"])

if archivo:
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(archivo.read())
    temp_file.close()

    if archivo.type == "application/pdf":
        doc = fitz.open(temp_file.name)
        texto = "".join([page.get_text() for page in doc])
    else:
        imagen = Image.open(temp_file.name)
        texto = pytesseract.image_to_string(imagen)

    datos = extraer_datos(texto)
    st.subheader(f"📄 Datos extraídos de {archivo.name}")
    for campo, valor in datos.items():
        st.write(f"**{campo}**: {valor}")

    if st.button("💾 Guardar en Excel"):
        df_nuevo = pd.DataFrame([datos])
        if os.path.exists(EXCEL_PATH):
            df_existente = pd.read_excel(EXCEL_PATH)
            df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
        else:
            df_final = df_nuevo
        df_final.to_excel(EXCEL_PATH, index=False)
        st.success(f"Factura guardada en: {EXCEL_PATH}")
