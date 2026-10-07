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


class XposedOrNotProvider:
    """XposedOrNot open provider for real-world breach verification with free API."""

    _catalog_cache: Optional[dict] = None
    _catalog_lock: asyncio.Lock = asyncio.Lock()

    async def _get_catalog(self) -> dict:
        """Lazy load and cache the global breach details catalog."""
        if XposedOrNotProvider._catalog_cache is not None:
            return XposedOrNotProvider._catalog_cache

        async with XposedOrNotProvider._catalog_lock:
            if XposedOrNotProvider._catalog_cache is not None:
                return XposedOrNotProvider._catalog_cache

            catalog = {}
            try:
                from xposedornot import XposedOrNot
                xon = XposedOrNot()
                breaches = await asyncio.to_thread(xon.get_breaches)
                for b in breaches:
                    key = getattr(b, "breach_id", "").strip().lower()
                    if key:
                        catalog[key] = b
                XposedOrNotProvider._catalog_cache = catalog
                logger.info("Loaded XposedOrNot catalog with %d breaches", len(catalog))
            except Exception as exc:
                logger.warning("Failed to fetch XposedOrNot breach catalog: %s", exc)
                XposedOrNotProvider._catalog_cache = {}

            return XposedOrNotProvider._catalog_cache

    async def check_email(
        self,
        email: str,
        settings: Settings,
    ) -> Tuple[str, List[ExposureRecord], bool, List[str]]:
        clean_email = email.strip()

        try:
            from xposedornot import XposedOrNot
            xon = XposedOrNot()
            res = await asyncio.to_thread(xon.check_email, clean_email)
            breach_names = getattr(res, "breaches", []) or []

            if not breach_names:
                return "ok", [], False, []

            catalog = await self._get_catalog()
            exposures: List[ExposureRecord] = []

            for b_name in breach_names:
                b_name_clean = str(b_name).strip()
                cat_match = catalog.get(b_name_clean.lower())

                if cat_match:
                    date_val = str(getattr(cat_match, "breached_date", "") or "Unknown Date")[:10]
                    exposed_data = getattr(cat_match, "exposed_data", []) or ["Email addresses"]
                    raw_cats = [str(c) for c in exposed_data]
                else:
                    date_val = "Unknown Date"
                    raw_cats = ["Email addresses"]

                risk_level, fin_exp = classify_exposure(raw_cats)
                remediation = get_remediation_notes(risk_level, fin_exp, raw_cats)

                exposures.append(
                    ExposureRecord(
                        breach_name=b_name_clean,
                        breach_date=date_val,
                        exposure_categories=raw_cats,
                        risk_level=risk_level,
                        financial_exposure=fin_exp,
                        provider="xposedornot",
                        remediation_notes=remediation,
                    )
                )

            return "ok", exposures, False, []

        except Exception as exc:
            logger.error("XposedOrNot check failed for %s: %s", clean_email.split("@")[0], exc)
            return "scan_unavailable", [], False, ["xposedornot_lookup_failed"]


class CompositeFallbackBreachProvider:
    """Primary XposedOrNot provider with automatic fallback to synthetic MockProvider."""

    def __init__(self):
        self.primary = XposedOrNotProvider()
        self.fallback = MockProvider()

    async def check_email(
        self,
        email: str,
        settings: Settings,
    ) -> Tuple[str, List[ExposureRecord], bool, List[str]]:
        # 1. Try Primary Provider (XposedOrNot live open breach API)
        status, exposures, is_demo, degraded = await self.primary.check_email(email, settings)
        if status == "ok":
            return status, exposures, is_demo, degraded

        # 2. If Primary Provider fails or is unavailable, fallback gracefully to MockProvider
        logger.warning(
            "Primary XposedOrNot provider failed (%s); falling back to MockProvider for %s",
            degraded,
            email.split("@")[0],
        )
        fb_status, fb_exposures, _, fb_degraded = await self.fallback.check_email(email, settings)
        combined_degraded = list(set(degraded + fb_degraded + ["xposedornot_fallback_active"]))
        return fb_status, fb_exposures, True, combined_degraded


