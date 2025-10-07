from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.config import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, unique=True)
    password = Column(String)
    role = Column(String, default="client")

    appointments = relationship("InspectionAppointment", back_populates="user")