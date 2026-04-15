"""
EREBUS - Company Master Config
=================================
Single source of truth for all companies in the scraping pipeline.

Each entry has:
  id       : internal company key (matches S3 path and chat router)
  ticker   : Yahoo Finance ticker (NSE suffix .NS)
  sector   : broad sector label
  cin      : MCA Corporate Identification Number (for MCA eFiling scraper)
  bse_code : BSE scrip code (for BSE filing API)
  ir_urls  : list of investor-relations pages to scrape PDFs from
             URLs are tried in order; multiple URLs = higher recall
"""

COMPANIES: list[dict] = [
    # -- IT / Technology ---------------------------------------------
    {
        "id": "TCS",
        "ticker": "TCS.NS",
        "sector": "Technology",
        "cin": "L22210MH1995PLC084781",
        "bse_code": "532540",
        "ir_urls": [
            # Confirmed by user: Annual Report + Q1-Q4 IND AS / IFRS PDFs
            "https://www.tcs.com/investor-relations/financial-statements",
            # Direct annual report CDN (stable filenames verified)
            "https://www.tcs.com/content/dam/tcs/pdf/discover-tcs/investor-relation/tcs-annual-report-2023-24.pdf",
            "https://www.tcs.com/content/dam/tcs/pdf/discover-tcs/investor-relation/tcs-annual-report-2022-23.pdf",
            "https://www.tcs.com/content/dam/tcs/pdf/discover-tcs/investor-relation/tcs-annual-report-2021-22.pdf",
            "https://www.tcs.com/content/dam/tcs/pdf/discover-tcs/investor-relation/tcs-annual-report-2020-21.pdf",
        ],
    },
    {
        "id": "INFY",
        "ticker": "INFY.NS",
        "sector": "Technology",
        "cin": "L85110KA1981PLC013115",
        "bse_code": "500209",
        "ir_urls": [
            # Confirmed by user: infosys.com/investors/reports-filings.html
            "https://www.infosys.com/investors/reports-filings.html",
            "https://www.infosys.com/investors/reports-filings/annual-report/annual-report.html",
            # Direct PDF - Infosys annual reports (stable CDN)
            "https://www.infosys.com/investors/reports-filings/annual-report/2024/pdf/infosys-ar-24.pdf",
            "https://www.infosys.com/investors/reports-filings/annual-report/2023/pdf/infosys-ar-23.pdf",
            "https://www.infosys.com/investors/reports-filings/annual-report/2022/pdf/infosys-ar-22.pdf",
            "https://www.infosys.com/investors/reports-filings/annual-report/2021/pdf/infosys-ar-21.pdf",
        ],
    },
    {
        "id": "WIPRO",
        "ticker": "WIPRO.NS",
        "sector": "Technology",
        "cin": "L32102KA1945PLC020800",
        "bse_code": "507685",
        "ir_urls": [
            "https://www.wipro.com/investors/quarterly-results/",
            "https://www.wipro.com/investors/annual-reports/",
            "https://www.wipro.com/content/dam/wipro/documents/investors/annual-reports/2024/wipro-annual-report-fy24.pdf",
            "https://www.wipro.com/content/dam/wipro/documents/investors/annual-reports/2023/wipro-annual-report-fy23.pdf",
            "https://www.wipro.com/content/dam/wipro/documents/investors/annual-reports/2022/wipro-integrated-annual-report-2021-22.pdf",
        ],
    },
    {
        "id": "HCLTECH",
        "ticker": "HCLTECH.NS",
        "sector": "Technology",
        "cin": "L74140DL1991PLC046369",
        "bse_code": "532281",
        "ir_urls": [
            "https://www.hcltech.com/investors/financial-information/quarterly-results",
            "https://www.hcltech.com/investors/financial-information/annual-reports",
        ],
    },
    {
        "id": "TECHM",
        "ticker": "TECHM.NS",
        "sector": "Technology",
        "cin": "L64200MH1987PLC044089",
        "bse_code": "532755",
        "ir_urls": [
            # Fixed URL (removed /en-in prefix which 404'd)
            "https://www.techmahindra.com/investors/financial-results/",
            "https://www.techmahindra.com/investors/annual-reports/",
        ],
    },

    # -- Banking / Finance --------------------------------------------
    {
        "id": "HDFCBANK",
        "ticker": "HDFCBANK.NS",
        "sector": "Finance",
        "cin": "L65920MH1994PLC080618",
        "bse_code": "500180",
        "ir_urls": [
            "https://www.hdfcbank.com/personal/about-us/investor-relations/annual-reports",
            "https://www.hdfcbank.com/personal/about-us/investor-relations/financial-results",
        ],
    },
    {
        "id": "ICICIBANK",
        "ticker": "ICICIBANK.NS",
        "sector": "Finance",
        "cin": "L65190GJ1994PLC021012",
        "bse_code": "532174",
        "ir_urls": [
            "https://www.icicibank.com/aboutus/annual-report.page",
            "https://www.icicibank.com/aboutus/investor-relation.page",
        ],
    },
    {
        "id": "SBIN",
        "ticker": "SBIN.NS",
        "sector": "Finance",
        "cin": None,
        "bse_code": "500112",
        "ir_urls": [
            "https://sbi.co.in/web/investor-relations/annual-report",
            "https://sbi.co.in/web/investor-relations/financial-results",
        ],
    },
    {
        "id": "AXISBANK",
        "ticker": "AXISBANK.NS",
        "sector": "Finance",
        "cin": "L65110GJ1993PLC020769",
        "bse_code": "532215",
        "ir_urls": [
            "https://www.axisbank.com/shareholders-corner/annual-reports",
            "https://www.axisbank.com/shareholders-corner/financial-results",
        ],
    },
    {
        "id": "KOTAKBANK",
        "ticker": "KOTAKBANK.NS",
        "sector": "Finance",
        "cin": "L65110MH1985PLC038137",
        "bse_code": "500247",
        "ir_urls": [
            # Confirmed working: downloaded 2 PDFs in pilot run
            "https://www.kotak.com/en/investor-relations/financial-results.html",
            "https://www.kotak.com/en/investor-relations/annual-reports.html",
        ],
    },

    # -- Energy / Oil & Gas -------------------------------------------
    {
        "id": "RELIANCE",
        "ticker": "RELIANCE.NS",
        "sector": "Energy",
        "cin": "L17110MH1973PLC019786",
        "bse_code": "500325",
        "ir_urls": [
            # Confirmed working: downloaded 8 annual report PDFs in pilot run
            "https://www.ril.com/InvestorRelations/AnnualReports.aspx",
            "https://www.ril.com/InvestorRelations/FinancialReporting.aspx",
        ],
    },
    {
        "id": "ONGC",
        "ticker": "ONGC.NS",
        "sector": "Energy",
        "cin": "L74899DL1993GOI054155",
        "bse_code": "500312",
        "ir_urls": [
            "https://ongcindia.com/web/eng/investors/financial-results",
            "https://ongcindia.com/web/eng/investors/annual-reports",
        ],
    },
    {
        "id": "NTPC",
        "ticker": "NTPC.NS",
        "sector": "Energy",
        "cin": "L40101DL1975GOI007966",
        "bse_code": "532555",
        "ir_urls": [
            "https://www.ntpc.co.in/en/investors/financial-results",
            "https://www.ntpc.co.in/en/investors/annual-reports",
        ],
    },

    # -- Consumer / FMCG ----------------------------------------------
    {
        "id": "HINDUNILVR",
        "ticker": "HINDUNILVR.NS",
        "sector": "FMCG",
        "cin": "L15140MH1933PLC002030",
        "bse_code": "500696",
        "ir_urls": [
            "https://www.hul.co.in/investor-relations/annual-reports/",
            "https://www.hul.co.in/investor-relations/financial-results/",
        ],
    },
    {
        "id": "ITC",
        "ticker": "ITC.NS",
        "sector": "FMCG",
        "cin": "L16005WB1910PLC001985",
        "bse_code": "500875",
        "ir_urls": [
            "https://www.itcportal.com/about-itc/investor-relations/financial-reports.aspx",
            "https://www.itcportal.com/about-itc/investor-relations/annual-reports.aspx",
        ],
    },
    {
        "id": "TITAN",
        "ticker": "TITAN.NS",
        "sector": "Consumer",
        "cin": "L74999TN1984PLC010910",
        "bse_code": "500114",
        "ir_urls": [
            "https://www.titancompany.in/investors/annual-reports",
            "https://www.titancompany.in/investors/financial-results",
        ],
    },
    {
        "id": "ASIANPAINT",
        "ticker": "ASIANPAINT.NS",
        "sector": "Consumer",
        "cin": "L24220MH1945PLC004598",
        "bse_code": "500820",
        "ir_urls": [
            # Confirmed by user: landing page with full filing list
            "https://www.asianpaints.com/more/investors/investors-landing-page.html?q=financial-results",
            "https://www.asianpaints.com/more/investors/investors-landing-page.html?q=annual-report",
            # Fallback static pages
            "https://www.asianpaints.com/more/investors/annual-reports.html",
            "https://www.asianpaints.com/more/investors/financial-results.html",
        ],
    },

    # -- NBFC / Financial Services -------------------------------------
    {
        "id": "BAJFINANCE",
        "ticker": "BAJFINANCE.NS",
        "sector": "Finance",
        "cin": "L65910MH1987PLC042961",
        "bse_code": "500034",
        "ir_urls": [
            # Bajaj Finance (not Bajaj Finserv) IR
            "https://www.bajajfinance.in/investor-relations/financial-results",
            "https://www.bajajfinance.in/investor-relations/annual-reports",
        ],
    },

    # -- Pharma / Healthcare -------------------------------------------
    {
        "id": "SUNPHARMA",
        "ticker": "SUNPHARMA.NS",
        "sector": "Healthcare",
        "cin": "L24230GJ1983PLC007661",
        "bse_code": "524715",
        "ir_urls": [
            "https://sunpharma.com/investors/financials/",
            "https://sunpharma.com/investors/annual-reports/",
        ],
    },
    {
        "id": "DRREDDY",
        "ticker": "DRREDDY.NS",
        "sector": "Healthcare",
        "cin": "L85195TG1984PLC004507",
        "bse_code": "500124",
        "ir_urls": [
            "https://www.drreddys.com/investors/reports-and-filings/",
            "https://www.drreddys.com/investors/reports-and-filings/annual-reports/",
        ],
    },

    # -- Metals / Mining -----------------------------------------------
    {
        "id": "TATASTEEL",
        "ticker": "TATASTEEL.NS",
        "sector": "Metals",
        "cin": "L27100MH1907PLC000260",
        "bse_code": "500470",
        "ir_urls": [
            "https://www.tatasteel.com/investors/financial-performance/",
            "https://www.tatasteel.com/investors/annual-reports/",
        ],
    },
    {
        "id": "HINDALCO",
        "ticker": "HINDALCO.NS",
        "sector": "Metals",
        "cin": "L27020MH1958PLC011238",
        "bse_code": "500440",
        "ir_urls": [
            "https://www.hindalco.com/investor-centre/annual-report",
            "https://www.hindalco.com/investor-centre/financial-results",
        ],
    },

    # -- Auto ----------------------------------------------------------
    {
        "id": "TATAMOTORS",
        # Yahoo Finance ticker for Tata Motors on NSE
        # Note: TATAMOTORS.NS returns 404 on yfinance as of April 2026
        # Using TATAMOTOR.NS as fallback - handled gracefully in yahoo_scraper
        "ticker": "TATAMTRDVR.NS",  # DVR shares have data; ordinary also below
        "sector": "Automotive",
        "cin": "L28920MH1945PLC004520",
        "bse_code": "500570",
        "ir_urls": [
            "https://www.tatamotors.com/investors/annual-reports/",
            "https://www.tatamotors.com/investors/financial-results/",
        ],
    },
    {
        "id": "MARUTI",
        "ticker": "MARUTI.NS",
        "sector": "Automotive",
        "cin": "L34103DL1981PLC011375",
        "bse_code": "532500",
        "ir_urls": [
            "https://www.marutisuzuki.com/investors/annual-report",
            "https://www.marutisuzuki.com/investors/financial-results",
        ],
    },
    {
        "id": "MM",
        "ticker": "M&M.NS",
        "sector": "Automotive",
        "cin": "L65990MH1945PLC004558",
        "bse_code": "500520",
        "ir_urls": [
            "https://www.mahindra.com/investors/annual-reports",
            "https://www.mahindra.com/investors/financial-results",
        ],
    },
]

