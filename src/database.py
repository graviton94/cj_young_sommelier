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
    lot_number = Column(String(100), nullable=False, unique=True)
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
    production_date = Column(DateTime)
    entry_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(Text)
    
    def __repr__(self):
        return f"<LOTData(lot={self.lot_number}, product={self.product_name})>"


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
    is_gcms = Column(Integer, default=0)  # Boolean: 0=Basic, 1=GCMS
    csv_header = Column(String(200))  # Header name in CSV uploads
    flavor_hint = Column(Text)  # Flavor description
    
    display_order = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<AnalysisIndex(code={self.code}, name={self.name})>"


class LotMeasurement(Base):
    """Model for storing dynamic measurement values linked to AnalysisIndex"""
    __tablename__ = "lot_measurements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lot_number = Column(String(100), nullable=False)
    index_code = Column(String(100), nullable=False)  # Foreign Key to AnalysisIndex.code effectively
    value = Column(Float)
    
    def __repr__(self):
        return f"<LotMeasurement(lot={self.lot_number}, code={self.index_code}, value={self.value})>"


def init_database():
    """Initialize the database and create all tables"""
    Base.metadata.create_all(engine)
    
    # Seed default indices if table is empty
    session = SessionLocal()
    if session.query(AnalysisIndex).count() == 0:
        defaults = [
            # Basic Physicochemical Properties
            {'code': 'alcohol_content', 'name': '알코올 도수', 'unit': '% ABV', 'min_value': 0.0, 'max_value': 100.0, 'step': 0.1, 'display_order': 1, 'is_gcms': 0},
            {'code': 'acidity', 'name': '산도', 'unit': 'pH', 'min_value': 0.0, 'max_value': 14.0, 'step': 0.1, 'display_order': 2, 'is_gcms': 0},
            {'code': 'sugar_content', 'name': '당 함량', 'unit': 'g/L', 'min_value': 0.0, 'max_value': None, 'step': 0.1, 'display_order': 3, 'is_gcms': 0},
            {'code': 'tannin_level', 'name': '타닌 수치', 'unit': 'mg/L', 'min_value': 0.0, 'max_value': None, 'step': 0.1, 'display_order': 4, 'is_gcms': 0},
            {'code': 'ester_concentration', 'name': '에스터 농도', 'unit': 'mg/L', 'min_value': 0.0, 'max_value': None, 'step': 0.1, 'display_order': 5, 'is_gcms': 0},
            {'code': 'aldehyde_level', 'name': '알데히드 수치', 'unit': 'mg/L', 'min_value': 0.0, 'max_value': None, 'step': 0.1, 'display_order': 6, 'is_gcms': 0},
            
            # Example GCMS Compounds (User can add more)
            {'code': 'ethyl_acetate', 'name': 'Ethyl Acetate', 'unit': 'mg/L', 'flavor_hint': '과일향, 파인애플, 달콤함', 'csv_header': 'Peak_EthylAc', 'is_gcms': 1, 'display_order': 10},
            {'code': 'isoamyl_acetate', 'name': 'Isoamyl Acetate', 'unit': 'mg/L', 'flavor_hint': '바나나, 배', 'csv_header': 'Peak_IsoAmyl', 'is_gcms': 1, 'display_order': 11}
        ]
        
        for item in defaults:
            idx = AnalysisIndex(**item)
            session.add(idx)
        session.commit()
    session.close()
    
    return engine


def get_session():
    """Get a new database session"""
    return SessionLocal()


def add_lot_data(session, lot_data_dict):
    """
    Add new LOT data to the database.
    Also handles dynamic measurements if present in dictionary with matching keys in AnalysisIndex.
    """
    try:
        # Separate standard LOTData fields
        lot_fields = [c.key for c in LOTData.__table__.columns]
        standard_data = {k: v for k, v in lot_data_dict.items() if k in lot_fields}
        
        lot = LOTData(**standard_data)
        session.add(lot)
        session.flush() # Flush to check for errors but don't commit yet
        
        # Handle extra fields as LotMeasurement
        # First get all valid codes
        valid_codes = {idx.code for idx in session.query(AnalysisIndex).all()}
        
        for key, value in lot_data_dict.items():
            if key not in lot_fields and key in valid_codes and value is not None:
                # This is a dynamic measurement
                msmt = LotMeasurement(lot_number=lot.lot_number, index_code=key, value=value)
                session.add(msmt)
                
        session.commit()
        session.refresh(lot)
        return lot
    except Exception as e:
        session.rollback()
        raise e


def get_all_lots(session):
    """Retrieve all LOT data from database"""
    return session.query(LOTData).all()


def get_lot_by_number(session, lot_number):
    """Retrieve specific LOT by lot number"""
    return session.query(LOTData).filter(LOTData.lot_number == lot_number).first()


def update_lot_data(session, lot_number, update_dict):
    """Update existing LOT data and dynamic measurements"""
    try:
        lot = get_lot_by_number(session, lot_number)
        if lot:
            # Update standard fields
            lot_fields = [c.key for c in LOTData.__table__.columns]
            
            for key, value in update_dict.items():
                if key in lot_fields:
                    setattr(lot, key, value)
            
            # Update dynamic measurements
            valid_codes = {idx.code for idx in session.query(AnalysisIndex).all()}
            
            for key, value in update_dict.items():
                if key not in lot_fields and key in valid_codes:
                    # Check if measurement exists
                    msmt = session.query(LotMeasurement).filter_by(
                        lot_number=lot_number, index_code=key
                    ).first()
                    
                    if msmt:
                        msmt.value = value
                    else:
                        if value is not None:
                            msmt = LotMeasurement(lot_number=lot.lot_number, index_code=key, value=value)
                            session.add(msmt)

            session.commit()
            session.refresh(lot)
            return lot
        return None
    except Exception as e:
        session.rollback()
        raise e


def delete_lot_data(session, lot_number):
    """Delete LOT data and associated measurements"""
    try:
        lot = get_lot_by_number(session, lot_number)
        if lot:
            # Delete associated measurements first
            session.query(LotMeasurement).filter_by(lot_number=lot_number).delete()
            session.delete(lot)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e


# Analysis Index Management Functions

def get_all_indices(session, gcms_only=False, basic_only=False):
    """Get all analysis indices"""
    query = session.query(AnalysisIndex)
    if gcms_only:
        query = query.filter(AnalysisIndex.is_gcms == 1)
    if basic_only:
        query = query.filter(AnalysisIndex.is_gcms == 0)
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
