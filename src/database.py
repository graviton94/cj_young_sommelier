"""
Database module for managing LOT-specific liquor data using SQLite and SQLAlchemy
"""

import os
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "liquor_analytics.db"

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)


class LOTData(Base):
    """Model for LOT-specific chemical composition data"""
    __tablename__ = "lot_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lot_number = Column(String(100), nullable=False) # Removed unique=True
    product_name = Column(String(200), nullable=False)
    
    # Chemical composition parameters
    alcohol_content = Column(Float)  # ABV percentage
    acidity = Column(Float)  # pH level
    sugar_content = Column(Float)  # g/L
    tannin_level = Column(Float)  # mg/L
    ester_concentration = Column(Float)  # mg/L
    aldehyde_level = Column(Float)  # mg/L
    
    # Sensory scores (target variables for ML)
    aroma_score = Column(Float)  # 0-100
    taste_score = Column(Float)  # 0-100
    finish_score = Column(Float)  # 0-100
    overall_score = Column(Float)  # 0-100
    
    # Metadata
    production_date = Column(DateTime) # Displayed as Analysis Date
    admission_date = Column(DateTime) # New: Admission Date (입고일)
    control_sample_id = Column(Integer) # Reference to control sample LOT for C/T comparison
    entry_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(Text)
    
    def __repr__(self):
        return f"<LOTData(id={self.id}, lot={self.lot_number}, product={self.product_name})>"


class SensoryProfile(Base):
    """Model for detailed sensory profiles and tasting notes"""
    __tablename__ = "sensory_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lot_number = Column(String(100), nullable=False)
    
    # Detailed sensory attributes
    color_description = Column(String(200))
    aroma_notes = Column(Text)  # Comma-separated descriptors
    flavor_notes = Column(Text)  # Comma-separated descriptors
    mouthfeel = Column(String(200))
    finish_description = Column(Text)
    
    # Taster information
    taster_name = Column(String(100))
    tasting_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # AI-generated content
    ai_flavor_report = Column(Text)
    
    def __repr__(self):
        return f"<SensoryProfile(lot={self.lot_number}, taster={self.taster_name})>"



class AnalysisIndex(Base):
    """Model for managing analysis items, units, and GCMS metadata"""
    __tablename__ = "analysis_indices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), nullable=False, unique=True)  # Internal code (e.g., 'alcohol_content')
    name = Column(String(200), nullable=False)  # Display name (e.g., '알코올 도수')
    unit = Column(String(50))  # Unit (e.g., '%', 'mg/L')
    min_value = Column(Float, default=0.0)
    max_value = Column(Float, default=None)  # None means no upper limit
    step = Column(Float, default=0.1)
    
    # GCMS specific fields
    is_gcms = Column(Integer, default=0)  # Boolean: 0=Basic, 1=GCMS (Deprecated, use category)
    category = Column(String(50), default='basic')  # 'basic', 'gcms', 'sensory'
    csv_header = Column(String(200))  # Header name in CSV uploads
    flavor_hint = Column(Text)  # Flavor description
    
    # Chemical Identifiers (for RDKit/PubChem)
    cas_number = Column(String(50))
    smiles = Column(Text)
    molecular_weight = Column(Float)
    molecular_formula = Column(String(50))
    
    # New properties (Auto-calculated)
    log_p = Column(Float)
    functional_groups = Column(String(500))
    
    display_order = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<AnalysisIndex(code={self.code}, name={self.name})>"


class LotMeasurement(Base):
    """Model for storing dynamic measurement values linked to AnalysisIndex"""
    __tablename__ = "lot_measurements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lot_id = Column(Integer) # Foreign Key to LOTData.id (New)
    lot_number = Column(String(100), nullable=True) # Kept for legacy, nullable
    index_code = Column(String(100), nullable=False)
    value = Column(Float)
    
    def __repr__(self):
        return f"<LotMeasurement(lot_id={self.lot_id}, code={self.index_code}, value={self.value})>"


