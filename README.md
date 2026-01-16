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
├── src/                    # 핵심 모듈
├── pages/                  # Streamlit 페이지 (1~7)
│   ├── 1_Data_Entry.py     # 데이터 입력 및 관리
│   ├── 2_Flavor_Analysis.py # 향미 상세 분석 (정밀/시제품)
│   ├── 3_Analysis_Result.py # 통합 분석 결과 조회
│   ├── 4_Prediction.py      # 품질 예측 (ML)
│   ├── 5_Sensory.py         # 관능 평가
│   ├── 6_Report.py          # AI 리포트 (Gemini)
│   └── 7_Settings.py        # 시스템 설정
├── requirements.txt        # Python 의존성
├── .env.template          # 환경 변수 템플릿
├── Dockerfile              # [NEW] 배포용 도커 설정
└── README.md
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
   - **Step 1**: "데이터 입력"에서 신규 원료/LOT 정보 등록
   - **Step 2**: "향미 상세 분석"에서 정밀 분석 데이터(GCMS 등) 입력
   - **Step 3**: "전체 분석 결과"에서 통합 히스토리 확인
   - **Step 4**: "품질 예측"에서 ML 모델을 통한 관능 점수 예측
   - **Step 5**: "관능 평가"에서 상세 관능 프로파일링
   - **Step 6**: "AI 리포트"에서 Gemini 기반 종합 리포트 생성

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

## 배포 방법

### 1. 로컬 네트워크 배포 (사내 서버)
동일한 네트워크망 내 다른 사용자가 접속하게 하려면 서버 IP를 지정하여 실행합니다.
```bash
streamlit run main.py --server.address 0.0.0.0 --server.port 8501
```

### 2. Docker 배포
컨테이너 환경에서 안정적으로 배포하려면 제공된 Dockerfile을 사용합니다.
```bash
# 이미지 빌드
docker build -t cj-sommelier .

# 컨테이너 실행 (데이터 보존을 위한 볼륨 마운트 권장)
docker run -d -p 8501:8501 -v $(pwd)/data:/app/data --name sommelier-app cj-sommelier
```

### 3. Streamlit Community Cloud
GitHub 저장소와 연동하여 가장 간편하게 배포할 수 있습니다.
- [Streamlit Cloud](https://streamlit.io/cloud) 접속 후 GitHub 레포지토리 연결
- **Advanced settings**에서 `GEMINI_API_KEY`를 Secrets에 등록
