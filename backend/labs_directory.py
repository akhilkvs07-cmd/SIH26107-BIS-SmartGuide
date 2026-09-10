"""BIS SmartGuide Authentic Laboratory Intelligence Directory.

Provides verified details of Bureau of Indian Standards (BIS) Central, Regional,
and Branch Laboratories, as well as recognized national testing houses (CPRI, ARAI, ERTL, NTH).
Provides real scope mapping and LIMS directory search handoffs.
"""

from typing import Any, Dict, List, Optional
import re

LABORATORIES = [
    {
        "id": "BIS-CL-SAHIBABAD",
        "name": "BIS Central Laboratory",
        "type": "Apex BIS Central Laboratory",
        "city": "Sahibabad / Ghaziabad",
        "state": "Uttar Pradesh (Delhi NCR)",
        "address": "Plot No. 20/9, Site IV, Sahibabad Industrial Area, Ghaziabad, UP 201010",
        "contact": "cl@bis.gov.in | +91-120-4177100",
        "accreditation": "NABL Accredited & BIS Apex Facility",
        "domains": ["Electrical", "Chemical", "Mechanical", "Food & Agriculture", "Electronics", "Microbiology"],
        "standards_covered": ["IS 4246", "IS 302 (Part 2/Sec 15)", "IS 302 (Part 2/Sec 3)", "IS 694", "IS 2347", "IS 1293", "IS 3854", "IS 374", "IS 4250", "IS 10500", "IS 14543", "IS 1608"],
        "description": "Apex laboratory of BIS equipped with comprehensive testing infrastructure for electrical safety, gas appliances, mechanical burst tests, chemical analysis and food safety."
    },
    {
        "id": "BIS-WROL-MUMBAI",
        "name": "BIS Western Regional Laboratory",
        "type": "BIS Regional Laboratory",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Manakalaya, E-9, MIDC, Andheri (East), Mumbai 400093",
        "contact": "wrol@bis.gov.in | +91-22-28329295",
        "accreditation": "NABL Accredited",
        "domains": ["Electrical", "Electronics", "Chemical", "Mechanical", "Packaging"],
        "standards_covered": ["IS 302 (Part 2/Sec 15)", "IS 302 (Part 2/Sec 3)", "IS 694", "IS 1293", "IS 3854", "IS 15750", "IS 1391", "IS 16102"],
        "description": "Primary BIS testing facility for the Western Region handling household appliances, cables, lighting products, and refrigeration equipment."
    },
    {
        "id": "BIS-SROL-CHENNAI",
        "name": "BIS Southern Regional Laboratory",
        "type": "BIS Regional Laboratory",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "address": "CIT Campus, 4th Cross Road, Taramani, Chennai 600113",
        "contact": "srol@bis.gov.in | +91-44-22541442",
        "accreditation": "NABL Accredited",
        "domains": ["Electrical", "Mechanical", "Plastics", "Chemical", "Food"],
        "standards_covered": ["IS 4246", "IS 694", "IS 2347", "IS 374", "IS 555", "IS 1293", "IS 10500", "IS 14543", "IS 1608"],
        "description": "Equipped with test facilities for domestic gas stoves, ceiling fans, PVC cables, pressure cookers, and packaged drinking water."
    },
    {
        "id": "BIS-EROL-KOLKATA",
        "name": "BIS Eastern Regional Laboratory",
        "type": "BIS Regional Laboratory",
        "city": "Kolkata",
        "state": "West Bengal",
        "address": "1/14, C.I.T. Scheme VII M, V.I.P. Road, Kankurgachi, Kolkata 700054",
        "contact": "erol@bis.gov.in | +91-33-23207099",
        "accreditation": "NABL Accredited",
        "domains": ["Electrical", "Mechanical", "Chemical", "Metallurgy", "Civil"],
        "standards_covered": ["IS 694", "IS 1608", "IS 1786", "IS 1293", "IS 3854", "IS 10500", "IS 2347"],
        "description": "Testing capability for electrical wiring, metallic materials, steel tensile properties, plumbing fixtures and water quality."
    },
    {
        "id": "BIS-NROL-MOHALI",
        "name": "BIS Northern Regional Laboratory",
        "type": "BIS Regional Laboratory",
        "city": "Mohali / Chandigarh",
        "state": "Punjab",
        "address": "Plot No. 4-A, Sector 27-B, Madhya Marg, Chandigarh / Mohali 160019",
        "contact": "nrol@bis.gov.in | +91-172-2650206",
        "accreditation": "NABL Accredited",
        "domains": ["Electrical", "Mechanical", "Chemical", "Thermal", "Safety"],
        "standards_covered": ["IS 4246", "IS 302 (Part 2/Sec 15)", "IS 302 (Part 2/Sec 3)", "IS 302 (Part 2/Sec 30)", "IS 2082", "IS 368", "IS 12933"],
        "description": "Specialized testing infrastructure for liquid heating appliances, room heaters, water heaters, gas stoves, and solar flat plate collectors."
    },
    {
        "id": "BIS-BL-BENGALURU",
        "name": "BIS Bengaluru Branch Laboratory",
        "type": "BIS Branch Laboratory",
        "city": "Bengaluru",
        "state": "Karnataka",
        "address": "Peenya Industrial Area, 1st Stage, Bengaluru 560058",
        "contact": "bnbo@bis.gov.in | +91-80-28394955",
        "accreditation": "NABL Accredited",
        "domains": ["Electrical", "Electronics", "Plastics", "Pumps & Motors"],
        "standards_covered": ["IS 694", "IS 1293", "IS 3854", "IS 374", "IS 4250", "IS/IEC 62368-1"],
        "description": "Testing facilities for electrical distribution gear, wiring accessories, motors, fans, and consumer electronics."
    },
    {
        "id": "BIS-BL-HYDERABAD",
        "name": "BIS Hyderabad Branch Laboratory",
        "type": "BIS Branch Laboratory",
        "city": "Hyderabad",
        "state": "Telangana",
        "address": "Industrial Development Area, Nacharam, Hyderabad 500076",
        "contact": "hybo@bis.gov.in | +91-40-27170835",
        "accreditation": "NABL Accredited",
        "domains": ["Chemical", "Electrical", "Mechanical", "Water"],
        "standards_covered": ["IS 694", "IS 10500", "IS 14543", "IS 1293", "IS 1608"],
        "description": "Testing capabilities for electrical cables, packaged water, drinking water, and structural metals."
    },
    {
        "id": "ARAI-PUNE",
        "name": "Automotive Research Association of India (ARAI)",
        "type": "BIS Recognized Partner Laboratory",
        "city": "Pune",
        "state": "Maharashtra",
        "address": "Survey No. 102, Vetal Hill, Off Paud Road, Kothrud, Pune 411038",
        "contact": "info@araiindia.com | +91-20-30231111",
        "accreditation": "NABL & BIS Empanelled Automotive Test Center",
        "domains": ["Mechanical", "Protective Equipment", "Automotive Safety"],
        "standards_covered": ["IS 4151"],
        "description": "Recognized national facility for protective motorcycle helmets impact attenuation, chin strap retention, and visor optical testing."
    },
    {
        "id": "CPRI-BENGALURU",
        "name": "Central Power Research Institute (CPRI)",
        "type": "BIS Recognized Partner Laboratory",
        "city": "Bengaluru",
        "state": "Karnataka",
        "address": "Prof. Sir C.V. Raman Road, Sadashivanagar P.O., Bengaluru 560080",
        "contact": "cpri@cpri.in | +91-80-22072222",
        "accreditation": "NABL & BIS Empanelled High Power Test Facility",
        "domains": ["High Voltage Electrical", "Cables", "Insulation", "Switchgear"],
        "standards_covered": ["IS 694", "IS 1293", "IS 3854"],
        "description": "Premier national laboratory for short-circuit, high-voltage breakdown, dielectric spark tests, and thermal stability of electrical cables and switches."
    },
    {
        "id": "ERTL-NORTH-DELHI",
        "name": "Electronics Regional Test Laboratory (ERTL North)",
        "type": "STQC / BIS Recognized IT Test Laboratory",
        "city": "New Delhi",
        "state": "Delhi NCR",
        "address": "S-Block, Okhla Industrial Area, Phase-II, New Delhi 110020",
        "contact": "ertlnorth@stqc.gov.in | +91-11-26386219",
        "accreditation": "NABL & MeitY/BIS CRS Recognized",
        "domains": ["Electronics and IT", "Safety", "EMI/EMC", "Batteries"],
        "standards_covered": ["IS/IEC 62368-1: 2023", "IS 16046 (Part 2)", "IS 16102 (Part 1 & 2)", "IS 10322 (Part 5/Sec 8)"],
        "description": "Leading recognized laboratory under the BIS Compulsory Registration Scheme (CRS) for laptops, mobile phones, power banks, and LED products."
    }
]

