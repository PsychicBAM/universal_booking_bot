import enum
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class SupportMessageStatus(str, enum.Enum):
    OPEN = "open"
    REPLIED = "replied"
    CLOSED = "closed"


class ServiceOrderStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


SERVICE_TYPE_BOOKING = "booking"
SERVICE_TYPE_ORDER = "order"


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phone_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="ru")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bookings: Mapped[list["Booking"]] = relationship(back_populates="client")
    orders: Mapped[list["ServiceOrder"]] = relationship(back_populates="client")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    buffer_after_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requires_location: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ask_client_comment: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_media_to_clients: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    price: Mapped[int] = mapped_column(Integer, default=0)
    service_type: Mapped[str] = mapped_column(String(20), default="booking", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    bookings: Mapped[list["Booking"]] = relationship(back_populates="service")
    orders: Mapped[list["ServiceOrder"]] = relationship(back_populates="service")
    media: Mapped[list["ServiceMedia"]] = relationship(back_populates="service", cascade="all, delete-orphan")
    locations: Mapped[list["ServiceLocation"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )


class ServiceLocation(Base):
    __tablename__ = "service_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    address_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    service: Mapped["Service"] = relationship(back_populates="locations")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="service_location")


class ServiceMedia(Base):
    __tablename__ = "service_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False, index=True)
    media_type: Mapped[str] = mapped_column(String(10), nullable=False)
    telegram_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    service: Mapped["Service"] = relationship(back_populates="media")


class WorkingHours(Base):
    __tablename__ = "working_hours"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday .. 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkingBreak(Base):
    __tablename__ = "working_breaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 0=Monday .. 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UnavailableDate(Base):
    __tablename__ = "unavailable_dates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class UnavailableTimeRange(Base):
    __tablename__ = "unavailable_time_ranges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), default=BookingStatus.PENDING, index=True
    )
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("service_locations.id"), nullable=True, index=True
    )
    service_location_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    service_location_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_reminder_1_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    client_reminder_2_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    admin_reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attendance_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    attendance_responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attendance_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    attendance_reminder_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    attendance_manual_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attendance_manual_sent_by_admin_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attendance_manual_sent_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    # Legacy SQLite columns — kept for INSERT compatibility with existing databases.
    reminder_24h_sent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    reminder_2h_sent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    admin_reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    client: Mapped["Client"] = relationship(back_populates="bookings")
    service: Mapped["Service"] = relationship(back_populates="bookings")
    service_location: Mapped["ServiceLocation | None"] = relationship(back_populates="bookings")


class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    client_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=ServiceOrderStatus.NEW.value, nullable=False)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    service: Mapped["Service"] = relationship(back_populates="orders")
    client: Mapped["Client"] = relationship(back_populates="orders")


class CalendarSettings(Base):
    __tablename__ = "calendar_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    google_calendar_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    google_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_calendar_id: Mapped[str] = mapped_column(String(255), default="primary")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BotSettings(Base):
    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str | None] = mapped_column(String(50), nullable=True)
    booking_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    admin_reply_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    replied_by_admin_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[SupportMessageStatus] = mapped_column(
        Enum(SupportMessageStatus), default=SupportMessageStatus.OPEN, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
