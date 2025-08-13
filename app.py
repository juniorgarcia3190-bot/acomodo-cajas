
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import xlsxwriter
import tempfile
import os

# Dimensiones de la tarima (en cm)
PALLET_WIDTH = 100
PALLET_LENGTH = 120
PALLET_HEIGHT = 200

st.title("Acomodo de Cajas en Tarima")
st.markdown("Simula cómo acomodar cajas en una tarima de 1m x 1.2m x 2m")

# Entrada de datos
st.sidebar.header("Agregar cajas")
item = st.sidebar.text_input("Nombre del ítem")
ancho = st.sidebar.number_input("Ancho (cm)", min_value=1)
largo = st.sidebar.number_input("Largo (cm)", min_value=1)
alto = st.sidebar.number_input("Alto (cm)", min_value=1)
cantidad = st.sidebar.number_input("Cantidad", min_value=1, step=1)

if "cajas" not in st.session_state:
    st.session_state.cajas = []

if st.sidebar.button("Agregar caja"):
    st.session_state.cajas.append({
        "item": item,
        "ancho": ancho,
        "largo": largo,
        "alto": alto,
        "cantidad": cantidad
    })

# Mostrar tabla de cajas
if st.session_state.cajas:
    st.subheader("Cajas ingresadas")
    df = pd.DataFrame(st.session_state.cajas)
    st.dataframe(df)

    # Acomodo de cajas (algoritmo simple por capas)
    posiciones = []
    x, y, z = 0, 0, 0
    max_z = 0
    for caja in st.session_state.cajas:
        for _ in range(caja["cantidad"]):
            if x + caja["ancho"] > PALLET_WIDTH:
                x = 0
                y += max_z
                max_z = 0
            if y + caja["largo"] > PALLET_LENGTH:
                y = 0
                z += max_z
                max_z = 0
            if z + caja["alto"] > PALLET_HEIGHT:
                st.warning(f"No cabe más cajas. Se detuvo en el ítem {caja['item']}")
                break
            posiciones.append({
                "item": caja["item"],
                "x": x,
                "y": y,
                "z": z,
                "ancho": caja["ancho"],
                "largo": caja["largo"],
                "alto": caja["alto"]
            })
            x += caja["ancho"]
            max_z = max(max_z, caja["largo"])

    # Visualización 3D
    st.subheader("Visualización 3D del acomodo")
    fig = go.Figure()
    for pos in posiciones:
        fig.add_trace(go.Mesh3d(
            x=[pos["x"], pos["x"]+pos["ancho"], pos["x"]+pos["ancho"], pos["x"], pos["x"], pos["x"]+pos["ancho"], pos["x"]+pos["ancho"], pos["x"]],
            y=[pos["y"], pos["y"], pos["y"]+pos["largo"], pos["y"]+pos["largo"], pos["y"], pos["y"], pos["y"]+pos["largo"], pos["y"]+pos["largo"]],
            z=[pos["z"], pos["z"], pos["z"], pos["z"], pos["z"]+pos["alto"], pos["z"]+pos["alto"], pos["z"]+pos["alto"], pos["z"]+pos["alto"]],
            color='lightblue',
            opacity=0.5,
            name=pos["item"]
        ))
    fig.update_layout(scene=dict(
        xaxis_title='Ancho',
        yaxis_title='Largo',
        zaxis_title='Alto'
    ))
    st.plotly_chart(fig)

    # Exportar a Excel
    if st.button("Exportar a Excel"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            writer = pd.ExcelWriter(tmp.name, engine='xlsxwriter')
            pd.DataFrame(posiciones).to_excel(writer, index=False, sheet_name='Acomodo')
            writer.close()
            st.download_button("Descargar Excel", data=open(tmp.name, "rb").read(), file_name="acomodo.xlsx")

    # Exportar a PDF
    if st.button("Exportar a PDF"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            c = canvas.Canvas(tmp.name, pagesize=letter)
            c.drawString(100, 750, "Resumen de acomodo de cajas")
            y = 720
            for pos in posiciones:
                c.drawString(50, y, f"{pos['item']} - Posición: ({pos['x']}, {pos['y']}, {pos['z']}) Tamaño: {pos['ancho']}x{pos['largo']}x{pos['alto']}")
                y -= 20
                if y < 50:
                    c.showPage()
                    y = 750
            c.save()
            st.download_button("Descargar PDF", data=open(tmp.name, "rb").read(), file_name="acomodo.pdf")
