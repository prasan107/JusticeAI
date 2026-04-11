from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.sql import func
from database import Base

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True)
    title = Column(String)
    court = Column(String)
    year = Column(Integer)
    case_type = Column(String)
    ipc_sections = Column(String)       # stored as comma-separated string
    outcome = Column(String)            # "Guilty", "Acquitted", "Appeal Dismissed" etc.
    full_text = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime, default=func.now())
