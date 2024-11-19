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


class ExistenciaReferencia(BaseModel):
    """
    Clase para representar la existencia de una referencia bibliográfica académica.
    """

    existe: bool = Field(description="Indica si la referencia bibliográfica existe")


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


def supervisar_bibliografia(referencias: List[ReferenciaBibliografica]):
    """
    Busca si las referencias entregadas realmente existen según el conocimiento del LLM.
    """
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, temperature=0.7, model="gpt-4o-mini")
    structured_llm = llm.with_structured_output(ExistenciaReferencia)

    prompt = """
    Dime si esta referencia bibliográfica existe:
    {referencia}
    Revisa si realmente estás seguro de que existe la referencia bibliográfica.
    """
    referencias_validas = []
    for ref in referencias:
        prompt_ref = prompt.format(referencia=ref)
        resultado = structured_llm.invoke(prompt_ref)
        if resultado.existe:
            referencias_validas.append(ref)
    return referencias_validas


# Interfaz en Streamlit
st.title("Buscador de Bibliografía Académica")
tema = st.text_input(
    "Ingresa el tema que deseas estudiar (ej: probabilidades avanzadas):"
)

if st.button("Buscar"):
    if tema:
        referencias = buscar_bibliografia_sin_links(tema)
        referencias_validas = supervisar_bibliografia(referencias)
        st.write("### Bibliografía recomendada:")

        if referencias_validas == []:
            st.markdown("No se encontraron referencias bibliográficas válidas.")
        else:
            for ref in referencias_validas:
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
