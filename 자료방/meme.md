## pdf 대신 csv 넣는 방법

```
from crewai_tools import CSVSearchTool

csv_tool = CSVSearchTool(csv='conv.csv')
```

> 의문점: csv나 pdf 데이터를 통해 추천하는 무언가가 없는 느낌? 순수하게 search api를 통해 플래닝을 하는 것 같음

---
