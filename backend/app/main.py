from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError

from .config import settings
from .db import SessionLocal, engine
from .errors import (
    ApiError,
    api_error_handler,
    integrity_error_handler,
    validation_error_handler,
)
from .models import Base
from .routes import router
from .seed import seed_if_empty

logger = logging.getLogger("auction")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.seed_demo_data:
        with SessionLocal() as db:
            if seed_if_empty(db):
                logger.info("Seeded demo auctions")
    yield


app = FastAPI(
    title="RFQ British Auction API",
    version="1.0.0",
    summary="Reverse-auction RFQs with configurable British auction extensions.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.include_router(router)
