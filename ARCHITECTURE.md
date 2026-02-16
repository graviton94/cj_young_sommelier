# CJ Young Sommelier - Architecture Documentation

## Data Flow

### 1. Data Ingestion Path
```
User Input (Streamlit UI)
  ↓
pages/1_Data_Entry.py: LOT registration
  ↓
src/database.py: add_lot_data()
  ↓
SQLite DB (LOTData table + LotMeasurement table)
  ↓
Automatic mirror: FlavorAnalysis table (type='initial')
```

**Key Points:**
- New LOT data flows through dual-write pattern to both LOTData (legacy) and FlavorAnalysis (unified)
- Dynamic measurements stored separately in LotMeasurement table with lot_id foreign key
- production_date becomes analysis_date in unified storage

### 2. Detailed Analysis Path
```
User uploads GCMS CSV + enters flavor indicators
  ↓
pages/2_Flavor_Analysis.py
  ↓
Parse CSV → validate against AnalysisIndex table
  ↓
Create FlavorAnalysis record (is_prototype=1 for prototypes, 0 for LOTs)
  ↓
Store measurements in FlavorMeasurement table
  ↓
Optional: PubChemPy/RDKit enrichment for unknown compounds
```

**Key Points:**
- GCMS data stored as file_path reference + individual measurements
- Analysis indices (AnalysisIndex) define valid codes, units, ranges, and categories
- Compound metadata (CAS, SMILES, molecular properties) calculated on-demand via chem_utils

### 3. ML Prediction Path
```
User selects model type (Random Forest, Gradient Boosting, etc.)
  ↓
pages/4_Prediction.py
  ↓
src/analysis.py: SensoryPredictor.train()
  ↓
Extract features: [alcohol_content, acidity, sugar_content, tannin_level, ester_concentration, aldehyde_level]
  ↓
Train separate models for each target: [aroma_score, taste_score, finish_score, overall_score]
  ↓
StandardScaler normalization per target
  ↓
Save models to data/models/*.pkl
  ↓
Predict on new data via SensoryPredictor.predict()
```

**Key Points:**
- Each sensory target (aroma, taste, finish, overall) has independent model + scaler
- Missing feature values filled with column median or 0.0
- Model selection: Random Forest (default), Gradient Boosting, Linear, Ridge, Lasso

### 4. AI Report Generation Path
```
User selects LOT(s) for reporting
  ↓
pages/6_Report.py
  ↓
src/llm.py: GeminiFlavorReporter
  ↓
Construct prompt with chemical data + sensory scores + tasting notes
  ↓
Call Google Gemini API (models/gemini-pro-latest)
  ↓
Return structured flavor report with sections:
  - Flavor Profile Summary
  - Aroma Analysis
  - Taste & Palate
  - Finish
  - Quality Assessment
  - Pairing Suggestions
```

**Key Points:**
- API key loaded from environment variable GEMINI_API_KEY
- Prompts engineered for sommelier expertise and Korean market context
- Supports single LOT reports, comparison reports, and chemical insights

### 5. Sensory Evaluation Path
```
User selects LOT(s) for comparison
  ↓
pages/5_Sensory.py
  ↓
Query SensoryProfile table for detailed notes
  ↓
Visualize with Plotly radar charts
  ↓
Store new sensory profiles via src/database.py: add_sensory_profile()
```

**Key Points:**
- Sensory profiles stored with taster_name and tasting_date
- AI-generated flavor reports saved in ai_flavor_report column
- Multi-LOT comparison via side-by-side radar chart rendering

## Design Patterns

### 1. Repository Pattern
- **Implementation:** src/database.py functions (get_all_lots, add_lot_data, update_lot_data, delete_lot_data)
- **Purpose:** Encapsulate database access logic and provide clean interface to UI layer
- **Benefit:** Pages never directly execute SQL; all queries abstracted through typed functions

### 2. Factory Pattern
- **Implementation:** SensoryPredictor._get_model() in src/analysis.py
- **Purpose:** Dynamically instantiate ML models based on string identifier
- **Benefit:** User can switch models via dropdown without code changes

### 3. Dual-Write Pattern
- **Implementation:** add_lot_data() writes to both LOTData and FlavorAnalysis tables
- **Purpose:** Gradual migration from legacy schema to unified storage
- **Benefit:** Maintains backward compatibility while enabling unified analysis queries

### 4. Strategy Pattern
- **Implementation:** Multiple regression algorithms (Random Forest, Gradient Boosting, Linear, Ridge, Lasso)
- **Purpose:** Allow runtime selection of prediction strategy
- **Benefit:** A/B testing of models without architecture changes

