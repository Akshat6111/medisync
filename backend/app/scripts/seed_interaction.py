from app.db.database import SessionLocal
from app.models.drug_interaction import DrugInteraction
from app.scheduling.seed_interaction import CURATED_INTERACTIONS


def seed():
    db = SessionLocal()

    try:
        created = 0

        for interaction in CURATED_INTERACTIONS:

            exists = (
                db.query(DrugInteraction)
                .filter(
                    DrugInteraction.drug_a == interaction["drug_a"],
                    DrugInteraction.drug_b == interaction["drug_b"],
                )
                .first()
            )

            if exists:
                continue

            db.add(DrugInteraction(**interaction))
            created += 1

        db.commit()

        print(f"Seeded {created} interactions successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    seed()