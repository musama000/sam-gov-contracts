"""
SAM.gov Contract Opportunities Scraper
Uses the official SAM.gov Opportunities API (v2)

Get your free API key:
  1. Log in at https://sam.gov
  2. Go to Account Details -> Request Public API Key
API docs: https://open.gsa.gov/api/get-opportunities-public-api/
"""

import os
import json
import time
from datetime import datetime, timedelta

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SAM_API_KEY")
BASE_URL = "https://api.sam.gov/prod/opportunities/v2/search"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def search_opportunities(
    keyword=None,
    naics_code=None,
    posted_from=None,
    posted_to=None,
    set_aside=None,
    notice_type=None,
    limit=100,
    offset=0,
):
    """Search SAM.gov contract opportunities.

    Args:
        keyword: Search term (e.g. "cybersecurity", "IT services")
        naics_code: NAICS code filter (e.g. "541512" for computer systems design)
        posted_from: Start date MM/dd/yyyy
        posted_to: End date MM/dd/yyyy
        set_aside: Set-aside type (e.g. "SBA", "8a", "HUBZone", "SDVOSBC", "WOSB")
        notice_type: Type of notice (e.g. "o" solicitation, "p" presolicitation,
                     "k" combined synopsis, "r" sources sought, "s" special notice)
        limit: Results per page (max 1000)
        offset: Pagination offset
    """
    if not API_KEY:
        raise ValueError(
            "SAM_API_KEY not set. Get one at https://sam.gov/content/entity-registration"
        )

    params = {
        "api_key": API_KEY,
        "limit": limit,
        "offset": offset,
        "postedFrom": posted_from or (datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y"),
        "postedTo": posted_to or datetime.now().strftime("%m/%d/%Y"),
    }

    if keyword:
        params["keyword"] = keyword
    if naics_code:
        params["ncode"] = naics_code
    if set_aside:
        params["typeOfSetAside"] = set_aside
    if notice_type:
        params["ptype"] = notice_type

    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def extract_records(data):
    """Flatten API response into a list of dicts for CSV/DataFrame."""
    records = []
    for opp in data.get("opportunitiesData", []):
        records.append({
            "notice_id": opp.get("noticeId"),
            "title": opp.get("title"),
            "department": opp.get("department"),
            "sub_tier": opp.get("subTier"),
            "office": opp.get("office"),
            "posted_date": opp.get("postedDate"),
            "response_deadline": opp.get("responseDeadLine"),
            "notice_type": opp.get("type"),
            "set_aside": opp.get("typeOfSetAside"),
            "naics_code": opp.get("naicsCode"),
            "classification_code": opp.get("classificationCode"),
            "active": opp.get("active"),
            "description": opp.get("description", "")[:500],
            "link": f"https://sam.gov/opp/{opp.get('noticeId')}/view" if opp.get("noticeId") else "",
        })
    return records


def scrape(keyword=None, naics_code=None, notice_type=None, set_aside=None,
           days_back=30, max_results=500):
    """Main scrape function. Paginates through results and saves to CSV."""
    posted_from = (datetime.now() - timedelta(days=days_back)).strftime("%m/%d/%Y")
    posted_to = datetime.now().strftime("%m/%d/%Y")

    all_records = []
    offset = 0
    page_size = 100

    print(f"Searching SAM.gov: keyword={keyword}, naics={naics_code}, "
          f"type={notice_type}, set_aside={set_aside}, last {days_back} days")

    while offset < max_results:
        data = search_opportunities(
            keyword=keyword,
            naics_code=naics_code,
            posted_from=posted_from,
            posted_to=posted_to,
            set_aside=set_aside,
            notice_type=notice_type,
            limit=page_size,
            offset=offset,
        )

        total = data.get("totalRecords", 0)
        records = extract_records(data)

        if not records:
            break

        all_records.extend(records)
        offset += page_size
        print(f"  Fetched {len(all_records)}/{min(total, max_results)} opportunities...")

        if offset >= total:
            break

        time.sleep(1)  # rate limit courtesy

    if not all_records:
        print("No opportunities found.")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = keyword or naics_code or "all"
    tag = tag.replace(" ", "_").lower()
    filename = f"sam_opportunities_{tag}_{timestamp}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    df.to_csv(filepath, index=False)
    print(f"\nSaved {len(df)} opportunities to {filepath}")
    return df


if __name__ == "__main__":
    all_dfs = []

    # Targeted searches based on Mohammed's background:
    # - BS Aerospace Engineering (USC), NASA RASC-AL finalist
    # - CAD: Siemens NX (Advanced), SolidWorks, ANSYS FEA/CFD
    # - Software/web dev skills (Python, JS, APIs)
    # - Data analysis (Matlab, research)
    #
    # Relevant NAICS codes:
    #   541330 - Engineering Services
    #   541715 - R&D in Physical/Engineering Sciences
    #   541512 - Computer Systems Design
    #   541380 - Testing Laboratories
    #   336414 - Guided Missile & Space Vehicle Mfg

    searches = [
        # Engineering services — broadest fit for aero eng background
        {"keyword": "engineering services", "naics_code": "541330", "days_back": 30,
         "max_results": 100, "label": "Engineering Services (NAICS 541330)"},

        # CAD/drafting/3D modeling — direct skill match
        {"keyword": "CAD modeling", "days_back": 60,
         "max_results": 100, "label": "CAD Modeling & Drafting"},

        # IT/software development — matches current skills
        {"keyword": "software development", "naics_code": "541512", "days_back": 30,
         "max_results": 100, "label": "Software Development (NAICS 541512)"},

        # Aerospace-specific
        {"keyword": "aerospace", "days_back": 60,
         "max_results": 100, "label": "Aerospace Contracts"},

        # Data analysis / research support — NOAA background + current data skills
        {"keyword": "data analysis", "days_back": 30,
         "max_results": 100, "label": "Data Analysis & Research Support"},

        # Small biz set-asides for engineering
        {"keyword": "engineering", "set_aside": "SBA", "days_back": 30,
         "max_results": 100, "label": "Small Business Engineering Set-Asides"},
    ]

    for s in searches:
        label = s.pop("label")
        print("\n" + "=" * 60)
        print(label)
        print("=" * 60)
        df = scrape(**s)
        all_dfs.append(df)

    # Combine and deduplicate
    combined = pd.concat([df for df in all_dfs if not df.empty], ignore_index=True)
    combined = combined.drop_duplicates(subset="notice_id")

    if not combined.empty:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(OUTPUT_DIR, f"sam_mohammed_targeted_{timestamp}.csv")
        combined.to_csv(filepath, index=False)

        print("\n" + "=" * 60)
        print(f"TOTAL: {len(combined)} unique opportunities saved to {filepath}")
        print("=" * 60)

        print("\nTop 20 results:")
        cols = ["title", "department", "notice_type", "naics_code",
                "posted_date", "response_deadline"]
        available = [c for c in cols if c in combined.columns]
        print(combined[available].head(20).to_string())
    else:
        print("\nNo opportunities found.")
