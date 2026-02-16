# CJ Young Sommelier - Architecture Documentation

## Data Flow

### 1. Data Ingestion Path (LOT Registration)
```
User Input (Streamlit UI)
  ↓
pages/1_Data_Entry.py: LOT registration form
  ↓
src/database.py: add_lot_data()
  ↓
Dual-Write Pattern:
  ├─> LOTData table (legacy compatibility)
  │     - alcohol_content, acidity, sugar_content, tannin_level, ester_concentration, aldehyde_level
  │     - aroma_score, taste_score, finish_score, overall_score
  │     - lot_number, product_name, production_date, admission_date, notes
  │
  └─> FlavorAnalysis table (unified storage, type='initial')
        - Mirrors LOT metadata
        - sample_name = lot_number
        - analysis_date = production_date
  ↓
LotMeasurement table (dynamic measurements)
  - Linked via lot_id FK
  - index_code from AnalysisIndex table
```

**Key Points:**
- Dual-write maintains backward compatibility while enabling unified analysis
- LOT number NOT unique - allows time-series tracking of same production batch
- Dynamic measurements extend schema without ALTER TABLE migrations
- Auto-creates initial FlavorAnalysis record on LOT registration

### 2. Detailed Analysis Path (GCMS Upload)
```
User uploads GCMS CSV + enters flavor indicators
  ↓
pages/2_Flavor_Analysis.py
  ↓
CSV Validation:
  - Check for required columns ('성분' compound name minimum)
  - Validate measurement codes against AnalysisIndex table
  ↓
File Storage:
  - Save to data/gcms_uploads/{timestamp}_{uuid}_{filename}.csv
  - Generate unique filename to prevent collisions
  ↓
Database Write:
  ├─> FlavorAnalysis record
  │     - is_prototype (0=production LOT, 1=prototype)
  │     - lot_id (nullable FK - NULL for prototypes)
  │     - analysis_type ('detailed', 'aging', or 'prototype')
  │     - gcms_file_path (relative path reference)
  │
  └─> FlavorMeasurement records
        - flavor_analysis_id FK
        - index_code, value pairs
  ↓
Optional Chemical Enrichment:
  - PubChemPy lookup by CAS or compound name
  - RDKit SMILES parsing and property calculation
  - Update AnalysisIndex with molecular data
```

**Key Points:**
- Supports both LOT-linked and standalone prototype analyses
- GCMS files stored physically, database stores references only
- Chemical metadata calculated on-demand, cached in AnalysisIndex
- Flexible measurement storage via EAV pattern

### 3. Unified Analysis Management
```
User views/manages analyses
  ↓
pages/3_Analysis_Result.py
  ↓
Query: JOIN FlavorAnalysis + LOTData (via lot_id)
  ↓
Display: Unified table with filtering and sorting
  ↓
User Actions:
  ├─> Edit: Update FlavorMeasurement values
  ├─> Delete: Cascade removal of FlavorMeasurement + physical file cleanup
  └─> Download: Retrieve GCMS file from gcms_uploads/
```

**Key Points:**
- Central repository eliminates data silos across analysis types
- Cascade delete ensures no orphaned measurements or files
- Query optimization via lot_id (PK), not lot_number

### 4. ML Prediction Path
```
User selects model type (Random Forest, Gradient Boosting, etc.)
  ↓
pages/4_Prediction.py
  ↓
src/analysis.py: SensoryPredictor.train()
  ↓
Feature Extraction (hardcoded 6 features):
  [alcohol_content, acidity, sugar_content, tannin_level, ester_concentration, aldehyde_level]
  ↓
Missing Value Imputation:
  - Fill with column median
  - Fallback to 0.0 if median unavailable
  ↓
Per-Target Training (4 independent models):
  ├─> aroma_score model + StandardScaler
  ├─> taste_score model + StandardScaler
  ├─> finish_score model + StandardScaler
  └─> overall_score model + StandardScaler
  ↓
Model Persistence:
  - Save to data/models/{target}_model.pkl
  - Save to data/models/{target}_scaler.pkl
  ↓
Prediction:
  - Load models via SensoryPredictor.predict()
  - Input: new chemical composition
  - Output: predicted sensory scores
```

