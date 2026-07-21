from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ==========================================
# 1. DATABASE SETUP (SQLite)
# ==========================================
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define how the user table looks in the database
class DBUser(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

# Create the database table
Base.metadata.create_all(bind=engine)

# Dependency to get a fresh database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 2. API SETUP & CORS
# ==========================================
app = FastAPI()

# CRITICAL: This allows your frontend (even if running on localhost) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with your actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define what data we expect from the frontend (Validation)
class UserCreate(BaseModel):
    name: str
    email: EmailStr # Ensures the frontend sends a valid email format

# ==========================================
# 3. THE ENDPOINTS (The routes your frontend hits)
# ==========================================

@app.post("/api/users")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if the email already exists
    existing_user = db.query(DBUser).filter(DBUser.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Save to database
    new_user = DBUser(name=user_data.name, email=user_data.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User stored successfully", "user_id": new_user.id}

@app.get("/api/users")
def get_all_users(db: Session = Depends(get_db)):
    # Optional endpoint just to see what's stored
    return db.query(DBUser).all()
