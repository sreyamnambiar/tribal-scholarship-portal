import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.seed_data import INITIAL_SCHEMES_SEED
from app.core.security import hash_password


def _demo_application(application_id: str, scheme_id: str, scheme_name: str, status: str, applicant_name: str, email: str, state: str, has_deficiency: bool = False) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "_id": application_id,
        "application_id": application_id,
        "user_id": f"USR-DEMO-{application_id[-4:]}",
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "status": status,
        "current_step": 4 if status not in {"DRAFT", "SUBMITTED"} else 2,
        "personal_details": {
            "full_name": applicant_name,
            "father_or_husband_name": "Demo Applicant Guardian",
            "gender": "FEMALE",
            "dob": "2001-06-15",
            "aadhaar_masked": "XXXXXXXX1234",
            "category": "ST",
            "tribe_community": "Santhal",
            "mobile": "9876543210",
            "email": email,
            "state": state,
            "district": "Ranchi",
            "pincode": "834001",
        },
        "academic_details": {
            "current_course": "Bachelor of Arts",
            "institution_name": "Demo Government College",
            "institution_state": state,
            "aishe_code": "U-0001",
            "roll_number": "DEMO-2026-01",
            "year_of_study": "2nd Year",
            "previous_exam_name": "Higher Secondary",
            "previous_exam_percentage": 72.5,
            "passing_year": "2024",
            "board_or_university": "State Board",
        },
        "financial_details": {
            "annual_family_income": 180000,
            "bank_name": "State Bank of India",
            "account_holder_name": applicant_name,
            "account_number_masked": "XXXXXXXX5678",
            "ifsc_code": "SBIN0000001",
            "branch_name": "Ranchi Main Branch",
            "is_aadhaar_seeded": True,
        },
        "documents": [],
        "has_deficiency": has_deficiency,
        "deficiency_notes": "Updated income certificate required." if has_deficiency else None,
        "officer_remarks": None,
        "created_at": now,
        "updated_at": now,
    }


DEMO_APPLICATIONS = [
    _demo_application("MOTA/2026-27/PMS/10001", "pre-matric-st", "Pre-Matric ST", "SUBMITTED", "Asha Munda", "asha.munda@example.com", "Jharkhand"),
    _demo_application("MOTA/2026-27/POST/10002", "post-matric-st", "Post-Matric ST", "DOCUMENT_VERIFICATION", "Birsa Kisku", "birsa.kisku@example.com", "Odisha"),
    _demo_application("MOTA/2026-27/POST/10003", "post-matric-st", "Post-Matric ST", "APPROVED", "Chandni Soren", "chandni.soren@example.com", "Chhattisgarh"),
    _demo_application("MOTA/2026-27/NSTE/10004", "national-scholarship-top-class", "National Scholarship", "DEFICIENT", "Deepak Gond", "deepak.gond@example.com", "Madhya Pradesh", True),
    _demo_application("MOTA/2026-27/NSTE/10005", "national-scholarship-top-class", "National Scholarship", "ELIGIBILITY_VERIFICATION", "Esha Kerketta", "esha.kerketta@example.com", "Jharkhand"),
    _demo_application("MOTA/2026-27/NF/10006", "national-fellowship-st", "National Fellowship", "SELECTION", "Fatima Toppo", "fatima.toppo@example.com", "West Bengal"),
    _demo_application("MOTA/2026-27/NOS/10007", "national-overseas-scholarship-st", "National Overseas", "DRAFT", "Gopal Tirkey", "gopal.tirkey@example.com", "Odisha"),
    _demo_application("MOTA/2026-27/DBT/10008", "dbt-fellowship-st", "DBT Fellowship", "SUBMITTED", "Hema Lakra", "hema.lakra@example.com", "Jharkhand"),
]

def generate_application_id(scheme_code: str) -> str:
    """
    Generate an authentic MoTA Government Application ID.
    Format: MOTA/{FinancialYear}/{SchemeAbbrev}/{RandomSeq}
    Example: MOTA/2025-26/NF/10492
    """
    now = datetime.now(timezone.utc)
    fy = f"{now.year}-{str(now.year + 1)[-2:]}"
    parts = scheme_code.split("-")
    abbrev = parts[1] if len(parts) > 1 else "ST"
    seq = random.randint(10000, 99999)
    return f"MOTA/{fy}/{abbrev}/{seq}"

async def seed_schemes_if_empty(db: AsyncIOMotorDatabase) -> None:
    """
    Seed initial MoTA schemes into MongoDB if the collection is empty.
    """
    try:
        count = await db["schemes"].count_documents({})
        if count == 0:
            await db["schemes"].insert_many(INITIAL_SCHEMES_SEED)
    except Exception:
        pass


async def seed_applications_if_empty(db: AsyncIOMotorDatabase) -> None:
    if await db["applications"].count_documents({}) == 0:
        await db["applications"].insert_many(DEMO_APPLICATIONS)

async def seed_users_if_empty(db: AsyncIOMotorDatabase) -> None:
    """
    Seed initial authorized Officer and Admin accounts if not present.
    """
    now = datetime.now(timezone.utc)
    # Admin
    existing_admin = await db["users"].find_one({"email": "admin@gmail.com"})
    if not existing_admin:
        admin_doc = {
            "_id": "USR-ADM-01",
            "name": "Dr. Navaljit Kapoor",
            "email": "admin@gmail.com",
            "phone": "9810054321",
            "hashed_password": hash_password("Admin@2026"),
            "role": "ADMIN",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        await db["users"].insert_one(admin_doc)

