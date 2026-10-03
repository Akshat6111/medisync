import asyncio
from app.db.database import SessionLocal
from app.services.price_scraper_service import PriceScraperService
from app.services.salt_dictionary import resolve_medicine_salt

async def main():
    db = SessionLocal()
    res = resolve_medicine_salt("Montecip LC")
    print("Resolved salt:", res)
    if res:
        prices, s_succ, s_fail = await PriceScraperService.get_prices_for_medicine_cluster(
            db, res["query_matched_to"], res["generic_name"], res["brands"]
        )
        for p in prices:
            print(f"Price item: {p.brand_name} | {p.pharmacy_source} | Rs. {p.price}")
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
