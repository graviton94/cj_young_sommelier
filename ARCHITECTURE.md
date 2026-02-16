# Architecture

## Data Flow

### User Workflow Pipeline

```
1. DATA ENTRY (pages/1_Data_Entry.py)
   Input: LOT metadata + basic chemical parameters + sensory scores
   ↓
   Creates: LOTData record + LotMeasurement records
   Auto-generates: FlavorAnalysis record (type='initial')
   ↓
   Storage: SQLite tables via SQLAlchemy ORM

2. DETAILED ANALYSIS (pages/2_Flavor_Analysis.py)
   Input: GCMS CSV file + flavor indicators + (optional) linked LOT
   ↓
   Processes: CSV parsing → validate columns → extract measurements
   Creates: FlavorAnalysis (type='detailed'/'prototype') + FlavorMeasurement records
   File Storage: data/gcms_uploads/{timestamp}_{uuid}_{filename}.csv
   ↓
   Database: FlavorAnalysis.gcms_file_path references physical file

3. VIEW & MANAGE (pages/3_Analysis_Result.py)
   Query: JOIN FlavorAnalysis + LOTData
   ↓
   Display: Unified table with filtering and sorting
   Actions: Edit (update measurements) | Delete (cascade + file cleanup) | Download GCMS
   ↓
   Updates propagate back to database

4. ML PREDICTION (pages/4_Prediction.py)
   Input: Historical LOTData with complete sensory scores (min 5 samples)
   ↓
   Feature Engineering: Chemical parameters → StandardScaler normalization
   Training: sklearn models (Random Forest, Gradient Boosting, Linear, Ridge, Lasso)
   ↓
   Model Persistence: data/models/{target_variable}_model.pkl
   Prediction: New chemical composition → predicted sensory scores

5. FLAVOR KNOWLEDGE (pages/5_Sensory.py)
   Input: Compound name or CAS number
   ↓
   Lookup Chain:
     - Search master_flavor_db.csv (local cache)
     - If not found → PubChemPy API (by CAS or name)
     - Extract SMILES → RDKit molecular property calculation
     - Detect functional groups via SMARTS patterns
   ↓
   Output: Molecular weight, LogP, functional groups, flavor descriptors
   Update: master_flavor_db.csv + AnalysisIndex table

6. AI REPORT (pages/6_Report.py)
   Input: Selected FlavorAnalysis ID
   ↓
   Data Aggregation:
     - FlavorAnalysis metadata
     - FlavorMeasurement values
     - AnalysisIndex names/units
     - master_flavor_db flavor descriptors
   Prompt Construction:
     - knowledge_base/system_persona.md (AI role definition)
     - knowledge_base/flavor_chemistry.md (chemical context)
     - knowledge_base/report_template.md (output structure)
     - Structured data payload
   ↓
   Google Gemini API (gemini-pro model)
   ↓
   Output: Markdown formatted comprehensive flavor report

7. SETTINGS (pages/7_Settings.py)
   Input: New analysis parameter definition
   ↓
   Creates: AnalysisIndex record (code, name, unit, range, category, chemical identifiers)
   ↓
   Effect: Dynamic schema extension without database migration
```

### Database Schema

**5 Core Tables:**

**1. LOTData** (Production batch master records)
- Primary key: id (auto-increment)
- Unique constraint: REMOVED (allows multiple analyses per lot_number)
- Chemical fields: alcohol_content, acidity, sugar_content, tannin_level, ester_concentration, aldehyde_level
- Sensory fields: aroma_score, taste_score, finish_score, overall_score
- Metadata: lot_number, product_name, production_date, admission_date, notes

**2. LotMeasurement** (Dynamic measurements for LOTData)
- Foreign key: lot_id → LOTData.id
- Foreign key: index_code → AnalysisIndex.code
- value: float (measurement value)
- Purpose: Extensible schema without ALTER TABLE

**3. FlavorAnalysis** (Unified analysis records for all types)
- Primary key: id
- sample_name: string (required)
- is_prototype: boolean (0=production, 1=prototype)
- lot_id: nullable foreign key → LOTData.id
- analysis_type: enum ('initial', 'detailed', 'aging', 'prototype')
- gcms_file_path: nullable string (physical file reference)
- analysis_date, notes
- Purpose: Central repository eliminating data silos

**4. FlavorMeasurement** (Dynamic measurements for FlavorAnalysis)
- Foreign key: flavor_analysis_id → FlavorAnalysis.id
- Foreign key: index_code → AnalysisIndex.code
- value: float
- Purpose: Flexible measurement storage

**5. AnalysisIndex** (Configuration schema for measurements)
- code: unique string (internal identifier, e.g., 'ph', 'ethyl_acetate')
- name: string (display name in Korean)
- unit, min_value, max_value, step: float
- category: enum ('basic', 'gcms', 'sensory', 'flavor_indicator')
- Chemical identifiers: cas_number, smiles, molecular_weight, molecular_formula, log_p, functional_groups
- Purpose: Runtime-configurable fields without schema migrations

**6. SensoryProfile** (Legacy sensory tasting notes)
- Detailed sensory descriptions
- Taster information
- AI-generated reports

### Data Storage Strategy

**Dual Storage Pattern:**
- **LOTData**: Legacy compatibility, direct chemical/sensory fields
- **FlavorAnalysis**: Unified modern approach, supports all analysis types
- Migration path: Both tables coexist, new features use FlavorAnalysis

