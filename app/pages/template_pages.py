import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import dotenv
import os

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)

dotenv.load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(openai_api_key=api_key, model="gpt-3.5-turbo")

system_template_message = """
You are a geography teacher.
"""

user_template_message = """
What is the capital of {country}?
"""

prompt_template = ChatPromptTemplate.from_messages(
    messages=[
        ("system", system_template_message),
        ("user", user_template_message),
    ]
)

# El StrOutputParser se puede cambiar según el tipo de output que se espere
chain = prompt_template | llm | StrOutputParser()


st.markdown("# Crea tu evaluación")

country_selected = st.selectbox(
    "Selecciona un país",
    [
        "Argentina",
        "Brasil",
        "Chile",
        "Colombia",
        "Ecuador",
        "México",
        "Perú",
        "Venezuela",
    ],
)

template_prompt_input = {
    "country": country_selected,
}

if st.button("Generar pregunta"):
    respuesta_generada = chain.invoke(template_prompt_input)
    st.write("Respuesta generada:", respuesta_generada)
