import asyncio

import google.generativeai
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser, create_react_agent
from langchain.prompts import StringPromptTemplate
from langchain import SerpAPIWrapper, LLMChain
from typing import List, Union
from langchain.schema import AgentAction, AgentFinish, OutputParserException
import re
from langchain.agents.output_parsers import ReActJsonSingleInputOutputParser
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import DuckDuckGoSearchRun
from langchain import hub
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.tools.render import render_text_description_and_args
from langchain_community.agent_toolkits.amadeus.toolkit import AmadeusToolkit

from langchain.cache import RedisSemanticCache
from langchain_openai import OpenAIEmbeddings
from langchain.globals import set_llm_cache
from datetime import timedelta
from langchain.cache import MomentoCache

import hashlib
from gptcache import Cache
from gptcache.adapter.api import init_similar_cache
from langchain.cache import GPTCache, InMemoryCache
from gptcache.embedding.langchain import LangChain
from langchain.globals import set_llm_cache
from langchain_openai import OpenAIEmbeddings
from langchain_openai.llms.base import OpenAI

import os
import chainlit as cl
import streamlit as st

from core_files.hotel_core import input_parser_hotel
from core_files.flight_core import input_parser_flight
from core_files.chatbot_add_agent import all_in_1_agent, sms_or_email
from datetime import datetime

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.base import AsyncCallbackHandler, BaseCallbackHandler

# os.environ["OPENAI_API_KEY"] = "<openai-key>"
# os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
os.environ["AMADEUS_CLIENT_ID"] = st.secrets["AMADEUS_CLIENT_ID"]
os.environ["AMADEUS_CLIENT_SECRET"] = st.secrets["AMADEUS_CLIENT_SECRET"]


# @st.cache_resource
# def init_connection():
#     return redis.Redis(host='redis-19483.c294.ap-northeast-1-2.ec2.redns.redis-cloud.com', port=19483,
#                        password=st.secrets["REDIS_API_KEY"])
#
#
# conn = init_connection()


@st.cache_resource(show_spinner=False)
def get_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


# template = """Answer the following questions as best you can, but speaking as passionate travel expert. You have
# access to the following tools:
#
# {tools}
#
# Use the following format:
#
# Question: the input question you must answer
# Thought: you should always think about what to do
# Action: the action to take, should be one of [{tool_names}]
# Action Input: the input to the action
# Observation: the result of the action
# ... (this Thought/Action/Action Input/Observation can repeat N times)
# Thought: I now know the final answer
# Final Answer: a detailed day by day final answer to the original input question, You must answer in Korean
#
# Begin! Remember to answer as a passionate and informative travel expert when giving your final answer.
#
#
# Question: {input}
# {agent_scratchpad}"""

template = """
Answer the following questions as best you can, but speaking as passionate travel expert. You have access to the following tools:

{tools}

당신의 임무는 user가 원활하게 여행을 계획하고 마칠 수 있도록 돕는 것입니다.
무조건 한국어로 답하십시오.
다음 context와 history를 통해 user가 입력한 내용을 바탕으로 여행을 계획할 수 있도록 지원하세요.
만약 user가 일정을 계획하기를 원한다면 user에게 몇 명과 함께 가는지, 누구와 가는지, 언제 가는지, 몇 박 몇 일 일정인지를 물어보고 이동거리를 고려한 일정을 세워주세요.
user가 원한 기간 동안의 완벽한 일정이 일별로 각각, 세부적으로 수립되어야 합니다.
해당 계획에는 항공편, 호텔, 관광지 및 소요 예산이 포함됩니다.
동일한 tool을 연속해서 사용하지 마십시오.

만약에 hotel_search_tool을 사용한다면 무조건 다음을 따라야합니다.:
You need to give action input like this "destination, IN, OUT, person, rooms"
Do not put anything else, but only “destination, IN, OUT, person, rooms.”
destination: The place where user will stay.
IN: It is your check-in date, It has to be like this: 2024-05-04")
OUT: It is your check-out date, It has to be like this: 2024-05-05")
person: It is how many people will stay.")
rooms: It is how many rooms to reserve, Default is 1.

만약에 flight_search_tool을 사용한다면 무조건 다음을 따라야합니다.:
You need to give action input like this "starting, destination, d1, d2, adults, where, oneway"
Do not put anything else, but only “starting, destination, d1, d2, adults, where, oneway”.
starting: The place where user will start, must be IATA code.
destination: The place where user want to go, must be IATA code.
d1: It is your departure date, It has to be like this: 20240501
d2: It is your return date, It has to be like this: 20240502, in case of one-way travel it has to be like this: 00000000
adults: It is how many people to reserve.
where: It is about traveling abroad or domestically, if user wants to move within Korea it has to be: dome, if it is not it has to be: inte
oneway: It is about whether the user wants to travel one way or round trip, if user wants to travel one way it has to be: one, , if it is not it has to be: round
연도가 제공되지 않으면 기본은 2024년으로 검색하십시오.

만약에 Search_poi을 사용한다면 무조건 다음을 따라야합니다.:
You must search in Traditional Chinese/Mandarin or english.


Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question, You must answer in Korean, Do not omit it and print it out as is.


Begin! Remember to answer as a passionate and informative travel expert when giving your final answer.

Previous conversation history:
{history}

Question: {input}
{agent_scratchpad}
"""