**Key Points:**
- Minimum 5 samples required for training (raises ValueError if insufficient)
- Each sensory target has independent model + scaler (no shared normalization)
- Model types: Random Forest (default), Gradient Boosting, Linear, Ridge, Lasso
- Feature engineering is minimal - uses raw chemical parameters
- Breaking change: Adding/removing features invalidates trained models

### 5. Flavor Knowledge Management
```
User looks up compound or manages flavor database
  ↓
pages/5_Sensory.py
  ↓
Compound Lookup Chain:
  1. Search master_flavor_db.csv (local cache)
  2. If not found → PubChemPy API (by CAS or compound name)
  3. Extract SMILES → RDKit molecular calculation
  4. Functional group detection (13 SMARTS patterns)
  ↓
Properties Calculated:
  - Molecular weight (via RDKit MolWt, not PubChem)
  - LogP (partition coefficient)
  - Functional groups (alcohol, aldehyde, ester, ketone, etc.)
  - SMILES canonical representation
  ↓
Update:
  - master_flavor_db.csv (flavor descriptors + thresholds)
  - AnalysisIndex table (chemical identifiers for GCMS compounds)
  ↓
Visualization:
  - Radar charts for sensory profile comparison
  - Multi-LOT comparison (limit: 10 LOTs per chart)
```

**Key Points:**
- Two-tier lookup: local CSV cache → external API
- RDKit provides more accurate molecular weight than PubChem
- Functional groups detected via predefined SMARTS patterns
- PubChem API rate limit: 5 requests/second (handled by library)

### 6. AI Report Generation Path
```
User selects LOT(s) for reporting
  ↓
pages/6_Report.py
  ↓
src/llm.py: GeminiFlavorReporter
  ↓
Data Aggregation:
  - FlavorAnalysis metadata
  - FlavorMeasurement values
  - AnalysisIndex names/units
  - master_flavor_db flavor descriptors
  - Chemical composition from LOTData
  ↓
Prompt Construction:
  - Load knowledge_base/system_persona.md (AI role definition)
  - Load knowledge_base/flavor_chemistry.md (chemical context)
  - Load knowledge_base/report_template.md (output structure)
  - Inject structured data payload
  ↓
Google Gemini API Call:
  - Model: models/gemini-pro-latest (auto-upgrades)
  - Temperature: configured for sommelier expertise
  - Context: Korean market flavor preferences
  ↓
Structured Report Output:
  - Flavor Profile Summary
  - Aroma Analysis
  - Taste & Palate
  - Finish
  - Quality Assessment
  - Pairing Suggestions
```

**Key Points:**
- API key required via GEMINI_API_KEY environment variable
- Uses latest Gemini model (trade-off: newest features vs. reproducibility)
- Prompts engineered for sommelier expertise and Korean context
- Reports generated in Korean unless specified otherwise
- Graceful degradation if API key missing

### 7. Sensory Evaluation Path
```
User performs sensory evaluation or comparison
  ↓
pages/5_Sensory.py
  ↓
Query SensoryProfile table:
  - taster_name, tasting_date
  - Detailed sensory descriptions
  - AI-generated flavor reports
  ↓
Visualization:
  - Plotly radar charts (limit: ~50 data points per axis)
  - Multi-LOT side-by-side comparison
  ↓
Store new sensory profiles:
  - src/database.py: add_sensory_profile()
  - Link to LOT via lot_id FK
```

**Key Points:**
- Sensory profiles support human tasting notes + AI reports
- Radar chart visualization for intuitive comparison
- Chart render limit prevents performance degradation

## Design Patterns

### 1. Multi-Tier Monolithic Architecture
- **Presentation Layer**: Streamlit pages (7 numbered pages enforce workflow order)
- **Business Logic Layer**: src/ modules (database, analysis, llm, chem_utils)
- **Data Layer**: SQLite + CSV reference data
- **Benefit**: Simple deployment, single database file, no network latency

