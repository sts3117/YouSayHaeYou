# 환경변수에서 api키 가져오기
import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY=os.getenv("TAVILY_API_KEY")

# crewAI 라이브러리에서 필요한 클래스 가져오기
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

import gradio as gr

#llm
llm = ChatGoogleGenerativeAI(model='gemini-1.5-pro-latest', temperature=0, api_key=GOOGLE_API_KEY)

# web search tools
from langchain_community.tools.tavily_search import TavilySearchResults
search_tool = TavilySearchResults(api_key=TAVILY_API_KEY)

# PDF Search Tool
from crewai_tools import PDFSearchTool
pdf_tool = PDFSearchTool(pdf='2024 서울관광안내서_KR.pdf')


def run_trip_crew(topic):
    # Agent
    tour_planning_expert = Agent(
    role='Tour Planning Expert',
    goal=f'Select the best locations within {topic} based on weather, season, prices, and tourist preferences',
    backstory='An expert in analyzing local data to pick ideal destinations within destination',
    verbose=True,
    tools=[search_tool, pdf_tool],
    allow_delegation=False,
    llm=llm,
    max_iter=3,
    max_rpm=10,
    )

    local_expert = Agent(
    role='Seoul Local Expert',
    goal=f'Provide the BEST insights about the selected locations in {topic}',
    backstory="""A knowledgeable local guide with extensive information
    about destinations's attractions, customs, and hidden gems""",
    verbose=True,
    tools=[search_tool, pdf_tool],
    allow_delegation=False,
    llm=llm,
    max_iter=3,
    max_rpm=10,
    )

    # 여행 일정 짜줌
    travel_concierge = Agent(
    role='Seoul Custom Travel Concierge',
    goal=f"Create the most amazing travel itineraries for {topic} including budget and packing suggestions",
    backstory="Specialist in travel planning and logistics with extensive experience",
    verbose=True,
    ls=[search_tool],
    allow_delegation=False,
    llm=llm,
    )

    # Tasks
    seoul_location_selection_task = Task(
        description=f'Identify the best locations within {topic} for visiting based on current weather, season, and tourist preferences. Explain in Korean Hangul',
        agent=tour_planning_expert,
        expected_output=f'A list of recommended locations in {topic}, including reasons for each selection'
    )


    seoul_local_insights_task = Task(
        description=f'Provide detailed insights and information about selected locations in {topic}, including attractions, customs, and hidden gems. Explain in Korean Hangul',
        agent=local_expert,
        expected_output='Comprehensive information about each location, including what to see, do, and eat'
    )

    seoul_travel_itinerary_task = Task(
        description='Create a detailed travel itinerary for Seoul that includes budgeting, packing suggestions, accommodations, and transportation. Explain in Korean Hangul',
        agent=travel_concierge,
        expected_output='A complete travel plan for my destination, including a day-by-day itinerary, budget estimates, and packing list. Key locations and place names should be provided in Korean'
    )

    # Crew 생성  
    trip_crew = Crew(
        agents=[tour_planning_expert, local_expert, travel_concierge],
        tasks=[seoul_location_selection_task, seoul_local_insights_task, seoul_travel_itinerary_task],
        process=Process.hierarchical,
        manager_llm=ChatGoogleGenerativeAI(model='gemini-1.5-pro-latest') 
    )

    # Process 실행
    result = trip_crew.kickoff()
    return result


def process_query(message, history):
    return run_trip_crew(message)

# gradio chat interface
if __name__ =='__main__':
    app = gr.ChatInterface(
        fn=process_query,
        title='Travel planning bot',
        description="여행하고자 하는 지역의 여행계획을 만들어드립니다"
    )

    app.launch()