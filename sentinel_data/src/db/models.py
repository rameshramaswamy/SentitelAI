# sentinel_data/src/db/models.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Organization(Base):
    """Top-level tenant."""
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    api_key_hash = Column(String, nullable=True) # For API access
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="organization")

class User(Base):
    """Agents or Managers."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="agent") # agent, manager, admin
    created_at = Column(DateTime, default=datetime.utcnow, primary_key=True) 
    organization = relationship("Organization", back_populates="users")
    calls = relationship("Call", back_populates="user")
    __table_args__ = (
        # OPTIMIZATION: Partition by Range (Time)
        {"postgresql_partition_by": "RANGE (created_at)"},
    )

class Call(Base):
    """A single voice interaction session."""
    __tablename__ = "calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    session_id = Column(String, unique=True, nullable=False) # Maps to websocket session
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    # Storage References
    s3_key_raw = Column(String, nullable=True) # Path to minio/s3 audio
    status = Column(String, default="in_progress") # in_progress, completed, processed
    
    # Metadata
    customer_phone = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)

    user = relationship("User", back_populates="calls")
    transcripts = relationship("TranscriptSegment", back_populates="call")

class TranscriptSegment(Base):
    """Granular speech segments for search/replay."""
    __tablename__ = "transcript_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id"), nullable=False)
    
    text = Column(Text, nullable=False)
    start_offset = Column(Float, nullable=False) # Seconds from start
    end_offset = Column(Float, nullable=False)
    speaker = Column(String, default="agent") # agent vs customer (diarization)
    
    # Vector ID for Qdrant lookup
    vector_id = Column(String, nullable=True)

    call = relationship("Call", back_populates="transcripts")