### 2. Repository Pattern
- **Implementation**: src/database.py functions (get_all_lots, add_lot_data, update_lot_data, delete_lot_data)
- **Purpose**: Encapsulate database access logic, provide clean interface to UI layer
- **Constraint**: Pages never import sqlalchemy.text or execute raw SQL
- **Benefit**: Transaction safety, validation centralized, easier testing

### 3. Entity-Attribute-Value (EAV) Pattern
- **Implementation**: AnalysisIndex + LotMeasurement/FlavorMeasurement tables
- **Purpose**: Add new chemical parameters without schema migration
- **Trade-off**: Complex queries, denormalized for flexibility
- **Validation**: All measurement codes MUST exist in AnalysisIndex before storage

### 4. Dual-Write Pattern
- **Implementation**: add_lot_data() writes to both LOTData and FlavorAnalysis tables
- **Purpose**: Gradual migration from legacy schema to unified storage
- **Benefit**: Maintains backward compatibility while enabling unified queries
- **Migration Path**: Both tables coexist, new features use FlavorAnalysis

### 5. Factory Pattern
- **Implementation**: SensoryPredictor._get_model() in src/analysis.py
- **Purpose**: Dynamically instantiate ML models based on string identifier
- **Benefit**: User can switch models via dropdown without code changes
- **Supported Models**: Random Forest, Gradient Boosting, Linear, Ridge, Lasso

### 6. Strategy Pattern
- **Implementation**: Multiple regression algorithms with uniform interface
- **Purpose**: Allow runtime selection of prediction strategy
- **Interface**: train() → save() → predict()
- **Benefit**: A/B testing of models without architecture changes

