import logging
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.medication import Medication
from app.models.patient import Patient
from app.models.user import User
from app.schemas.generic_finder import (
    CabinetSavingsItem,
    CabinetSavingsResponse,
    GenericFinderResponse,
    PharmacyPriceItem,
    PMBJPReference,
    SavingsCalculationRequest,
    SavingsCalculationResponse,
)
from app.services.price_scraper_service import PriceScraperService
from app.services.salt_dictionary import SALT_DICTIONARY, resolve_medicine_salt

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/generic-finder",
    tags=["GenericFinder"],
)


def _is_exact_searched_brand(item_name: str, target_brand: str) -> bool:
    clean_target = re.sub(r"[^a-zA-Z0-9\s]", " ", target_brand).lower().strip()
    clean_item = re.sub(r"[^a-zA-Z0-9\s]", " ", item_name).lower().strip()
    if "generic" in clean_item or "janaushadhi" in clean_item:
        return False
    # If target doesn't specify pediatric keywords, exclude pediatric formulations
    if "kid" not in clean_target and "junior" not in clean_target:
        if "kid" in clean_item or "junior" in clean_item or "pediatric" in clean_item:
            return False
    tokens_target = clean_target.split()
    tokens_item = clean_item.split()
    if not tokens_target or not tokens_item:
        return False
    len_t = len(tokens_target)
    for i in range(len(tokens_item) - len_t + 1):
        if tokens_item[i : i + len_t] == tokens_target:
            return True
    return clean_target == clean_item


