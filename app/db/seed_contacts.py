"""
Seed emergency contacts with verified public data.
Run: python -m app.db.seed_contacts
"""
import asyncio
from datetime import datetime, timezone
from app.db.database import AsyncSessionLocal
from app.models.models import EmergencyContact, ContactType

CONTACTS = [
    {
        "organisation": "International Committee of the Red Cross",
        "acronym": "ICRC",
        "region": "Global",
        "country": "Switzerland",
        "city": "Geneva",
        "phone": "+41227346001",
        "website": "https://www.icrc.org",
        "contact_type": ContactType.SWITCHBOARD,
        "sms_confirmed": False,
        "source_url": "https://www.icrc.org/en/contact",
        "last_verified_at": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "notes": "Main switchboard. Not verified for SMS. For field emergencies contact nearest delegation.",
        "lat": 46.2044,
        "lng": 6.1432,
    },
    {
        "organisation": "United Nations High Commissioner for Refugees",
        "acronym": "UNHCR",
        "region": "Global",
        "country": "Switzerland",
        "city": "Geneva",
        "phone": "+41227398111",
        "website": "https://www.unhcr.org",
        "contact_type": ContactType.SWITCHBOARD,
        "sms_confirmed": False,
        "source_url": "https://www.unhcr.org/contact-us",
        "last_verified_at": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "notes": "Automatic switchboard. Not verified for SMS. For refugees contact nearest UNHCR office.",
        "lat": 46.2044,
        "lng": 6.1432,
    },
    {
        "organisation": "Médecins Sans Frontières",
        "acronym": "MSF",
        "region": "Ireland",
        "country": "Ireland",
        "city": "Dublin",
        "phone": "+35316603337",
        "website": "https://www.msf.org",
        "contact_type": ContactType.OFFICE,
        "sms_confirmed": False,
        "source_url": "https://www.msf.org/contact-us",
        "last_verified_at": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "notes": "MSF Ireland office. Not verified for SMS. For emergencies contact nearest MSF field office.",
        "lat": 53.3331,
        "lng": -6.2489,
    },
    {
        "organisation": "International Rescue Committee",
        "acronym": "IRC",
        "region": "Europe",
        "country": "Belgium",
        "city": "Brussels",
        "phone": "+3225115700",
        "website": "https://www.rescue.org",
        "contact_type": ContactType.OFFICE,
        "sms_confirmed": False,
        "source_url": "https://www.rescue.org/contact",
        "last_verified_at": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "notes": "IRC Brussels office. Not verified for SMS.",
        "lat": 50.8503,
        "lng": 4.3517,
    },
    {
        "organisation": "United Nations Office for the Coordination of Humanitarian Affairs",
        "acronym": "OCHA",
        "region": "Global",
        "country": "United States",
        "city": "New York",
        "phone": "+12129632440",
        "website": "https://www.unocha.org",
        "contact_type": ContactType.OFFICE,
        "sms_confirmed": False,
        "source_url": "https://www.unocha.org/contact-us",
        "last_verified_at": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "notes": "OCHA New York HQ. Not verified for SMS.",
        "lat": 40.7489,
        "lng": -73.9680,
    },
]

async def seed():
    async with AsyncSessionLocal() as db:
        for data in CONTACTS:
            contact = EmergencyContact(**data)
            db.add(contact)
        await db.commit()
        print(f"Seeded {len(CONTACTS)} emergency contacts.")

if __name__ == "__main__":
    asyncio.run(seed())
