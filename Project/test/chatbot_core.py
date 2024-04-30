import asyncio
import aiohttp

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser, create_react_agent
from langchain.prompts import StringPromptTemplate
from langchain import OpenAI, SerpAPIWrapper, LLMChain
from typing import List, Union
from langchain.schema import AgentAction, AgentFinish, OutputParserException
import re
from langchain.agents.output_parsers import ReActJsonSingleInputOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.tools import DuckDuckGoSearchRun
from langchain import hub
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.tools.render import render_text_description_and_args
from langchain_community.agent_toolkits.amadeus.toolkit import AmadeusToolkit

import os
import chainlit as cl
import streamlit as st

from core_files.chatbot_add_agent import all_in_1_agent, sms_or_email
from datetime import datetime

# os.environ["OPENAI_API_KEY"] = "<openai-key>"
os.environ["GOOGLE_API_KEY"]
os.environ["AMADEUS_CLIENT_ID"]
os.environ["AMADEUS_CLIENT_SECRET"]
llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.4)
toolkit = AmadeusToolkit(llm=llm)
tool_amadeus = toolkit.get_tools()


template = """
Answer the following questions as best you can, but speaking as passionate travel expert. You have access to the following tools:

{tools}

당신의 임무는 user가 원활하게 여행을 계획하고 마칠 수 있도록 돕는 것입니다.
무조건 한국어로 답하십시오.
다음 context와 history를 통해 user가 입력한 내용을 바탕으로 여행을 계획할 수 있도록 지원하세요.
만약 user가 일정을 계획하기를 원한다면 user에게 몇 명과 함께 가는지, 누구와 가는지, 언제 가는지, 몇 박 몇 일 일정인지를 물어보고 이동거리를 고려한 일정을 세워주세요.
user가 원한 기간 동안의 완벽한 일정이 수립되어야 합니다.
해당 계획에는 항공편, 호텔 및 소요 예산이 포함됩니다.

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer,
user가 원한 기간 동안의 완벽한 일정이 수립되어야 합니다,
해당 계획에는 항공편, 호텔 및 소요 예산이 포함됩니다.
Final Answer: the final answer to the original input question, You must answer in Korean, Do not omit it and print it out as is


Begin! Remember to answer as a passionate and informative travel expert when giving your final answer.

Previous conversation history:
{history}

Question: {input}
{agent_scratchpad}
"""

template_with_history = """Answer the following questions as best you can, but speaking as passionate travel expert. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question, You must answer in Korean

Begin! Remember to answer as a passionate and informative travel expert when giving your final answer.

Previous conversation history:
{history}

Question: {input}
{agent_scratchpad}
"""
template += "\nHuman: {input}\nAssistant:"

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
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()+"\nHuman: "},
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


def search_hotel(input_text):
    search = DuckDuckGoSearchRun().run(f"site:agoda.com {input_text}")
    return search


def search_flight(input_text):
    search = DuckDuckGoSearchRun().run(f"site:skyscanner.com {input_text}")
    return search


def search_general(input_text):
    search = DuckDuckGoSearchRun().run(f"{input_text}")
    return search

async def async_search_online(input_text):
    async with aiohttp.ClientSession() as session:
        search = await DuckDuckGoSearchRun(session).arun(f"site:tripadvisor.com things to do{input_text}")
    return search.result

async def async_search_hotel(input_text):
    async with aiohttp.ClientSession() as session:
        search = await DuckDuckGoSearchRun(session).arun(f"site:agoda.com {input_text}")
    return search.result

async def async_search_flight(input_text):
    async with aiohttp.ClientSession() as session:
        search = await DuckDuckGoSearchRun(session).arun(f"site:skyscanner.com {input_text}")
    return search.result

async def async_search_general(input_text):
    async with aiohttp.ClientSession() as session:
        search = await DuckDuckGoSearchRun(session).arun(f"{input_text}")
    return search.result

memory = ConversationBufferWindowMemory(k=15)


def _handle_error(error) -> str:
    return str(error)[:50]


@cl.on_chat_start
async def agent():
    tools = [

        Tool(
            name="Search general",
            func=async_search_general,
            description="useful for when you need to answer general travel questions",
            coroutine=True
        ),
        Tool(
            name="Search tripadvisor",
            func=async_search_online,
            description="useful for when you need to answer trip plan questions",
            coroutine=True
        ),
        Tool(
            name="Search hotel",
            func=async_search_hotel,
            description="useful for when you need to answer hotel questions",
            coroutine=True
        ),

        Tool.from_function(
            name="Search flight and airport",
            func=lambda x: agent_executor2.invoke({"input": x}),
            description="useful for when you need to answer flight questions and airport questions"
        ),
        Tool.from_function(
            name="Search experience and poi",
            func=lambda x: all_in_1_agent({"input": x}),
            description="useful for when you need to answer travel experience questions or get the keyword about travel information"
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
    ]

    prompt = CustomPromptTemplate(
        template=template,
        tools=tools,
        # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
        # This includes the `intermediate_steps` variable because that is needed
        input_variables=["input", "intermediate_steps", "history"]
    )
    prompt_with_history = CustomPromptTemplate(
        template=template,
        tools=tools,
        # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
        # This includes the `intermediate_steps` variable because that is needed
        input_variables=["input", "intermediate_steps", "history"]
    )
    output_parser = CustomOutputParser()
    # memory = ConversationBufferWindowMemory(k=2)
    # llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
    # llm = ChatOpenAI(temperature=0.7, model="gpt-4-turbo")
    # LLM chain consisting of the LLM and a prompt
    llm_chain = LLMChain(llm=llm, prompt=prompt)

    prompt_for_amadeus1 = hub.pull("hwchase17/react-json")
    prompt_for_amadeus2 = """"
    Here is instructions to use "tool":
    departureDateTimeEarliest" and "departureDateTimeEarliest" MUST be the same date.
    You can only find one day's worth at a time.
    If you want to find flights for a multiple days, you have to use the "tool" N times for that period.
    If you're trying to search for round-trip flights, call this function for the outbound flight first, and then call again for the return flight.
    If there is no specific input for the year, it defaults to 2024.
    The currency must be converted to Korean Won before Final Answer."""
    agent2 = create_react_agent(
        llm,
        tool_amadeus,
        (prompt_for_amadeus1 + prompt_for_amadeus2),
        tools_renderer=render_text_description_and_args,
        output_parser=ReActJsonSingleInputOutputParser(),
    )
    agent_executor2 = AgentExecutor(
        agent=agent2,
        tools=tool_amadeus,
        verbose=True,
        handle_parsing_errors="Check your output and make sure it conforms, use the Action/Action Input syntax",
        max_iterations=5
    )

    tool_names = [tool.name for tool in tools]
    agent = LLMSingleActionAgent(
        llm_chain=llm_chain,
        output_parser=output_parser,
        stop=["\nObservation:"],
        allowed_tools=tool_names
    )
    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory,
                                                        handle_parsing_errors="Check your output and make sure it conforms, use the Action/Action Input syntax, If the current output is the final answer, add 'Final Answer:' at the beginning.",
                                                        max_iterations=20)

    async def async_agent_executor(input_text):
        return await agent_executor.arun(input_text)

    return async_agent_executor, memory