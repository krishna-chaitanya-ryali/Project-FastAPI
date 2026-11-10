import asyncio
import os
import sys

# --------------------------------------------------
# Windows Asyncio Event Loop Configuration
# --------------------------------------------------

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )


from collections.abc import AsyncGenerator

# --------------------------------------------------
# Test Environment Configuration
# --------------------------------------------------

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg_async://bloguser:blogpass@localhost/test_blog"
)

os.environ["S3_BUCKET_NAME"] = "test-bucket"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

# Dummy S3/AWS Credentials
os.environ["S3_ACCESS_KEY_ID"] = "testing"
os.environ["S3_SECRET_ACCESS_KEY"] = "testing"
os.environ["S3_REGION"] = "eu-north-1"

os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "eu-north-1"


# --------------------------------------------------
# Application Imports
# --------------------------------------------------

import boto3
import pytest

from httpx import ASGITransport, AsyncClient

from moto import mock_aws

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sqlalchemy.pool import NullPool

from database import Base, get_db
from main import app


# --------------------------------------------------
# AnyIO Configuration
# --------------------------------------------------

pytest_plugins = ["anyio"]


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# --------------------------------------------------
# Test Database Engine
# --------------------------------------------------

@pytest.fixture(scope="session")
def test_engine():
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        poolclass=NullPool,
    )
    return engine


# --------------------------------------------------
# Database Setup and Teardown
# --------------------------------------------------

@pytest.fixture(scope="session")
async def setup_database(
    test_engine,
    anyio_backend,
):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


# --------------------------------------------------
# Database Session - Transactional Rollback
# --------------------------------------------------

@pytest.fixture
async def db_session(
    test_engine,
    setup_database,
    anyio_backend,
) -> AsyncGenerator[AsyncSession, None]:

    async with test_engine.connect() as conn:

        trans = await conn.begin()

        test_async_session = async_sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async with test_async_session() as session:
            try:
                yield session
            finally:
                await trans.rollback()


# --------------------------------------------------
# Mock AWS S3
# --------------------------------------------------


@pytest.fixture
def mocked_aws():

    with mock_aws():

        region = os.environ["S3_REGION"]
        bucket_name = os.environ["S3_BUCKET_NAME"]

        s3 = boto3.client(
            "s3",
            region_name=region,
        )

        # Create S3 bucket based on AWS region
        if region == "us-east-1":
            s3.create_bucket(
                Bucket=bucket_name
            )
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    "LocationConstraint": region
                },
            )

        yield s3



# --------------------------------------------------
# FastAPI Async Test Client
# --------------------------------------------------

@pytest.fixture
async def client(
    db_session: AsyncSession,
    mocked_aws,
    anyio_backend,
) -> AsyncGenerator[AsyncClient, None]:

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:

        yield ac

    app.dependency_overrides.clear()


# --------------------------------------------------
# Authentication Helpers
# --------------------------------------------------

async def create_test_user(
    client: AsyncClient,
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "testpassword123",
) -> dict:

    response = await client.post(
        "/api/users",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201, (
        f"Failed to create user: {response.text}"
    )

    return response.json()


async def login_user(
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "testpassword123",
) -> str:

    response = await client.post(
        "/api/users/token",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200, (
        f"Failed to login: {response.text}"
    )

    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:

    return {
        "Authorization": f"Bearer {token}"
    }
