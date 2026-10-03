from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PharmacyPriceItem(BaseModel):
    brand_name: str = Field(..., description="Brand or formulation name")
    price: float = Field(..., description="Price in INR (₹)")
    pharmacy_source: str = Field(..., description="Pharmacy name (e.g. PharmEasy, 1mg, Apollo)")
    url: str = Field(..., description="Direct link to medicine on the pharmacy website")
    is_generic: bool = Field(default=False, description="Whether this is a pure generic equivalent")
    is_cached: bool = Field(default=False, description="Whether this result was served from the 24h cache")
    is_fallback: bool = Field(default=False, description="Whether this result was generated from the static reference benchmark fallback")
    dosage_form: str = Field(default="tablet", description="Dosage form (e.g. tablet, syrup, capsule, injection, drops)")
    is_searched_medicine: bool = Field(default=False, description="Whether this is the exact brand/medicine the user searched for")


class PMBJPReference(BaseModel):
    available: bool = Field(default=True, description="Whether generic salt is available under PMBJP / Jan Aushadhi")
    generic_name: str = Field(..., description="Official PMBJP generic formulation name")
    typical_price: float = Field(..., description="Typical PMBJP ceiling price per strip/unit in INR (₹)")
    market_avg_price: float = Field(..., description="Average branded market price in INR (₹)")
    savings_percent: float = Field(..., description="Approximate savings percentage at Jan Aushadhi Kendras")
    product_url: str = Field(
        default="https://janaushadhi.gov.in/product-portfolio/product-mrp-list",
        description="Direct link to PMBJP Product & MRP portfolio catalog",
    )
    kendra_url: str = Field(
        default="https://janaushadhi.gov.in/locate-kendra",
        description="Direct link to locate nearby Jan Aushadhi Kendras",
    )


class SavingsCalculationRequest(BaseModel):
    medicine_name: str = Field(..., description="Medicine or active salt name")
    doses_per_day: float = Field(default=1.0, ge=0.5, le=6.0, description="Number of tablets/doses taken per day")
    duration_days: int = Field(default=30, ge=7, le=365, description="Duration in days (e.g. 30, 90, 365)")


class SavingsCalculationResponse(BaseModel):
    medicine_name: str
    generic_name: str
    doses_per_day: float
    duration_days: int
    total_tablets_needed: int
    current_brand_price_per_unit: float
    cheapest_generic_price_per_unit: float
    pmbjp_price_per_unit: Optional[float] = None
    brand_total_cost: float
    generic_total_cost: float
    pmbjp_total_cost: Optional[float] = None
    total_savings_inr: float
    savings_percent: float
    annual_projected_savings_inr: float


class CabinetSavingsItem(BaseModel):
    medication_name: str
    generic_name: Optional[str] = None
    current_estimated_price: float
    cheapest_substitute_price: float
    savings_percent: float
    monthly_savings_inr: float
    annual_savings_inr: float
    recommended_generic_name: str


class CabinetSavingsResponse(BaseModel):
    total_medications_analyzed: int
    medications_with_substitutes: int
    total_monthly_savings_inr: float
    total_annual_savings_inr: float
    items: List[CabinetSavingsItem]


class GenericFinderResponse(BaseModel):
    query_matched_to: str = Field(..., description="Canonically matched medicine name from the search")
    generic_name: str = Field(..., description="Active chemical salt / generic composition")
    category: str = Field(default="General", description="Therapeutic category")
    description: Optional[str] = Field(default=None, description="Clinical summary of the salt")
    how_to_use: Optional[str] = Field(default=None, description="Clinical consumption guidance")
    common_strengths: List[str] = Field(default_factory=list, description="Available standard strengths")
    side_effects: List[str] = Field(default_factory=list, description="Common mild side effects")
    dosage_form: str = Field(default="tablet", description="Primary dosage form of the searched medicine")
    active_ingredients: List[str] = Field(default_factory=list, description="Exact active chemical ingredients")
    pmbjp_reference: Optional[PMBJPReference] = Field(default=None, description="Jan Aushadhi benchmark comparison")
    all_generic_substitutes: List[str] = Field(
        default_factory=list,
        description="Peer brand formulations sharing the exact active salt and dosage form",
    )
    other_form_substitutes: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Peer brands sharing identical salt in other dosage forms (e.g. syrups, drops)",
    )
    results: List[PharmacyPriceItem] = Field(
        default_factory=list,
        description="List of pharmacy prices matching the searched medicine dosage form, sorted by price",
    )
    other_form_results: List[PharmacyPriceItem] = Field(
        default_factory=list,
        description="List of pharmacy prices in alternative dosage forms (clearly separated)",
    )
    cheapest_option: Optional[PharmacyPriceItem] = Field(
        default=None,
        description="The lowest-priced medicine found among the alternatives",
    )
    most_expensive_price: Optional[float] = Field(
        default=None,
        description="Highest price found among the options for baseline comparison",
    )
    estimated_savings_percent: float = Field(
        default=0.0,
        description="Estimated percentage savings comparing the cheapest substitute to the most expensive option",
    )
    sources_checked: List[str] = Field(
        default_factory=list,
        description="List of pharmacy sources queried",
    )
    sources_failed: List[str] = Field(
        default_factory=list,
        description="List of pharmacy sources that failed or timed out",
    )
    is_salt_dictionary_match: bool = Field(
        default=True,
        description="Whether query was successfully resolved in salt_dictionary",
    )