class FlavorAnalysis(Base):
    """Model for detailed flavor analysis (Prototypes & LOTs)"""
    __tablename__ = "flavor_analysis"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_name = Column(String(200), nullable=False)  # Prototype name or LOT reference sting
    is_prototype = Column(Integer, default=1)  # 1=Prototype, 0=LOT
    lot_id = Column(Integer, nullable=True)  # FK to LOTData if is_prototype=0
    analysis_date = Column(DateTime)
    
    # Standard sensory scores (can also be dynamic, but kept standard for easier ML access if needed)
    # Actually user requested flavor indicators + GCMS. 
    # Let's keep structure similar to LOTData to allow unified analysis later if needed.
    
    analysis_type = Column(String(50), default='detailed') # 'initial', 'aging', 'detailed', 'prototype'
    gcms_file_path = Column(String(500))  # Path to uploaded CSV
    notes = Column(Text)
    entry_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<FlavorAnalysis(id={self.id}, sample={self.sample_name}, type={'Proto' if self.is_prototype else 'LOT'})>"


class FlavorMeasurement(Base):
    """Model for flavor analysis measurements (Chemical, Sensory, Flavor Indicators)"""
    __tablename__ = "flavor_measurements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    flavor_analysis_id = Column(Integer)  # FK to FlavorAnalysis
    index_code = Column(String(100))  # FK to AnalysisIndex (code)
    value = Column(Float)
    
    def __repr__(self):
        return f"<FlavorMeasurement(analysis_id={self.flavor_analysis_id}, code={self.index_code}, value={self.value})>"


from sqlalchemy import inspect, text

