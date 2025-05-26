
import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
import tempfile
import os
import re
import fitz  # PyMuPDF

st.set_page_config(page_title="Factura Luz App", layout="centered")
st.title("Factura Luz App - Toni Ortiz")
st.write("Extrae y compara datos clave de tus facturas de luz.")

EXCEL_PATH = os.path.expanduser("~/OneDrive/FacturasComparadas/facturas_comparadas.xlsx")
os.makedirs(os.path.dirname(EXCEL_PATH), exist_ok=True)

def extraer_datos(texto):
    datos = {
        "Titular": re.search(r"(?i)ANTONIO ORTIZ REBOLLAR", texto),
        "Dirección de suministro": re.search(r"Dirección de suministro:\s*(C.*?)\n", texto, re.IGNORECASE),
        "CUPS": re.search(r"(ES\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?[A-Z0-9]{2})", texto),
        "Mercado": re.search(r"Mercado[:\s]*(Libre|Regulado)", texto, re.IGNORECASE),
        "Peaje de acceso": re.search(r"Peaje[s]? de acceso a la red[^:]*[:\s]*(\d\.\dTD)", texto, re.IGNORECASE),
        "Potencia Punta (kW)": re.search(r"Potencia punta[:\s]*(\d+[\.,]?\d*)\s*kW", texto, re.IGNORECASE),
        "Potencia Valle (kW)": re.search(r"Potencia valle[:\s]*(\d+[\.,]?\d*)\s*kW", texto, re.IGNORECASE),
        "Periodo Facturación": re.search(r"PERIODO DE FACTURACI[ÓO]N[:\s\n]*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})", texto),
        "Días Facturados": re.search(r"D[ÍI]AS FACTURADOS[:\s\n]*(\d+)", texto),
        "Consumo Total (kWh)": re.search(r"Energ[ií]a consumida[^\d]*(\d+)\s*kWh", texto, re.IGNORECASE),
        "IVA (€)": re.search(r"IVA[^€\d]*(\d+[\.,]\d{2})[^€\d]*(\d+[\.,]\d{2})", texto),
        "Total Factura": re.search(r"TOTAL IMPORTE FACTURA[^\d]*(\d+[\.,]\d{2})", texto),
        "Fecha Fin Contrato": re.search(r"Fecha final del contrato[:\s]*(\d{2}/\d{2}/\d{4})", texto),
        "Permanencia": re.search(r"Permanencia[:\s]*(Sí|Si|No)", texto, re.IGNORECASE),
        "Tipo Tarifa TD": re.search(r"\b(2\.0TD|3\.0TD|6\.1TD|6\.0TD|3\.1TD)\b", texto)
    }

    resultado = {}
    for campo, match in datos.items():
        if match:
            if campo == "Periodo Facturación":
                resultado[campo] = f"{match.group(1)} - {match.group(2)}"
            elif campo == "IVA (€)":
                resultado[campo] = f"{match.group(2).replace(',', '.')}€"
            elif campo == "Total Factura":
                resultado[campo] = f"{match.group(1).replace(',', '.')}€"
            elif campo == "CUPS":
                resultado[campo] = match.group(1).replace(" ", "")
            elif campo == "Titular":
                resultado[campo] = "Antonio Ortiz RebollAR"
            else:
                resultado[campo] = match.group(1).strip().replace(",", ".")
        else:
            resultado[campo] = "-"
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
