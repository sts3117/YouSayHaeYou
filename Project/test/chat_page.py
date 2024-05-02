# import streamlit as st
# from langchain.chat_models import ChatOpenAI
# from langchain.embeddings import HuggingFaceEmbeddings
# from langchain.text_splitter import CharacterTextSplitter
# from langchain.vectorstores import FAISS
# from langchain.document_loaders import DataFrameLoader
# from langchain.agents import tool
# import datetime
# import json
# import requests
# import os
# from pydantic import BaseModel, Field
# import folium
# from streamlit_folium import folium_static
# import core_files.chatbot_core as chatbot_core
# import core_files.data_core as data_core
# from firebase_admin import auth
# import pandas as pd
# import time


# os.environ["GOOGLE_MAP_API_KEY"]
# url = 'https://places.googleapis.com/v1/places:searchText'

# def createPage():
    
#     class Message(BaseModel):
#         actor: str
#         payload: str



#     # llm = ChatOpenAI(openai_api_key=os.environ["OPENAI_API_KEY"], model_name='gpt-3.5-turbo', temperature=0)

#     USER = "user"
#     ASSISTANT = "ai"
#     MESSAGES = "messages"

#     if MESSAGES not in st.session_state:
#         st.session_state[MESSAGES] = [Message(actor=ASSISTANT, payload="안녕하세요! 어떤 도움이 필요하신가요?")]

#     msg: Message
#     for msg in st.session_state[MESSAGES]:
#         st.chat_message(msg.actor).write(msg.payload)


#     # Prompt
#     query: str = st.chat_input("이곳에 질문을 입력하세요.")

#     agent_executor, memory = chatbot_core.agent()
    
#     data_core.main(memory)

#     if query:
#         st.session_state[MESSAGES].append(Message(actor=USER, payload=str(query)))
#         st.chat_message(USER).write(query)

#         with st.spinner("생각중이에요..."):
#             start_time = time.time()
#             # response: str = qa.run(query=query)
#             # response: str = agent.invoke({'input': query})['output']
#             response: str = agent_executor.invoke({'input': query})['output']
#             st.session_state[MESSAGES].append(Message(actor=ASSISTANT, payload=response))
#             st.chat_message(ASSISTANT).write(response)
#             end_time = time.time()
#             execution_time = end_time - start_time
#             print(f"Response Generation Time: {execution_time:.2f} seconds")
#     # st.write("Chatbot")


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
import time
import asyncio

os.environ["GOOGLE_MAP_API_KEY"]
url = 'https://places.googleapis.com/v1/places:searchText'

def createPage():
    class Message(BaseModel):
        actor: str
        payload: str

    # llm = ChatOpenAI(openai_api_key=os.environ["OPENAI_API_KEY"], model_name='gpt-3.5-turbo', temperature=0)

    USER = "user"
    ASSISTANT = "ai"
    MESSAGES = "messages"

    if MESSAGES not in st.session_state:
        st.session_state[MESSAGES] = [Message(actor=ASSISTANT, payload="안녕하세요! 어떤 도움이 필요하신가요?")]

    for msg in st.session_state[MESSAGES]:
        st.chat_message(msg.actor).write(msg.payload)

    query: str = st.chat_input("이곳에 질문을 입력하세요.")

    async def run_agent():
        agent_executor, memory = await chatbot_core.agent()
        # await data_core.main(memory)

        if query:
            st.session_state[MESSAGES].append(Message(actor=USER, payload=str(query)))
            st.chat_message(USER).write(query)

            with st.spinner("생각중이에요..."):
                start_time = time.time()
                response: str = await agent_executor({'input': query})
                st.session_state[MESSAGES].append(Message(actor=ASSISTANT, payload=response))
                st.chat_message(ASSISTANT).write(response)
                end_time = time.time()
                execution_time = end_time - start_time
                print(f"Response Generation Time: {execution_time:.2f} seconds")

    if query:
        asyncio.run(run_agent())