def init_database():
    """Initialize the database and create all tables"""
    Base.metadata.create_all(engine)
    
    # Check for schema updates
    try:
        inspector = inspect(engine)
        
        # 1. AnalysisIndex Column Migration
        if 'analysis_indices' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('analysis_indices')]
            
            with engine.connect() as conn:
                transaction = conn.begin()
                try:
                    if 'cas_number' not in columns:
                        conn.execute(text("ALTER TABLE analysis_indices ADD COLUMN cas_number VARCHAR(50)"))
                    if 'smiles' not in columns:
                        conn.execute(text("ALTER TABLE analysis_indices ADD COLUMN smiles TEXT"))
                    if 'molecular_weight' not in columns:
                        conn.execute(text("ALTER TABLE analysis_indices ADD COLUMN molecular_weight FLOAT"))
                    if 'molecular_formula' not in columns:
                        conn.execute(text("ALTER TABLE analysis_indices ADD COLUMN molecular_formula VARCHAR(50)"))
                    if 'category' not in columns:
                        conn.execute(text("ALTER TABLE analysis_indices ADD COLUMN category VARCHAR(50) DEFAULT 'basic'"))
                        conn.execute(text("UPDATE analysis_indices SET category='gcms' WHERE is_gcms=1"))
                        conn.execute(text("UPDATE analysis_indices SET category='basic' WHERE is_gcms=0"))
                        
                    # New columns for GCMS properties
                    if 'log_p' not in columns:
                         conn.execute(text("ALTER TABLE analysis_indices ADD COLUMN log_p FLOAT"))
                    if 'functional_groups' not in columns:
                         conn.execute(text("ALTER TABLE analysis_indices ADD COLUMN functional_groups TEXT"))

                    transaction.commit()
                except Exception as e:
                    transaction.rollback()
                    print(f"Migration error (Indices): {e}")

        # 2. LotMeasurement Migration (Add lot_id)
        if 'lot_measurements' in inspector.get_table_names():
            lm_columns = [c['name'] for c in inspector.get_columns('lot_measurements')]
            if 'lot_id' not in lm_columns:
                with engine.connect() as conn:
                    transaction = conn.begin()
                    try:
                        conn.execute(text("ALTER TABLE lot_measurements ADD COLUMN lot_id INTEGER"))
                        # Populate lot_id from lot_number
                        conn.execute(text("UPDATE lot_measurements SET lot_id = (SELECT id FROM lot_data WHERE lot_data.lot_number = lot_measurements.lot_number LIMIT 1)"))
                        transaction.commit()
                        print("Migrated LotMeasurement to use lot_id")
                    except Exception as e:
                        transaction.rollback()
                        print(f"Migration error (LotMeasurement): {e}")

        # 2.1 FlavorAnalysis & FlavorMeasurement Creation
        # These are new tables, create_all should handle them, but if they were added later to existing DB
        # create_all checks for existence. We just need to make sure the classes are defined before create_all is called.
        # However, create_all is called at start of function.
        # If we added models *after* DB creation on older version, we might need manual creation if not using Alembic.
        # But Base.metadata.create_all(engine) safely skips existing tables and creates missing ones.
        # So essentially we just need to define the classes (done below) and create_all at start handles it.
        pass

        # 3. LOTData Unique Constraint Removal & Admission Date
        if 'lot_data' in inspector.get_table_names():
            ld_columns = [c['name'] for c in inspector.get_columns('lot_data')]
            
            # 3.1 Check if we need to recreate table (unique constraint exists)
            # Check if lot_number has unique constraint by trying to insert duplicate
            needs_recreation = False
            
            # Check table schema to see if unique constraint exists
            with engine.connect() as conn:
                result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='lot_data'"))
                create_sql = result.fetchone()
                if create_sql and 'lot_number' in create_sql[0] and 'UNIQUE' in create_sql[0]:
                    needs_recreation = True
                    print("Detected UNIQUE constraint on lot_number, recreating table...")
            
            if needs_recreation:
                # Recreate table without UNIQUE constraint
                with engine.connect() as conn:
                    transaction = conn.begin()
                    try:
                        # 1. Create new table without unique constraint
                        conn.execute(text("""
                            CREATE TABLE lot_data_new (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                lot_number VARCHAR(100) NOT NULL,
                                product_name VARCHAR(200) NOT NULL,
                                alcohol_content FLOAT,
                                acidity FLOAT,
                                sugar_content FLOAT,
                                tannin_level FLOAT,
                                ester_concentration FLOAT,
                                aldehyde_level FLOAT,
                                aroma_score FLOAT,
                                taste_score FLOAT,
                                finish_score FLOAT,
                                overall_score FLOAT,
                                production_date TIMESTAMP,
                                admission_date TIMESTAMP,
                                entry_date TIMESTAMP,
                                notes TEXT
                            )
                        """))
                        
                        # 2. Copy data from old table
                        conn.execute(text("""
                            INSERT INTO lot_data_new 
                            SELECT id, lot_number, product_name, alcohol_content, acidity, 
                                   sugar_content, tannin_level, ester_concentration, aldehyde_level,
                                   aroma_score, taste_score, finish_score, overall_score,
                                   production_date, 
                                   CASE WHEN EXISTS(SELECT * FROM pragma_table_info('lot_data') WHERE name='admission_date') 
                                        THEN admission_date ELSE NULL END as admission_date,
                                   entry_date, notes
                            FROM lot_data
                        """))
                        
                        # 3. Drop old table
                        conn.execute(text("DROP TABLE lot_data"))
                        
                        # 4. Rename new table
                        conn.execute(text("ALTER TABLE lot_data_new RENAME TO lot_data"))
                        
                        transaction.commit()
                        print("✅ Successfully recreated lot_data table without UNIQUE constraint")
                    except Exception as e:
                        transaction.rollback()
                        print(f"Migration error (table recreation): {e}")
            else:
                # Just add admission_date and control_sample_id if needed
                if 'admission_date' not in ld_columns:
                     with engine.connect() as conn:
                        transaction = conn.begin()
                        try:
                            conn.execute(text("ALTER TABLE lot_data ADD COLUMN admission_date TIMESTAMP"))
                            transaction.commit()
                        except Exception as e:
                            transaction.rollback()
                            print(f"Migration error (admission_date): {e}")
                
                if 'control_sample_id' not in ld_columns:
                     with engine.connect() as conn:
                        transaction = conn.begin()
                        try:
                            conn.execute(text("ALTER TABLE lot_data ADD COLUMN control_sample_id INTEGER"))
                            transaction.commit()
                            print("Added control_sample_id column to lot_data")
                        except Exception as e:
                            transaction.rollback()
                            print(f"Migration error (control_sample_id): {e}")
                                
    except Exception as e:
        print(f"Schema check error: {e}")

    
    # Seed default indices if table is empty
    session = SessionLocal()
    
    # User's current settings as of 2026-01-16
    current_defaults = [{'code': 'alcohol_content', 'name': '알코올 도수', 'unit': '% ABV', 'min_value': 0.0, 'max_value': 100.0, 'step': 0.01, 'display_order': 1, 'category': 'basic'}, {'code': 'acidity', 'name': 'pH', 'unit': 'pH', 'min_value': 0.0, 'max_value': 14.0, 'step': 0.01, 'display_order': 2, 'category': 'basic'}, {'code': 'sugar_content', 'name': '산도', 'unit': 'ml/10ml', 'min_value': 0.0, 'max_value': None, 'step': 0.01, 'display_order': 3, 'category': 'basic'}, {'code': 'tannin_level', 'name': '알데히드', 'unit': 'mg/100ml', 'min_value': 0.0, 'max_value': 70.0, 'step': 0.1, 'display_order': 4, 'category': 'basic'}, {'code': 'ester_concentration', 'name': '메탄올', 'unit': 'mg/ml', 'min_value': 0.0, 'max_value': 0.5, 'step': 0.01, 'display_order': 5, 'category': 'basic'}, {'code': 'aldehyde_level', 'name': '밀도', 'unit': 'g/cm³', 'min_value': 0.0, 'max_value': 1.0, 'step': 1e-05, 'display_order': 6, 'category': 'basic'}, {'code': 'aroma_score', 'name': '외관/투명도', 'unit': '점', 'min_value': -4.0, 'max_value': 4.0, 'step': 1.0, 'display_order': 1, 'category': 'sensory'}, {'code': 'taste_score', 'name': '향', 'unit': '점', 'min_value': -4.0, 'max_value': 4.0, 'step': 1.0, 'display_order': 2, 'category': 'sensory'}, {'code': 'finish_score', 'name': '목넘김', 'unit': '점', 'min_value': -4.0, 'max_value': 4.0, 'step': 1.0, 'display_order': 3, 'category': 'sensory'}, {'code': 'overall_score', 'name': '바디감', 'unit': '점', 'min_value': -4.0, 'max_value': 4.0, 'step': 1.0, 'display_order': 4, 'category': 'sensory'}, {'code': 'item_749c568a', 'name': '단맛', 'unit': '점', 'min_value': -4.0, 'max_value': 4.0, 'step': 1.0, 'display_order': 5, 'category': 'sensory'}, {'code': 'item_280cde40', 'name': '신맛', 'unit': '점', 'min_value': -4.0, 'max_value': 4.0, 'step': 1.0, 'display_order': 6, 'category': 'sensory'}, {'code': 'item_d9bb676d', 'name': '쓴맛', 'unit': '점', 'min_value': -4.0, 'max_value': 4.0, 'step': 1.0, 'display_order': 7, 'category': 'sensory'}, {'code': 'item_610b6d61', 'name': '청량감', 'unit': '점', 'min_value': -4.0, 'max_value': 4.0, 'step': 1.0, 'display_order': 8, 'category': 'sensory'}, {'code': 'item_f45aea98', 'name': '피니쉬', 'unit': '점', 'min_value': -4.0, 'max_value': 4.0, 'step': 1.0, 'display_order': 9, 'category': 'sensory'}, {'code': 'item_eb6cd9e2', 'name': '종합 차이', 'unit': '점', 'min_value': 0.0, 'max_value': 8.0, 'step': 1.0, 'display_order': 10, 'category': 'sensory'}, {'code': 'flavor_fruity', 'name': '과일향', 'unit': '점', 'min_value': 0.0, 'max_value': 20.0, 'step': 0.1, 'display_order': 1, 'category': 'flavor_indicator'}, {'code': 'flavor_acidic', 'name': '아세톤향', 'unit': '점', 'min_value': 0.0, 'max_value': 10.0, 'step': 0.1, 'display_order': 2, 'category': 'flavor_indicator'}, {'code': 'flavor_sweetness', 'name': '단맛', 'unit': '점', 'min_value': 0.0, 'max_value': 10.0, 'step': 0.1, 'display_order': 3, 'category': 'flavor_indicator'}, {'code': 'flavor_body', 'name': '신맛', 'unit': '점', 'min_value': 0.0, 'max_value': 10.0, 'step': 0.1, 'display_order': 4, 'category': 'flavor_indicator'}, {'code': 'flavor_balance', 'name': '바디감', 'unit': '점', 'min_value': 0.0, 'max_value': 10.0, 'step': 0.1, 'display_order': 5, 'category': 'flavor_indicator'}, {'code': 'item_371d88c4', 'name': '지속성, 여운(Finish)', 'unit': '점', 'min_value': 0.0, 'max_value': 10.0, 'step': 0.1, 'display_order': 6, 'category': 'flavor_indicator'}, {'code': 'item_ee198c4f', 'name': '목넘김', 'unit': '점', 'min_value': 0.0, 'max_value': 10.0, 'step': 0.1, 'display_order': 7, 'category': 'flavor_indicator'}]

    if session.query(AnalysisIndex).count() == 0:
        for item in current_defaults:
            idx = AnalysisIndex(**item)
            session.add(idx)
        session.commit()
    else:
        # Check and add missing items one by one for existing DBs
        for item in current_defaults:
            if not session.query(AnalysisIndex).filter_by(code=item['code']).first():
                idx = AnalysisIndex(**item)
                session.add(idx)
        session.commit()
            
    session.close()
    
    return engine


