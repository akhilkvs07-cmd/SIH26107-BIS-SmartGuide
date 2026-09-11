"""Live BIS LIMS scope lookup for SmartGuide laboratory routing.

The BIS LIMS portal is the source of truth for recognized-lab scope. This
module performs a best-effort server-side lookup against the public LIMS
search-by-IS page and parses the returned table without inventing scope data.
If LIMS is temporarily unavailable, callers can fall back to the local BIS
Labs directory.
"""
from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
import re
import time

LIMS_SEARCH = "https://lims.bis.gov.in/home/search_is_number/"
_CACHE = {}
_CACHE_TTL = 300


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self._row = None
        self._cell = None
        self._link = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            self._row = []
        elif self._row is not None and tag == "td":
            self._cell = []
            self._link = None
        elif self._cell is not None and tag == "a":
            self._link = attrs.get("href")

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self._row is not None and self._cell is not None:
            text = re.sub(r"\s+", " ", " ".join(self._cell)).strip()
            self._row.append({"text": text, "href": self._link})
            self._cell = None
            self._link = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None


def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _lookup_url(standard):
    value = _clean(standard)
    return LIMS_SEARCH + "?" + urlencode({"is_number__doc_no": value})


def search_scope(standard, product="", city="", limit=50):
    """Return current LIMS search rows for an IS number/standard.

    Results are ranked by exact city mention first, then rows with a known
    product/standard match. The parser intentionally preserves the official
    LIMS row text so SmartGuide does not manufacture test capability claims.
    """
    standard = _clean(standard)
    if not standard:
        return {"results": [], "source_url": LIMS_SEARCH, "live": False, "error": "No Indian Standard supplied."}

    key = standard.lower()
    now = time.time()
    cached = _CACHE.get(key)
    if cached and now - cached["time"] < _CACHE_TTL:
        payload = dict(cached["payload"])
        payload["cached"] = True
        return payload

    url = _lookup_url(standard)
    req = Request(url, headers={"User-Agent": "BIS-SmartGuide/1.0 (standards research)"})
    try:
        with urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return {"results": [], "source_url": url, "live": False, "error": str(exc)[:180]}

    parser = _TableParser()
    parser.feed(html)
    rows = parser.rows
    parsed = []
    city_key = _clean(city).lower()

    for row in rows:
        cells = [x.get("text", "") for x in row]
        if len(cells) < 5:
            continue
        joined = " | ".join(cells).lower()
        if "lab name" in joined and "indian standard" in joined:
            continue
        lab_name = cells[0]
        osl_code = cells[1] if len(cells) > 1 else ""
        std_no = cells[2] if len(cells) > 2 else standard
        product_name = cells[3] if len(cells) > 3 else ""
        designation = cells[4] if len(cells) > 4 else ""
        charges = cells[5] if len(cells) > 5 else ""
        validity = cells[6] if len(cells) > 6 else ""
        remark = cells[7] if len(cells) > 7 else ""
        if not lab_name or lab_name.lower() in {"image", "none"}:
            continue
        text = " ".join(cells).lower()
        city_match = bool(city_key and city_key in text)
        parsed.append({
            "lab_name": _clean(lab_name),
            "osl_code": _clean(osl_code),
            "standard_number": _clean(std_no),
            "product": _clean(product_name),
            "designation": _clean(designation),
            "testing_charges": _clean(charges),
            "validity_date": _clean(validity),
            "remark": _clean(remark),
            "city_match": city_match,
            "source_url": url,
            "source_status": "LIVE_BIS_LIMS_SCOPE_SEARCH",
            "scope_status": "LIMS_SCOPE_MATCH",
            "verification_status": "BIS_LIMS_SCOPE_FOUND",
            "nabl_status": "NOT_ASSERTED_BY_SMARTGUIDE",
        })

    parsed.sort(key=lambda x: (0 if x["city_match"] else 1, x["lab_name"].lower()))
    payload = {
        "results": parsed[:max(1, min(int(limit or 50), 50))],
        "total_found": len(parsed),
        "source_url": url,
        "live": True,
        "cached": False,
        "source": "BIS LIMS Search by IS Number",
    }
    _CACHE[key] = {"time": now, "payload": payload}
    return payload
