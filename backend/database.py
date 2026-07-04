from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# This creates a local file named 'nail_parlor.db' inside the container
DATABASE_URL = "sqlite:///./nail_parlor.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 1. Nail Techs Table
class NailTech(Base):
    __tablename__ = "nail_techs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    role = Column(String, default="tech")  # 'tech' or 'admin'

# 2. Daily Transactions & Commission Math Table
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, index=True)
    service_name = Column(String)
    total_charged = Column(Float)
    
    # The automatic math rules live here
    tech_commission = Column(Float)  # Total * 0.40 (40%)
    shop_profit = Column(Float)      # Total * 0.60 (60%)
    
    tech_id = Column(Integer, ForeignKey("nail_techs.id"))
    date = Column(DateTime, default=datetime.datetime.utcnow)

# Helper function to get database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()