### 5. Singleton-like Session Management
- **Implementation:** SessionLocal = sessionmaker(bind=engine) in database.py
- **Purpose:** Reuse database connection pool across requests
- **Benefit:** Connection pooling and transaction management

### 6. Template Method Pattern
- **Implementation:** GeminiFlavorReporter._build_flavor_report_prompt()
- **Purpose:** Define prompt structure skeleton while allowing customization for different report types
- **Benefit:** Consistent LLM interaction with extensible prompt engineering

## Constraints

### Strict Rules (Enforced by Code)

1. **No Raw SQL in UI Layer**
   - All database operations MUST go through src/database.py repository functions
   - UI files (pages/*.py) never import sqlalchemy.text or execute raw queries
   - Violations would bypass validation and break transaction safety

2. **Dynamic Measurement Validation**
   - All measurement codes MUST exist in AnalysisIndex table before storage
   - LotMeasurement and FlavorMeasurement tables validate index_code against AnalysisIndex.code
   - Invalid codes rejected silently or raise exceptions (prevents schema drift)

3. **LOT Number Non-Uniqueness**
   - LOTData.lot_number is NOT unique (removed UNIQUE constraint)
   - Multiple measurements of same LOT allowed (time-series tracking)
   - Queries MUST use lot_id (PK) for specific record access, not lot_number

4. **Sensory Score Range**
   - Legacy scores: 0-100 (aroma_score, taste_score, finish_score, overall_score)
   - New sensory indices: -4 to 4 (defined in AnalysisIndex with category='sensory')
   - UI enforces min_value/max_value/step from AnalysisIndex table

5. **Model Feature Count**
   - ML models REQUIRE exactly 6 features: [alcohol_content, acidity, sugar_content, tannin_level, ester_concentration, aldehyde_level]
   - Adding/removing features breaks trained models (no automatic retraining)
   - Feature names hardcoded in SensoryPredictor.feature_names

6. **API Key Security**
   - GEMINI_API_KEY MUST be in environment variables, never committed to source
   - .env file excluded via .gitignore
   - .env.template provided as example

7. **File Upload Path Sanitization**
   - GCMS CSV files stored in data/gcms_uploads/ with sanitized filenames
   - FlavorAnalysis.gcms_file_path stores relative path, not absolute
   - File deletion on record deletion (cascade cleanup)

8. **Database Migration Safety**
   - init_database() checks for missing columns before ALTER TABLE
   - Uses transactions with rollback on error
   - Never DROP existing data without backup

### Architectural Constraints

1. **No Direct Model Serialization in DB**
   - ML models saved to filesystem (data/models/*.pkl), not BLOB columns
   - Database stores model metadata only (type, training date)

2. **Stateless Page Design**
   - Streamlit pages are stateless; session_state used for temporary UI state only
   - No global variables for data caching (Streamlit handles caching internally)

3. **Single Database File**
   - All data in single SQLite file (data/liquor_analytics.db)
   - No sharding or distributed database
   - Backup strategy: file-level copy of .db file

4. **Chemical Data Read-Only After Calculation**
   - RDKit properties (logP, molecular_weight, SMILES) calculated once and stored
   - No recalculation unless user explicitly requests refresh

5. **Gemini Model Version Pinning**
   - Always use 'models/gemini-pro-latest' endpoint
   - No hardcoded version numbers (follow Google's latest stable)

### Performance Constraints

1. **CSV Upload Size Limit**
   - GCMS CSV files limited to Streamlit's default upload limit (200MB)
   - Large files may cause timeout; recommend splitting datasets

2. **ML Training Data Minimum**
   - Requires minimum 5 samples with complete sensory scores for training
   - Less than 5 samples raises ValueError in SensoryPredictor.train()

3. **Plotly Chart Render Limit**
   - Radar charts limited to ~50 data points per axis for readability
   - Multi-LOT comparison capped at 10 LOTs per chart

### Data Quality Constraints

1. **Missing Value Handling**
   - Chemical features: filled with column median or 0.0
   - Sensory targets: rows with missing targets excluded from training
   - GCMS measurements: None values allowed, stored as NULL

2. **Date Field Validation**
   - production_date, admission_date, analysis_date stored as timezone-aware DateTime
   - Default timezone: UTC (datetime.now(timezone.utc))

3. **Compound Name Uniqueness**
   - AnalysisIndex.code MUST be unique (enforced by database UNIQUE constraint)
   - Compound names (Name_Common, Name_IUPAC) may have duplicates (different CAS)
