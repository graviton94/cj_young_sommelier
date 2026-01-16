# 🍷 CJ Young Sommelier

AI 기반 주류 분석 및 향미 예측 플랫폼. LOT별 화학 성분 변화를 추적하고, 머신러닝을 사용하여 관능 점수를 예측하며, Gemini LLM을 통해 시음 리포트를 생성합니다.

## 기능

- **📊 LOT 데이터 관리**: 주류 배치의 화학 성분 데이터 추적 및 관리
- **🎯 ML 예측**: 회귀 모델을 사용한 관능 점수(향, 맛, 여운, 종합) 예측
- **👃 관능 분석**: 상세한 관능 프로파일 작성 및 다중 LOT 비교
- **🤖 AI 리포트**: Google Gemini AI를 사용한 종합적인 향미 리포트 생성

## 기술 스택

- **Frontend**: Streamlit
- **Database**: SQLite with SQLAlchemy ORM
- **Machine Learning**: scikit-learn, pandas, numpy
- **Visualization**: Plotly
- **AI**: Google Gemini API

## 프로젝트 구조

```
cj_young_sommelier/
├── main.py                 # Streamlit 앱 진입점
├── data/                   # SQLite 데이터베이스 및 ML 모델
│   ├── liquor_analytics.db (자동 생성됨)
│   └── models/             (자동 생성됨)
├── src/                    # 핵심 모듈
│   ├── __init__.py
│   ├── database.py        # SQLite/SQLAlchemy 데이터베이스 계층
│   ├── analysis.py        # 예측을 위한 ML 모델
│   └── llm.py             # Google Gemini 통합
├── pages/                  # Streamlit 페이지
│   ├── 1_Data_Entry.py    # LOT 데이터 입력 및 관리
│   ├── 2_Prediction.py    # 관능 점수 예측
│   ├── 3_Sensory.py       # 관능 분석 및 프로파일링
│   └── 4_Report.py        # AI 기반 향미 리포트
├── knowledge_base/         # 참조 자료
├── requirements.txt        # Python 의존성
├── .env.template          # 환경 변수 템플릿
└── .gitignore             # Git 제외 규칙
```

## 설치 방법

1. **저장소 클론**:
   ```bash
   git clone https://github.com/graviton94/cj_young_sommelier.git
   cd cj_young_sommelier
   ```

2. **가상 환경 생성** (권장):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows의 경우: venv\Scripts\activate
   ```

3. **의존성 설치**:
   ```bash
   pip install -r requirements.txt
   ```

4. **환경 변수 설정**:
   ```bash
   cp .env.template .env
   # .env 파일을 수정하여 GEMINI_API_KEY를 추가하세요
   ```

5. **Gemini API 키 발급**:
   - [Google AI Studio](https://makersuite.google.com/app/apikey) 방문
   - API 키 생성
   - `.env` 파일에 추가

## 사용 방법

1. **애플리케이션 시작**:
   ```bash
   streamlit run main.py
   ```

2. **웹 인터페이스 접속**:
   - 브라우저에서 `http://localhost:8501` 열기

3. **워크플로우**:
   - **Step 1**: "데이터 입력" 페이지에서 LOT 데이터 추가
   - **Step 2**: (선택 사항) 관능 점수 입력 또는 예측을 위한 ML 모델 훈련
   - **Step 3**: "예측" 페이지에서 관능 점수 예측
   - **Step 4**: "관능 분석" 페이지에서 관능 프로파일 작성
   - **Step 5**: "리포트" 페이지에서 AI 리포트 생성

## 기능 가이드

### 📊 데이터 입력
- 화학 성분 데이터 입력 (알코올 도수, 산도, 당 함량, 타닌, 에스터, 알데히드)
- 실제 관능 점수 추가 (있는 경우)
- LOT 기록 조회, 수정 및 삭제
- CSV로 데이터 내보내기

### 🎯 예측
- ML 모델 훈련 (Random Forest, Gradient Boosting, Linear, Ridge, Lasso)
- 화학 성분을 기반으로 관능 점수 예측
- 특성 중요도 분석
- 상관관계 행렬 보기

### 👃 관능 분석
- 상세 관능 프로파일 작성 (색상, 향, 향미, 입안감, 여운)
- 다중 LOT 나란히 비교
- 레이더 차트로 관능 데이터 시각화
- 여러 시음자의 시음 노트 추적

### 📝 AI 리포트
- Gemini AI로 종합적인 향미 리포트 생성
- 화학 성분 인사이트 확보
- 다중 LOT 비교 분석 생성
- 관능 묘사어 자동 생성

## 머신러닝 모델

이 플랫폼은 여러 회귀 알고리즘을 지원합니다:

- **Random Forest**: 앙상블 방법, 비선형 관계에 좋음
- **Gradient Boosting**: 순차적 앙상블, 종종 더 높은 정확도 제공
- **Linear Regression**: 간단한 기준 모델
- **Ridge Regression**: L2 정규화가 포함된 선형 모델
- **Lasso Regression**: L1 정규화가 포함된 선형 모델

모델은 다음을 예측하기 위해 화학적 특성으로 훈련됩니다:
- 향 점수 (0-100)
- 맛 점수 (0-100)
- 여운 점수 (0-100)
- 종합 점수 (0-100)

## 데이터베이스 스키마

### LOTData 테이블
- LOT 식별 (lot_number, product_name)
- 화학 성분 (alcohol_content, acidity, sugar_content, tannin_level, ester_concentration, aldehyde_level)
- 관능 점수 (aroma_score, taste_score, finish_score, overall_score)
- 메타데이터 (production_date, entry_date, notes)

### SensoryProfile 테이블
- 상세 관능 설명 (color, aroma_notes, flavor_notes, mouthfeel, finish)
- 시음자 정보 (taster_name, tasting_date)
- AI 생성 리포트

## 기여하기

기여는 언제나 환영합니다! Pull Request를 제출해 주세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 감사의 말

- Streamlit으로 제작
- Google Gemini AI 구동
- scikit-learn을 사용한 머신러닝