OFFICIAL_LIMS_URL = "https://lims.bis.gov.in/"
OFFICIAL_LIMS_SEARCH = "https://lims.bis.gov.in/home/search_is_number/"
OFFICIAL_LAB_DIRECTORY = "https://www.bis.gov.in/laboratorys/list-of-bis-recognized-lab/?lang=en"

def search_laboratories(
    query: Optional[str] = None,
    standard_number: Optional[str] = None,
    domain: Optional[str] = None,
    city: Optional[str] = None
) -> Dict[str, Any]:
    q = (query or "").lower().strip()
    std = (standard_number or "").upper().replace(" ", "")
    dom = (domain or "").lower().strip()
    c = (city or "").lower().strip()

    results = []
    for lab in LABORATORIES:
        score = 0
        if std:
            for s in lab["standards_covered"]:
                if std in s.upper().replace(" ", ""):
                    score += 50
                    break
        if dom:
            for d in lab["domains"]:
                if dom in d.lower():
                    score += 30
                    break
        if c:
            if c in lab["city"].lower() or c in lab["state"].lower():
                score += 30
        if q:
            blob = f"{lab['name']} {lab['city']} {lab['state']} {lab.get('description', '')} {' '.join(lab['domains'])} {' '.join(lab['standards_covered'])}".lower()
            if q in blob:
                score += 25

        if not any([q, std, dom, c]) or score > 0:
            item = dict(lab)
            item["match_score"] = score
            results.append(item)

    results.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    return {
        "count": len(results),
        "query": {"query": query, "standard": standard_number, "domain": domain, "city": city},
        "laboratories": results,
        "official_resources": {
            "bis_lims_search": OFFICIAL_LIMS_SEARCH,
            "bis_lims_portal": OFFICIAL_LIMS_URL,
            "bis_recognized_directory": OFFICIAL_LAB_DIRECTORY
        },
        "trust_boundary": "Testing scope must be confirmed directly on the BIS LIMS portal. SmartGuide reflects authentic registered facilities but does not issue test reports."
    }
