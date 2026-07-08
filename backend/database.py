from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import datetime

# Local database file path
DATABASE_URL = "sqlite:////tmp/nail_parlor.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 1. Accounts Table (Handles both Boss & Workers)
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="tech")  # 'admin' (Boss) or 'tech' (Nail Tech)
    is_active = Column(Boolean, default=True)
    
    # Links this user to their logged transactions
    transactions = relationship("Transaction", back_populates="tech")

# 2. Daily Sales & Commission Math Table
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, index=True, nullable=False)
    service_name = Column(String, nullable=False)
    total_charged = Column(Float, nullable=False)
    
    # Splitting automated math (40% tech / 60% shop)
    tech_commission = Column(Float, nullable=False)
    shop_profit = Column(Float, nullable=False)
    
    tech_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relational link back to the user account
    tech = relationship("User", back_populates="transactions")

# 3. Client Bookings Table (With WhatsApp Automation Tracker Flags)
class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, index=True, nullable=False)
    client_phone = Column(String, nullable=False)
    service_requested = Column(String, nullable=False)
    booking_time = Column(DateTime, nullable=False)  # Saved as actual timestamp object
    status = Column(String, default="Scheduled")     # Scheduled, In-Progress, Completed, Cancelled
    
    # ─── ADD THESE TWO LINES HERE ───
    tech_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Nullable=True allows unassigned bookings if needed
    tech = relationship("User")
    # ────────────────────────────────
    
    # n8n loop uses these flags to make sure it never sends duplicate messages!
    reminded_30m = Column(Boolean, default=False)   
    reminded_30d = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    
# Database session helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()