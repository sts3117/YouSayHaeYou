from firebase_admin import firestore, auth
from google.cloud.firestore_v1 import aggregation
from google.cloud.firestore_v1.base_query import FieldFilter
from pydantic import BaseModel
import streamlit as st
import re
from datetime import datetime
from streamlit_extras.stylable_container import stylable_container


db = firestore.client()


class Message(BaseModel):
    actor: str
    payload: str


def load_chat_message():
    user = None
    # 사용자 입력 받기
    try:
        user = auth.get_user_by_email(st.session_state["username"])
    except auth.UserNotFoundError:
        st.error("사용자를 찾을 수 없습니다.")

    uid = user.uid

    chats_ref = db.collection("chats").where("user", "==", uid).get()
    sorted_docs = sorted(chats_ref, key=lambda doc: doc.id)

    serv = []
    for doc in sorted_docs:
        doc_data = doc.to_dict()
        extracted_data = {
            "actor": doc_data.get("actor"),
            "message": doc_data.get("message")
        }
        serv.append(extracted_data)

    serv1, serv2 = [], []

    [[serv1.append(item["actor"]), serv2.append(item["message"])] for item in serv]

    cc = len(serv1) // 2 + len(serv1) % 2

    st.session_state["messages"] = []
    for i in range(cc):
        index = i * 2
        st.session_state["messages"].append(Message(actor=serv1[index], payload=serv2[index]))
        if index + 1 < len(serv1):
            st.session_state["messages"].append(Message(actor=serv1[index + 1], payload=serv2[index + 1]))

    mem_list_input, mem_list_output = [], []
    serv2.pop(0)

    for i in range(cc):
        index = i * 2
        input_data = serv2[index] if index < len(serv2) else ""
        output_data = serv2[index + 1] if index + 1 < len(serv2) else ""
        mem_list_input.append({"input": input_data})
        mem_list_output.append({"output": output_data})

    return mem_list_input, mem_list_output


def save_chat_message():
    user = None
    # 사용자 입력 받기
    try:
        user = auth.get_user_by_email(st.session_state["username"])
    except auth.UserNotFoundError:
        st.error("사용자를 찾을 수 없습니다.")

    uid = user.uid

    timestamp = datetime.now()
    for i in range(len(st.session_state["messages"])):
        chat_data = {
            "user": uid,
            "user_name": st.session_state["name"],
            "message": st.session_state["messages"][i].payload,
            "actor": st.session_state["messages"][i].actor,
            "timestamp": timestamp
        }
        db.collection("chats").document(st.session_state["name"] + str(0) + str(i)).set(chat_data)


def delete_chat_message(memory):
    collection_ref = db.collection("chats")
    query = collection_ref.where(filter=FieldFilter("user_name", "==", st.session_state["name"]))
    aggregate_query = aggregation.AggregationQuery(query)

    aggregate_query.count(alias="all")
    counts = aggregate_query.get()
    count = counts[0]
    count = re.search(r'value=(\d+)', str(count)).group(1)

    for i in range(int(count)):
        db.collection("chats").document(st.session_state["name"] + str(0) + str(i)).delete()

    st.session_state["messages"] = []
    memory.aclear()


# def save_button(email, uid):
#     st.title("채팅 기록 저장 및 불러오기")
#
#     message = st.text_area("메시지를 입력하세요:")
#
#     # '전송' 버튼 클릭 시 채팅 저장
#     if st.button("저장"):
#         if uid.strip() != "" and message.strip() != "":
#             save_chat_message(uid, message)
#             st.success("채팅이 저장되었습니다!")
#         else:
#             st.error("사용자 UID 또는 메시지가 비어있습니다.")


def main(memory):
    # with st.sidebar:
    
    with stylable_container(
            key='prev_data',
            css_styles="""
            {
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 0.5rem;
                padding: calc(1em - 1px);
            }
            """,
        ):
        st.subheader("채팅 기록 옵션")
        c1, c2, c3 = st.columns([2,3,2])
        create_chat_button = c1.button(
            "채팅 내용 저장", use_container_width=True, key="create_chat_button"
        )
        if create_chat_button:
            try:
                save_chat_message()
                st.success("성공적으로 저장했습니다.")
            except Exception as e:
                st.error("저장 실패: ", e)

        load_chat_button = c2.button(
            "과거 채팅 내용 불러오기", use_container_width=True, key="load_chat_button"
        )
        if load_chat_button:
            try:
                mem_list_input, mem_list_output = load_chat_message()
                for i in range(len(mem_list_input)):
                    memory.save_context(mem_list_input[i], mem_list_output[i])
                memory.load_memory_variables({})
                st.rerun()
                st.success("성공적으로 불러왔습니다.")
            except Exception as e:
                st.error("불러오기 실패: ", e)

        delete_chat_button = c3.button(
            "삭제", use_container_width=True, key="delete_chat_button"
        )
        if delete_chat_button:
            try:
                delete_chat_message(memory)
                st.session_state["messages"] = [Message(actor="ai", payload="안녕하세요! 어떤 도움이 필요하신가요?")]
                st.rerun()
                st.success("성공적으로 삭제되었습니다.")
            except Exception as e:
                st.error("삭제 실패: ", e)


def database_save(df):
    for index, row in df.iterrows():
        query = db.collection("city").where("Name", "==", row["Name"]).limit(1).get()
        existing_docs = [doc for doc in query]
        if not existing_docs:
            doc_ref = db.collection("city").document()
            doc_ref.set(row.to_dict())
            st.success(f'Document {doc_ref.id} 업로드 완료')
        else:
            st.warning(f'{row["Name"]} 문서가 이미 존재합니다. 무시합니다.')


def database_delete_with_country(country):
    query = db.collection("city").stream()
    result = [doc for doc in query if country in doc.to_dict()["Address"]]
    for doc in result:
        doc.reference.delete()
        st.success(f'Document {doc.id} 삭제 완료')
