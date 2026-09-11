"""BIS LIMS scope-matched laboratory candidates for product/IS routing.

These records are only emitted when the requested Indian Standard is known to
be present in the corresponding BIS LIMS scope page. Location coordinates are
routing coordinates used only for approximate distance ordering; SmartGuide
never treats proximity as proof of test capability.
"""

RECOGNIZED_LABS = [
    {
        "id": "BIS-REC-CSA-BENGALURU",
        "name": "CSA INDIA PRIVATE LIMITED, BENGALURU",
        "type": "BIS Recognized Laboratory",
        "city": "Bengaluru",
        "state": "Karnataka",
        "address": "A-3 III Floor, Bearys GRT, Tower A Einstein Building, SY 63/3B, Gorvigere Bidarhalli Hobli, Bengaluru 560067",
        "phone": "+91-9900056802",
        "email": "harsh.juneja@csagroup.org",
        "lat": 13.0370,
        "lon": 77.6810,
        "scope_standard": "IS/IEC 62368 : Part 1 (2023)",
        "scope_url": "https://lims.bis.gov.in/home_lab_scope/90/",
        "scope_source": "BIS LIMS scope record",
    },
    {
        "id": "BIS-REC-UL-BENGALURU",
        "name": "UL INDIA PRIVATE LIMITED, BENGALURU",
        "type": "BIS Recognized Laboratory",
        "city": "Bengaluru",
        "state": "Karnataka",
        "address": "Kalyani Platina Campus, EPIP Zone Phase II / Visveshwarya Industrial Estate, Bengaluru 560066/560048",
        "phone": "+91-9986066622",
        "email": "sarangan.nandakumar@ul.com",
        "lat": 12.9695,
        "lon": 77.7500,
        "scope_standard": "IS/IEC 62368 : Part 1 (2023)",
        "scope_url": "https://lims.bis.gov.in/home_lab_scope/94/",
        "scope_source": "BIS LIMS scope record",
    },
    {
        "id": "BIS-REC-SGS-BENGALURU",
        "name": "SGS INDIA PRIVATE LIMITED, BENGALURU",
        "type": "BIS Recognized Laboratory",
        "city": "Bengaluru",
        "state": "Karnataka",
        "address": "No 38/1 and 38/2, New BBMP No.88/45/45, Beretena Agrahara, Begur Hobli, Hosur Main Road, Bengaluru 560100",
        "phone": "+91-8095661144",
        "email": "rajesh.sp@sgs.com",
        "lat": 12.8598,
        "lon": 77.6619,
        "scope_standard": "IS/IEC 62368 : Part 1 (2023)",
        "scope_url": "https://lims.bis.gov.in/home_lab_scope/159/",
        "scope_source": "BIS LIMS scope record",
    },
    {
        "id": "BIS-REC-TUVSUD-BENGALURU",
        "name": "TUV SUD SOUTH ASIA PRIVATE LIMITED, BENGALURU",
        "type": "BIS Recognized Laboratory",
        "city": "Bengaluru",
        "state": "Karnataka",
        "address": "Plot No. 3, P1-B, Hitech, Devanahalli Defence & Aerospace Park, KIADB Industrial Area, Bengaluru 562149",
        "phone": "+91-8882641647",
        "email": "vinod.suryavanshi@tuvsud.com",
        "lat": 13.1840,
        "lon": 77.6500,
        "scope_standard": "IS/IEC 62368 : Part 1 (2023)",
        "scope_url": "https://lims.bis.gov.in/home_lab_scope/1538/",
        "scope_source": "BIS LIMS scope record",
    },
]


def recognized_labs_for_standard(standard: str):
    normalized = str(standard or "").lower().replace(" ", "")
    if "62368" not in normalized:
        return []
    return [dict(item) for item in RECOGNIZED_LABS]