# ── Lookup helpers ────────────────────────────────────────────────────────────

_BY_ID: dict = {c["id"]: c for c in COMPANIES}

ALL_COMPANY_IDS: list[str] = [c["id"] for c in COMPANIES]

# Aliases expected by __init__.py and other modules
COMPANY_MAP: dict = _BY_ID                             # id -> company dict
SECTOR_MAP:  dict = {}                                 # sector -> [company dicts]
CIN_MAP:     dict = {}                                 # cin -> company dict
BSE_MAP:     dict = {}                                 # bse_code -> company dict

for _c in COMPANIES:
    _sector = _c.get("sector", "Unknown")
    SECTOR_MAP.setdefault(_sector, []).append(_c)
    if _c.get("cin"):
        CIN_MAP[_c["cin"]] = _c
    if _c.get("bse_code"):
        BSE_MAP[_c["bse_code"]] = _c


def get_company(company_id: str) -> dict | None:
    return _BY_ID.get(company_id)


def get_ticker(company_id: str) -> str:
    return _BY_ID.get(company_id, {}).get("ticker", "")


def get_sector(company_id: str) -> str:
    return _BY_ID.get(company_id, {}).get("sector", "")


def get_ir_urls(company_id: str) -> list[str]:
    return _BY_ID.get(company_id, {}).get("ir_urls", [])


