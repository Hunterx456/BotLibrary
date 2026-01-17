from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean, BigInteger
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship
from datetime import datetime
import config

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    role = Column(String, default="user") # owner, sudo, mod, user
    join_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    submissions = relationship("BotSubmission", back_populates="submitter", foreign_keys="BotSubmission.submitted_by")
    reviews = relationship("BotSubmission", back_populates="reviewer", foreign_keys="BotSubmission.claimed_by")

class Bot(Base):
    __tablename__ = "bots"
    bot_id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    username = Column(String, unique=True)
    description = Column(String)
    features = Column(String)
    category = Column(String)
    
    # Rating stats
    rating = Column(Float, default=0.0)
    vote_count = Column(Integer, default=0)
    # Keeping track of who voted to prevent duplicates: {user_id: score}
    votes_data = Column(JSON, default=dict)
    
    submitted_by = Column(BigInteger, ForeignKey("users.user_id"))
    approved_by = Column(BigInteger, ForeignKey("users.user_id"))
    
    submission_date = Column(DateTime)
    approval_date = Column(DateTime, default=datetime.utcnow)
    channel_message_id = Column(Integer, nullable=True)

class BotSubmission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_username = Column(String)
    description = Column(String)
    features = Column(String)
    category = Column(String)
    
    submitted_by = Column(BigInteger, ForeignKey("users.user_id"))
    submitter = relationship("User", foreign_keys=[submitted_by], back_populates="submissions")
    
    submission_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending") # pending, under_review, approved, rejected
    rejection_reason = Column(String, nullable=True)
    
    claimed_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    reviewer = relationship("User", foreign_keys=[claimed_by], back_populates="reviews")
    claim_time = Column(DateTime, nullable=True)
    
engine = create_engine(config.DB_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
