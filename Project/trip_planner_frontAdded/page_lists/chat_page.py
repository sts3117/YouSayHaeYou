import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import DataFrameLoader
from langchain.agents import tool
import datetime
import json
import requests
import os
from pydantic import BaseModel, Field
import folium
from streamlit_folium import folium_static
import core_files.chatbot_core as chatbot_core
import core_files.data_core as data_core
from firebase_admin import auth
import pandas as pd
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

os.environ["GOOGLE_MAP_API_KEY"] = st.secrets["GOOGLE_MAP_API_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
url = 'https://places.googleapis.com/v1/places:searchText'


def createPage():
    st.markdown('')
    history, col4 = st.columns(2)
    with history:
        agent_executor, memory = chatbot_core.agent()
        data_core.main(memory)
    
    with col4:
        placeholer= st.container()
        with placeholer:
            col1, col2, col3 = st.columns([6, 1, 1])
            with col2:
                rerun_btn = st.button('Rerun', key='rerun')
            with col3:
                stop_btn = st.button('Stop', key='stop')
        
        if rerun_btn:
            st.rerun()
        if stop_btn:
            st.stop()
    
    
    class Message(BaseModel):
        actor: str
        payload: str

  
    USER = "user"
    ASSISTANT = "ai"
    MESSAGES = "messages"

    # def initialize_session_state():
    if MESSAGES not in st.session_state:
        st.session_state[MESSAGES] = [Message(actor=ASSISTANT, payload="안녕하세요! 어떤 도움이 필요하신가요?")]

    msg: Message
    for msg in st.session_state[MESSAGES]:
        st.chat_message(msg.actor).write(msg.payload)


    # Prompt
    query: str = st.chat_input("이곳에 질문을 입력하세요.")

  
    # agent_executor, memory = chatbot_core.agent()

    # data_core.main(memory)

    
    
    if query:
        st.session_state[MESSAGES].append(Message(actor=USER, payload=str(query)))
        st.chat_message(USER).write(query)

        with st.chat_message(ASSISTANT):
            st_callback = StreamlitCallbackHandler(st.container())
            response = agent_executor.invoke({'input': query}, {"callbacks": [st_callback]})
            output_message = response.get("output", "")
            output_message_str = str(output_message)
            st.session_state[MESSAGES].append(Message(actor=ASSISTANT, payload=output_message_str))
            st.write(response["output"])    

  
        
        