class LeakCheckProvider:
    """LeakCheck.io API provider for real-world data breach exposure lookups.

    Supports:
    - Pro API v2 (https://leakcheck.io/api/v2/query/{query}) using X-API-Key.
    - Automatic graceful fallback to Public API (https://leakcheck.io/api/public?check={query})
      if Pro API returns 403 (e.g. 'Active plan required' / quota exhausted) or if no API key is set.
    - Zero persistence: raw breach data discarded immediately; returns sanitized ExposureRecord objects.
    - Strict privacy invariants: raw credentials/passwords never logged, stored, or returned.
    """

    async def check_email(
        self,
        email: str,
        settings: Settings,
    ) -> Tuple[str, List[ExposureRecord], bool, List[str]]:
        """Query LeakCheck for an email address."""
        clean = email.strip().lower()
        return await self._query(clean, "email", settings)

    async def check_phone(
        self,
        phone: str,
        settings: Settings,
    ) -> Tuple[str, List[ExposureRecord], bool, List[str]]:
        """Query LeakCheck for a phone number."""
        digits = "".join(ch for ch in phone if ch.isdigit())
        return await self._query(digits, "phone", settings)

    async def _query(
        self,
        query: str,
        query_type: str,
        settings: Settings,
    ) -> Tuple[str, List[ExposureRecord], bool, List[str]]:
        api_key = getattr(settings, "LEAKCHECK_API_KEY", "").strip()

        # Step 1: If an API key is provided, try Pro API v2 first
        if api_key:
            pro_status, pro_exposures, pro_flags, should_try_public = await self._query_pro_api(
                query=query,
                query_type=query_type,
                api_key=api_key,
            )
            if not should_try_public:
                return pro_status, pro_exposures, False, pro_flags

        # Step 2: Use or fallback to Public API
        return await self._query_public_api(query=query)

    async def _query_pro_api(
        self,
        query: str,
        query_type: str,
        api_key: str,
    ) -> Tuple[str, List[ExposureRecord], List[str], bool]:
        """Query LeakCheck Pro API v2.

        Returns:
            (status, exposures, degraded_flags, should_try_public)
        """
        encoded_query = httpx.URL(f"https://leakcheck.io/api/v2/query/{query}").raw_path.decode("utf-8")
        url = f"https://leakcheck.io{encoded_query}"
        headers = {
            "X-API-Key": api_key,
            "Accept": "application/json",
            "User-Agent": "Ruko-Security-Monitor/1.0",
        }
        params = {"type": query_type, "limit": 100}

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, headers=headers, params=params)

                if resp.status_code == 200:
                    raw_data = resp.json()
                    if raw_data.get("success"):
                        results = raw_data.get("result", [])
                        exposures = self._map_pro_results(results)
                        del raw_data
                        return "ok", exposures, [], False
                    error_msg = str(raw_data.get("error") or "").lower()
                    if "not found" in error_msg:
                        return "ok", [], [], False
                    logger.warning("LeakCheck Pro API returned unsuccessful response: %s", raw_data.get("error"))
                    return "ok", [], [], True

                elif resp.status_code == 403:
                    # e.g., 'Active plan required' or quota reached -> gracefully fall back to Public API
                    logger.info("LeakCheck Pro API returned 403 (Active plan required or quota reached); falling back to Public API")
                    return "ok", [], [], True

                elif resp.status_code == 404:
                    return "ok", [], [], False

                elif resp.status_code == 429:
                    logger.warning("LeakCheck Pro API rate limited; attempting Public API")
                    return "ok", [], ["leakcheck_pro_rate_limited"], True

                else:
                    logger.warning("LeakCheck Pro API unexpected status %s; falling back to Public API", resp.status_code)
                    return "ok", [], [], True

        except Exception as exc:
            logger.warning("LeakCheck Pro API request failed (%s); falling back to Public API", type(exc).__name__)
            return "ok", [], [], True

    async def _query_public_api(
        self,
        query: str,
    ) -> Tuple[str, List[ExposureRecord], bool, List[str]]:
        """Query LeakCheck Public API with retry logic and error mapping."""
        url = "https://leakcheck.io/api/public"
        params = {"check": query}
        headers = {
            "Accept": "application/json",
            "User-Agent": "Ruko-Security-Monitor/1.0",
        }

        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(url, params=params, headers=headers)

                    if resp.status_code == 200:
                        raw_data = resp.json()
                        if not raw_data.get("success"):
                            err = str(raw_data.get("error") or "").lower()
                            if "not found" in err or "nothing found" in err:
                                return "ok", [], False, []
                            logger.warning("LeakCheck Public API error: %s", raw_data.get("error"))
                            return "scan_unavailable", [], False, [f"leakcheck_{raw_data.get('error', 'unknown')}"]

                        sources = raw_data.get("sources", [])
                        fields = raw_data.get("fields", [])
                        exposures = self._map_public_results(sources, fields)
                        del raw_data
                        return "ok", exposures, False, []

                    elif resp.status_code == 404:
                        return "ok", [], False, []

                    elif resp.status_code == 429:
                        logger.warning("LeakCheck Public API rate limit (429), attempt %d", attempt + 1)
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(1.5)
                            continue
                        return "scan_unavailable", [], False, ["leakcheck_rate_limited"]

                    elif resp.status_code >= 500:
                        logger.warning("LeakCheck Public API server error (%s), attempt %d", resp.status_code, attempt + 1)
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(1.0)
                            continue
                        return "scan_unavailable", [], False, ["leakcheck_upstream_5xx"]

                    else:
                        logger.warning("Unexpected LeakCheck Public API status code: %s", resp.status_code)
                        return "scan_unavailable", [], False, ["leakcheck_unexpected_response"]

            except Exception as exc:
                logger.warning("LeakCheck Public API network attempt %d failed: %s", attempt + 1, type(exc).__name__)
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1.0)
                    continue
                return "scan_unavailable", [], False, ["leakcheck_network_error"]

        return "scan_unavailable", [], False, ["leakcheck_unavailable"]

    def _map_pro_results(self, raw_list: list) -> List[ExposureRecord]:
        records: List[ExposureRecord] = []
        if not isinstance(raw_list, list):
            return records

        seen = set()
        for item in raw_list:
            if not isinstance(item, dict):
                continue

            src = item.get("source") or {}
            if isinstance(src, dict):
                name = str(src.get("name") or "Unknown Incident")
                date_val = str(src.get("breach_date") or src.get("date") or "Unknown Date")
            else:
                name = str(src) if src else "Unknown Incident"
                date_val = "Unknown Date"

            key = (name.lower(), date_val)
            if key in seen:
                continue
            seen.add(key)

            fields = item.get("fields") or []
            if not isinstance(fields, list):
                fields = []
            sanitized_cats = [str(f) for f in fields]

            risk_level, fin_exp = classify_exposure(sanitized_cats)
            remediation = get_remediation_notes(risk_level, fin_exp, sanitized_cats)

            records.append(
                ExposureRecord(
                    breach_name=name,
                    breach_date=date_val,
                    exposure_categories=sanitized_cats,
                    risk_level=risk_level,
                    financial_exposure=fin_exp,
                    provider="leakcheck",
                    remediation_notes=remediation,
                )
            )

        return records

    def _map_public_results(self, sources: list, fields: list) -> List[ExposureRecord]:
        records: List[ExposureRecord] = []
        if not isinstance(sources, list):
            return records

        sanitized_cats = [str(f) for f in (fields or []) if isinstance(f, str)]
        risk_level, fin_exp = classify_exposure(sanitized_cats)
        remediation = get_remediation_notes(risk_level, fin_exp, sanitized_cats)

        seen = set()
        for item in sources:
            if not isinstance(item, dict):
                continue

            name = str(item.get("name") or "Unknown Incident")
            date_val = str(item.get("date") or "Unknown Date")

            key = (name.lower(), date_val)
            if key in seen:
                continue
            seen.add(key)

            records.append(
                ExposureRecord(
                    breach_name=name,
                    breach_date=date_val,
                    exposure_categories=sanitized_cats,
                    risk_level=risk_level,
                    financial_exposure=fin_exp,
                    provider="leakcheck",
                    remediation_notes=remediation,
                )
            )

        return records


