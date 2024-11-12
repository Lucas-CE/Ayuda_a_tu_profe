import streamlit as st
import PyPDF2
import re

st.set_page_config(
    page_title="Recalendarizador de Curso",
    page_icon="⏳",
)

st.markdown("# Recalendariza tu curso")

# Cargar el PDF del programa del curso
uploaded_file = st.file_uploader("Carga el programa del curso en formato PDF", type=["pdf"])

# Input para que el profesor indique las materias ya vistas
materias_vistas = st.text_area("Escribe las materias que ya has pasado, separadas por comas")

# Input para indicar cuántas semanas menos tiene el curso
semanas_menos = st.number_input("Indica cuántas semanas menos tiene el curso", min_value=1, step=1)

# Procesar el PDF y obtener información de las materias y semanas
def extraer_programa(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    contenido = ""
    for page in reader.pages:
        contenido += page.extract_text()
    
    # Usar una expresión regular para encontrar las unidades temáticas y la duración
    patron = r"D\. Unidades temáticas:.*?(Nombre de la unidad.*?Duración en semanas.*?)\n\n"
    seccion_unidades = re.search(patron, contenido, re.DOTALL)
    if not seccion_unidades:
        return []
    
    seccion_contenido = seccion_unidades.group(1)
    patron_materias = r"Nombre de la unidad\s+(.*?)\s+Duración en semanas\s+(\d+) semanas"
    materias = re.findall(patron_materias, seccion_contenido, re.DOTALL)
    materias = [(m.strip(), s) for m, s in materias]
    return materias

# Calcular la recalendarización
def recalendarizar(materias, materias_vistas, semanas_menos):
    # Convertir materias vistas a una lista
    materias_vistas_lista = [m.strip() for m in materias_vistas.split(",")]
    
    # Filtrar las materias que ya se han visto
    materias_pendientes = [m for m in materias if m[0] not in materias_vistas_lista]
    
    # Calcular las semanas disponibles
    semanas_totales = sum(int(m[1]) for m in materias_pendientes)
    semanas_disponibles = semanas_totales - semanas_menos
    
    # Ajustar la distribución de semanas para las materias pendientes
    if semanas_disponibles < 0:
        return "No hay suficientes semanas para cubrir todas las materias pendientes."
    
    semanas_por_materia = {}
    for materia, semanas in materias_pendientes:
        semanas_por_materia[materia] = int(semanas)
    
    # Recalendarizar distribuyendo semanas de forma proporcional
    factor_ajuste = semanas_disponibles / semanas_totales
    for materia in semanas_por_materia:
        semanas_por_materia[materia] = max(1, round(semanas_por_materia[materia] * factor_ajuste))
    
    return semanas_por_materia

if uploaded_file and materias_vistas and semanas_menos:
    materias = extraer_programa(uploaded_file)
    if materias:
        recalendarizacion = recalendarizar(materias, materias_vistas, semanas_menos)
        if isinstance(recalendarizacion, str):
            st.error(recalendarizacion)
        else:
            st.markdown("## Recalendarización Propuesta")
            for materia, semanas in recalendarizacion.items():
                st.write(f"- {materia}: {semanas} semanas")
    else:
        st.error("No se pudo extraer información de las materias del archivo PDF.")