"""NEBANK ORM models. Single source of truth for the schema."""
from __future__ import annotations

import enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TxKind(str, enum.Enum):
    expense = "expense"
    income = "income"


class TxSource(str, enum.Enum):
    text = "text"
    voice = "voice"
    photo = "photo"
    sms = "sms"
    crypto = "crypto"
    manual = "manual"
    stash = "stash"


class SubPeriod(str, enum.Enum):
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))

    language: Mapped[str] = mapped_column(String(2), default="en")  # ru | en
    base_currency: Mapped[str] = mapped_column(String(8), default="USD")
    voice_lang: Mapped[str] = mapped_column(String(2), default="en")
    onboarded: Mapped[bool] = mapped_column(Boolean, default=False)
    theme: Mapped[str] = mapped_column(String(16), default="light")  # always light per TZ

    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Round-up stash
    stash_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    stash_round_to: Mapped[int] = mapped_column(Integer, default=100)  # round expenses up to nearest N
    stash_balance: Mapped[float] = mapped_column(Numeric(18, 2), default=0)

    referral_code: Mapped[str | None] = mapped_column(String(16), unique=True, index=True)
    referred_by: Mapped[int | None] = mapped_column(BigInteger)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    categories: Mapped[list["Category"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("user_id", "name", "kind", name="uq_cat_user_name_kind"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    kind: Mapped[TxKind] = mapped_column(Enum(TxKind, name="txkind"), default=TxKind.expense)
    color: Mapped[str] = mapped_column(String(9), default="#C9A227")  # gold default
    icon: Mapped[str] = mapped_column(String(32), default="dot")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="categories")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_tx_user_date", "user_id", "occurred_at"),
        UniqueConstraint("user_id", "dedup_hash", name="uq_tx_dedup"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))

    kind: Mapped[TxKind] = mapped_column(Enum(TxKind, name="txkind"), default=TxKind.expense)
    # amount stored in the user's base currency (positive magnitude)
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    # original input
    original_amount: Mapped[float] = mapped_column(Numeric(28, 10))
    original_currency: Mapped[str] = mapped_column(String(8))
    fx_rate: Mapped[float] = mapped_column(Numeric(28, 10), default=1)  # original->base on occurred day

    title: Mapped[str | None] = mapped_column(String(160))  # item / place name, kept verbatim
    note: Mapped[str | None] = mapped_column(Text)
    source: Mapped[TxSource] = mapped_column(Enum(TxSource, name="txsource"), default=TxSource.text)
    raw_text: Mapped[str | None] = mapped_column(Text)

    # crypto provenance (optional)
    crypto_network: Mapped[str | None] = mapped_column(String(16))  # bitcoin | erc20 | trc20
    crypto_txid: Mapped[str | None] = mapped_column(String(128))

    dedup_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    occurred_at: Mapped[date] = mapped_column(Date, default=lambda: utcnow().date())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="transactions")
    category: Mapped[Category | None] = relationship()


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(120))
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    period: Mapped[SubPeriod] = mapped_column(Enum(SubPeriod, name="subperiod"), default=SubPeriod.monthly)
    next_charge: Mapped[date] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    # fingerprint to detect recurring charges (merchant+amount)
    fingerprint: Mapped[str | None] = mapped_column(String(80), index=True)
    remind_3d_sent_for: Mapped[date | None] = mapped_column(Date)
    remind_1d_sent_for: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("user_id", "category_id", name="uq_budget_user_cat"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    limit_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Habit(Base):
    """'Отказ от вредных платежей' — refusing harmful payments."""

    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    # estimated cost avoided per day (in base currency)
    daily_cost: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    started_at: Mapped[date] = mapped_column(Date, default=lambda: utcnow().date())
    last_relapse: Mapped[date | None] = mapped_column(Date)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    target_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    current_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    achieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AchievementProgress(Base):
    __tablename__ = "achievement_progress"
    __table_args__ = (UniqueConstraint("user_id", "code", name="uq_ach_user_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(48))
    best_value: Mapped[float] = mapped_column(Float, default=0)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FamilyGroup(Base):
    __tablename__ = "family_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    invite_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FamilyMember(Base):
    __tablename__ = "family_members"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_member"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("family_groups.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16), default="member")  # owner | member
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    stars: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(32), default="premium")
    payload: Mapped[str | None] = mapped_column(String(128))
    charge_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RatePoint(Base):
    """On-disk cache of real rates (historical, by day) to avoid re-fetching."""

    __tablename__ = "rate_points"
    __table_args__ = (UniqueConstraint("symbol", "quote", "day", name="uq_rate_point"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)  # e.g. BTC, EUR
    quote: Mapped[str] = mapped_column(String(16), default="USD")
    day: Mapped[date] = mapped_column(Date, index=True)
    price: Mapped[float] = mapped_column(Numeric(28, 10))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
