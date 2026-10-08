"""Small, bounded event ingestion service with data-quality telemetry."""
import os
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, field_validator
from sqlalchemy import DateTime, Float, String, create_engine, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class EventRow(Base):
    __tablename__ = "events"
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source: Mapped[str] = mapped_column(String(32), index=True)
    value: Mapped[float] = mapped_column(Float)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    source: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,31}$")
    value: float = Field(ge=0, le=1_000_000, allow_inf_nan=False)
    event_time: AwareDatetime

    @field_validator("event_time")
    @classmethod
    def valid_time(cls, value):
        if value > datetime.now(timezone.utc) + timedelta(seconds=60):
            raise ValueError("event_time must not be more than 60 seconds in the future")
        return value


def create_app(database_url=None, api_key=None):
    url = database_url or os.environ["DATABASE_URL"]
    key = api_key or os.environ["INGEST_API_KEY"]
    if len(key) < 16:
        raise ValueError("INGEST_API_KEY must contain at least 16 characters")
    engine = create_engine(url, pool_pre_ping=True, **(
        {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else
        {"connect_args": {"connect_timeout": 3, "options": "-c statement_timeout=5000"}}
    ))
    sessions = sessionmaker(engine)
    registry = CollectorRegistry()
    ingested = Counter("dop_events", "Event outcomes", ["outcome"], registry=registry)
    for outcome in ("accepted", "rejected", "duplicate", "db_error"):
        ingested.labels(outcome)
    stale = Counter("dop_stale_events", "Accepted events older than 5 minutes", registry=registry)
    latency = Histogram("dop_ingest_duration_seconds", "Ingest request duration", registry=registry)
    age = Histogram("dop_event_age_seconds", "Age at acceptance", buckets=(1, 10, 60, 300, 900, 3600), registry=registry)

    @asynccontextmanager
    async def lifespan(app):
        # Schema creation is an explicit one-shot init step, not a replica startup race.
        yield
        engine.dispose()

    app = FastAPI(title="Data Observability Platform", version="1.0.0", lifespan=lifespan)
    app.state.engine = engine
    app.state.registry = registry

    @app.middleware("http")
    async def measure(request: Request, call_next):
        if request.url.path != "/v1/events" or request.method != "POST":
            return await call_next(request)
        started = time.perf_counter()
        try:
            return await call_next(request)
        finally:
            latency.observe(time.perf_counter() - started)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        if request.url.path == "/v1/events" and request.method == "POST":
            ingested.labels("rejected").inc()
        # Do not echo submitted data or exception internals.
        return JSONResponse(status_code=422, content={"detail": "Invalid event schema, value, or timestamp"})

    def authenticate(x_api_key: str = Header(default="")):
        if not secrets.compare_digest(x_api_key.encode(), key.encode()):
            raise HTTPException(401, "Invalid API key")

    @app.get("/health/live")
    def live():
        return {"status": "alive"}

    @app.get("/health/ready")
    def ready():
        try:
            with sessions() as session:
                session.execute(text("SELECT event_id FROM events LIMIT 1"))
        except SQLAlchemyError:
            raise HTTPException(503, "Database unavailable") from None
        return {"status": "ready"}

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(generate_latest(registry), headers={"Content-Type": CONTENT_TYPE_LATEST})

    @app.post("/v1/events", status_code=201, dependencies=[Depends(authenticate)])
    def ingest(event: Event):
        now = datetime.now(timezone.utc)
        row = EventRow(event_id=str(event.event_id), source=event.source, value=event.value,
                       event_time=event.event_time, received_at=now)
        try:
            with sessions.begin() as session:
                session.add(row)
        except IntegrityError:
            ingested.labels("duplicate").inc()
            raise HTTPException(409, "event_id already exists") from None
        except SQLAlchemyError:
            ingested.labels("db_error").inc()
            raise HTTPException(503, "Database unavailable") from None
        ingested.labels("accepted").inc()
        seconds = max(0, (now - event.event_time).total_seconds())
        age.observe(seconds)
        if seconds > 300:
            stale.inc()
        return {"event_id": str(event.event_id), "status": "accepted", "stale": seconds > 300}

    @app.get("/v1/events/{event_id}", dependencies=[Depends(authenticate)])
    def get_event(event_id: UUID):
        try:
            with sessions() as session:
                row = session.scalar(select(EventRow).where(EventRow.event_id == str(event_id)))
                if row is None:
                    raise HTTPException(404, "Event not found")
                return {"event_id": row.event_id, "source": row.source, "value": row.value,
                        "event_time": row.event_time, "received_at": row.received_at}
        except SQLAlchemyError:
            raise HTTPException(503, "Database unavailable") from None
    return app