class XposedOrNotProvider:
    """XposedOrNot open community breach database provider.

    - 100% free, community-driven OSINT breach search.
    - Requires zero API keys or commercial accounts.
    - Resolves breach metadata (dates, categories, descriptions) via in-memory cached catalog.
    - Zero persistence: in-memory only, no identifiers or raw leaks stored.
    """

    _catalog_cache = None
    _catalog_timestamp = 0

    async def _get_catalog(self) -> dict:
        import time
        now = time.time()
        if self._catalog_cache is not None and (now - self._catalog_timestamp) < 3600:
            return self._catalog_cache

        url = "https://api.xposedornot.com/v1/breaches"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    catalog = {}
                    for item in data.get("exposedBreaches", []):
                        if isinstance(item, dict) and "breachID" in item:
                            catalog[item["breachID"].lower()] = item
                    self._catalog_cache = catalog
                    self._catalog_timestamp = now
                    return catalog
        except Exception as exc:
            logger.warning("Failed to fetch XposedOrNot catalog (%s); continuing with fallback", type(exc).__name__)

        return self._catalog_cache or {}

    async def check_email(
        self,
        email: str,
        settings: Settings,
    ) -> Tuple[str, List[ExposureRecord], bool, List[str]]:
        clean = email.strip().lower()
        url = f"https://api.xposedornot.com/v1/check-email/{clean}"

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url)

                if resp.status_code == 200:
                    raw_data = resp.json()
                    err = str(raw_data.get("Error") or "").lower()
                    if "not found" in err:
                        return "ok", [], False, []

                    breach_lists = raw_data.get("breaches", [])
                    catalog = await self._get_catalog()

                    exposures: List[ExposureRecord] = []
                    seen = set()

                    all_breaches = []
                    for sub in breach_lists:
                        if isinstance(sub, list):
                            all_breaches.extend(sub)
                        elif isinstance(sub, str):
                            all_breaches.append(sub)

                    for b_name in all_breaches:
                        if not isinstance(b_name, str):
                            continue
                        norm_name = b_name.strip()
                        key = norm_name.lower()
                        if key in seen:
                            continue
                        seen.add(key)

                        cat_entry = catalog.get(key)
                        if cat_entry:
                            display_name = cat_entry.get("breachID") or norm_name
                            date_str = cat_entry.get("breachedDate") or "Unknown Date"
                            if "T" in date_str:
                                date_str = date_str.split("T")[0]
                            exposed_fields = cat_entry.get("exposedData") or []
                            if isinstance(exposed_fields, list):
                                sanitized_cats = [str(f) for f in exposed_fields]
                            else:
                                sanitized_cats = [str(exposed_fields)]
                        else:
                            display_name = norm_name
                            date_str = "Unknown Date"
                            sanitized_cats = ["Email addresses", "Account credentials"]

                        risk_level, fin_exp = classify_exposure(sanitized_cats)
                        remediation = get_remediation_notes(risk_level, fin_exp, sanitized_cats)

                        exposures.append(
                            ExposureRecord(
                                breach_name=display_name,
                                breach_date=date_str,
                                exposure_categories=sanitized_cats,
                                risk_level=risk_level,
                                financial_exposure=fin_exp,
                                provider="xposedornot",
                                remediation_notes=remediation,
                            )
                        )

                    del raw_data
                    return "ok", exposures, False, []

                elif resp.status_code == 404:
                    return "ok", [], False, []

                elif resp.status_code == 429:
                    return "scan_unavailable", [], False, ["xposedornot_rate_limited"]

                else:
                    return "scan_unavailable", [], False, ["xposedornot_upstream_error"]

        except Exception as exc:
            logger.warning("XposedOrNot network error: %s", type(exc).__name__)
            return "scan_unavailable", [], False, ["xposedornot_network_error"]


