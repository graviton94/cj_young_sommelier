# Quick Start Guide

## Getting Started in 5 Minutes

### 1. Installation

```bash
# Clone and navigate to the repository
cd cj_young_sommelier

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key (Optional for AI Reports)

```bash
# Copy the template
cp .env.template .env

# Edit .env and add your Gemini API key
# Get one from: https://makersuite.google.com/app/apikey
```

### 3. Run the Application

```bash
streamlit run main.py
```

The application will open in your browser at `http://localhost:8501`

## First Steps

### Add Your First LOT

1. Navigate to **📊 Data Entry** in the sidebar
2. Fill in the LOT information:
   - LOT Number: `LOT-001`
   - Product Name: `Premium Whiskey`
   - Chemical composition values
3. Click **💾 Save LOT Data**

### Predict Sensory Scores

1. Add at least 5 LOTs with complete sensory scores
2. Go to **🎯 Prediction**
3. Click on **🏋️ Train Model** tab
4. Click **Train Model** button
5. Switch to **🔮 Make Predictions** tab
6. Select a LOT or enter manual values
7. Click **Predict Sensory Scores**

### Generate AI Reports

1. Go to **📝 Report** page
2. Configure your Gemini API key (if not in .env)
3. Select a LOT
4. Click **🤖 Generate AI Flavor Report**

## Example Workflow

```
1. Add LOT data → Data Entry page
2. Add sensory profiles → Sensory page
3. Train ML model → Prediction page
4. Predict new scores → Prediction page
5. Generate reports → Report page
```

## Tips

- **Minimum Data**: You need at least 5 LOTs with complete sensory scores to train ML models
- **API Key**: AI reports require a Gemini API key (free tier available)
- **Export Data**: Use the "Download as CSV" button to export your LOT data
- **Model Types**: Experiment with different model types (Random Forest usually works best)

## Troubleshooting

### Database Error
- The database is created automatically in `data/liquor_analytics.db`
- Ensure the `data/` directory exists and is writable

### Model Not Found
- Train a model first in the Prediction page before making predictions
- Models are saved in `data/models/`

### API Key Error
- Ensure your Gemini API key is correctly set in `.env`
- Test the connection using the "Test Connection" button in the Report page

## Need Help?

Check the main README.md for detailed documentation or create an issue on GitHub.