# Set up a prompt template
class CustomPromptTemplate(StringPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]

    def format(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        return self.template.format(**kwargs)


class CustomOutputParser(AgentOutputParser):

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise OutputParserException(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)


def search_online(input_text):
    search = DuckDuckGoSearchRun().run(f"site:tripadvisor.com things to do{input_text}")
    return search


# def search_hotel(input_text):
#     search = DuckDuckGoSearchRun().run(f"site:agoda.com {input_text}")
#     return search


# def search_flight(input_text):
#     search = DuckDuckGoSearchRun().run(f"site:skyscanner.com {input_text}")
#     return search


def search_general(input_text):
    search = DuckDuckGoSearchRun().run(f"{input_text}")
    return search


def search_hotel(input_text):
    search = input_parser_hotel(f"{input_text}")
    return search


def search_flight(input_text):
    search = input_parser_flight(f"{input_text}")
    return search

def search_online_naver(input_text):
    search = DuckDuckGoSearchRun().run(f"site:naver.com things to do{input_text}")
    return search


memory = ConversationBufferWindowMemory(k=15)


def _handle_error(error) -> str:
    return str(error)[:50]


@cl.on_chat_start
def agent():
    toolkit = AmadeusToolkit()
    tool_amadeus = toolkit.get_tools()
    tools = [

        Tool(
            name="Search general",
            func=search_general,
            description="useful for when you need to answer general travel questions"
        ),
        Tool(
            name="Search tripadvisor",
            func=search_online,
            description="useful for when you need to answer trip plan questions, especially useful when looking for things to do and see."
        ),
        # Tool(
        #     name="Search hotel",
        #     func=search_hotel,
        #     description="useful for when you need to answer hotel questions"
        # ),
        # Tool(
        #     name="Search flight",
        #     func=search_flight,
        #     description="useful for when you need to answer flight questions"
        # ),
        Tool.from_function(
            name="Search airport",
            func=lambda x: agent_executor2.invoke({"input": x}),
            description="useful for when you need to answer airport questions or need to get IATA code"
        ),
        Tool.from_function(
            name="Search_poi",
            func=lambda x: all_in_1_agent({"input": x}),
            description="useful for when you need to get the keyword about travel information or get experience about travel"
        ),
        Tool(
            name="Search datetime",
            func=lambda x: datetime.now().isoformat(),
            description="useful for when you need to know the current datetime",
        ),
        Tool(
            name="Send email",
            func=lambda x: sms_or_email().invoke({"input": x}),
            description="Send Email via Infobip. If you need to send email, use Send email",
        ),
        Tool.from_function(
            name="hotel_search_tool",
            func=search_hotel,
            description="useful when you need to search hotel"
        ),
        Tool.from_function(
            name="flight_search_tool",
            func=search_flight,
            description="useful when you need to search flight"
        ),
        Tool(
            name="Search naver",
            func=search_online_naver,
            description="useful for when you need to answer trip plan questions within korea, including restaurant,"
        ),
    ]

    prompt = CustomPromptTemplate(
        template=template,
        tools=tools,
        # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
        # This includes the `intermediate_steps` variable because that is needed
        input_variables=["input", "intermediate_steps", "history"]
    )
    output_parser = CustomOutputParser()

    # memory = ConversationBufferWindowMemory(k=2)
    # llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
    llm = ChatOpenAI(temperature=0.7, model="gpt-4-turbo", streaming=True, callbacks=[StreamingStdOutCallbackHandler()], cache=True)
    # llm = ChatGoogleGenerativeAI(model="gemini-pro")
    # LLM chain consisting of the LLM and a prompt
    llm_chain = LLMChain(llm=llm, prompt=prompt)

    # set_llm_cache(
    #     RedisSemanticCache(redis_url="redis://default:{a}@{b}:{c}".format(a=st.secrets["REDIS_API_KEY"], b="redis-19483.c294.ap-northeast-1-2.ec2.redns.redis-cloud.com", c=19483), embedding=OpenAIEmbeddings(model="text-embedding-3-small"))
    # )
    # cache_client = CacheClient(
    #     Configurations.Laptop.v1(),
    #     CredentialProvider.from_environment_variable("MOMENTO_API_KEY"),
    #     default_ttl=timedelta(days=1))
    #
    # # Choose a Momento cache name of your choice
    # cache_name = "langchain"
    #
    # # Instantiate the LLM cache
    # set_llm_cache(MomentoCache(cache_client, cache_name))

    @st.cache_resource(ttl=10800, show_spinner=False)
    def get_hashed_name(name):
        return hashlib.sha256(name.encode()).hexdigest()

    @st.cache_resource(ttl=10800, show_spinner=False)
    def init_gptcache(_cache_obj: Cache, llm: str):
        hashed_llm = get_hashed_name(llm)
        init_similar_cache(cache_obj=_cache_obj, data_dir=f"similar_cache_{hashed_llm}",
                           embedding=LangChain(OpenAIEmbeddings(model="text-embedding-3-small")))


    @st.cache_resource(ttl=10800, show_spinner=False)
    def set_cache():
        return set_llm_cache(GPTCache(init_gptcache))

    # set_cache()

    set_llm_cache(InMemoryCache())

    prompt_for_amadeus1 = hub.pull("hwchase17/react-json")

    agent2 = create_react_agent(
        llm,
        tool_amadeus,
        prompt_for_amadeus1,
        tools_renderer=render_text_description_and_args,
        output_parser=ReActJsonSingleInputOutputParser(),
    )
    agent_executor2 = AgentExecutor(
        agent=agent2,
        tools=tool_amadeus,
        verbose=True,
        handle_parsing_errors="Check your output and make sure it conforms, use the Action/Action Input syntax",
        max_iterations=3
    )

    tool_names = [tool.name for tool in tools]
    agent = LLMSingleActionAgent(
        llm_chain=llm_chain,
        output_parser=output_parser,
        stop=["\nObservation:"],
        allowed_tools=tool_names
    )

    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory,
                                                        handle_parsing_errors="Check your output and make sure it conforms, use the Action/Action Input syntax, If the current output is the final answer, you must add 'Final Answer:' at the beginning.",
                                                        max_iterations=20)

    return agent_executor, memory
