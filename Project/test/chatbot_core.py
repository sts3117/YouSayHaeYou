import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.prompts import StringPromptTemplate
from langchain import OpenAI, SerpAPIWrapper, LLMChain
from typing import List, Union
from langchain.schema import AgentAction, AgentFinish, OutputParserException
import re
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import DuckDuckGoSearchRun
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from functools import lru_cache

import os, time
import chainlit as cl


# os.environ["OPENAI_API_KEY"] = "<openai-key>"
# OpenAI.api_key = os.environ["OPENAI_API_KEY"]
ChatGoogleGenerativeAI.google_api_key = os.environ["GOOGLE_API_KEY"]

template = """Gemini Pro, you will now take on the role of a passionate travel expert and do your best to answer the questions. You have access to the following tools: {tools}
Your task is to help the user smoothly plan and complete their trip. If the question is in English, answer in English first, then translate it into Korean. If the question is in Korean, answer directly in Korean.
Based on the following context and conversation history, support the user in planning their trip according to their input.
If the user wants to plan an itinerary, confirm the following:

How many people are traveling together?
Who are they traveling with? (partner, family, friends, etc.)
When is the travel period?
How many nights and days is the trip?

After confirmation, create an optimal itinerary considering the travel distances. The perfect itinerary for the user's desired duration should be prepared with the following contents:

Daily subtitles highlighting the main theme or activities
Detailed transportation information (flights, trains, rental cars, etc.) with specific routes and estimated costs
Accommodation details (hotel names, locations, amenities) with estimated nightly rates
Estimated daily budget considering activities, meals, shopping, etc.

Use the following format:
Question: The question you need to answer
Thought: Always consider what actions to take
Action: The action to take, should be one of [{tool_names}]
Action Input: The input for the action
Observation: The result of the action
... (This Thought/Action/Action Input/Observation can repeat N times)
Thought: Now I know the final answer. The perfect itinerary for the user's desired duration should include daily subtitles, detailed transportation, accommodations with estimated costs, and daily budget.
Final Answer: The final answer to the original question. If the question is in English, translate it into Korean; if it's in Korean, provide it in Korean as is.
Begin! When providing the final answer, don't forget to answer as a passionate and informative travel expert.
Previous conversation history: {history}
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

@lru_cache(maxsize=128)
def search_online(input_text):
    search = DuckDuckGoSearchRun().run(f"site:tripadvisor.com things to do{input_text}")
    return search if search else "No relevant search results found on TripAdvisor."

@lru_cache(maxsize=128)
def search_hotel(input_text):
    search = DuckDuckGoSearchRun().run(f"site:booking.com {input_text}")
    return search if search else "No relevant hotel search results found on Booking.com."

@lru_cache(maxsize=128)
def search_flight(input_text):
    search = DuckDuckGoSearchRun().run(f"site:skyscanner.com {input_text}")
    return search if search else "No relevant flight search results found on Skyscanner."

@lru_cache(maxsize=128)
def search_general(input_text):
    search = DuckDuckGoSearchRun().run(f"{input_text}")
    return search if search else "No relevant general search results found."





def _handle_error(error) -> str:
    return str(error)[:50]


@cl.on_chat_start
def agent():
    tools = [

        Tool(
            name="Search general",
            func=search_general,
            description="useful for when you need to answer general travel questions"
        ),
        Tool(
            name="Search tripadvisor",
            func=search_online,
            description="useful for when you need to answer trip plan questions"
        ),
        Tool(
            name="Search booking",
            func=search_hotel,
            description="useful for when you need to answer hotel questions"
        ),
        Tool(
            name="Search flight",
            func=search_flight,
            description="useful for when you need to answer flight questions"
        )
    ]

    prompt = CustomPromptTemplate(
        template=template,
        tools=tools,
        input_variables=["input", "intermediate_steps", "history"]
    )
    memory = ConversationBufferWindowMemory(k=4)
    output_parser = CustomOutputParser()
    # llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
    llm = ChatGoogleGenerativeAI(model="gemini-pro")
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    tool_names = [tool.name for tool in tools]
    agent = LLMSingleActionAgent(
        llm_chain=llm_chain,
        output_parser=output_parser,
        stop=["\nObservation:"],
        allowed_tools=tool_names
    )
    start_time = time.time()
    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory, handle_parsing_errors="Check your output and make sure it conforms, use the Action/Action Input syntax", max_iterations=10)
    end_time = time.time()  # 종료 시간 기록
    execution_time = end_time - start_time
    print(f"Agent Execution Time: {execution_time:.2f} seconds")

    return agent_executor