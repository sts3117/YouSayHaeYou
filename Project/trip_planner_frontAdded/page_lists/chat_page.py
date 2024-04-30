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


os.environ["GOOGLE_MAP_API_KEY"] = st.secrets["GOOGLE_MAP_API_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
url = 'https://places.googleapis.com/v1/places:searchText'

def createPage():
    
    class Message(BaseModel):
        actor: str
        payload: str

    # 사용자 입력 받기
    user = None
    try:
        user = auth.get_user_by_email(st.session_state["username"])
    except auth.UserNotFoundError:
        st.error("사용자를 찾을 수 없습니다.")

    uid = user.uid

    # llm = ChatOpenAI(openai_api_key=os.environ["OPENAI_API_KEY"], model_name='gpt-3.5-turbo', temperature=0)

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

    # # Combine info
    # df_place['combined_info'] = df_place.apply(lambda
    #                                                 row: f"Type: {row['type']}, Name: {row['displayName.text']}. Rating: {row['rating']}. Address: {row['formattedAddress']}. Website: {row['websiteUri']}",
    #                                             axis=1)
    # # Load Processed Dataset
    # loader = DataFrameLoader(df_place, page_content_column="combined_info")
    # docs = loader.load()

    # # Document splitting
    # text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    # texts = text_splitter.split_documents(docs)

    # # embeddings model
    # # Define the path to the pre-trained model you want to use
    # modelPath = "sentence-transformers/all-MiniLM-l6-v2"

    # # Create a dictionary with model configuration options, specifying to use the CPU for computations
    # model_kwargs = {'device': 'cpu'}

    # # Create a dictionary with encoding options, specifically setting 'normalize_embeddings' to False
    # encode_kwargs = {'normalize_embeddings': False}

    # # Initialize an instance of HuggingFaceEmbeddings with the specified parameters
    # embeddings = HuggingFaceEmbeddings(
    #     model_name=modelPath,  # Provide the pre-trained model's path
    #     model_kwargs=model_kwargs,  # Pass the model configuration options
    #     encode_kwargs=encode_kwargs  # Pass the encoding options
    # )

    # # Vector DB
    # vectorstore = FAISS.from_documents(texts, embeddings)

    # template = """
    # 당신의 임무는 user가 원활하게 여행을 계획하고 마칠 수 있도록 돕는 것입니다.
    # 무조건 한국어로 답하십시오.
    # 다음 context와 chat history를 통해 user가 입력한 내용을 바탕으로 원하는 내용을 찾을 수 있도록 지원하고, 여행을 계획할 수 있도록 지원하세요.
    # 만약 user가 일정을 계획하기를 원한다면 user에게 몇 명과 함께 가는지, 누구와 가는지, 언제 가는지, 몇 박 몇 일 일정인지를 물어보고 이동거리를 고려한 일정을 세워주세요.
    # 만약, 장소를 추천해야 한다면 주소, 전화번호, 웹사이트와 함께 3가지의 추천을 제공하세요.
    # 평점과 사용자 평점 수를 기준으로 추천을 정렬합니다.
    #
    # {context}
    #
    # chat history: {history}
    #
    # input: {question}
    # Your Response:
    # """
    #
    # # prompt = PromptTemplate(
    # #     input_variables=["context", "history", "question"],
    # #     template=template,
    # # )
    #
    # prompt = ChatPromptTemplate.from_template(template)
    #
    # memory = ConversationBufferMemory(memory_key="history", input_key="question", return_messages=True)
    # qa = RetrievalQA.from_chain_type(
    #     llm=llm,
    #     chain_type='stuff',
    #     retriever=vectorstore.as_retriever(),
    #     verbose=True,
    #     chain_type_kwargs={
    #         "verbose": True,
    #         "prompt": prompt,
    #         "memory": memory}
    # )
    #
    # google_search = GoogleSerperAPIWrapper()
    # tools = [
    #     Tool(name="Intermediate Answer",
    #          func=google_search.run,
    #          description="검색이 필요할 때 사용"),
    #
    #     Tool(name="Knowledge Base",
    #          func=qa.run,
    #          description="데이터베이스에서 필요한 정보가 있을 때 사용")
    # ]
    # agent = initialize_agent(tools=tools, llm=llm, agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

    agent_executor, memory = chatbot_core.agent()

    data_core.main(memory)

    if query:
        st.session_state[MESSAGES].append(Message(actor=USER, payload=str(query)))
        st.chat_message(USER).write(query)

        with st.spinner("생각중이에요..."):
            # response: str = qa.run(query=query)
            # response: str = agent.invoke({'input': query})['output']
            response: str = agent_executor.invoke({'input': query})['output']
            st.session_state[MESSAGES].append(Message(actor=ASSISTANT, payload=response))
            st.chat_message(ASSISTANT).write(response)
    # st.write("Chatbot")
