import asyncio
from functools import lru_cache

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

import os, time
import chainlit as cl
import streamlit as st

template = """Answer the following questions as best you can, speaking as a passionate travel expert. You have access to the following tools:

{tools}

Your task is to help the user smoothly plan and complete their trip. If the question is in English, answer in English first, then translate the final answer into Korean. If the question is in Korean, answer directly in Korean.

Based on the given context and conversation history, assist the user in planning their trip according to their input. Analyze the question to extract relevant keywords and search for useful information using the available tools.

If key details are missing for creating an itinerary, politely ask the user for that information using the following format:
Action: Request more information
Action Input: Politely ask the user for the missing details needed to create an itinerary, such as destination, number of travelers, travel dates, trip duration, budget range, and specific preferences.

Once you have enough information, create an optimal day-by-day itinerary considering travel distances, transportation, and the user's preferences. Propose the perfect itinerary for the user's desired duration, including:
- Flight/transportation information
- Accommodation recommendations
- Key activities and sightseeing spots for each day
- Restaurant/dining suggestions
- Estimated budget breakdown

Use the following format for your response:
Question: The question you need to answer
Thought: Examine the question and the given context, and consider which tools could provide relevant information
Action: Choose from the available tools: {tool_names}
Action Input: Extract keywords from the question or context that can be used as input for the selected tool
Observation: Summarize the relevant information obtained from the tool
... (This Thought/Action/Action Input/Observation can repeat N times)
Thought: Determine if you have enough information to propose an itinerary. If not, request more information from the user.
Final Answer: Based on the information provided, here is the proposed itinerary for your trip:

Day 1: Detailed itinerary for day 1
Day 2: Detailed itinerary for day 2
...
Day N: Detailed itinerary for final day

Estimated Trip Budget: Breakdown of estimated expenses
Transportation Details: Recommended flight/train/car rental details
Accommodation Recommendations: Suggested hotels/Airbnbs for each location

I hope this itinerary matches your travel style and preferences! Let me know if you have any other questions. I'm here to help you have an amazing trip!

(If the original question is in English, translate the full itinerary into Korean after the English version. If the original question is in Korean, provide the itinerary in Korean only.)

Begin! Engage in conversation as needed to gather missing details before proposing the itinerary. Respond as a passionate, knowledgeable, and helpful travel expert.

Previous conversation history:
{history}

Question: {input}
{agent_scratchpad}"""

# Set up a prompt template
class CustomPromptTemplate(StringPromptTemplate):
    template: str
    tools: List[Tool]

    def format(self, **kwargs) -> str:
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        return self.template.format(**kwargs)

class CustomOutputParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        if "Final Answer:" in llm_output:
            return AgentFinish(
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise OutputParserException(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)

@lru_cache(maxsize=128)
def search_online(input_text):
    ddg = DuckDuckGoSearchRun()
    search = ddg.run(f"site:tripadvisor.com {input_text}")
    return search if search else "No relevant search results found on TripAdvisor."

@lru_cache(maxsize=128)
def search_hotel(input_text):
    ddg = DuckDuckGoSearchRun()  
    search = ddg.run(f"site:booking.com {input_text}")
    return search if search else "No relevant hotel search results found on Booking.com."

@lru_cache(maxsize=128)
def search_flight(input_text):
    ddg = DuckDuckGoSearchRun()
    search = ddg.run(f"site:skyscanner.com {input_text}")
    return search if search else "No relevant flight search results found on Skyscanner."

@lru_cache(maxsize=128)
def search_general(input_text):
    ddg = DuckDuckGoSearchRun()
    search = ddg.run(f"{input_text}")
    return search if search else "No relevant general search results found."

memory = ConversationBufferWindowMemory(k=4)

def _handle_error(error) -> str:
    return str(error)[:50]

async def async_agent_executor(agent, tools, memory, query):
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True,
        memory=memory,
        handle_parsing_errors=True,
        max_iterations=10,
    )
    result = await asyncio.to_thread(agent_executor.run, query)
    return result

@cl.on_chat_start
def agent():
    tools = [
        Tool(name="Search general", func=search_general, description="useful for when you need to answer general travel questions"),
        Tool(name="Search tripadvisor", func=search_online, description="useful for when you need to answer trip plan questions"),  
        Tool(name="Search booking", func=search_hotel, description="useful for when you need to answer hotel questions"),
        Tool(name="Search flight", func=search_flight, description="useful for when you need to answer flight questions"),
    ]

    prompt = CustomPromptTemplate(
        template=template,
        tools=tools,
        input_variables=["input", "intermediate_steps", "history"]
    )
    
    output_parser = CustomOutputParser()
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3, max_output_tokens=1024)
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    tool_names = [tool.name for tool in tools]
    
    agent = LLMSingleActionAgent(
        llm_chain=llm_chain,
        output_parser=output_parser,
        stop=["\nObservation:"],
        allowed_tools=tool_names
    )
    
    async def run_agent(query):
        response = await async_agent_executor(agent, tools, memory, query)
        return response
    
    return run_agent