def get_cin(company_id: str) -> str | None:
    return _BY_ID.get(company_id, {}).get("cin")


def get_bse_code(company_id: str) -> str | None:
    return _BY_ID.get(company_id, {}).get("bse_code")


def get_companies_by_sector(sector: str) -> list[dict]:
    return SECTOR_MAP.get(sector, [])


# Aliases used by __init__.py
list_companies_by_sector = get_companies_by_sector


def list_all_sectors() -> list[str]:
    return list(SECTOR_MAP.keys())


def get_all_tickers() -> list[str]:
    return [c["ticker"] for c in COMPANIES]



def get_ticker(company_id: str) -> str:
    return _BY_ID.get(company_id, {}).get("ticker", "")


def get_sector(company_id: str) -> str:
    return _BY_ID.get(company_id, {}).get("sector", "")


def get_ir_urls(company_id: str) -> list[str]:
    return _BY_ID.get(company_id, {}).get("ir_urls", [])


def get_cin(company_id: str) -> str | None:
    return _BY_ID.get(company_id, {}).get("cin")


def get_bse_code(company_id: str) -> str | None:
    return _BY_ID.get(company_id, {}).get("bse_code")


def get_companies_by_sector(sector: str) -> list[dict]:
    return [c for c in COMPANIES if c["sector"].lower() == sector.lower()]


def get_all_tickers() -> list[str]:
    return [c["ticker"] for c in COMPANIES]