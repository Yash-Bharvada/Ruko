"""Breach data providers interface with MockProvider and HibpProvider implementations."""

import asyncio
from typing import List, Optional, Protocol, Tuple
import httpx

from app.core.config import Settings
from app.core.logging import logger
from app.core.schemas import ExposureRecord
from app.modules.breach.risk_classifier import classify_exposure
from app.modules.breach.remediation import get_remediation_notes


class BreachProvider(Protocol):
    """Protocol for stateless breach index lookup providers."""

    async def check_email(
        self,
        email: str,
        settings: Settings,
    ) -> Tuple[str, List[ExposureRecord], bool, List[str]]:
        """Query breach provider for an email address.

        Returns:
            (status: "ok" | "incomplete" | "scan_unavailable", exposures, is_demo, degraded_flags)
        """
        ...


class MockProvider:
    """Deterministic mock provider returning synthetic sample breach records for testing and demos."""

    async def check_email(
        self,
        email: str,
        settings: Settings,
    ) -> Tuple[str, List[ExposureRecord], bool, List[str]]:
        clean = email.strip().lower()

        # If email contains 'clean' or 'safe' or 'none', return 0 exposures
        if "clean" in clean or "safe" in clean or "nobreach" in clean:
            return "ok", [], True, []

        # Otherwise return deterministic synthetic breach records
        exposures: List[ExposureRecord] = []

        # Breach 1: Financial & Card leak (HIGH risk)
        cats_1 = ["Email addresses", "Passwords", "Bank account numbers", "Credit cards", "Phone numbers"]
        risk_1, fin_1 = classify_exposure(cats_1)
        exposures.append(
            ExposureRecord(
                breach_name="FinPay Global Gateway 2025 Incident",
                breach_date="2025-08-14",
                exposure_categories=cats_1,
                risk_level=risk_1,
                financial_exposure=fin_1,
                provider="mock",
                remediation_notes=get_remediation_notes(risk_1, fin_1, cats_1),
            )
        )

        # Breach 2: Credential & Profile leak (HIGH risk)
        cats_2 = ["Email addresses", "Password hashes", "Usernames", "IP addresses"]
        risk_2, fin_2 = classify_exposure(cats_2)
        exposures.append(
            ExposureRecord(
                breach_name="RetailHub E-Commerce Aggregator 2024",
                breach_date="2024-11-02",
                exposure_categories=cats_2,
                risk_level=risk_2,
                financial_exposure=fin_2,
                provider="mock",
                remediation_notes=get_remediation_notes(risk_2, fin_2, cats_2),
            )
        )

        # Breach 3: General Profile (LOW risk)
        cats_3 = ["Usernames", "Website activity", "Public profiles"]
        risk_3, fin_3 = classify_exposure(cats_3)
        exposures.append(
            ExposureRecord(
                breach_name="Online Gaming Community 2023",
                breach_date="2023-04-19",
                exposure_categories=cats_3,
                risk_level=risk_3,
                financial_exposure=fin_3,
                provider="mock",
                remediation_notes=get_remediation_notes(risk_3, fin_3, cats_3),
            )
        )

        return "ok", exposures, True, []


class HibpProvider:
    """HaveIBeenPwned API provider for real-world breach verification with rate limiting and retry."""

    async def check_email(
        self,
        email: str,
        settings: Settings,
    ) -> Tuple[str, List[ExposureRecord], bool, List[str]]:
        api_key = getattr(settings, "HIBP_API_KEY", "")
        if not api_key or not api_key.strip():
            logger.warning("HIBP_API_KEY is not configured; returning scan_unavailable")
            return "scan_unavailable", [], False, ["hibp_api_key_missing"]

        encoded_account = httpx.URL(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email.strip()}").raw_path.decode("utf-8")
        url = f"https://haveibeenpwned.com{encoded_account}?truncateResponse=false"
        headers = {
            "hibp-api-key": api_key.strip(),
            "user-agent": "Ruko-Security-Monitor/1.0",
        }

        # 8-second timeout, 1 retry on 5xx or network timeout
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(url, headers=headers)

                    if resp.status_code == 200:
                        raw_data = resp.json()
                        exposures = self._map_hibp_breaches(raw_data)
                        # Discard raw response
                        del raw_data
                        return "ok", exposures, False, []

                    elif resp.status_code == 404:
                        # 404 in HIBP signifies 0 breaches found for this account
                        return "ok", [], False, []

                    elif resp.status_code == 429:
                        logger.warning("HIBP rate limit encountered (429)")
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(2.0)
                            continue
                        return "scan_unavailable", [], False, ["hibp_rate_limited"]

                    elif resp.status_code in (401, 403):
                        logger.error("HIBP authentication error (%s)", resp.status_code)
                        return "scan_unavailable", [], False, ["hibp_auth_failed"]

                    elif resp.status_code >= 500:
                        logger.warning("HIBP server error (%s), attempt %d", resp.status_code, attempt + 1)
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(1.0)
                            continue
                        return "scan_unavailable", [], False, ["hibp_upstream_5xx"]

                    else:
                        logger.warning("Unexpected HIBP status code: %s", resp.status_code)
                        return "scan_unavailable", [], False, ["hibp_unexpected_response"]

            except Exception as exc:
                logger.warning("HIBP network attempt %d failed: %s", attempt + 1, type(exc).__name__)
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1.0)
                    continue
                return "scan_unavailable", [], False, ["hibp_network_error"]

        return "scan_unavailable", [], False, ["hibp_unavailable"]

    def _map_hibp_breaches(self, raw_list: list) -> List[ExposureRecord]:
        """Normalize raw HIBP list into strictly sanitized ExposureRecord objects."""
        records: List[ExposureRecord] = []
        if not isinstance(raw_list, list):
            return records

        for item in raw_list:
            if not isinstance(item, dict):
                continue

            name = str(item.get("Title") or item.get("Name") or "Unknown Incident")
            date_val = str(item.get("BreachDate") or "Unknown Date")
            data_classes = item.get("DataClasses") or []
            if not isinstance(data_classes, list):
                data_classes = []
            sanitized_cats = [str(c) for c in data_classes]

            risk_level, fin_exp = classify_exposure(sanitized_cats)
            remediation = get_remediation_notes(risk_level, fin_exp, sanitized_cats)

            records.append(
                ExposureRecord(
                    breach_name=name,
                    breach_date=date_val,
                    exposure_categories=sanitized_cats,
                    risk_level=risk_level,
                    financial_exposure=fin_exp,
                    provider="hibp",
                    remediation_notes=remediation,
                )
            )

        return records


def get_breach_provider(settings: Settings) -> BreachProvider:
    """Factory selecting provider based on configuration."""
    provider_name = getattr(settings, "BREACH_PROVIDER", "mock").lower().strip()
    if provider_name == "hibp":
        return HibpProvider()
    return MockProvider()
