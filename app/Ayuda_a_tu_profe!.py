import streamlit as st

st.set_page_config(layout="wide")

st.title("Ayuda a tu profe! 🧑‍🏫")

col1, col2 = st.columns([0.6, 2])

with col1:
    st.image("app/elprofe.jpg")

with col2:
    st.markdown(
        """
        Sabemos lo cansador que es crear evaluaciones, buscar bibliografía,
        actualizar el curso, etc, y todo eso sin contar con todo el trabajo que
        implica preocuparse de que tus estudiantes aprendan.

        Es por esto que hemos creado **Ayuda a tu profe! 🧑‍🏫**, una plataforma
        web que disponibiliza un amplio set de herramientas que permitiran a
        los profesores mejorar su desempeño en la docencia.

        Actualmente la aplicación cuenta con 3 modulos que buscan alivianarle
        la pega a los profesores:

        - **Generador de evaluaciones**: Permite crear evaluaciones de manera
        rápida solo usando información de tus clases.
        - **Buscar bibliografía**: Encuentra referencias bibliográficas de manera
        sencilla.
        - **Actualización curricular**: Actualiza tu curso de manera automática
        con la información más novedosa.
        """
    )
