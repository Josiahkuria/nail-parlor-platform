from fastapi import FastAPI

app = FastAPI(
    title="Nail Parlor Platform API",
    description="Backend service for managing appointments, services, and staff.",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Welcome to the Nail Parlor Platform API"}

@app.get("/api/v1/services")
def get_services():
    return [
        {"id": 1, "name": "Manicure", "price": 1500, "duration_mins": 45},
        {"id": 2, "name": "Pedicure", "price": 2000, "duration_mins": 60},
        {"id": 3, "name": "Gel Polish Application", "price": 1200, "duration_mins": 30}
    ]