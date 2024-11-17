from pydantic import BaseModel, Field
from typing import List
import streamlit as st
from langchain_openai import ChatOpenAI

# Configurar OpenAI
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]


class ReferenciaBibliografica(BaseModel):
    """
    Clase para representar una referencia bibliográfica académica.
    """

    titulo: str = Field(description="Título exacto del libro o publicación")
    autores: str = Field(description="Nombre(s) del autor o autores")
    anio: str = Field(description="Año de publicación")
    editorial: str = Field(default="", description="Editorial que publicó el trabajo")


class ListaReferencias(BaseModel):
    """
    Clase para representar una lista de referencias bibliográficas académicas.
    """

    referencias: List[ReferenciaBibliografica] = Field(
        description="Lista de referencias bibliográficas académicas"
    )


def buscar_bibliografia_sin_links(tema: str) -> List[ReferenciaBibliografica]:
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, temperature=0.7, model="gpt-4o-mini")
    structured_llm = llm.with_structured_output(ListaReferencias)

    prompt = f"""Genera 5 referencias bibliográficas académicas sobre '{tema}'.
    Cada referencia debe incluir título, autores, año de publicación y editorial si está disponible."""

    try:
        resultado = structured_llm.invoke(prompt)
        return resultado.referencias
    except Exception as e:
        st.error(f"Error al procesar las referencias: {str(e)}")
        return []


# Interfaz en Streamlit
st.title("Buscador de Bibliografía Académica")
tema = st.text_input(
    "Ingresa el tema que deseas estudiar (ej: probabilidades avanzadas):"
)

if st.button("Buscar"):
    if tema:
        referencias = buscar_bibliografia_sin_links(tema)
        st.write("### Bibliografía recomendada:")

        for ref in referencias:
            # Mostrar cada referencia en formato continuo
            referencia_texto = f"""**Título:** {ref.titulo}
            **Autores:** {ref.autores}
            **Año:** {ref.anio}"""

            if ref.editorial:
                referencia_texto += f"""
                **Editorial:** {ref.editorial}"""

            st.markdown(referencia_texto)

            # Botón de búsqueda en Google
            st.markdown(
                f"[Buscar en Google](https://www.google.com/search?q={ref.titulo.replace(' ', '+')})",
                unsafe_allow_html=True,
            )
            st.markdown("---")
    else:
        st.write("Por favor, ingresa un tema.")
