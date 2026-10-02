"""Registry snapshot verification service."""

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.core.schemas import RegistryInfo
from app.modules.registry.matcher import calculate_name_similarity
from app.modules.registry.validators import normalize_reg_no, validate_reg_no_format


class RegistryRecord(BaseModel):
    """Single registered intermediary entity from offline snapshot."""

    reg_no: str
    name: str
    category: str
    status: str
    source_url: str
    snapshot_date: str
    is_sample: bool


class RegistryService:
    """Provides local, dated offline SEBI intermediary snapshot lookup and claim verification.

    HONESTY & UNCERTAINTY MANDATE:
    - Never calls an unverified registration number 'fake'.
    - Reports 'not_found_in_snapshot' meaning 'we could not confirm this in our dated snapshot'.
    - Discloses when sample/demo data is active.
    """

    def __init__(self, snapshot_csv_path: Optional[str] = None) -> None:
        self.settings = get_settings()
        self.verify_url = getattr(self.settings, "SEBI_VERIFY_URL", "https://www.sebi.gov.in")
        self.records: List[RegistryRecord] = []
        self.reg_no_index: Dict[str, RegistryRecord] = {}
        self.is_available: bool = False
        self.snapshot_date: str = "2026-03-01"
        self.is_sample_data: bool = True

        self._load_snapshot(snapshot_csv_path)

    def _resolve_csv_path(self, custom_path: Optional[str]) -> Optional[Path]:
        if custom_path is not None:
            p = Path(custom_path)
            if p.is_file():
                return p.resolve()
            return None

        candidates = [
            Path.cwd() / "data" / "registry" / "sebi_registry_snapshot.csv",
            Path.cwd() / "backend" / "data" / "registry" / "sebi_registry_snapshot.csv",
            Path(__file__).resolve().parent.parent.parent.parent / "data" / "registry" / "sebi_registry_snapshot.csv",
        ]
        for c in candidates:
            if c.is_file():
                return c.resolve()

        return None

    def _load_snapshot(self, custom_path: Optional[str]) -> None:
        path = self._resolve_csv_path(custom_path)
        if not path:
            logger.warning("SEBI registry snapshot CSV not found. Registry verification will be degraded.")
            self.is_available = False
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                sample_count = 0
                for row in reader:
                    reg_no = normalize_reg_no(row.get("reg_no", ""))
                    if not reg_no:
                        continue

                    is_sample_val = str(row.get("is_sample", "false")).lower() in ("true", "1", "yes")
                    if is_sample_val:
                        sample_count += 1

                    record = RegistryRecord(
                        reg_no=reg_no,
                        name=row.get("name", "").strip(),
                        category=row.get("category", "").strip(),
                        status=row.get("status", "").strip(),
                        source_url=row.get("source_url", "").strip() or self.verify_url,
                        snapshot_date=row.get("snapshot_date", "2026-03-01").strip(),
                        is_sample=is_sample_val,
                    )
                    self.records.append(record)
                    self.reg_no_index[reg_no] = record
                    self.snapshot_date = record.snapshot_date

                self.is_sample_data = (sample_count / max(len(self.records), 1)) > 0.5
                self.is_available = True
                logger.info(
                    "Loaded %d SEBI registry records from snapshot %s (sample_data=%s, snapshot_date=%s)",
                    len(self.records),
                    path,
                    self.is_sample_data,
                    self.snapshot_date,
                )
        except Exception as exc:
            logger.warning("Failed to load SEBI registry snapshot CSV from %s: %s", path, exc)
            self.is_available = False

    def check(self, claims: Dict[str, Any]) -> Tuple[RegistryInfo, List[str]]:
        """Verify claimed registration numbers and entity names against local snapshot.

        Returns (RegistryInfo, degraded_flags).
        """
        degraded: List[str] = []
        if not self.is_available:
            degraded.append("registry_unavailable")
            return (
                RegistryInfo(
                    status="not_checked",
                    matches=[],
                    snapshot_date=self.snapshot_date,
                    is_sample_data=True,
                    verify_url=self.verify_url,
                ),
                degraded,
            )

        reg_numbers = claims.get("registration_numbers", []) or claims.get("claimed_registration_numbers", [])
        entity_names = claims.get("entity_names", []) or claims.get("claimed_entity_names", [])

        # If no claim to check
        if not reg_numbers and not entity_names:
            return (
                RegistryInfo(
                    status="not_checked",
                    matches=[],
                    snapshot_date=self.snapshot_date,
                    is_sample_data=self.is_sample_data,
                    verify_url=self.verify_url,
                ),
                degraded,
            )

        matches: List[Dict[str, Any]] = []
        found_exact = False
        found_possible = False

        # 1. Match registration numbers (exact match on normalized reg_no)
        for raw_reg in reg_numbers:
            norm_reg = normalize_reg_no(raw_reg)
            is_valid_format, inferred_cat = validate_reg_no_format(norm_reg)

            if norm_reg in self.reg_no_index:
                rec = self.reg_no_index[norm_reg]
                found_exact = True
                matches.append(
                    {
                        "reg_no": rec.reg_no,
                        "name": rec.name,
                        "category": rec.category,
                        "status": rec.status,
                        "match_type": "exact_reg_no",
                        "format_valid": is_valid_format,
                        "is_sample": rec.is_sample,
                    }
                )
            else:
                # Track unconfirmed claim
                matches.append(
                    {
                        "reg_no": norm_reg,
                        "match_type": "unconfirmed_reg_no",
                        "format_valid": is_valid_format,
                        "inferred_category": inferred_cat,
                    }
                )

        # 2. Match claimed entity names using rapidfuzz token_set_ratio
        for name in entity_names:
            if not name or not name.strip():
                continue
            for rec in self.records:
                sim = calculate_name_similarity(name, rec.name)
                if sim >= 90.0:
                    found_possible = True
                    # Avoid duplicate if already matched by reg_no
                    if not any(m.get("reg_no") == rec.reg_no for m in matches):
                        matches.append(
                            {
                                "reg_no": rec.reg_no,
                                "name": rec.name,
                                "category": rec.category,
                                "status": rec.status,
                                "similarity_score": round(sim, 1),
                                "match_type": "fuzzy_name",
                                "is_sample": rec.is_sample,
                            }
                        )

        # Decide registry status honestly
        if found_exact:
            status_val = "found_in_snapshot"
        elif found_possible:
            status_val = "possible_match"
        else:
            status_val = "not_found_in_snapshot"

        return (
            RegistryInfo(
                status=status_val,
                matches=matches,
                snapshot_date=self.snapshot_date,
                is_sample_data=self.is_sample_data or any(m.get("is_sample") for m in matches),
                verify_url=self.verify_url,
            ),
            degraded,
        )

    def lookup(self, query: str) -> Dict[str, Any]:
        """Free-text query search against the offline registry snapshot."""
        if not self.is_available:
            return {
                "status": "not_checked",
                "query": query,
                "matches": [],
                "snapshot_date": self.snapshot_date,
                "is_sample_data": True,
                "verify_url": self.verify_url,
                "degraded": ["registry_unavailable"],
            }

        norm_q = normalize_reg_no(query)
        matches: List[Dict[str, Any]] = []

        # Try registration number exact match
        if norm_q in self.reg_no_index:
            rec = self.reg_no_index[norm_q]
            matches.append(
                {
                    "reg_no": rec.reg_no,
                    "name": rec.name,
                    "category": rec.category,
                    "status": rec.status,
                    "similarity": 100.0,
                    "is_sample": rec.is_sample,
                }
            )

        # Try fuzzy name matching across records
        for rec in self.records:
            if norm_q and rec.reg_no == norm_q:
                continue
            sim = calculate_name_similarity(query, rec.name)
            if sim >= 80.0:
                matches.append(
                    {
                        "reg_no": rec.reg_no,
                        "name": rec.name,
                        "category": rec.category,
                        "status": rec.status,
                        "similarity": round(sim, 1),
                        "is_sample": rec.is_sample,
                    }
                )

        # Sort matches by similarity descending
        matches.sort(key=lambda m: m.get("similarity", 0.0), reverse=True)

        status_val = "found_in_snapshot" if any(m.get("similarity", 0) >= 99.0 for m in matches) else (
            "possible_match" if matches else "not_found_in_snapshot"
        )

        return {
            "status": status_val,
            "query": query,
            "matches": matches,
            "snapshot_date": self.snapshot_date,
            "is_sample_data": self.is_sample_data or any(m.get("is_sample") for m in matches),
            "verify_url": self.verify_url,
        }


# Global singleton
_service: Optional[RegistryService] = None


def get_registry_service() -> RegistryService:
    """Get or initialize singleton RegistryService."""
    global _service
    if _service is None:
        _service = RegistryService()
    return _service
