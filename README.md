# 🍷 CJ Young Sommelier

AI-driven Liquor Analytics & Flavor Prediction Platform. Tracks LOT-specific chemical changes, predicts sensory scores using ML, and generates tasting reports via Gemini LLM.

## Features

- **📊 LOT Data Management**: Track and manage chemical composition data for liquor batches
- **🎯 ML Predictions**: Predict sensory scores (aroma, taste, finish, overall) using regression models
- **👃 Sensory Analysis**: Create detailed sensory profiles and compare multiple LOTs
- **🤖 AI Reports**: Generate comprehensive flavor reports using Google Gemini AI

## Tech Stack

- **Frontend**: Streamlit
- **Database**: SQLite with SQLAlchemy ORM
- **Machine Learning**: scikit-learn, pandas, numpy
- **Visualization**: Plotly
- **AI**: Google Gemini API

## Project Structure

```
cj_young_sommelier/
├── main.py                 # Streamlit app entry point
├── data/                   # SQLite database and ML models
│   ├── liquor_analytics.db (auto-generated)
│   └── models/             (auto-generated)
├── src/                    # Core modules
│   ├── __init__.py
│   ├── database.py        # SQLite/SQLAlchemy database layer
│   ├── analysis.py        # ML models for prediction
│   └── llm.py             # Google Gemini integration
├── pages/                  # Streamlit pages
│   ├── 1_Data_Entry.py    # LOT data input and management
│   ├── 2_Prediction.py    # Sensory score prediction
│   ├── 3_Sensory.py       # Sensory analysis and profiling
│   └── 4_Report.py        # AI-powered flavor reports
├── knowledge_base/         # Reference materials
├── requirements.txt        # Python dependencies
├── .env.template          # Environment variables template
└── .gitignore             # Git ignore rules
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/graviton94/cj_young_sommelier.git
   cd cj_young_sommelier
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.template .env
   # Edit .env and add your GEMINI_API_KEY
   ```

5. **Get a Gemini API key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an API key
   - Add it to your `.env` file

## Usage

1. **Start the application**:
   ```bash
   streamlit run main.py
   ```

2. **Access the web interface**:
   - Open your browser to `http://localhost:8501`

3. **Workflow**:
   - **Step 1**: Add LOT data in the "Data Entry" page
   - **Step 2**: (Optional) Enter sensory scores or train ML model for predictions
   - **Step 3**: Use "Prediction" page to predict sensory scores
   - **Step 4**: Create sensory profiles in "Sensory" page
   - **Step 5**: Generate AI reports in "Report" page

## Features Guide

### 📊 Data Entry
- Input chemical composition data (ABV, pH, sugar, tannin, esters, aldehydes)
- Add actual sensory scores (if available)
- View, edit, and delete LOT records
- Export data as CSV

### 🎯 Prediction
- Train ML models (Random Forest, Gradient Boosting, Linear, Ridge, Lasso)
- Predict sensory scores from chemical composition
- Analyze feature importance
- View correlation matrices

### 👃 Sensory Analysis
- Create detailed sensory profiles (color, aroma, flavor, mouthfeel, finish)
- Compare multiple LOTs side-by-side
- Visualize sensory data with radar charts
- Track tasting notes by multiple tasters

### 📝 AI Reports
- Generate comprehensive flavor reports with Gemini AI
- Get chemical composition insights
- Create comparative analyses of multiple LOTs
- Generate sensory descriptors automatically

## Machine Learning Models

The platform supports multiple regression algorithms:

- **Random Forest**: Ensemble method, good for non-linear relationships
- **Gradient Boosting**: Sequential ensemble, often higher accuracy
- **Linear Regression**: Simple baseline model
- **Ridge Regression**: Linear with L2 regularization
- **Lasso Regression**: Linear with L1 regularization

Models are trained on chemical features to predict:
- Aroma Score (0-100)
- Taste Score (0-100)
- Finish Score (0-100)
- Overall Score (0-100)

## Database Schema

### LOTData Table
- LOT identification (lot_number, product_name)
- Chemical composition (alcohol_content, acidity, sugar_content, tannin_level, ester_concentration, aldehyde_level)
- Sensory scores (aroma_score, taste_score, finish_score, overall_score)
- Metadata (production_date, entry_date, notes)

### SensoryProfile Table
- Detailed sensory descriptions (color, aroma_notes, flavor_notes, mouthfeel, finish)
- Taster information (taster_name, tasting_date)
- AI-generated reports

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Acknowledgments

- Built with Streamlit
- Powered by Google Gemini AI
- Machine learning with scikit-learn
