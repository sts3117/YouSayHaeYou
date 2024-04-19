# memo

[Home](https://docs.crewai.com/)

## 24.04.17

### pdf 대신 csv 넣는 방법

```
from crewai_tools import CSVSearchTool

csv_tool = CSVSearchTool(csv='conv.csv')

```

- [Q] csv나 pdf 데이터를 통해 추천하는 무언가가 없는 느낌? 순수하게 search api를 통해 플래닝을 하는 것 같음

---

## 24.04.18

> 도큐먼트를 조금 더 자세히 봐서 개선점을 찾아야할 것 같음
> 
- 메모리 시스템이 있음
    - Short-Term Memory
        - 최근 상호 작용 및 결과를 임시로 저장하여 상담원이 현재 상황과 관련된 정보를 기억하고 활용할 수 있도록 합니다.
    - Long-Term Memory
        - 과거 실행에서 얻은 귀중한 통찰력과 학습 내용을 보존하여 상담원이 시간이 지남에 따라 지식을 구축하고 개선할 수 있도록 합니다
    - Entity Memory
        - 작업 중에 접하는 개체(사람, 장소, 개념)에 대한 정보를 캡처하고 구성하여 더 깊은 이해와 관계 매핑을 촉진합니다.
    - Contextual Memory
        - 상호작용의 맥락을 유지하여 일련의 작업이나 대화에 대한 상담원 응답의 일관성과 관련성을 지원합니다.
    

> 코드 예시
> 

```python
from crewai import Crew, Agent, Task, Process

# Assemble your crew with memory capabilities
my_crew = Crew(
    agents=[...],
    tasks=[...],
    process=Process.sequential,
    memory=True,
    verbose=True
```

- 계층적, 순차적 프로세스 구조에 대해서도 고민해봐야 함
---

# 0419
## [오후]

[https://imsi-0419.streamlit.app](https://imsi-0419.streamlit.app)

### 웹 內 발견된 문제점 및 개선사항

- 구글맵 API(~~틈만 나면 오류남~~😡)
    - 대중교통 길찾기 외에는 한글 지원이 안됨
    - 또한 어떤 길찾기든, 지도에 경로만 찍어주지 구체적인 대중교통 종류라던지, 시간에 대한 언급이 없음
- 스크롤 맨 위로 올리는 기능
- 지역을 바꾸거나 그랬을 때, 이전 질문 내용이 그대로 유지됨, 즉 질문했던 내용을 초기화한다던지, 새로운 탭을 제공한다던지 하는게 미존재
- Gemini → 글렀음.
- Claude → 실험 중
- 

### CODE

```python
llm = ChatAnthropic(temperature=0.7, model_name='claude-3-sonnet-20240229') # sonnet , opu

```
