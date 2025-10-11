from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fastapi.security import HTTPBearer
from app.database import get_db
from app.models import Car, Inspection, Booking
from app.routes import router

app = FastAPI()
security = HTTPBearer()

# Define the base for declarative models
Base = declarative_base()

# Define the async engine and session
async_engine = create_async_engine(
    "mysql+mysqlconnector://authuser:authpass@localhost:3306/authdb",
    pool_pre_ping=True,
    pool_size=10,
    pool_recycle=1800,
)
async_session_maker = sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)

# Dependency for getting the database session
async def get_db():
    async with async_session_maker() as session:
        yield session

# Include the routes
app.include_router(router)

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)