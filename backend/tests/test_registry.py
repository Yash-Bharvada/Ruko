"""Tests for Module M3: Local SEBI Registry Snapshot Verifier."""

from pathlib import Path
from typing import Any, Dict
import pytest
from fastapi.testclient import TestClient

from app.modules.registry.service import RegistryService, get_registry_service
from app.modules.registry.validators import normalize_reg_no, validate_reg_no_format
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_normalize_and_validate_reg_no() -> None:
    """Verify normalization and format hint validation."""
    assert normalize_reg_no("ina-0000 00001") == "INA000000001"
    assert normalize_reg_no(" inh / 000000002 ") == "INH000000002"

    is_valid, cat = validate_reg_no_format("INA000000001")
    assert is_valid is True
    assert cat == "Investment Adviser"

    is_valid_inh, cat_inh = validate_reg_no_format("INH000000002")
    assert is_valid_inh is True
    assert cat_inh == "Research Analyst"

    # Malformed number
    is_valid_bad, cat_bad = validate_reg_no_format("XYZ123")
    assert is_valid_bad is False
    assert cat_bad is None


def test_sample_number_present_in_csv() -> None:
    """Acceptance check: sample number in CSV -> found_in_snapshot (even with spaces/dashes/lowercase)."""
    service = get_registry_service()

    # Exact standard
    info1, degraded1 = service.check({"registration_numbers": ["INA000000001"]})
    assert info1.status == "found_in_snapshot"
    assert len(info1.matches) >= 1
    assert info1.is_sample_data is True
    assert degraded1 == []

    # Spaces, dashes, lowercase
    info2, degraded2 = service.check({"registration_numbers": ["  ina - 0000 00001  "]})
    assert info2.status == "found_in_snapshot"
    assert len(info2.matches) >= 1
    assert info2.matches[0]["reg_no"] == "INA000000001"


def test_random_well_formed_number_not_in_csv() -> None:
    """Acceptance check: random well-formed number not in CSV -> not_found_in_snapshot."""
    service = get_registry_service()
    random_reg = "INA999999999"

    info, degraded = service.check({"registration_numbers": [random_reg]})
    assert info.status == "not_found_in_snapshot"
    assert len(info.matches) >= 1
    # Format valid flag is true even though unconfirmed
    assert info.matches[0]["format_valid"] is True
    assert info.matches[0]["inferred_category"] == "Investment Adviser"


def test_fuzzy_name_matching() -> None:
    """Acceptance check: slightly misspelled sample name -> possible_match; unrelated name -> not_found."""
    service = get_registry_service()

    # Slightly misspelled: "Sample Advisor One" vs "SAMPLE ADVISORY ONE (DEMO)"
    info_match, _ = service.check({"entity_names": ["Sample Advisor One"]})
    assert info_match.status == "possible_match"
    assert len(info_match.matches) >= 1
    assert info_match.matches[0]["reg_no"] == "INA000000001"

    # Completely unrelated name
    info_unrelated, _ = service.check({"entity_names": ["Totally Unrelated Space Rocket Corporation"]})
    assert info_unrelated.status == "not_found_in_snapshot"


def test_missing_csv_degrades_gracefully(tmp_path: Path) -> None:
    """Acceptance check: missing CSV -> status not_checked, degraded contains registry_unavailable."""
    fake_csv = tmp_path / "non_existent_snapshot.csv"
    service = RegistryService(snapshot_csv_path=str(fake_csv))

    assert service.is_available is False
    info, degraded = service.check({"registration_numbers": ["INA000000001"]})

    assert info.status == "not_checked"
    assert "registry_unavailable" in degraded


def test_no_claims_to_check() -> None:
    """Verify that when no claims are provided, status is not_checked."""
    service = get_registry_service()
    info, degraded = service.check({})
    assert info.status == "not_checked"
    assert info.matches == []
    assert degraded == []


def test_honest_wording_prohibits_fake_and_fraudster() -> None:
    """Acceptance check: no test or response contains 'fake' or 'fraudster' for registry results."""
    service = get_registry_service()
    info, _ = service.check({"registration_numbers": ["INA888888888"]})

    # The word 'not_found_in_snapshot' must be used, never 'fake' or 'fraud'
    info_str = str(info.model_dump()).lower()
    assert "fake" not in info_str
    assert "fraudster" not in info_str
    assert "fraud" not in info_str
    assert info.status == "not_found_in_snapshot"


def test_registry_lookup_api_endpoint(client: TestClient) -> None:
    """Acceptance check: GET /v1/registry/lookup?q= returns matches with honest fields."""
    response = client.get("/v1/registry/lookup?q=INA000000001")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "found_in_snapshot"
    assert data["is_sample_data"] is True
    assert "snapshot_date" in data
    assert "verify_url" in data
    assert len(data["matches"]) >= 1

    # Query with a non-existent name
    resp_unrelated = client.get("/v1/registry/lookup?q=XYZNonExistentCompany")
    assert resp_unrelated.status_code == 200
    data_unrelated = resp_unrelated.json()
    assert data_unrelated["status"] == "not_found_in_snapshot"
