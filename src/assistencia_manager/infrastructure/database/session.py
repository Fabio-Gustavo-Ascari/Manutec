from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker


def create_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)
