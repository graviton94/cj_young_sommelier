"""
Database module for managing LOT-specific liquor data using SQLite and SQLAlchemy
"""

import os
from pathlib import Path
from datetime import datetime
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
    entry_date = Column(DateTime, default=datetime.utcnow)
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
    tasting_date = Column(DateTime, default=datetime.utcnow)
    
    # AI-generated content
    ai_flavor_report = Column(Text)
    
    def __repr__(self):
        return f"<SensoryProfile(lot={self.lot_number}, taster={self.taster_name})>"


def init_database():
    """Initialize the database and create all tables"""
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Get a new database session"""
    return SessionLocal()


def add_lot_data(session, lot_data_dict):
    """
    Add new LOT data to the database
    
    Args:
        session: SQLAlchemy session
        lot_data_dict: Dictionary containing LOT data fields
    
    Returns:
        LOTData object if successful, None otherwise
    """
    try:
        lot = LOTData(**lot_data_dict)
        session.add(lot)
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
    """
    Update existing LOT data
    
    Args:
        session: SQLAlchemy session
        lot_number: LOT number to update
        update_dict: Dictionary of fields to update
    
    Returns:
        Updated LOTData object if successful, None otherwise
    """
    try:
        lot = get_lot_by_number(session, lot_number)
        if lot:
            for key, value in update_dict.items():
                if hasattr(lot, key):
                    setattr(lot, key, value)
            session.commit()
            session.refresh(lot)
            return lot
        return None
    except Exception as e:
        session.rollback()
        raise e


def delete_lot_data(session, lot_number):
    """Delete LOT data by lot number"""
    try:
        lot = get_lot_by_number(session, lot_number)
        if lot:
            session.delete(lot)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e


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
