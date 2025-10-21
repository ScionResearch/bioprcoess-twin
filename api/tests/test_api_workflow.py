"""
Integration tests for the complete batch workflow.
Tests the full lifecycle from batch creation to closure.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from datetime import datetime, timedelta

from app.main import app
from app.database import get_db
from app.models import Base


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://pichia_api:changeme@localhost:5432/pichia_manual_data_test"


# Setup test database
@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_db_engine):
    """Create a database session for tests."""
    async_session = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session):
    """Create test client with overridden database dependency."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_token(client: AsyncClient):
    """Get admin authentication token."""
    # Note: This assumes default users are seeded in test DB
    # You may need to create users first in a setup fixture
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def tech_token(client: AsyncClient):
    """Get technician authentication token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "tech01", "password": "tech123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def engineer_token(client: AsyncClient):
    """Get engineer authentication token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "eng01", "password": "eng123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestAuthentication:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]


class TestBatchManagement:
    """Test batch CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_batch(self, client: AsyncClient, admin_token: str):
        """Test batch creation."""
        response = await client.post(
            "/api/v1/batches",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "batch_number": 1,
                "phase": "A",
                "vessel_id": "V-FR-01",
                "operator_id": "admin",
                "notes": "Test batch"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["batch_number"] == 1
        assert data["phase"] == "A"
        assert data["status"] == "pending"
        assert data["batch_id"] is not None

    @pytest.mark.asyncio
    async def test_list_batches(self, client: AsyncClient, admin_token: str):
        """Test listing batches."""
        response = await client.get(
            "/api/v1/batches",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_create_duplicate_batch(self, client: AsyncClient, admin_token: str):
        """Test that duplicate batch numbers are rejected."""
        # Create first batch
        await client.post(
            "/api/v1/batches",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "batch_number": 2,
                "phase": "A",
                "vessel_id": "V-FR-02",
                "operator_id": "admin"
            }
        )

        # Try to create duplicate
        response = await client.post(
            "/api/v1/batches",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "batch_number": 2,
                "phase": "A",
                "vessel_id": "V-FR-03",
                "operator_id": "admin"
            }
        )
        assert response.status_code == 409


class TestCalibrationWorkflow:
    """Test sensor calibration workflow."""

    @pytest.mark.asyncio
    async def test_ph_calibration_with_slope_calculation(
        self, client: AsyncClient, admin_token: str
    ):
        """Test pH calibration with automatic slope calculation."""
        # Create batch
        batch_response = await client.post(
            "/api/v1/batches",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "batch_number": 3,
                "phase": "A",
                "vessel_id": "V-FR-03",
                "operator_id": "admin"
            }
        )
        batch_id = batch_response.json()["batch_id"]

        # Add pH calibration
        response = await client.post(
            f"/api/v1/batches/{batch_id}/calibrations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "probe_type": "pH",
                "buffer_low_value": 4.01,
                "buffer_high_value": 7.00,
                "reading_low": 4.02,
                "reading_high": 6.99,
                "pass": True,
                "calibrated_by": "admin"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["probe_type"] == "pH"
        assert data["pass"] is True
        # Check that slope was auto-calculated
        assert data["slope_percent"] is not None
        assert float(data["slope_percent"]) > 0

    @pytest.mark.asyncio
    async def test_do_calibration_with_response_time(
        self, client: AsyncClient, admin_token: str
    ):
        """Test DO calibration with response time validation."""
        # Create batch
        batch_response = await client.post(
            "/api/v1/batches",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "batch_number": 4,
                "phase": "A",
                "vessel_id": "V-FR-04",
                "operator_id": "admin"
            }
        )
        batch_id = batch_response.json()["batch_id"]

        # Add DO calibration
        response = await client.post(
            f"/api/v1/batches/{batch_id}/calibrations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "probe_type": "DO",
                "buffer_low_value": 0.0,
                "buffer_high_value": 100.0,
                "reading_low": 0.1,
                "reading_high": 99.9,
                "response_time_sec": 25,
                "pass": True,
                "calibrated_by": "admin"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["probe_type"] == "DO"
        assert data["response_time_sec"] == 25

    @pytest.mark.asyncio
    async def test_cannot_calibrate_after_inoculation(
        self, client: AsyncClient, admin_token: str
    ):
        """Test that calibrations cannot be added after batch is inoculated."""
        # Create batch
        batch_response = await client.post(
            "/api/v1/batches",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "batch_number": 5,
                "phase": "A",
                "vessel_id": "V-FR-05",
                "operator_id": "admin"
            }
        )
        batch_id = batch_response.json()["batch_id"]

        # Add required calibrations (pH, DO, Temp)
        for probe_type in ["pH", "DO", "Temp"]:
            await client.post(
                f"/api/v1/batches/{batch_id}/calibrations",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "probe_type": probe_type,
                    "buffer_low_value": 0.0,
                    "buffer_high_value": 100.0,
                    "reading_low": 0.1,
                    "reading_high": 99.9,
                    "pass": True,
                    "calibrated_by": "admin"
                }
            )

        # Inoculate batch
        await client.post(
            f"/api/v1/batches/{batch_id}/inoculation",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "preculture_vessel_id": "V-PC-01",
                "preculture_od600": 5.5,
                "inoculum_volume_ml": 100.0,
                "dilution_factor": 10.0,
                "performed_by": "admin"
            }
        )

        # Try to add calibration after inoculation
        response = await client.post(
            f"/api/v1/batches/{batch_id}/calibrations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "probe_type": "Pressure",
                "buffer_low_value": 0.0,
                "buffer_high_value": 2.0,
                "reading_low": 0.0,
                "reading_high": 2.0,
                "pass": True,
                "calibrated_by": "admin"
            }
        )

        assert response.status_code == 422
        assert "already started" in response.json()["detail"]


class TestCompleteWorkflow:
    """Test the complete batch workflow from creation to closure."""

    @pytest.mark.asyncio
    async def test_full_batch_lifecycle(
        self, client: AsyncClient, admin_token: str, engineer_token: str
    ):
        """Test complete workflow: batch → calibrations → inoculation → samples → closure."""

        # 1. Create batch
        batch_response = await client.post(
            "/api/v1/batches",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "batch_number": 10,
                "phase": "B",
                "vessel_id": "V-FR-10",
                "operator_id": "admin"
            }
        )
        assert batch_response.status_code == 201
        batch_id = batch_response.json()["batch_id"]

        # 2. Add required calibrations (pH, DO, Temp)
        calibrations = [
            {
                "probe_type": "pH",
                "buffer_low_value": 4.01,
                "buffer_high_value": 7.00,
                "reading_low": 4.02,
                "reading_high": 6.99,
            },
            {
                "probe_type": "DO",
                "buffer_low_value": 0.0,
                "buffer_high_value": 100.0,
                "reading_low": 0.1,
                "reading_high": 99.9,
                "response_time_sec": 22,
            },
            {
                "probe_type": "Temp",
                "buffer_low_value": 0.0,
                "buffer_high_value": 100.0,
                "reading_low": 0.0,
                "reading_high": 100.0,
            }
        ]

        for cal in calibrations:
            cal.update({"pass": True, "calibrated_by": "admin"})
            response = await client.post(
                f"/api/v1/batches/{batch_id}/calibrations",
                headers={"Authorization": f"Bearer {admin_token}"},
                json=cal
            )
            assert response.status_code == 201

        # 3. Inoculate batch
        inoc_response = await client.post(
            f"/api/v1/batches/{batch_id}/inoculation",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "preculture_vessel_id": "V-PC-01",
                "preculture_od600": 8.5,
                "inoculum_volume_ml": 150.0,
                "dilution_factor": 10.0,
                "performed_by": "admin"
            }
        )
        assert inoc_response.status_code == 201
        assert inoc_response.json()["initial_od600"] is not None

        # 4. Add samples (need at least 8 for closure)
        sample_data = [
            {"hours_post_inoc": 0, "od600_raw": 0.85},
            {"hours_post_inoc": 4, "od600_raw": 2.1},
            {"hours_post_inoc": 8, "od600_raw": 5.3},
            {"hours_post_inoc": 12, "od600_raw": 12.5},
            {"hours_post_inoc": 16, "od600_raw": 25.8},
            {"hours_post_inoc": 20, "od600_raw": 42.3},
            {"hours_post_inoc": 24, "od600_raw": 55.2},
            {"hours_post_inoc": 28, "od600_raw": 58.1},
        ]

        for sample in sample_data:
            sample.update({
                "ph": 6.5,
                "do_percent": 30.0,
                "temp_c": 28.5,
                "methanol_added_ml": 0.0,
                "sampled_by": "admin"
            })
            response = await client.post(
                f"/api/v1/batches/{batch_id}/samples",
                headers={"Authorization": f"Bearer {admin_token}"},
                json=sample
            )
            assert response.status_code == 201
            # Check that DCW was auto-calculated
            assert response.json()["dcw_g_l"] is not None

        # 5. Close batch (requires engineer role)
        close_response = await client.post(
            f"/api/v1/batches/{batch_id}/close",
            headers={"Authorization": f"Bearer {engineer_token}"},
            json={
                "final_biomass_g_l": 58.0,
                "final_product_titer_g_l": 12.5,
                "approved_by": "eng01",
                "notes": "Successful batch completion"
            }
        )
        assert close_response.status_code == 201

        # 6. Verify batch status is now 'complete'
        batch_check = await client.get(
            f"/api/v1/batches/{batch_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert batch_check.json()["status"] == "complete"
        assert batch_check.json()["completed_at"] is not None


class TestRoleBasedAccess:
    """Test role-based access control."""

    @pytest.mark.asyncio
    async def test_technician_cannot_close_batch(
        self, client: AsyncClient, tech_token: str
    ):
        """Test that technicians cannot close batches (engineer required)."""
        # This would require a properly set up batch, but testing the auth check
        fake_batch_id = "00000000-0000-0000-0000-000000000000"

        response = await client.post(
            f"/api/v1/batches/{fake_batch_id}/close",
            headers={"Authorization": f"Bearer {tech_token}"},
            json={
                "final_biomass_g_l": 50.0,
                "final_product_titer_g_l": 10.0,
                "approved_by": "tech01"
            }
        )

        # Should get 403 Forbidden due to insufficient permissions
        # (or 404 if batch check happens first)
        assert response.status_code in [403, 404]


class TestDatabaseTriggers:
    """Test database triggers and auto-calculations."""

    @pytest.mark.asyncio
    async def test_od600_to_dcw_conversion(
        self, client: AsyncClient, admin_token: str
    ):
        """Test automatic OD600 to DCW conversion."""
        # Create and prepare batch
        batch_response = await client.post(
            "/api/v1/batches",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "batch_number": 15,
                "phase": "C",
                "vessel_id": "V-FR-15",
                "operator_id": "admin"
            }
        )
        batch_id = batch_response.json()["batch_id"]

        # Add minimal calibrations and inoculate
        for probe_type in ["pH", "DO", "Temp"]:
            await client.post(
                f"/api/v1/batches/{batch_id}/calibrations",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "probe_type": probe_type,
                    "buffer_low_value": 0.0,
                    "buffer_high_value": 100.0,
                    "reading_low": 0.0,
                    "reading_high": 100.0,
                    "pass": True,
                    "calibrated_by": "admin"
                }
            )

        await client.post(
            f"/api/v1/batches/{batch_id}/inoculation",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "preculture_vessel_id": "V-PC-01",
                "preculture_od600": 5.0,
                "inoculum_volume_ml": 100.0,
                "dilution_factor": 10.0,
                "performed_by": "admin"
            }
        )

        # Add sample with known OD600
        response = await client.post(
            f"/api/v1/batches/{batch_id}/samples",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "hours_post_inoc": 24,
                "od600_raw": 50.0,
                "ph": 6.5,
                "do_percent": 30.0,
                "temp_c": 28.5,
                "methanol_added_ml": 0.0,
                "sampled_by": "admin"
            }
        )

        assert response.status_code == 201
        data = response.json()

        # DCW should be OD600 * 0.33 (standard conversion factor)
        expected_dcw = 50.0 * 0.33
        actual_dcw = float(data["dcw_g_l"])
        assert abs(actual_dcw - expected_dcw) < 0.1  # Allow small rounding differences


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
