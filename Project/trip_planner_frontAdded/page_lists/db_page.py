import streamlit as st
import os
from dotenv import load_dotenv
import requests
from streamlit_lottie import st_lottie
import time

# langchain 패키지
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# RAG Chain 구현을 위한 패키지
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from langchain_openai import OpenAIEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain


load_dotenv()
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# pdf 파일을 읽어서 벡터 저장소에 저장
def load_pdf_to_vector_store(pdf_file, chunk_size=1000, chunk_overlap=100):
    print("파일경로: ",pdf_file)
    # PDF 파일 로딩
    loader = PyPDFLoader(f'{pdf_file}')
    documents = loader.load()

    # 텍스트 분할
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    splits = text_splitter.split_documents(documents)

    # FAISS 인스턴스 생성 및 문서 임베딩으로 초기화
    vectorstore = FAISS.from_documents(documents=splits, 
                                        embedding=OpenAIEmbeddings(api_key=os.environ["OPENAI_API_KEY"])
                                        )

    return vectorstore


# 벡터 저장소에서 문서를 검색하고 답변을 생성
def retrieve_and_generate_answers(vectorstore, message, temperature=0):

    # RAG 체인 생성
    retriever = vectorstore.as_retriever()

    # Prompt
    template = '''Answer the question based only on the following context:
    <context>
    {context}
    </context>

    Question: {input}
    '''


    prompt = ChatPromptTemplate.from_template(template)

     # ChatModel 인스턴스 생성
    model = ChatOpenAI(model='gpt-3.5-turbo-0125', 
                       temperature=temperature,
                       api_key=os.environ["OPENAI_API_KEY"])

    # Prompt와 ChatModel을 Chain으로 연결
    document_chain = create_stuff_documents_chain(model, prompt)

    # Retriever를 Chain에 연결
    rag_chain = create_retrieval_chain(retriever, document_chain)

    # 검색 결과를 바탕으로 답변 생성
    response = rag_chain.invoke({'input': message})
    print(response)
    
    return response['answer']

# 최종 결과
def location_analysis(file_path, message):
    # file_path = f'pdf_datas/2024서울관광안내서_KR.pdf'
    v_store = load_pdf_to_vector_store(file_path)
    ans = retrieve_and_generate_answers(v_store, message)            
    print(ans)
    return ans

# 로딩화면 애니메이션
def render_animation():
    animation_response = requests.get('https://lottie.host/702e6d74-eeb5-428a-8efc-9f65b908f9ef/BdmkfpJjjh.json')
    animation_json = dict()
    
    if animation_response.status_code == 200:
        animation_json = animation_response.json()
    else:
        print("Error in the URL")     
    return st_lottie(animation_json, height=200, width=300)
    
def createPage():
    option = st.radio( "원하는 지역을 클릭해주세요", ["서울", "강릉"])
    
    # # s_travel = st.checkbox('서울 관광')
    # print("체크박스", s_travel)
    
    if option:
        file_path=''
        if '서울' in option:
            file_path = f'pdf_datas/2024서울관광안내서_KR.pdf'
        elif '강릉' in option:
            file_path = f'pdf_datas/240124_강릉시관광안내지도_국문_웹용.pdf'
        
        col1, col2 = st.columns(2)
        with col1:
            form = st.form(key='my-form')
            message = form.text_input("원하는 질문을 적어주세요: ")
            submit = form.form_submit_button('Submit')

            if submit:
                ans = location_analysis(file_path, message)
                progress_text = "Operation in progress. Please wait."
                my_bar = st.progress(0, text=progress_text)
                render_animation()
                for percent_complete in range(100):
                    time.sleep(0.01)
                    my_bar.progress(percent_complete + 1, text=progress_text)
                time.sleep(5)
                my_bar.empty()
                st.success("로딩완료!")
                
                st.subheader("답변")
                form = st.form(key='answer-form')
                st.write(ans)

    