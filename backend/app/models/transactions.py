"""
Sentinel — Database Models: Transactions and Risk
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Integer, Float, Text, ForeignKey, JSON, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.entities import Customer, Merchant


def utcnow():
    return datetime.now(timezone.utc)


class Transaction(Base):
    """
    Core transaction record.
    Every payment event becomes a transaction.
    """
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)

    # Amounts
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")

    # Status
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    # PENDING / AUTHORIZED / CAPTURED / FAILED / REFUNDED

    # Relationships
    customer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    merchant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("merchants.id"), index=True)
    device_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("devices.id"), index=True)
    ip_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ip_addresses.id"), index=True)

    # Metadata
    payment_method: Mapped[str | None] = mapped_column(String(50))
    # card / upi / netbanking / wallet

    # Source
    source: Mapped[str] = mapped_column(String(30), default="API")
    # API / RAZORPAY_WEBHOOK / SIMULATOR / SEED

    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    transaction_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    customer: Mapped["Customer | None"] = relationship("Customer", back_populates="transactions")
    merchant: Mapped["Merchant | None"] = relationship("Merchant", back_populates="transactions")
    risk_score: Mapped["RiskScore | None"] = relationship("RiskScore", back_populates="transaction", uselist=False)
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="transaction")
    analyst_review: Mapped["AnalystReview | None"] = relationship("AnalystReview", back_populates="transaction", uselist=False)
    investigation: Mapped["Investigation | None"] = relationship("Investigation", back_populates="transaction", uselist=False)


class PaymentEvent(Base):
    """
    Raw payment event from Razorpay webhook or simulator.
    Events are stored raw before processing.
    Implements idempotency via event_id.
    """
    __tablename__ = "payment_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)  # idempotency key
    event_type: Mapped[str] = mapped_column(String(100))
    # payment.authorized / payment.captured / payment.failed / order.paid

    source: Mapped[str] = mapped_column(String(30), default="RAZORPAY")
    # RAZORPAY / SIMULATOR

    payload: Mapped[dict] = mapped_column(JSON)  # Raw event payload (sanitized)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    transaction_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("transactions.id"), index=True)

    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RiskScore(Base):
    """
    Risk assessment for a transaction.
    Every risk decision is traceable to model version + features.
    """
    __tablename__ = "risk_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id: Mapped[str] = mapped_column(String(36), ForeignKey("transactions.id"), unique=True)

    # Composite risk score
    risk_score: Mapped[int] = mapped_column(Integer)  # 0-100
    decision: Mapped[str] = mapped_column(String(10))  # APPROVE / REVIEW / HOLD

    # Component scores
    ml_score: Mapped[float | None] = mapped_column(Float)          # XGBoost probability
    behavioral_score: Mapped[float | None] = mapped_column(Float)  # Isolation Forest score
    graph_score: Mapped[float | None] = mapped_column(Float)       # Graph risk score

    # Model metadata
    model_version: Mapped[str | None] = mapped_column(String(50))

    # Feature snapshot (for reproducibility)
    features_snapshot: Mapped[dict | None] = mapped_column(JSON)

    # SHAP / explanation
    risk_reasons: Mapped[list | None] = mapped_column(JSON)
    # [{"reason": "Unusual amount", "contribution": 28}, ...]

    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="risk_score")


class FraudCluster(Base):
    """
    A detected cluster of suspicious entities.
    """
    __tablename__ = "fraud_clusters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cluster_type: Mapped[str] = mapped_column(String(50))
    # DEVICE_SHARING / IP_CLUSTER / TRANSACTION_BURST / COORDINATED_FRAUD

    node_count: Mapped[int] = mapped_column(Integer)
    edge_count: Mapped[int] = mapped_column(Integer)
    max_risk_score: Mapped[int] = mapped_column(Integer)
    entity_ids: Mapped[list] = mapped_column(JSON)  # list of entity IDs in cluster
    cluster_metadata: Mapped[dict | None] = mapped_column(JSON)

    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Investigation(Base):
    """
    AI investigation report for a transaction.
    LLM-generated but structured with verified evidence.
    """
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id: Mapped[str] = mapped_column(String(36), ForeignKey("transactions.id"), unique=True)

    # AI output — always labeled as AI-generated
    summary: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[list | None] = mapped_column(JSON)
    suspicious_relationships: Mapped[list | None] = mapped_column(JSON)
    recommended_action: Mapped[str | None] = mapped_column(String(30))
    analyst_questions: Mapped[list | None] = mapped_column(JSON)
    confidence: Mapped[str | None] = mapped_column(String(10))  # LOW / MEDIUM / HIGH

    model_used: Mapped[str | None] = mapped_column(String(50))
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    generation_error: Mapped[str | None] = mapped_column(Text)
    # If LLM is unavailable, error is stored, not silently ignored

    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="investigation")


class AnalystReview(Base):
    """
    Human analyst review and override for a transaction.
    Every analyst action creates a permanent record.
    """
    __tablename__ = "analyst_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id: Mapped[str] = mapped_column(String(36), ForeignKey("transactions.id"), unique=True)

    analyst_id: Mapped[str | None] = mapped_column(String(255))  # future: JWT user ID
    action: Mapped[str] = mapped_column(String(30))
    # CONFIRM_FRAUD / MARK_FALSE_POSITIVE / RELEASE / KEEP_ON_HOLD / APPROVE

    reason: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="analyst_review")


class AuditLog(Base):
    """
    Immutable audit log for every important action.
    Never deleted, never modified.
    """
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("transactions.id"), index=True)
    event_id: Mapped[str | None] = mapped_column(String(255), index=True)

    action: Mapped[str] = mapped_column(String(50))
    # RISK_DECISION / ANALYST_OVERRIDE / WEBHOOK_RECEIVED / SIMULATION_RUN / etc.

    actor: Mapped[str] = mapped_column(String(50), default="SYSTEM")
    # SYSTEM / ANALYST / SIMULATOR

    details: Mapped[dict | None] = mapped_column(JSON)
    # {risk_score, decision, model_version, reason, ...}

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transaction: Mapped["Transaction | None"] = relationship("Transaction", back_populates="audit_logs")


class ModelVersion(Base):
    """
    Tracks trained model versions.
    Every risk decision is linked to the model that made it.
    """
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version: Mapped[str] = mapped_column(String(50), unique=True)  # e.g. "xgb-v1"
    model_type: Mapped[str] = mapped_column(String(50))  # XGBoost / LogisticRegression / etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    # Dataset info
    dataset_name: Mapped[str | None] = mapped_column(String(255))
    dataset_checksum: Mapped[str | None] = mapped_column(String(64))  # SHA256

    # Features
    feature_names: Mapped[list | None] = mapped_column(JSON)
    feature_count: Mapped[int | None] = mapped_column(Integer)

    # Metrics (actual evaluated values, not fabricated)
    pr_auc: Mapped[float | None] = mapped_column(Float)
    roc_auc: Mapped[float | None] = mapped_column(Float)
    precision: Mapped[float | None] = mapped_column(Float)
    recall: Mapped[float | None] = mapped_column(Float)
    f1_score: Mapped[float | None] = mapped_column(Float)
    false_positive_rate: Mapped[float | None] = mapped_column(Float)
    false_negative_rate: Mapped[float | None] = mapped_column(Float)

    # Policy thresholds used at training
    low_threshold: Mapped[int | None] = mapped_column(Integer)
    high_threshold: Mapped[int | None] = mapped_column(Integer)

    artifact_path: Mapped[str | None] = mapped_column(String(500))
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