**File Management:**
- GCMS files: Physical storage in `data/gcms_uploads/`
- Naming: `{timestamp}_{uuid}_{original_filename}.csv`
- Lifecycle: Created on upload, deleted on record deletion
- Reference: FlavorAnalysis.gcms_file_path stores relative path

## Design Patterns

### 1. Multi-Tier Monolithic Architecture
- **Presentation Layer**: Streamlit pages (7 numbered pages enforce workflow order)
- **Business Logic Layer**: src/ modules (database, analysis, llm, chem_utils)
- **Data Layer**: SQLite + CSV reference data

### 2. Entity-Attribute-Value (EAV) Pattern
- Implementation: AnalysisIndex + Measurement tables
- Benefit: Add new chemical parameters without schema migration
- Trade-off: Complex queries, denormalized for flexibility

### 3. Repository Pattern (Implicit)
- database.py encapsulates all ORM operations
- Pages call database functions, never raw SQL
- Session management centralized in get_session()

### 4. Strategy Pattern (ML Models)
- SensoryPredictor class supports multiple sklearn algorithms
- model_type parameter selects: 'random_forest', 'gradient_boosting', 'linear', 'ridge', 'lasso'
- Uniform interface: train() → save() → predict()

### 5. Template Method Pattern (AI Reports)
- GeminiFlavorReporter.generate_report()
- Fixed algorithm: load_knowledge_base() → prepare_prompt() → call_api() → format_response()
- Customization: knowledge_base/*.md files define AI behavior without code changes

### 6. Singleton Pattern (Database Session)
- SQLAlchemy engine created once in database.py
- get_session() returns new session per request
- Thread-safe via sessionmaker

### 7. Facade Pattern
- chem_utils.py wraps PubChemPy + RDKit complexity
- Simple interface: lookup_by_cas(), lookup_by_name(), calculate_properties()
- Hides API calls, error handling, SMILES parsing

### 8. Observer Pattern (Streamlit State)
- st.session_state manages reactive UI
- Changes trigger automatic re-renders
- Used for multi-step forms and data refresh

## Constraints

### 1. Database Constraints
- **NO raw SQL**: All database operations via SQLAlchemy ORM
- **NO hard deletes without cascade**: FlavorAnalysis deletion must remove FlavorMeasurement records AND physical files
- **lot_number is NOT unique**: Allows multiple analyses per production LOT (constraint removed in migration)
- **Foreign key integrity**: lot_id nullable (supports prototypes without production LOT)

### 2. Data Validation
- **Measurement ranges**: Enforced via AnalysisIndex (min_value, max_value, step)
- **CAS number format**: Regex `\d{1,7}-\d{2}-\d` validation before lookup
- **SMILES validation**: RDKit MolFromSmiles() must succeed or reject
- **CSV format**: GCMS upload requires '성분' (compound name) column minimum

### 3. ML Model Constraints
- **Minimum training samples**: 5 complete records with sensory scores
- **Feature imputation**: Missing values replaced with median (fallback to 0.0)
- **Normalization**: StandardScaler per target variable (fit on training data only)
- **NO feature engineering beyond basic composition**: Use chemical parameters as-is

### 4. AI/LLM Constraints (from system_persona.md)
- **NO hallucination**: Only analyze provided data, cite sources
- **NO medical/health claims**: Avoid therapeutic or safety assertions
- **Probabilistic language**: Use "may", "possibly", "suggests" for predictions
- **Korean primary**: Reports generated in Korean unless specified
- **API key required**: Graceful degradation if GEMINI_API_KEY missing

### 5. Coding Standards (Karpathy Guidelines)
- **Minimalism**: NO surprise refactoring, touch only surgical lines
- **NO speculation**: Avoid "future-proof" flexibility, extra config, unasked helpers (YAGNI)
- **Functions over classes**: Prefer flat logic over deep nesting
- **NO commented code**: Remove deprecated code completely
- **Style consistency**: Mimic existing file's style (quotes, indentation)

### 6. File Management
- **Unique filenames**: timestamp + UUID prevents collisions
- **Physical cleanup**: Delete files when database record deleted
- **Path safety**: Store relative paths in database, resolve at runtime
- **NO hardcoded paths**: Use os.path.join() for cross-platform compatibility

### 7. Workflow Constraints
- **Sequential pages**: Numbered 1-7 enforce recommended workflow
- **Auto-create initial analysis**: LOT registration triggers FlavorAnalysis (type='initial')
- **GCMS upload optional**: Can create FlavorAnalysis without file
- **Settings last**: AnalysisIndex should be configured before measurement entry

### 8. Deployment Constraints
- **SQLite Linux compatibility**: Streamlit Cloud requires pysqlite3-binary swap (main.py)
- **Volume persistence**: Docker requires -v mount for data/ directory
- **Environment variables**: GEMINI_API_KEY via .env or Streamlit secrets
- **NO database backups automated**: Manual export recommended before updates

### 9. Chemistry Constraints
- **PubChem API rate limits**: Respect 5 requests/second (handled by library)
- **RDKit molecular weight**: Calculate via MolWt() not PubChem (more accurate)
- **Functional groups**: Predefined SMARTS patterns (13 groups: alcohol, aldehyde, ester, etc.)
- **Threshold prediction**: Use master_flavor_db similarity search, fallback to median

### 10. Type Safety
- **Strict typing**: SQLAlchemy models use explicit types (Integer, Float, String, Boolean)
- **Nullable fields explicit**: Use nullable=True/False (default False)
- **Enum categories**: AnalysisIndex.category limited to 4 values
- **NO implicit conversions**: Cast types explicitly (int(), float(), str())