@router.get(
    "/search",
    response_model=GenericFinderResponse,
    summary="Search medicine prices and generic substitutes",
    description="Fuzzy-matches query to active salt, finds peer brand substitutes, and compares prices across online pharmacies with 24-hour caching.",
)
async def search_generic_prices(
    query: str = Query(..., min_length=2, description="Medicine brand name or generic chemical name"),
    db: Session = Depends(get_db),
):
    if not query or len(query.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must contain at least 2 characters.",
        )

    # Step 1: Fuzzy resolve against salt dictionary
    salt_match = resolve_medicine_salt(query.strip())

    if not salt_match:
        # Graceful not-found response
        return GenericFinderResponse(
            query_matched_to=query.strip(),
            generic_name="Not found in catalog",
            category="Uncategorized",
            description="This medication is not currently in the curated Indian salt dictionary. Please check the spelling or search by its generic chemical composition.",
            how_to_use="Always consult your doctor or registered pharmacist before taking or substituting medications.",
            common_strengths=[],
            side_effects=[],
            pmbjp_reference=None,
            all_generic_substitutes=[],
            results=[],
            cheapest_option=None,
            most_expensive_price=None,
            estimated_savings_percent=0.0,
            sources_checked=[],
            sources_failed=[],
            is_salt_dictionary_match=False,
        )

    query_matched_to = salt_match["query_matched_to"]
    generic_name = salt_match["generic_name"]
    category = salt_match.get("category", "General")
    description = salt_match.get("description", "")
    how_to_use = salt_match.get("how_to_use", "")
    common_strengths = salt_match.get("common_strengths", [])
    side_effects = salt_match.get("side_effects", [])
    dosage_form = salt_match.get("dosage_form", "tablet")
    active_ingredients = salt_match.get("active_salts", [])
    all_substitutes = salt_match.get("brands", [])
    other_form_substitutes = salt_match.get("other_form_substitutes", {})
    is_brand = salt_match.get("is_brand", True)

    pmbjp_price = salt_match.get("pmbjp_price", 20.0)
    market_avg_price = salt_match.get("market_avg_price", 80.0)
    pmbjp_savings_pct = salt_match.get("pmbjp_savings_percent", 75.0)

    pmbjp_ref = PMBJPReference(
        available=True,
        generic_name=f"{generic_name} ({dosage_form.capitalize()} - Jan Aushadhi)",
        typical_price=pmbjp_price,
        market_avg_price=market_avg_price,
        savings_percent=pmbjp_savings_pct,
        product_url="https://janaushadhi.gov.in/product-portfolio/product-mrp-list",
        kendra_url="https://janaushadhi.gov.in/locate-kendra",
    )

    # Step 2: Fetch prices via PriceScraperService (checks 24h DB cache first, then scrapes)
    same_form_results, other_form_results, sources_checked, sources_failed = await PriceScraperService.get_prices_for_medicine_cluster(
        db=db,
        primary_medicine=query_matched_to,
        generic_name=generic_name,
        peer_brands=all_substitutes,
        target_form=dosage_form,
        other_form_brands=other_form_substitutes,
    )

    # Step 3: Result ordering & Searched Medicine Pinning
    # When a user searches for a specific brand (e.g. "Montair LC"), pin the exact medicine
    # to Position #1 clearly labeled as their search, followed by substitute brands sorted by price.
    sorted_other_form = sorted(other_form_results, key=lambda x: x.price)

    if is_brand:
        searched_items: List[PharmacyPriceItem] = []
        substitute_items: List[PharmacyPriceItem] = []

        for it in same_form_results:
            if _is_exact_searched_brand(it.brand_name, query_matched_to):
                it.is_searched_medicine = True
                searched_items.append(it)
            else:
                it.is_searched_medicine = False
                substitute_items.append(it)

        # Ensure the exact searched brand exists in the list
        if not searched_items:
            fallback_searched = PharmacyPriceItem(
                brand_name=query_matched_to,
                price=round(float(market_avg_price), 2),
                pharmacy_source="PharmEasy / Apollo",
                url=f"https://pharmeasy.in/search/all?name={query_matched_to.replace(' ', '%20')}",
                is_generic=False,
                is_cached=False,
                is_fallback=True,
                dosage_form=dosage_form,
                is_searched_medicine=True,
            )
            searched_items.append(fallback_searched)

        # Primary searched listing (best price found for the searched medicine)
        searched_items_sorted = sorted(searched_items, key=lambda x: x.price)
        primary_searched = searched_items_sorted[0]
        primary_searched.is_searched_medicine = True

        # Substitutes sorted strictly ascending by price
        substitutes_sorted = sorted(substitute_items, key=lambda x: x.price)
        other_searched_sources = searched_items_sorted[1:]

        # Pinned order: Searched item at #1, followed by substitutes sorted by price
        sorted_same_form = [primary_searched] + substitutes_sorted + other_searched_sources

        # Cheapest substitute for baseline savings comparison against searched brand
        cheapest_option: Optional[PharmacyPriceItem] = (
            substitutes_sorted[0] if substitutes_sorted else (sorted_same_form[0] if sorted_same_form else None)
        )
        most_expensive_price: Optional[float] = (
            max(r.price for r in sorted_same_form) if sorted_same_form else None
        )

        estimated_savings_percent = 0.0
        if cheapest_option and primary_searched.price > cheapest_option.price:
            estimated_savings_percent = round(
                ((primary_searched.price - cheapest_option.price) / primary_searched.price) * 100, 1
            )
    else:
        sorted_same_form = sorted(same_form_results, key=lambda x: x.price)
        cheapest_option = sorted_same_form[0] if sorted_same_form else None
        most_expensive_price = (
            max(r.price for r in sorted_same_form) if sorted_same_form else None
        )
        estimated_savings_percent = 0.0
        if cheapest_option and most_expensive_price and most_expensive_price > cheapest_option.price:
            estimated_savings_percent = round(
                ((most_expensive_price - cheapest_option.price) / most_expensive_price) * 100, 1
            )

    return GenericFinderResponse(
        query_matched_to=query_matched_to,
        generic_name=generic_name,
        category=category,
        description=description,
        how_to_use=how_to_use,
        common_strengths=common_strengths,
        side_effects=side_effects,
        dosage_form=dosage_form,
        active_ingredients=active_ingredients,
        pmbjp_reference=pmbjp_ref,
        all_generic_substitutes=all_substitutes,
        other_form_substitutes=other_form_substitutes,
        results=sorted_same_form,
        other_form_results=sorted_other_form,
        cheapest_option=cheapest_option,
        most_expensive_price=most_expensive_price,
        estimated_savings_percent=estimated_savings_percent,
        sources_checked=sources_checked,
        sources_failed=sources_failed,
        is_salt_dictionary_match=True,
    )


@router.post(
    "/calculate-savings",
    response_model=SavingsCalculationResponse,
    summary="Calculate potential monthly and annual prescription savings",
    description="Calculates exact monetary savings based on daily tablet dosage and duration when switching from brand to generic.",
)
def calculate_prescription_savings(req: SavingsCalculationRequest):
    salt_match = resolve_medicine_salt(req.medicine_name.strip())
    if not salt_match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medication '{req.medicine_name}' could not be resolved in the reference database.",
        )

    generic_name = salt_match["generic_name"]
    market_avg_strip = float(salt_match.get("market_avg_price", 90.0))
    pmbjp_strip = float(salt_match.get("pmbjp_price", 22.0))
    cheapest_substitute_strip = round(pmbjp_strip * 1.35, 2)

    total_tablets = int(round(req.doses_per_day * req.duration_days))

    # Unit price (per tablet / dose, assuming 10 units per standard Indian strip)
    brand_unit_price = round(market_avg_strip / 10.0, 2)
    generic_unit_price = round(cheapest_substitute_strip / 10.0, 2)
    pmbjp_unit_price = round(pmbjp_strip / 10.0, 2)

    brand_total = round(total_tablets * brand_unit_price, 2)
    generic_total = round(total_tablets * generic_unit_price, 2)
    pmbjp_total = round(total_tablets * pmbjp_unit_price, 2)

    savings_inr = round(max(0.0, brand_total - generic_total), 2)
    savings_pct = (
        round((savings_inr / brand_total) * 100, 1) if brand_total > 0 else 0.0
    )
    annual_projected = round((savings_inr / req.duration_days) * 365, 2)

    return SavingsCalculationResponse(
        medicine_name=req.medicine_name,
        generic_name=generic_name,
        doses_per_day=req.doses_per_day,
        duration_days=req.duration_days,
        total_tablets_needed=total_tablets,
        current_brand_price_per_unit=brand_unit_price,
        cheapest_generic_price_per_unit=generic_unit_price,
        pmbjp_price_per_unit=pmbjp_unit_price,
        brand_total_cost=brand_total,
        generic_total_cost=generic_total,
        pmbjp_total_cost=pmbjp_total,
        total_savings_inr=savings_inr,
        savings_percent=savings_pct,
        annual_projected_savings_inr=annual_projected,
    )


