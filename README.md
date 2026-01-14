# 🍷 CJ Young Sommelier (CJ Young 소믈리에)

> **AI-Driven Liquor Analytics & Flavor Prediction Platform**
> 데이터 기반의 주류 성분 분석, 머신러닝을 이용한 향미 예측, 그리고 Gemini LLM을 활용한 자동 시음 리포트 생성 시스템입니다.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Google%20Gemini-Pro-8E75B2?style=flat&logo=google&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-ML-F7931E?style=flat&logo=scikit-learn&logoColor=white)

## 🎯 Project Overview (프로젝트 개요)

이 프로젝트는 주류 양조 및 품질 관리 과정에서 발생하는 데이터를 디지털화하고, AI를 통해 인사이트를 도출하는 것을 목표로 합니다.
NotebookLM을 통해 구축된 **화학 성분-향미 지식 베이스(Flavor Knowledge Base)**를 기반으로 분석의 깊이를 더합니다.

---

## 📂 Feature & Page Guide (기능 및 메뉴 설명)

이 어플리케이션은 총 5개의 핵심 기능을 수행하며, 각 기능은 독립된 페이지로 구성됩니다.

### 1️⃣ 성분 데이터 트래킹 (Lot Tracking & Data Entry)
* **기능:** 주류 제품의 LOT별 성분 변화를 기록하고 관리합니다.
* **입력 방식:**
    * **Manual Input:** 도수(ABV), 산도(pH), 비중, 당도 등을 직접 입력.
    * **Batch Upload:** GCMS 결과 테이블 등 대량의 실험 데이터를 CSV/Excel 형태로 업로드하여 일정한 포맷으로 DB에 적재합니다.
* **핵심 가치:** 흩어져 있는 실험 데이터를 하나의 표준화된 DB로 통합 관리합니다.

### 2️⃣ 성분 변화 분석 및 예측 (Analysis & Prediction)
* **기능:** 특정 제품의 분석 시점에 따른 성분 변화 추이를 시각화합니다.
* **시각화:** Plotly를 활용하여 성분별 변화 그래프와 상세 테이블을 제공합니다.
* **예측(ML):** Scikit-learn 회귀 모델을 통해 향후 숙성 과정에서 성분 수치가 어떻게 변할지 예측값을 제시합니다.

### 3️⃣ 관능 평가 및 정보 입력 (Sensory Scoring)
* **기능:** 실제 시음 데이터를 디지털화하는 과정입니다.
* **입력 항목:**
    * **제품 정보:** 제품명, 담당자명, 시음일 등 메타 데이터.
    * **성분 첨부:** 해당 시점의 도수(ABV), 산도(pH), 비중, 당도 등의 실험 데이터와, GCMS 성분 데이터 매핑.
    * **관능 점수:** 과실향(Fruity), 단맛(Sweet), 쓴맛(Bitter), 바디감(Body) 등 정해진 항목에 대한 점수(0-10) 입력.

### 4️⃣ AI 종합 향미 리포트 (AI Flavor Report)
* **기능:** 수집된 데이터(1~3번)와 지식 베이스(5번)를 결합하여 Gemini LLM이 종합 리포트를 작성합니다.
* **프로세스:**
    1.  특정 LOT의 현재 성분 상태와 ML 모델이 예측한 미래 시점 데이터를 로드합니다.
    2.  사용자가 입력한 관능 점수와 비교 분석합니다.
    3.  **Index Knowledge:** '에틸 아세테이트가 증가하여 과실향이 풍부해질 것'과 같은 화학적 근거가 포함된 문장을 생성합니다.
* **출력:** 소믈리에가 작성한 듯한 서술형 리포트 및 요약 인사이트.

### 5️⃣ 성분 인덱스 관리 (Flavor Index Manager)
* **기능:** 각 화학 성분이 어떤 맛과 향의 캐릭터(뉘앙스)를 갖는지 관리하는 사전(Dictionary) 메뉴입니다.
* **NotebookLM 연동:** 논문, 서적 등에서 추출한 전문 지식을 바탕으로 성분별 특징(Descriptor)을 서술형으로 관리합니다.
* **역할:** AI 리포트 생성 시 RAG(검색 증강 생성)의 기초 데이터로 활용되어 환각(Hallucination)을 줄이고 전문성을 높입니다.

---

## 🏗️ Project Structure (프로젝트 구조)

```text
cj_young_sommelier/
├── 📂 src/                  # 🧠 핵심 비즈니스 로직
│   ├── database.py          # SQLite DB 및 스키마 관리
│   ├── analysis.py          # 데이터 분석 및 예측 모델링
│   └── llm_engine.py        # Gemini API 및 프롬프트 관리
│
├── 📂 pages/                # 📱 Streamlit 메뉴 (위 기능 1~5에 대응)
│   ├── 1_📝_Data_Entry.py   # [기능 1] 데이터 입력 및 업로드
│   ├── 2_📈_Analysis.py     # [기능 2] 성분 변화 차트 및 예측
│   ├── 3_👅_Sensory.py      # [기능 3] 관능 평가 점수 기록
│   ├── 4_📑_AI_Report.py    # [기능 4] AI 리포트 생성
│   └── 5_📚_Flavor_Index.py # [기능 5] 성분 향미 인덱스 관리
│
├── 📂 data/                 # 💾 데이터 저장소 (DB & Excel)
├── 📂 knowledge_base/       # 🧠 NotebookLM 추출 지식 (JSON/Markdown)
├── main.py                  # 🏠 대시보드 홈
└── requirements.txt         # 📦 패키지 목록
