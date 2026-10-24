from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def upgrade_clothing_item_columns() -> None:
    columns = {column["name"] for column in inspect(engine).get_columns("clothing_items")}
    migrations = {
        "style": "ALTER TABLE clothing_items ADD COLUMN style VARCHAR(20) NOT NULL DEFAULT 'casual'",
        "gender": "ALTER TABLE clothing_items ADD COLUMN gender VARCHAR(20) NOT NULL DEFAULT 'unisex'",
    }
    with engine.begin() as connection:
        for column, statement in migrations.items():
            if column not in columns:
                connection.execute(text(statement))
        if "user_id" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE clothing_items ADD COLUMN user_id "
                    "INTEGER REFERENCES users(id)"
                )
            )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_clothing_items_user_id "
                "ON clothing_items (user_id)"
            )
        )
