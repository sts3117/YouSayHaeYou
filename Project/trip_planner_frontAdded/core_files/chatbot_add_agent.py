import json
import requests
from langchain.tools import BaseTool, StructuredTool
from langchain.agents import AgentType, initialize_agent, AgentExecutor, create_openai_functions_agent, Tool
from langchain.chat_models import ChatOpenAI

from langchain import hub

from typing import Optional, Type
from langchain_core.pydantic_v1 import BaseModel, Field

from langchain_community.utilities.infobip import InfobipAPIWrapper

import os
import streamlit as st


class TravelPOIInput(BaseModel):
    """Get the keyword about travel information."""

    keyword: str = Field(...,
                         description="The city and state, e.g. San Francisco, CA")


class TravelPOITool(BaseTool):
    name = "search_poi"
    description = "Get the keyword about travel information"

    def _run(self, keyword: str):
        poi_results = get_pois(keyword)

        return poi_results

    def _arun(self, keyword: str):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = TravelPOIInput


def get_pois(keyword):
    """
    Query the get-poi API with the provided keyword.

    Parameters:
    keyword (str): The keyword for searching the position of interest.

    Returns:
    dict: The response from the API, should comply with getPoiResponse schema.
    """
    url = "https://nextjs-chatgpt-plugin-starter.vercel.app/api/get-poi"
    headers = {'Content-Type': 'application/json'}

    # The request data should comply with searchPoiRequest schema
    data = {"keyword": keyword}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}


class TravelExpInput(BaseModel):
    """Get the keyword about travel experience."""

    keyword: str = Field(...,
                         description="The city and state, e.g. San Francisco, CA")


class TravelExpTool(BaseTool):
    name = "search_experience"
    description = "Get the keyword about travel experience"

    def _run(self, keyword: str):
        exp_results = get_experience(keyword)
        return exp_results

    def _arun(self, keyword: str):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = TravelExpInput


def get_experience(keyword):
    api_url = "https://nextjs-chatgpt-plugin-starter.vercel.app/api/get-experience"
    headers = {'Content-Type': 'application/json'}

    data = {
        "keyword": keyword
    }

    response = requests.post(api_url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()
    else:
        return None


def all_in_1_agent(input):
    model = ChatOpenAI(model="gpt-4-turbo")
    tools = [TravelPOITool(), TravelExpTool()]
    open_ai_agent = initialize_agent(tools,
                                     model,
                                     agent=AgentType.OPENAI_FUNCTIONS,
                                     verbose=True)
    tool_result = open_ai_agent.run(input)

    return tool_result


def sms_or_email():
    os.environ["INFOBIP_API_KEY"] = st.secrets["INFOBIP_API_KEY"]
    os.environ["INFOBIP_BASE_URL"] = st.secrets["INFOBIP_BASE_URL"]
    instructions = "You are the messenger. Convey exactly what the user wants to convey."
    base_prompt = hub.pull("langchain-ai/openai-functions-template")
    prompt = base_prompt.partial(instructions=instructions)
    llm = ChatOpenAI(temperature=0)

    class EmailInput(BaseModel):
        body: str = Field(description="Email body text")
        to: str = Field(description="Email address to send to. Example: email@example.com")
        sender: str = Field(description="Email address to send from, must be 'imsi@imsi.com'")
        subject: str = Field(description="Email subject")
        channel: str = Field(description="Email channel, must be 'email'")

    infobip_api_wrapper: InfobipAPIWrapper = InfobipAPIWrapper(infobip_api_key=os.environ["INFOBIP_API_KEY"], infobip_base_url=os.environ["INFOBIP_BASE_URL"])
    infobip_tool = StructuredTool.from_function(
        name="infobip_email",
        description="Send Email via Infobip. If you need to send email, use infobip_email",
        func=infobip_api_wrapper.run,
        args_schema=EmailInput,
    )
    tools = [infobip_tool]

    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
    )

    return agent_executor
