"""BIS laboratory router backed by the current BIS LIMS directory.

Important trust rule:
- The lab identities, addresses and contact details below mirror the BIS LIMS
  *BIS Labs* directory.
- BIS LIMS has the authoritative, current recognized-lab directory and scope.
- This module does NOT invent NABL accreditation, test capability or turnaround
  times. Scope must be checked in BIS LIMS before a user books testing.
- Distances are great-circle Haversine distances from supplied coordinates to
  stored map coordinates. The lab coordinates are routing coordinates, not a
  claim that BIS publishes latitude/longitude as part of its directory.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


OFFICIAL_LIMS_URL = "https://lims.bis.gov.in/"
OFFICIAL_LIMS_SEARCH = "https://lims.bis.gov.in/home/search_is_number/"
OFFICIAL_BIS_LABS_URL = "https://lims.bis.gov.in/home/bis_labs/"
OFFICIAL_LAB_DIRECTORY = "https://www.bis.gov.in/laboratorys/list-of-bis-recognized-lab/?lang=en"

LABORATORIES: List[Dict[str, Any]] = [
    {"id":"BIS-BNBL-BENGALURU","name":"BIS, Bengaluru Branch Laboratory (BNBL)","type":"BIS Laboratory","city":"Bengaluru","state":"Karnataka","address":"Peenya Industrial Area, 1st Stage, Tumkur Road, Bengaluru - 560058","contact_person":"Pyla Deshick (OIC - Sample Cell)","phone":"+91-80-29908860","email":"bnbol@bis.gov.in","lat":13.0287,"lon":77.5200},
    {"id":"BIS-CL-GHAZIABAD","name":"BIS, Central Laboratory (CL)","type":"BIS Laboratory","city":"Ghaziabad","state":"Uttar Pradesh","address":"20/9, Site 4, Sahibabad Industrial Area, Sahibabad, Ghaziabad, Uttar Pradesh - 201010","contact_person":"Mukund Madhav Mishra (OIC Sample Cell)","phone":"+91-120-2811989","email":"sample@bis.gov.in","lat":28.6946,"lon":77.3489},
    {"id":"BIS-ERL-KOLKATA","name":"BIS, Eastern Regional Laboratory (ERL)","type":"BIS Laboratory","city":"Kolkata","state":"West Bengal","address":"1/14, CIT Scheme VII M, VIP Road, Kankurgachi, Kolkata - 700054","contact_person":"TARIQUE SAJJAD (OIC- Sample Cell)","phone":"+91-33-23209474","email":"sample.erol@bis.gov.in","lat":22.5697,"lon":88.4069},
    {"id":"BIS-GBL-GUWAHATI","name":"BIS, Guwahati Branch Laboratory (GBL)","type":"BIS Laboratory","city":"Guwahati","state":"Assam","address":"2nd Floor, West End Block, Housefed Building Complex, Last Gate, Dispur, Guwahati, Assam - 781006","contact_person":"THECHANO C OVUNG (OIC Sample Cell)","phone":"+91-361-2224670","email":"gbol@bis.gov.in","lat":26.1445,"lon":91.7362},
    {"id":"BIS-NRL-MOHALI","name":"BIS, Northern Regional Laboratory (NRL)","type":"BIS Laboratory","city":"Mohali","state":"Punjab","address":"B-69, Industrial Focal Point, Phase VII, Mohali, Punjab - 160059","contact_person":"Ms. Sangeeta Choudhary (OIC-Sample Cell)","phone":"+91-172-4802676","email":"nrolsample@bis.gov.in","lat":30.7046,"lon":76.7179},
    {"id":"BIS-PBL-PATNA","name":"BIS, Patna Branch Laboratory (PBL)","type":"BIS Laboratory","city":"Patna","state":"Bihar","address":"Bureau of Indian Standards, Patliputra Industrial Estate, Patna, Bihar - 800013","contact_person":"Aabid Hussain (OIC Sample Cell)","phone":"+91-9471192544","email":"pbol@bis.gov.in","lat":25.5941,"lon":85.1376},
    {"id":"BIS-SRL-CHENNAI","name":"BIS, Southern Regional Laboratory (SRL)","type":"BIS Laboratory","city":"Chennai","state":"Tamil Nadu","address":"IV Cross Road, CIT Campus, Taramani, Chennai - 600113","contact_person":"Dr. Surya Kalyani Sreekanthan","phone":"+91-44-22541208","email":"srol@bis.gov.in","lat":12.9852,"lon":80.2440},
    {"id":"BIS-WRL-MUMBAI","name":"BIS, Western Regional Laboratory (WRL)","type":"BIS Laboratory","city":"Mumbai","state":"Maharashtra","address":"Plot No. E9, Road No. 8, M.I.D.C, Andheri (East), Mumbai, Maharashtra - 400093","contact_person":"Shri Anand Bhatt (OIC Sample Cell)","phone":"+91-22-28329295","email":"wrol@bis.gov.in","lat":19.1245,"lon":72.8687},
    {"id":"BIS-HYBL-HYDERABAD","name":"BIS, Hyderabad Branch Laboratory (HYBL)","type":"BIS Laboratory","city":"Hyderabad","state":"Telangana","address":"Bureau of Indian Standards, Hyderabad Branch Laboratory, Plot No. 1, Sy No. 367/1, Moula Ali, Hyderabad - 500040","contact_person":"MAJ Vinod","phone":"+91-9952993252","email":"hybl@bis.gov.in","lat":17.4639,"lon":78.5600},
    {"id":"BIS-JKBL-JAMMU","name":"BIS, Jammu Kashmir Branch Laboratory (JKBL)","type":"BIS Laboratory","city":"Jammu","state":"Jammu & Kashmir","address":"Lane No. 4, SIDCO Industrial Complex, Bari Brahmana, Jammu - 181133","contact_person":"Saaqib Raahi","phone":"+91-7006607673","email":"jkbl@bis.gov.in","lat":32.6540,"lon":74.8700},
]

ORIGINS = {
    "new delhi": (28.6139,77.2090), "delhi": (28.6139,77.2090), "mumbai": (19.0760,72.8777),
    "bengaluru": (12.9716,77.5946), "bangalore": (12.9716,77.5946), "kolkata": (22.5726,88.3639),
    "chennai": (13.0827,80.2707), "hyderabad": (17.3850,78.4867), "patna": (25.5941,85.1376),
    "guwahati": (26.1445,91.7362), "jaipur": (26.9124,75.7873), "ahmedabad": (23.0225,72.5714),
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float, ) -> float:
    radius=6371.0088; p1,p2=math.radians(lat1),math.radians(lat2); dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*radius*math.asin(math.sqrt(a))


def _origin(lat: Optional[float], lon: Optional[float], city: Optional[str]):
    if lat is not None and lon is not None: return float(lat),float(lon),"user_or_selected_coordinates"
    key=str(city or "new delhi").strip().lower(); point=ORIGINS.get(key,ORIGINS["new delhi"])
    return point[0],point[1],f"city_default:{key if key in ORIGINS else 'new delhi'}"


def search_laboratories(query: Optional[str]=None, standard_number: Optional[str]=None, domain: Optional[str]=None, city: Optional[str]=None, latitude: Optional[float]=None, longitude: Optional[float]=None) -> Dict[str,Any]:
    q=str(query or "").lower().strip(); std=str(standard_number or "").lower().replace(" ",""); dom=str(domain or "").lower().strip(); c=str(city or "").lower().strip()
    origin_lat,origin_lon,origin_source=_origin(latitude,longitude,city); results=[]
    for lab in LABORATORIES:
        blob=" ".join([lab["name"],lab["city"],lab["state"],lab["address"],lab.get("contact_person",""),lab.get("email","")]).lower()
        text_match=bool(q and q in blob); city_match=bool(c and (c in lab["city"].lower() or c in lab["state"].lower()))
        # A product name does not itself prove a laboratory scope. It should
        # never suppress official labs; scope is explicitly verified in LIMS.
        score=(25 if text_match else 0)+(30 if city_match else 0)+(5 if std else 0)+(5 if dom else 0)
        item=dict(lab); item["match_score"]=score
        item["distance_km"]=round(haversine_km(origin_lat,origin_lon,lab["lat"],lab["lon"]),2)
        item["source_status"]="OFFICIAL_BIS_LIMS_DIRECTORY"; item["verification_status"]="DIRECTORY_VERIFIED_SCOPE_PENDING"
        item["scope_status"]="VERIFY_CURRENT_SCOPE_IN_BIS_LIMS"; item["nabl_status"]="NOT_ASSERTED_BY_SMARTGUIDE"
        item["scope_url"]=OFFICIAL_BIS_LABS_URL; item["maps_url"]=f"https://www.google.com/maps/dir/?api=1&destination={lab['lat']},{lab['lon']}"
        results.append(item)
    results.sort(key=lambda x:(-x["match_score"],x["distance_km"]))
    return {"count":len(results),"query":{"query":query,"standard":standard_number,"domain":domain,"city":city,"latitude":origin_lat,"longitude":origin_lon},"distance_method":"Great-circle Haversine","origin_source":origin_source,"laboratories":results[:12],"official_resources":{"bis_lims_labs":OFFICIAL_BIS_LABS_URL,"bis_lims_portal":OFFICIAL_LIMS_URL,"bis_lims_is_search":OFFICIAL_LIMS_SEARCH,"bis_recognized_directory":OFFICIAL_LAB_DIRECTORY},"trust_boundary":"Lab identity, address and contact details are sourced from the BIS LIMS BIS Labs directory. SmartGuide does not claim NABL accreditation or testing scope unless independently evidenced. Confirm the exact IS number/test scope and current recognition in BIS LIMS before booking."}