### 7. Template Method Pattern
- **Implementation**: GeminiFlavorReporter._build_flavor_report_prompt()
- **Purpose**: Define prompt structure skeleton while allowing customization
- **Customization**: knowledge_base/*.md files define AI behavior without code changes
- **Benefit**: Consistent LLM interaction with extensible prompt engineering

### 8. Singleton Pattern (Database Session)
- **Implementation**: SQLAlchemy engine created once in database.py
- **Session Management**: get_session() returns new session per request
- **Thread Safety**: SessionLocal = sessionmaker(bind=engine)
- **Benefit**: Connection pooling and transaction management

### 9. Facade Pattern
- **Implementation**: chem_utils.py wraps PubChemPy + RDKit complexity
- **Simple Interface**: lookup_by_cas(), lookup_by_name(), calculate_properties()
- **Hidden Complexity**: API calls, error handling, SMILES parsing
- **Benefit**: Clean separation, easier mocking for tests

### 10. Observer Pattern (Streamlit State)
- **Implementation**: st.session_state manages reactive UI
- **Trigger**: Changes automatically trigger re-renders
- **Usage**: Multi-step forms and data refresh
- **Constraint**: Stateless page design (no global variables for data)

## Constraints

### Database Constraints

1. **NO Raw SQL in UI Layer**
   - All database operations MUST go through src/database.py repository functions
   - UI files (pages/*.py) never import sqlalchemy.text or execute raw queries
   - Violations bypass validation and break transaction safety

2. **Dynamic Measurement Validation**
   - All measurement codes MUST exist in AnalysisIndex table before storage
   - LotMeasurement and FlavorMeasurement validate index_code against AnalysisIndex.code
   - Invalid codes rejected to prevent schema drift

3. **LOT Number Non-Uniqueness**
   - LOTData.lot_number is NOT unique (UNIQUE constraint removed in migration)
   - Allows multiple analyses of same production LOT (time-series tracking)
   - Queries MUST use lot_id (PK) for specific record access, not lot_number

4. **Foreign Key Integrity**
   - lot_id nullable in FlavorAnalysis (supports prototypes without production LOT)
   - Cascade deletes: FlavorAnalysis deletion removes FlavorMeasurement records AND physical files

5. **Date Field Validation**
   - production_date, admission_date, analysis_date stored as timezone-aware DateTime
   - Default timezone: UTC (datetime.now(timezone.utc))

6. **Compound Name Uniqueness**
   - AnalysisIndex.code MUST be unique (enforced by database UNIQUE constraint)
   - Compound names may have duplicates (different CAS numbers)

### Data Validation Constraints

1. **Measurement Ranges**
   - Enforced via AnalysisIndex (min_value, max_value, step)
   - UI respects ranges dynamically without hardcoded limits
   - Example: pH (0-14), Alcohol % (0-100), sensory scores (-4 to 4)

2. **CAS Number Format**
   - Regex validation: `\d{1,7}-\d{2}-\d` before lookup
   - Prevents malformed API requests to PubChem

3. **SMILES Validation**
   - RDKit MolFromSmiles() must succeed or reject
   - Invalid SMILES not stored in database

4. **CSV Format Validation**
   - GCMS upload requires '성분' (compound name) column minimum
   - Additional columns validated against AnalysisIndex

5. **Sensory Score Range**
   - Legacy scores: 0-100 (aroma_score, taste_score, finish_score, overall_score)
   - New sensory indices: -4 to 4 (defined in AnalysisIndex with category='sensory')

### ML Model Constraints

1. **Minimum Training Samples**
   - Requires minimum 5 complete records with sensory scores
   - Raises ValueError in SensoryPredictor.train() if insufficient

2. **Feature Imputation**
   - Missing values replaced with column median (fallback to 0.0)
   - Sensory targets: rows with missing targets excluded from training

3. **Normalization**
   - StandardScaler per target variable (fit on training data only)
   - No shared normalization across targets

4. **NO Feature Engineering Beyond Basic Composition**
   - Uses chemical parameters as-is
   - No polynomial features, interaction terms, or derived variables

5. **Model Feature Lock**
   - ML models REQUIRE exactly 6 features: [alcohol_content, acidity, sugar_content, tannin_level, ester_concentration, aldehyde_level]
   - Feature names hardcoded in SensoryPredictor.feature_names
   - Adding/removing features breaks trained models (no automatic retraining)

### AI/LLM Constraints

1. **NO Hallucination**
   - Only analyze provided data, cite sources
   - From system_persona.md: "No speculation beyond data"

2. **NO Medical/Health Claims**
   - Avoid therapeutic or safety assertions
   - No health benefits or contraindications

3. **Probabilistic Language**
   - Use "may", "possibly", "suggests" for predictions
   - Avoid absolute claims

4. **Korean Primary Language**
   - Reports generated in Korean unless specified
   - Flavor descriptors localized for Korean market

5. **API Key Required**
   - GEMINI_API_KEY must be in environment variables
   - Graceful degradation if key missing (feature disabled, no crash)

6. **Gemini Model Version**
   - Uses 'models/gemini-pro-latest' endpoint (auto-upgrades)
   - Trade-off: Always uses newest features vs. reproducible outputs

### Coding Standards (Karpathy Guidelines)

1. **Minimalism**
   - NO surprise refactoring, touch only surgical lines
   - Make minimal changes to achieve goal

2. **NO Speculation**
   - Avoid "future-proof" flexibility, extra config, unasked helpers (YAGNI)
   - Don't add features beyond requirements

3. **Functions Over Classes**
   - Prefer flat logic over deep nesting
   - Use classes only when state management required

4. **NO Commented Code**
   - Remove deprecated code completely
   - Delete, don't comment out

5. **Style Consistency**
   - Mimic existing file's style (quotes, indentation)
   - Match the conventions already in the codebase

### File Management Constraints

1. **Unique Filenames**
   - timestamp + UUID prevents collisions
   - Format: {timestamp}_{uuid}_{original_filename}.csv

2. **Physical Cleanup**
   - Delete files when database record deleted
   - No orphaned files in gcms_uploads/

3. **Path Safety**
   - Store relative paths in database, resolve at runtime
   - FlavorAnalysis.gcms_file_path stores relative path, not absolute

4. **NO Hardcoded Paths**
   - Use os.path.join() for cross-platform compatibility
   - Never assume Unix-style paths

5. **File Upload Path Sanitization**
   - GCMS CSV files stored in data/gcms_uploads/
   - Sanitized filenames to prevent directory traversal

### Workflow Constraints

1. **Sequential Pages**
   - Numbered 1-7 enforce recommended workflow
   - Order suggests natural data entry progression

2. **Auto-Create Initial Analysis**
   - LOT registration triggers FlavorAnalysis (type='initial')
   - Ensures unified tracking from entry point

3. **GCMS Upload Optional**
   - Can create FlavorAnalysis without file
   - Supports manual measurement entry

4. **Settings Last**
   - AnalysisIndex should be configured before measurement entry
   - Prevents validation errors on data entry

### Deployment Constraints

1. **SQLite Linux Compatibility**
   - Streamlit Cloud requires pysqlite3-binary swap (main.py)
   - Platform detection: if platform.system() == 'Linux'

2. **Volume Persistence**
   - Docker requires -v mount for data/ directory
   - Single database file simplifies backup

3. **Environment Variables**
   - GEMINI_API_KEY via .env or Streamlit secrets
   - .env file excluded via .gitignore

4. **NO Database Backups Automated**
   - Manual export recommended before updates
   - Backup strategy: file-level copy of .db file

5. **API Key Security**
   - GEMINI_API_KEY never committed to source
   - .env.template provided as example

### Chemistry Constraints

1. **PubChem API Rate Limits**
   - Respect 5 requests/second (handled by library)
   - Avoid batch operations without throttling

2. **RDKit Molecular Weight**
   - Calculate via MolWt() not PubChem (more accurate)
   - Chemical data read-only after calculation

3. **Functional Groups**
   - Predefined SMARTS patterns (13 groups: alcohol, aldehyde, ester, ketone, etc.)
   - No dynamic pattern addition without code changes

4. **Threshold Prediction**
   - Use master_flavor_db similarity search
   - Fallback to median if no similar compounds

5. **Chemical Data Caching**
   - RDKit properties calculated once and stored
   - No recalculation unless user explicitly requests refresh

### Performance Constraints

1. **CSV Upload Size Limit**
   - GCMS CSV files limited to 200MB (Streamlit default)
   - Large files may cause timeout; recommend splitting datasets

2. **ML Training Data Minimum**
   - Requires minimum 5 samples for training
   - Performance degrades with < 20 samples (high variance)

3. **Plotly Chart Render Limit**
   - Radar charts limited to ~50 data points per axis for readability
   - Multi-LOT comparison capped at 10 LOTs per chart

4. **Database Query Optimization**
   - Use lot_id (PK indexed) for lookups, not lot_number
   - JOIN operations avoid N+1 queries

### Type Safety Constraints

1. **Strict Typing**
   - SQLAlchemy models use explicit types (Integer, Float, String, Boolean)
   - No implicit type conversions

2. **Nullable Fields Explicit**
   - Use nullable=True/False (default False)
   - Explicit NULL handling prevents bugs

3. **Enum Categories**
   - AnalysisIndex.category limited to 4 values: 'basic', 'gcms', 'sensory', 'flavor_indicator'
   - Validation at database level

4. **NO Implicit Conversions**
   - Cast types explicitly (int(), float(), str())
   - Avoid relying on Python's dynamic typing

### Architectural Constraints

1. **No Direct Model Serialization in DB**
   - ML models saved to filesystem (data/models/*.pkl), not BLOB columns
   - Database stores model metadata only (type, training date)

2. **Stateless Page Design**
   - Streamlit pages are stateless
   - session_state used for temporary UI state only
   - No global variables for data caching

3. **Single Database File**
   - All data in single SQLite file (data/liquor_analytics.db)
   - No sharding or distributed database
   - Simplifies backup and deployment

4. **Database Migration Safety**
   - init_database() checks for missing columns before ALTER TABLE
   - Uses transactions with rollback on error
   - Never DROP existing data without backup