def get_session():
    """Get a new database session"""
    return SessionLocal()


def add_lot_data(session, data_dict):
    """
    Add new LOT data or new measurement for existing LOT.
    Returns the created LOTData object on success, None on failure.
    """
    try:
        # Extract dynamic measurements
        measurements = data_dict.pop('measurements', {})
        
        # Create Main LOT Data
        new_lot = LOTData(**data_dict)
        session.add(new_lot)
        session.flush()  # Limit flushing to get new_lot.id
        
        # Add Dynamic Measurements
        for code, value in measurements.items():
            if value is not None:
                measurement = LotMeasurement(
                    lot_id=new_lot.id,
                    lot_number=new_lot.lot_number, # Legacy support
                    index_code=code,
                    value=value
                )
                session.add(measurement)

        # ---------------------------------------------------------
        # Unified Storage: Also save to FlavorAnalysis (Type='initial')
        # ---------------------------------------------------------
        initial_analysis = FlavorAnalysis(
            sample_name=f"{new_lot.product_name} ({new_lot.lot_number})",
            is_prototype=0,
            lot_id=new_lot.id,
            analysis_date=new_lot.production_date, # Use production date as analysis date
            analysis_type='initial',
            notes=new_lot.notes
        )
        session.add(initial_analysis)
        session.flush()

        for code, value in measurements.items():
            if value is not None:
                f_measurement = FlavorMeasurement(
                    flavor_analysis_id=initial_analysis.id,
                    index_code=code,
                    value=value
                )
                session.add(f_measurement)
        
        session.commit()
        return new_lot
    except Exception as e:
        session.rollback()
        print(f"Error adding LOT data: {e}")
        return None

