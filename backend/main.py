from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import database  # This imports the database.py file you have next to it

# This automatically creates the database file and tables if they don't exist
database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Nail Parlor Platform API",
    description="Backend service for handling tech commissions and shop operations.",
    version="2.0.0"
)

# Enable CORS so your Mac's frontend can securely talk to the VM container
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Add a new Nail Tech
@app.post("/api/v1/techs")
def create_tech(name: str, role: str = "tech", db: Session = Depends(database.get_db)):
    db_tech = db.query(database.NailTech).filter(database.NailTech.name == name).first()
    if db_tech:
        raise HTTPException(status_code=400, detail="Tech already exists")
    new_tech = database.NailTech(name=name, role=role)
    db.add(new_tech)
    db.commit()
    db.refresh(new_tech)
    return new_tech

# 2. Log a Service / Transaction (With Auto Math Splits!)
@app.post("/api/v1/transactions")
def log_transaction(
    client_name: str, 
    service_name: str, 
    total_charged: float, 
    tech_id: int, 
    db: Session = Depends(database.get_db)
):
    tech = db.query(database.NailTech).filter(database.NailTech.id == tech_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Nail Tech not found")
    
    # Calculate the splits automatically (40% to tech, 60% to shop)
    commission = total_charged * 0.40
    profit = total_charged * 0.60
    
    new_transaction = database.Transaction(
        client_name=client_name,
        service_name=service_name,
        total_charged=total_charged,
        tech_commission=commission,
        shop_profit=profit,
        tech_id=tech_id
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

# 3. Get Financial Dashboard Data (Boss View)
@app.get("/api/v1/operations/dashboard")
def get_dashboard_summary(db: Session = Depends(database.get_db)):
    transactions = db.query(database.Transaction).all()
    
    total_revenue = sum(t.total_charged for t in transactions)
    total_commissions = sum(t.tech_commission for t in transactions)
    total_shop_profit = sum(t.shop_profit for t in transactions)
    
    return {
        "total_transactions_logged": len(transactions),
        "gross_revenue": total_revenue,
        "payouts_to_techs": total_commissions,
        "net_shop_profit": total_shop_profit
    }

# 4. Get individual Tech Performance (Tech View)
@app.get("/api/v1/techs/{tech_id}/performance")
def get_tech_performance(tech_id: int, db: Session = Depends(database.get_db)):
    transactions = db.query(database.Transaction).filter(database.Transaction.tech_id == tech_id).all()
    total_earned = sum(t.tech_commission for t in transactions)
    
    return {
        "tech_id": tech_id,
        "services_rendered": len(transactions),
        "total_commission_earned": total_earned,
        "history": [
            {"client": t.client_name, "service": t.service_name, "earned": t.tech_commission, "date": t.date}
            for t in transactions
        ]
    }

# 5. Create a Client Booking
@app.post("/api/v1/bookings")
def create_booking(
    client_name: str, 
    client_phone: str, 
    service_requested: str, 
    booking_time: str, 
    db: Session = Depends(database.get_db)
):
    new_booking = database.Booking(
        client_name=client_name,
        client_phone=client_phone,
        service_requested=service_requested,
        booking_time=booking_time,
        status="Scheduled"
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking

# 6. Fetch All Bookings (Notion Database View style)
@app.get("/api/v1/bookings")
def get_bookings(db: Session = Depends(database.get_db)):
    return db.query(database.Booking).order_by(database.Booking.booking_time.asc()).all()