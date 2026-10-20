import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///./ns_capital.db"), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
class Base(DeclarativeBase): pass
class Audit(Base):
    __tablename__="audit_events"
    id=Column(Integer,primary_key=True)
    timestamp=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    actor=Column(String(200),nullable=False)
    action=Column(String(80),nullable=False)
    details=Column(Text,nullable=False)
class Signal(Base):
    __tablename__="signals"
    id=Column(Integer,primary_key=True)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    strategy=Column(String(100),nullable=False)
    symbol=Column(String(32),nullable=False)
    side=Column(String(8),nullable=False)
    volume=Column(Float,nullable=False)
    sl=Column(Float,nullable=False)
    tp=Column(Float,nullable=False)
    confidence=Column(Float,nullable=False)
    state=Column(String(32),default="PROPOSED")
    mt5_ticket=Column(String(40),nullable=True)
Base.metadata.create_all(engine)