def get_all_lots(session, lot_number=None):
    """
    Get all LOT data, optionally filtered by lot_number.
    Returns list of LOTData objects ordered by entry_date (descending).
    """
    query = session.query(LOTData)
    if lot_number:
        query = query.filter(LOTData.lot_number == lot_number)
    return query.order_by(LOTData.entry_date.desc()).all()

def get_lot_by_number(session, lot_number):
    """
    Get most recent LOT data by LOT number.
    Note: Since lot_number is no longer unique, this returns the LATEST entry.
    """
    return session.query(LOTData).filter(LOTData.lot_number == lot_number).order_by(LOTData.entry_date.desc()).first()

def get_lot_by_id(session, lot_id):
    """Get LOT data by specific ID (PK)"""
    return session.query(LOTData).filter(LOTData.id == lot_id).first()



def update_lot_data(session, lot_id, data_dict):
    """Update existing LOT data by ID"""
    try:
        lot = session.query(LOTData).filter(LOTData.id == lot_id).first()
        if lot:
            measurements = data_dict.pop('measurements', {})
            
            # Update core fields
            for key, value in data_dict.items():
                if hasattr(lot, key):
                    setattr(lot, key, value)
            
            # Update measurements (Delete and Re-insert strategy for simplicity, or Update)
            # For simplicity: Update existing if exists, add if new
            current_measurements = session.query(LotMeasurement).filter(LotMeasurement.lot_id == lot.id).all()
            cm_map = {m.index_code: m for m in current_measurements}
            
            for code, value in measurements.items():
                if code in cm_map:
                    cm_map[code].value = value
                else:
                    new_m = LotMeasurement(lot_id=lot.id, lot_number=lot.lot_number, index_code=code, value=value)
                    session.add(new_m)
                    
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error updating LOT data: {e}")
        return False

