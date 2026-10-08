"""Run once before starting API replicas. Use migrations for future schema changes."""
import os
from sqlalchemy import create_engine
from app.main import Base

if __name__ == "__main__":
    engine = create_engine(os.environ["DATABASE_URL"])
    Base.metadata.create_all(engine)
    engine.dispose()