@router.get(
    "/cabinet-savings",
    response_model=CabinetSavingsResponse,
    summary="Analyze patient's active medications for generic substitution savings",
    description="Scans user's active prescriptions to calculate total monthly and annual potential savings.",
)
def get_my_cabinet_savings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        return CabinetSavingsResponse(
            total_medications_analyzed=0,
            medications_with_substitutes=0,
            total_monthly_savings_inr=0.0,
            total_annual_savings_inr=0.0,
            items=[],
        )

    medications = (
        db.query(Medication)
        .filter(Medication.patient_id == patient.id)
        .all()
    )

    items: List[CabinetSavingsItem] = []
    total_monthly = 0.0

    for med in medications:
        match = resolve_medicine_salt(med.name)
        if not match:
            continue

        generic_name = match["generic_name"]
        market_avg = float(match.get("market_avg_price", 90.0))
        pmbjp_price = float(match.get("pmbjp_price", 22.0))
        cheapest_strip = round(pmbjp_price * 1.35, 2)

        # Monthly tablets needed based on frequency
        freq = med.frequency_per_day or 1
        monthly_tablets = freq * 30

        brand_unit = market_avg / 10.0
        generic_unit = cheapest_strip / 10.0

        brand_monthly = monthly_tablets * brand_unit
        generic_monthly = monthly_tablets * generic_unit

        monthly_saving = round(max(0.0, brand_monthly - generic_monthly), 2)
        annual_saving = round(monthly_saving * 12, 2)
        savings_pct = (
            round((monthly_saving / brand_monthly) * 100, 1)
            if brand_monthly > 0
            else 0.0
        )

        total_monthly += monthly_saving

        # Recommend top peer generic or pure salt name
        rec_generic = (
            match["brands"][0]
            if match.get("brands") and match["brands"][0].lower() != med.name.lower()
            else f"{generic_name} (Jan Aushadhi)"
        )

        items.append(
            CabinetSavingsItem(
                medication_name=med.name,
                generic_name=generic_name,
                current_estimated_price=round(brand_monthly, 2),
                cheapest_substitute_price=round(generic_monthly, 2),
                savings_percent=savings_pct,
                monthly_savings_inr=monthly_saving,
                annual_savings_inr=annual_saving,
                recommended_generic_name=rec_generic,
            )
        )

    return CabinetSavingsResponse(
        total_medications_analyzed=len(medications),
        medications_with_substitutes=len(items),
        total_monthly_savings_inr=round(total_monthly, 2),
        total_annual_savings_inr=round(total_monthly * 12, 2),
        items=items,
    )


@router.get(
    "/popular",
    summary="Get popular medicine suggestions by category",
    description="Returns curated popular medicines across key therapeutic categories for quick suggestion chips in UI.",
)
def get_popular_medicines() -> Dict[str, Any]:
    categories = [
        {
            "category": "Pain & Fever",
            "medicines": ["Dolo 650", "Combiflam", "Meftal Forte", "Zerodol-P"],
        },
        {
            "category": "Antibiotics",
            "medicines": ["Augmentin 625 Duo", "Azithral 500", "Zifi 200", "Ciplox 500"],
        },
        {
            "category": "Acidity & Digestion",
            "medicines": ["Pan 40", "Pan-D", "Omez 20", "Razo 20"],
        },
        {
            "category": "Allergy & Cough",
            "medicines": ["Montair LC", "Allegra 120", "Levocet 5", "Ascoril LS Syrup"],
        },
        {
            "category": "Diabetes",
            "medicines": ["Glycomet 500", "Galvus 50", "Januvia 100", "Jardiance 10"],
        },
        {
            "category": "Blood Pressure & Heart",
            "medicines": ["Telma 40", "Amlong 5", "Atorva 10", "Ecosprin 75"],
        },
        {
            "category": "Thyroid & Vitamins",
            "medicines": ["Thyronorm 50", "Shelcal 500", "Becosules", "Evion 400"],
        },
    ]
    return {"categories": categories}
