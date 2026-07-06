from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import List
import datetime
import database

# ─── SECURITY CONFIGURATION ───
# In production, change this secret key to a complex random password string!
SECRET_KEY = "NAIL_PARLOR_WORKSPACE_SUPER_SECRET_TOKEN_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # Locks authentication sessions to a standard 8-hour shift

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Automatically generate tables and structure mappings inside sqlite file
database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Nail Parlor Enterprise Management Hub",
    description="Secure Role-Based Access Engine and Operational Automation Interface.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── CRYPTOGRAPHY HELPERS ───
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(database.User).filter(database.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# ─── 1. AUTHENTICATION & BOOTSTRAP ROUTES ───

@app.post("/api/v1/auth/bootstrap-system", tags=["System Initialization"])
def bootstrap_system(db: Session = Depends(database.get_db)):
    """One-time route to seed the primary Boss admin account if it doesn't exist."""
    admin_exists = db.query(database.User).filter(database.User.role == "admin").first()
    if admin_exists:
        raise HTTPException(status_code=400, detail="System administration account is already initialized.")
    
    boss_user = database.User(
        username="bossadmin",
        hashed_password=get_password_hash("BossSecuredPass2026"),
        full_name="Studio Boss",
        role="admin"
    )
    db.add(boss_user)
    db.commit()
    return {"status": "Success", "message": "Admin profile created.", "username": "bossadmin"}

@app.post("/api/v1/auth/login", tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    """Validates login credentials and returns a secure role-scoped JWT token."""
    user = db.query(database.User).filter(database.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password configuration.")
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": user.role, 
        "full_name": user.full_name
    }


# ─── 2. BOSS ADMINISTRATIVE INTERFACES ───

@app.post("/api/v1/admin/techs", tags=["Admin Controls"])
def register_technician(username: str, plain_pass: str, full_name: str, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Allows Admin to create accounts for Nail Tech workers. Workers are blocked from here."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Requires Executive Privilege.")
    
    exists = db.query(database.User).filter(database.User.username == username).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists in the studio base.")
        
    new_tech = database.User(
        username=username,
        hashed_password=get_password_hash(plain_pass),
        full_name=full_name,
        role="tech"
    )
    db.add(new_tech)
    db.commit()
    return {"status": "Created", "tech_id": new_tech.id, "name": new_tech.full_name}

@app.get("/api/v1/admin/dashboard", tags=["Admin Controls"])
def get_global_metrics(current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Exposes global studio financials and a complete performance breakdown to the Boss."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Administrative verification required.")
    
    txs = db.query(database.Transaction).all()
    techs = db.query(database.User).filter(database.User.role == "tech").all()
    
    tech_matrix = []
    for t in techs:
        tech_txs = [x for x in txs if x.tech_id == t.id]
        tech_matrix.append({
            "tech_id": t.id,
            "name": t.full_name,
            "services_logged": len(tech_txs),
            "commission_earned": sum(x.tech_commission for x in tech_txs)
        })
        
    return {
        "gross_revenue": sum(x.total_charged for x in txs),
        "total_payouts_to_techs": sum(x.tech_commission for x in txs),
        "net_shop_profit": sum(x.shop_profit for x in txs),
        "total_transactions_logged": len(txs),
        "technicians_breakdown": tech_matrix
    }


# ─── 3. WORKER ACCOUNT INTERFACES ───

@app.post("/api/v1/transactions", tags=["Operational Sales"])
def log_transaction(client_name: str, service_name: str, total_charged: float, target_tech_id: int = None, current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Logs sales and auto-calculates splits. Techs default to self; Admin can log for anyone."""
    if current_user.role == "admin":
        if not target_tech_id:
            raise HTTPException(status_code=400, detail="Admin profiles must specify a target_tech_id.")
        assigned_id = target_tech_id
    else:
        assigned_id = current_user.id  # Workers are blocked from forging sales under another ID

    new_tx = database.Transaction(
        client_name=client_name,
        service_name=service_name,
        total_charged=total_charged,
        tech_commission=total_charged * 0.40,  # 40% Commission Math
        shop_profit=total_charged * 0.60,      # 60% Studio Profit Share
        tech_id=assigned_id
    )
    db.add(new_tx)
    db.commit()
    return {"status": "Success", "transaction_id": new_tx.id}

@app.get("/api/v1/tech/dashboard", tags=["Worker Performance"])
def get_isolated_tech_metrics(current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Isolates view states. Returns financial aggregates matching ONLY this worker's token identity."""
    if current_user.role != "tech":
        raise HTTPException(status_code=400, detail="Admin accounts must query the global metrics dashboard endpoint.")
    
    txs = db.query(database.Transaction).filter(database.Transaction.tech_id == current_user.id).all()
    return {
        "worker_name": current_user.full_name,
        "role": current_user.role,
        "total_services_logged": len(txs),
        "your_total_commission": sum(x.tech_commission for x in txs),
        "history": [{"client": x.client_name, "service": x.service_name, "commission": x.tech_commission, "date": x.date} for x in txs]
    }


# ─── 4. UNPROTECTED PUBLIC BOOKINGS NODE ───

@app.post("/api/v1/public/bookings", tags=["Public Client Bookings"])
def create_public_booking(client_name: str, client_phone: str, service_requested: str, booking_time_iso: str, db: Session = Depends(database.get_db)):
    """Public appointment gateway. Accepts standard ISO timestamp strings with zero login barriers."""
    try:
        parsed_time = datetime.datetime.fromisoformat(booking_time_iso)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO date format string. Match schema pattern: YYYY-MM-DDTHH:MM")
        
    new_booking = database.Booking(
        client_name=client_name,
        client_phone=client_phone,
        service_requested=service_requested,
        booking_time=parsed_time
    )
    db.add(new_booking)
    db.commit()
    return {"status": "Confirmed", "booking_id": new_booking.id}

@app.get("/api/v1/operations/bookings", tags=["Shared Schedules Feed"])
def get_shared_appointments(current_user: database.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    """Allows logged-in Admins and Techs to review upcoming appointments to coordinate slots."""
    return db.query(database.Booking).filter(
        database.Booking.booking_time >= datetime.datetime.utcnow() - datetime.timedelta(hours=4)
    ).order_by(database.Booking.booking_time.asc()).all()


# ─── 5. BACKGROUND AUTOMATION ENGINE FOR n8n WHATSAPP LOOPS ───

@app.get("/api/v1/automation/check-reminders", tags=["n8n Automation Pipeline"])
def harvest_pending_reminders(db: Session = Depends(database.get_db)):
    """n8n polls this endpoint. Extracts exact alert clusters and isolates targets to prevent message duplication."""
    now = datetime.datetime.utcnow()
    
    # Target 1: Appointments arriving in 30 minutes (25-35 min window)
    window_start = now + datetime.timedelta(minutes=25)
    window_end = now + datetime.timedelta(minutes=35)
    upcoming = db.query(database.Booking).filter(
        database.Booking.booking_time >= window_start,
        database.Booking.booking_time <= window_end,
        database.Booking.reminded_30m == False
    ).all()
    
    # Target 2: Clients who visited exactly 30 days ago (12-hour fuzzy window evaluation)
    past_target = now - datetime.timedelta(days=30)
    past_start = past_target - datetime.timedelta(hours=12)
    past_end = past_target + datetime.timedelta(hours=12)
    retention = db.query(database.Booking).filter(
        database.Booking.booking_time >= past_start,
        database.Booking.booking_time <= past_end,
        database.Booking.reminded_30d == False
    ).all()
    
    return {
        "upcoming_alerts": [
            {
                "id": b.id, "client_name": b.client_name, "client_phone": b.client_phone,
                "service": b.service_requested, "time": b.booking_time.strftime("%I:%M %p")
            } for b in upcoming
        ],
        "retention_alerts": [
            {
                "id": b.id, "client_name": b.client_name, "client_phone": b.client_phone,
                "service": b.service_requested
            } for b in retention
        ]
    }

@app.post("/api/v1/automation/mark-reminded/{booking_id}", tags=["n8n Automation Pipeline"])
def mark_reminder_flag_complete(booking_id: int, reminder_type: str, db: Session = Depends(database.get_db)):
    """Flip flags to True once n8n delivers the WhatsApp template to prevent looping."""
    booking = db.query(database.Booking).filter(database.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Target appointment index record does not exist.")
        
    if reminder_type == "30m":
        booking.reminded_30m = True
    elif reminder_type == "30d":
        booking.reminded_30d = True
        
    db.commit()
    return {"status": "Success", "message": "State flag logged."}