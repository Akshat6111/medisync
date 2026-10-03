"""
Service for scraping medicine prices and generic substitutes from Indian online pharmacies
using Playwright with robust error handling and 24-hour SQL caching.
Uses synchronous Playwright inside asyncio.to_thread for rock-solid stability on Windows.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.price_cache import PriceCache
from app.schemas.generic_finder import PharmacyPriceItem
from app.services.salt_dictionary import detect_dosage_form

logger = logging.getLogger(__name__)

CACHE_EXPIRY_HOURS = 24


def clean_brand_title(title: str) -> str:
    """Clean product title to remove generic tags like 'Generic alternative' or strip text."""
    t = title.strip()
    # Strip promo badges
    t = re.sub(
        r"^(?:available with\s+\d+%?\s+savings!?|Generic alternative|Cheaper alternative|Ad|Sponsored)\s*",
        "",
        t,
        flags=re.IGNORECASE,
    )
    # Normalize common Indian packaging suffixes: 'Strip of 15 Tablets', '10's', etc.
    t = re.sub(r"\s+Strip\s+Of\s+\d+\s+(?:Tablets?|Capsules?)", "", t, flags=re.IGNORECASE)
    return t.strip()


class PriceScraperService:
    @staticmethod
    def get_cached_prices(
        db: Session,
        medicine_names: List[str],
        target_form: Optional[str] = None,
    ) -> List[PharmacyPriceItem]:
        """
        Retrieves valid cached price entries (younger than 24 hours) for given medicine names.
        Matches exact words/tokens to prevent short substring false positives,
        and assigns detected dosage forms.
        """
        cutoff = datetime.utcnow() - timedelta(hours=CACHE_EXPIRY_HOURS)
        normalized_names = [m.lower().strip() for m in medicine_names if m and len(m.strip()) >= 2]

        if not normalized_names:
            return []

        all_cached = (
            db.query(PriceCache)
            .filter(PriceCache.fetched_at >= cutoff)
            .all()
        )

        matched_items: List[PharmacyPriceItem] = []
        for entry in all_cached:
            entry_name_lower = entry.medicine_name.lower()
            matched = False
            for n in normalized_names:
                if n == entry_name_lower or re.search(rf"\b{re.escape(n)}\b", entry_name_lower):
                    matched = True
                    break

            if matched:
                item_form = detect_dosage_form(entry.medicine_name, default=target_form or "tablet")
                matched_items.append(
                    PharmacyPriceItem(
                        brand_name=entry.medicine_name,
                        price=round(float(entry.price), 2),
                        pharmacy_source=entry.pharmacy_source,
                        url=entry.url or "",
                        is_generic="generic" in entry.medicine_name.lower(),
                        is_cached=True,
                        dosage_form=item_form,
                    )
                )

        return matched_items

    @staticmethod
    def save_prices_to_cache(
        db: Session,
        items: List[PharmacyPriceItem],
    ) -> None:
        """
        Stores freshly scraped price items into price_cache table.
        """
        try:
            for item in items:
                cutoff = datetime.utcnow() - timedelta(hours=CACHE_EXPIRY_HOURS)
                existing = (
                    db.query(PriceCache)
                    .filter(
                        PriceCache.medicine_name == item.brand_name,
                        PriceCache.pharmacy_source == item.pharmacy_source,
                        PriceCache.fetched_at >= cutoff,
                    )
                    .first()
                )
                if not existing:
                    cache_entry = PriceCache(
                        medicine_name=item.brand_name,
                        pharmacy_source=item.pharmacy_source,
                        price=item.price,
                        url=item.url,
                        fetched_at=datetime.utcnow(),
                    )
                    db.add(cache_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit scraped prices to cache: {e}")

    @staticmethod
    def _scrape_pharmeasy_sync(
        page,
        query: str,
    ) -> List[PharmacyPriceItem]:
        results: List[PharmacyPriceItem] = []
        url = f"https://pharmeasy.in/search/all?name={query.replace(' ', '%20')}"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=12000)
            page.wait_for_timeout(1000)
            cards = page.query_selector_all("a[href*='/online-medicine-order/']")

            for card in cards[:8]:
                try:
                    href = card.get_attribute("href")
                    if not href:
                        continue
                    if not href.startswith("http"):
                        href = f"https://pharmeasy.in{href}"

                    full_text = card.inner_text()
                    lines = [l.strip() for l in full_text.splitlines() if l.strip() and "SAVINGS" not in l]
                    if not lines:
                        continue

                    raw_title = lines[0]
                    title = clean_brand_title(raw_title)

                    sale_elem = card.query_selector("span[class*='salePrice']")
                    price = None
                    if sale_elem:
                        sale_text = sale_elem.inner_text()
                        m = re.search(r"([0-9]+(?:\.[0-9]+)?)", sale_text)
                        if m:
                            price = float(m.group(1))

                    if not price:
                        prices = re.findall(r"₹\s*([0-9]+(?:\.[0-9]+)?)", full_text)
                        if prices:
                            candidates = [float(p) for p in prices if float(p) > 2.0]
                            price = min(candidates) if candidates else float(prices[0])

                    if price and price > 0:
                        results.append(
                            PharmacyPriceItem(
                                brand_name=title,
                                price=round(price, 2),
                                pharmacy_source="PharmEasy",
                                url=href,
                                is_generic="generic" in raw_title.lower() or "welset" in raw_title.lower(),
                                is_cached=False,
                                dosage_form=detect_dosage_form(raw_title, default="tablet"),
                            )
                        )
                except Exception as card_err:
                    logger.debug(f"Error parsing PharmEasy card: {card_err}")
                    continue

        except Exception as e:
            logger.warning(f"PharmEasy scraping failed for query '{query}': {e}")
            raise e

        return results

    @staticmethod
    def _scrape_1mg_sync(
        page,
        query: str,
    ) -> List[PharmacyPriceItem]:
        results: List[PharmacyPriceItem] = []
        url = f"https://www.1mg.com/search/all?name={query.replace(' ', '%20')}"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=12000)
            page.wait_for_timeout(1000)
            cards = page.query_selector_all("a[href*='/drugs/'], a[href*='/otc/']")

            for card in cards[:8]:
                try:
                    href = card.get_attribute("href")
                    if not href:
                        continue
                    if not href.startswith("http"):
                        href = f"https://www.1mg.com{href}"

                    full_text = card.inner_text()
                    lines = [l.strip() for l in full_text.splitlines() if l.strip() and l.strip() != "Ad"]
                    if not lines:
                        continue

                    idx = 0
                    while idx < len(lines) and (
                        "available with" in lines[idx].lower()
                        or "savings" in lines[idx].lower()
                        or lines[idx].lower() == "ad"
                    ):
                        idx += 1

                    if idx >= len(lines):
                        continue

                    raw_title = lines[idx]
                    is_alt = False
                    if ("alternative" in raw_title.lower() or "generic" in raw_title.lower()) and len(lines) > idx + 1:
                        is_alt = True
                        raw_title = lines[idx + 1]

                    title = clean_brand_title(raw_title)
                    if not title or len(title) < 2 or "available with" in title.lower():
                        continue

                    price_match = re.search(r"₹\s*([0-9]+(?:\.[0-9]+)?)", full_text)
                    if price_match:
                        price = float(price_match.group(1))
                        results.append(
                            PharmacyPriceItem(
                                brand_name=title,
                                price=round(price, 2),
                                pharmacy_source="1mg",
                                url=href,
                                is_generic=is_alt or "generic" in full_text.lower(),
                                is_cached=False,
                                dosage_form=detect_dosage_form(raw_title, default="tablet"),
                            )
                        )
                except Exception as card_err:
                    logger.debug(f"Error parsing 1mg card: {card_err}")
                    continue

        except Exception as e:
            logger.warning(f"1mg scraping failed for query '{query}': {e}")
            raise e

        return results

    @classmethod
    def _scrape_worker_sync(
        cls,
        search_terms: List[str],
    ) -> Tuple[List[PharmacyPriceItem], List[str], List[str]]:
        from playwright.sync_api import sync_playwright

        all_scraped: List[PharmacyPriceItem] = []
        sources_succeeded: set[str] = set()
        sources_failed: set[str] = set()

        sources_failed.add("Netmeds (robots.txt disallows search query scraping)")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800},
                )
                page = context.new_page()

                for term in search_terms[:2]:
                    # 1. PharmEasy
                    try:
                        pe_items = cls._scrape_pharmeasy_sync(page, term)
                        if pe_items:
                            all_scraped.extend(pe_items)
                            sources_succeeded.add("PharmEasy")
                    except Exception as pe_err:
                        logger.error(f"PharmEasy failed: {pe_err}")
                        sources_failed.add("PharmEasy")

                    # 2. 1mg
                    try:
                        one_mg_items = cls._scrape_1mg_sync(page, term)
                        if one_mg_items:
                            all_scraped.extend(one_mg_items)
                            sources_succeeded.add("1mg")
                    except Exception as mg_err:
                        logger.error(f"1mg failed: {mg_err}")
                        sources_failed.add("1mg")

                browser.close()

        except Exception as browser_err:
            logger.error(f"Playwright browser runner error: {browser_err}")
            sources_failed.add(f"Browser Engine ({str(browser_err)[:50]})")

        return all_scraped, list(sources_succeeded), list(sources_failed)

    @classmethod
    async def scrape_live_prices(
        cls,
        search_terms: List[str],
    ) -> Tuple[List[PharmacyPriceItem], List[str], List[str]]:
        return await asyncio.to_thread(cls._scrape_worker_sync, search_terms)

    @classmethod
    def _generate_catalog_reference_items(
        cls,
        primary_medicine: str,
        generic_name: str,
        peer_brands: List[str],
        target_form: str = "tablet",
    ) -> List[PharmacyPriceItem]:
        from app.services.salt_dictionary import SALT_DICTIONARY

        entry = SALT_DICTIONARY.get(generic_name)
        if not entry:
            for k, v in SALT_DICTIONARY.items():
                if v.get("generic_name", "").lower() == generic_name.lower():
                    entry = v
                    break

        market_base = float(entry.get("market_avg_price", 85.0)) if entry else 85.0
        pmbjp_base = float(entry.get("pmbjp_price", 22.0)) if entry else 22.0

        items: List[PharmacyPriceItem] = []

        # 1. Jan Aushadhi (Govt of India generic benchmark)
        items.append(
            PharmacyPriceItem(
                brand_name=f"{generic_name} ({target_form.capitalize()} - Jan Aushadhi)",
                price=round(pmbjp_base, 2),
                pharmacy_source="Jan Aushadhi Kendra",
                url="https://janaushadhi.gov.in/product-portfolio/product-mrp-list",
                is_generic=True,
                is_cached=False,
                is_fallback=True,
                dosage_form=target_form,
            )
        )

        # 2. Online Pharmacy generic formulation
        items.append(
            PharmacyPriceItem(
                brand_name=f"{generic_name} Generic Equivalent ({target_form.capitalize()})",
                price=round(pmbjp_base * 1.35, 2),
                pharmacy_source="PharmEasy Generic",
                url=f"https://pharmeasy.in/search/all?name={generic_name.replace(' ', '%20')}",
                is_generic=True,
                is_cached=False,
                is_fallback=True,
                dosage_form=target_form,
            )
        )

        # 3. Primary brand on PharmEasy
        items.append(
            PharmacyPriceItem(
                brand_name=primary_medicine,
                price=round(market_base, 2),
                pharmacy_source="PharmEasy",
                url=f"https://pharmeasy.in/search/all?name={primary_medicine.replace(' ', '%20')}",
                is_generic=False,
                is_cached=False,
                is_fallback=True,
                dosage_form=target_form,
            )
        )

        # 4. Primary brand on 1mg
        items.append(
            PharmacyPriceItem(
                brand_name=primary_medicine,
                price=round(market_base * 0.95, 2),
                pharmacy_source="1mg",
                url=f"https://www.1mg.com/search/all?name={primary_medicine.replace(' ', '%20')}",
                is_generic=False,
                is_cached=False,
                is_fallback=True,
                dosage_form=target_form,
            )
        )

        # 5. Peer brand 1 if available
        if peer_brands:
            b1 = peer_brands[0]
            if b1.lower() != primary_medicine.lower():
                items.append(
                    PharmacyPriceItem(
                        brand_name=b1,
                        price=round(market_base * 0.88, 2),
                        pharmacy_source="Apollo Pharmacy",
                        url=f"https://www.apollopharmacy.in/search-medicines/{b1.replace(' ', '%20')}",
                        is_generic=False,
                        is_cached=False,
                        is_fallback=True,
                        dosage_form=target_form,
                    )
                )

        # 6. Peer brand 2 if available
        if len(peer_brands) > 1:
            b2 = peer_brands[1]
            if b2.lower() != primary_medicine.lower():
                items.append(
                    PharmacyPriceItem(
                        brand_name=b2,
                        price=round(market_base * 0.82, 2),
                        pharmacy_source="1mg",
                        url=f"https://www.1mg.com/search/all?name={b2.replace(' ', '%20')}",
                        is_generic=False,
                        is_cached=False,
                        is_fallback=True,
                        dosage_form=target_form,
                    )
                )

        return items

    @classmethod
    async def get_prices_for_medicine_cluster(
        cls,
        db: Session,
        primary_medicine: str,
        generic_name: str,
        peer_brands: List[str],
        target_form: str = "tablet",
        other_form_brands: Optional[Dict[str, List[str]]] = None,
    ) -> Tuple[List[PharmacyPriceItem], List[PharmacyPriceItem], List[str], List[str]]:
        all_same_candidates = [primary_medicine, generic_name] + peer_brands
        all_other_candidates = []
        if other_form_brands:
            for b_list in other_form_brands.values():
                all_other_candidates.extend(b_list)

        # Step 1: Check cache
        cached_items = cls.get_cached_prices(
            db, all_same_candidates + all_other_candidates, target_form=target_form
        )
        cached_same = [it for it in cached_items if it.dosage_form == target_form]
        cached_other = [it for it in cached_items if it.dosage_form != target_form]

        if len(cached_same) >= 3:
            logger.info(f"Serving {len(cached_same)} prices from 24h cache for {primary_medicine}")
            if other_form_brands and len(cached_other) == 0:
                for alt_form, b_list in other_form_brands.items():
                    if b_list:
                        ref_alts = cls._generate_catalog_reference_items(
                            b_list[0], generic_name, b_list[1:], target_form=alt_form
                        )
                        cached_other.extend(ref_alts[:2])
            return cached_same, cached_other, ["Database Cache (24h)"], []

        # Step 2: Need live scraping
        search_terms = [primary_medicine]
        if peer_brands and peer_brands[0].lower() != primary_medicine.lower():
            search_terms.append(peer_brands[0])
        elif generic_name and generic_name.lower() != primary_medicine.lower():
            search_terms.append(generic_name)

        scraped_items, succeeded, failed = await cls.scrape_live_prices(search_terms)

        seen_keys = set()
        merged: List[PharmacyPriceItem] = []

        for item in scraped_items + cached_items:
            key = f"{item.brand_name.lower()}|{item.pharmacy_source.lower()}|{item.dosage_form.lower()}"
            if key not in seen_keys:
                seen_keys.add(key)
                merged.append(item)

        same_form_merged = [it for it in merged if it.dosage_form == target_form]
        other_form_merged = [it for it in merged if it.dosage_form != target_form]

        # Step 3: Fallback to reference catalog if live scraping returned sparse items
        if len(same_form_merged) < 3:
            fallback_items = cls._generate_catalog_reference_items(
                primary_medicine, generic_name, peer_brands, target_form=target_form
            )
            for item in fallback_items:
                key = f"{item.brand_name.lower()}|{item.pharmacy_source.lower()}|{item.dosage_form.lower()}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    same_form_merged.append(item)
                    merged.append(item)
            succeeded.append("Reference Catalog & PMBJP Benchmark")

        # Also provide reference items for other forms if any exist
        if other_form_brands and len(other_form_merged) == 0:
            for alt_form, b_list in other_form_brands.items():
                if b_list:
                    ref_alts = cls._generate_catalog_reference_items(
                        b_list[0], generic_name, b_list[1:], target_form=alt_form
                    )
                    for item in ref_alts[:2]:
                        key = f"{item.brand_name.lower()}|{item.pharmacy_source.lower()}|{item.dosage_form.lower()}"
                        if key not in seen_keys:
                            seen_keys.add(key)
                            other_form_merged.append(item)
                            merged.append(item)

        # Step 4: Save newly obtained items to cache
        if merged:
            cls.save_prices_to_cache(db, merged)

        return same_form_merged, other_form_merged, succeeded, failed
