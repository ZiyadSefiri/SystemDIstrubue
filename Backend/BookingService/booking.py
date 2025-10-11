# backend.py
from datetime import datetime, timedelta
from typing import List
from fastapi import FastAPI, HTTPException, Query, Header, Depends
from pydantic import BaseModel
from sqlalchemy import text
from Utility.connect import connect_database
from jose import jwt, JWTError

# --- JWT settings ---
SECRET_KEY = "YOUR_SECRET_KEY"  # Must match the AuthService secret
ALGORITHM = "HS256"

# --- Create engine using utility function ---
engine = connect_database()

# --- FastAPI app ---
app = FastAPI(title="Car Booking Service")

# --- Pydantic models ---
class AvailableSlot(BaseModel):
    start_time: str
    end_time: str

class ReservationRequest(BaseModel):
    start_time: str
    day: str
    car_model: str
    car_license_plate: str

# --- Helper functions ---
def get_reserved_slots(car_id: int, day: str):
    query = text("""
        SELECT reservation_date
        FROM reservations
        WHERE car_id = :car_id
        AND DATE(reservation_date) = :day
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"car_id": car_id, "day": day}).fetchall()
    return [row[0] for row in result]

def generate_available_slots(reserved_slots: List[datetime], day: str):
    opening = datetime.strptime(f"{day} 08:00", "%Y-%m-%d %H:%M")
    closing = datetime.strptime(f"{day} 18:00", "%Y-%m-%d %H:%M")
    slot_duration = timedelta(hours=2)

    slots = []
    current = opening
    while current + slot_duration <= closing:
        overlap = any(
            current < reserved + slot_duration and current + slot_duration > reserved
            for reserved in reserved_slots
        )
        if not overlap:
            slots.append(AvailableSlot(
                start_time=current.strftime("%H:%M"),
                end_time=(current + slot_duration).strftime("%H:%M")
            ))
        current += slot_duration
    return slots

# --- JWT dependency ---
def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[len("Bearer "):]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# --- API endpoints ---
@app.get("/cars", summary="List all cars")
def list_cars():
    query = text("SELECT car_id, model, license_plate FROM cars")
    with engine.connect() as conn:
        result = conn.execute(query).fetchall()
    return [{"car_id": r[0], "model": r[1], "license_plate": r[2]} for r in result]

@app.get("/availability/{car_id}", response_model=List[AvailableSlot])
def get_availability(car_id: int, day: str = Query(..., description="Date in YYYY-MM-DD format")):
    try:
        datetime.strptime(day, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")
    
    reserved_slots = get_reserved_slots(car_id, day)
    slots = generate_available_slots(reserved_slots, day)
    return slots

@app.post("/reserve", summary="Reserve a car")
def reserve_car(request: ReservationRequest, user_id: int = Depends(get_current_user)):
    # Parse reservation datetime
    try:
        reservation_datetime = datetime.strptime(f"{request.day} {request.start_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format, use HH:MM")

    # Ensure car exists or insert it
    with engine.connect() as conn:
        car_row = conn.execute(
            text("SELECT car_id FROM cars WHERE license_plate = :license_plate"),
            {"license_plate": request.car_license_plate}
        ).fetchone()

        if car_row is None:
            # Insert new car
            conn.execute(
                text("INSERT INTO cars (model, license_plate) VALUES (:model, :license_plate)"),
                {"model": request.car_model, "license_plate": request.car_license_plate}
            )
            conn.commit()
            car_id = conn.execute(
                text("SELECT car_id FROM cars WHERE license_plate = :license_plate"),
                {"license_plate": request.car_license_plate}
            ).fetchone()[0]
        else:
            car_id = car_row[0]

        # Check for overlapping reservations
        reserved_slots = get_reserved_slots(car_id, request.day)
        slot_duration = timedelta(hours=2)
        for reserved in reserved_slots:
            if reservation_datetime < reserved + slot_duration and reservation_datetime + slot_duration > reserved:
                raise HTTPException(status_code=400, detail="Time slot already reserved")

        # Insert reservation
        conn.execute(
            text("""
                INSERT INTO reservations (reservation_date, user_id, car_id)
                VALUES (:reservation_date, :user_id, :car_id)
            """),
            {"reservation_date": reservation_datetime, "user_id": user_id, "car_id": car_id}
        )
        conn.commit()

    return {"message": "Reservation successful", "reservation_time": request.start_time, "car_id": car_id}

# --- Run server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("BookingService.booking:app", host="0.0.0.0", port=8080, reload=True)