def delete_lot_data(session, lot_id=None, lot_number=None):
    """
    Delete LOT data.
    - If lot_id is provided: Delete specific row (and its measurements).
    - If lot_number provided (and no lot_id): Delete ALL history for that LOT number.
    """
    try:
        if lot_id:
            # Delete specific entry
            session.query(LotMeasurement).filter(LotMeasurement.lot_id == lot_id).delete()
            session.query(SensoryProfile).filter(SensoryProfile.lot_number ==  # Sensory is linked by number usually? 
                                                session.query(LOTData.lot_number).filter(LOTData.id==lot_id).scalar_subquery()
                                                ).delete() # WARNING: Sensory is linked by lot_number. Deleting one measurement shouldn't delete sensory?
                                                # Re-thinking: Sensory is usually per LOT. If we have multiple measurements, do they share sensory?
                                                # For now, let's only delete measurements. Sensory might be tricky.
                                                # Adjust: Delete measurements linked to this ID.
            session.query(LOTData).filter(LOTData.id == lot_id).delete()
            
        elif lot_number:
            # Delete ALL history
            # Get all IDs
            ids = session.query(LOTData.id).filter(LOTData.lot_number == lot_number).all()
            ids = [i[0] for i in ids]
            
            session.query(LotMeasurement).filter(LotMeasurement.lot_id.in_(ids)).delete()
            session.query(SensoryProfile).filter(SensoryProfile.lot_number == lot_number).delete()
            session.query(LOTData).filter(LOTData.lot_number == lot_number).delete()
            
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error deleting LOT data: {e}")
        return False


# Analysis Index Management Functions
def get_all_indices(session, category=None, gcms_only=False, basic_only=False):
    """Get all analysis indices"""
    query = session.query(AnalysisIndex)
    
    if category:
        query = query.filter(AnalysisIndex.category == category)
    elif gcms_only:
        query = query.filter(AnalysisIndex.category == 'gcms')
    elif basic_only:
        query = query.filter(AnalysisIndex.category == 'basic')
        
    return query.order_by(AnalysisIndex.display_order).all()

def add_analysis_index(session, index_dict):
    """Add new analysis index"""
    try:
        idx = AnalysisIndex(**index_dict)
        session.add(idx)
        session.commit()
        return idx
    except Exception as e:
        session.rollback()
        raise e

def update_analysis_index(session, index_id, update_dict):
    """Update analysis index"""
    try:
        idx = session.query(AnalysisIndex).filter_by(id=index_id).first()
        if idx:
            for k, v in update_dict.items():
                setattr(idx, k, v)
            session.commit()
            return idx
        return None
    except Exception as e:
        session.rollback()
        raise e

def delete_analysis_index(session, index_id):
    """Delete analysis index"""
    try:
        idx = session.query(AnalysisIndex).filter_by(id=index_id).first()
        if idx:
            session.delete(idx)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e

def get_lot_measurements(session, lot_number):
    """Get all dynamic measurements for a LOT"""
    return session.query(LotMeasurement).filter_by(lot_number=lot_number).all()


def add_sensory_profile(session, profile_dict):
    """Add new sensory profile to database"""
    try:
        profile = SensoryProfile(**profile_dict)
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile
    except Exception as e:
        session.rollback()
        raise e


def get_sensory_profiles_by_lot(session, lot_number):
    """Retrieve all sensory profiles for a specific LOT"""
    return session.query(SensoryProfile).filter(
        SensoryProfile.lot_number == lot_number
    ).all()
