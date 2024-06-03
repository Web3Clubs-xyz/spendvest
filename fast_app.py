from fastapi import FastAPI, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLAlchemy models
Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

# FastAPI app
app = FastAPI()

# Database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# CRUD operations
@app.post("/sessions/", response_model=Session)
def create_session(name: str):
    db = SessionLocal()
    session = Session(name=name)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@app.get("/sessions/{session_id}", response_model=Session)
def read_session(session_id: int):
    db = SessionLocal()
    session = db.query(Session).filter(Session.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@app.put("/sessions/{session_id}", response_model=Session)
def update_session(session_id: int, name: str):
    db = SessionLocal()
    session = db.query(Session).filter(Session.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    session.name = name
    db.commit()
    db.refresh(session)
    return session

@app.delete("/sessions/{session_id}", response_model=Session)
def delete_session(session_id: int):
    db = SessionLocal()
    session = db.query(Session).filter(Session.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()
    return session