class HybridBreachProvider:
    """Multi-source breach aggregator querying both LeakCheck and XposedOrNot.

    Combines coverage across independent public breach indices:
    - Queries both providers in parallel.
    - Merges results and deduplicates incidents by breach name.
    - If one provider is offline or rate-limited, gracefully yields results from the active provider.
    - Zero persistence, 100% in-memory processing.
    """

    def __init__(self):
        self.leakcheck = LeakCheckProvider()
        self.xposed = XposedOrNotProvider()

    async def check_email(
        self,
        email: str,
        settings: Settings,
    ) -> Tuple[str, List[ExposureRecord], bool, List[str]]:
        tasks = [
            self.leakcheck.check_email(email, settings),
            self.xposed.check_email(email, settings),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        merged_exposures: List[ExposureRecord] = []
        degraded_flags: List[str] = []
        statuses = []
        seen_names = set()

        for res in results:
            if isinstance(res, Exception):
                degraded_flags.append(f"upstream_{type(res).__name__}")
                continue

            status, exposures, is_demo, flags = res
            statuses.append(status)
            degraded_flags.extend(flags)

            for exp in exposures:
                key = exp.breach_name.strip().lower()
                if key not in seen_names:
                    seen_names.add(key)
                    merged_exposures.append(exp)

        # Sort exposures with HIGH risk first
        merged_exposures.sort(
            key=lambda e: (0 if e.risk_level == "HIGH" else 1 if e.risk_level == "MEDIUM" else 2),
        )

        overall_status = "ok" if ("ok" in statuses or not statuses) else "scan_unavailable"
        return overall_status, merged_exposures, False, list(set(degraded_flags))


class CompositeFallbackBreachProvider:
    """Primary XposedOrNot provider with automatic fallback to Hybrid/LeakCheck and MockProvider."""

    def __init__(self):
        self.primary = XposedOrNotProvider()
        self.secondary = HybridBreachProvider()
        self.mock_fallback = MockProvider()

    async def check_email(
        self,
        email: str,
        settings: Settings,
    ) -> Tuple[str, List[ExposureRecord], bool, List[str]]:
        # 1. Primary: XposedOrNot (User's main open breach index)
        status, exposures, is_demo, degraded = await self.primary.check_email(email, settings)
        if status == "ok":
            return status, exposures, is_demo, degraded

        # 2. Secondary fallback: Hybrid (LeakCheck + XON)
        logger.warning(
            "Primary XposedOrNot provider degraded (%s); attempting Hybrid/LeakCheck fallback for %s",
            degraded,
            email.split("@")[0],
        )
        sec_status, sec_exposures, sec_demo, sec_degraded = await self.secondary.check_email(email, settings)
        if sec_status == "ok":
            return sec_status, sec_exposures, False, list(set(degraded + sec_degraded + ["fallback_hybrid_used"]))

        # 3. Tertiary fallback: MockProvider (guarantees system resilience)
        logger.warning("Secondary fallback also degraded; using MockProvider for demo resilience")
        mock_status, mock_exposures, _, mock_degraded = await self.mock_fallback.check_email(email, settings)
        return mock_status, mock_exposures, True, list(set(degraded + sec_degraded + ["fallback_mock_used"]))


# Backward-compatibility alias
HibpProvider = HybridBreachProvider


def get_breach_provider(settings: Settings) -> BreachProvider:
    """Factory selecting provider based on configuration."""
    provider_name = getattr(settings, "BREACH_PROVIDER", "xposedornot").lower().strip()
    if provider_name == "mock":
        return MockProvider()
    if provider_name == "hibp":
        return HibpProvider()
    if provider_name in ("leakcheck", "leak_check"):
        return LeakCheckProvider()
    if provider_name in ("hybrid", "multi", "all"):
        return HybridBreachProvider()
    return CompositeFallbackBreachProvider()
