import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from io import BytesIO
from io import StringIO
from pathlib import Path

output_dir = Path("data/raw")
output_dir.mkdir(parents=True, exist_ok=True)

def load_raw_macro_data() -> dict[str, pd.DataFrame]:
    raw_data: dict[str, pd.DataFrame] = {}
    # ONS downloads
    # GDP Growth & Unemployment Rate
    url = "https://www.ons.gov.uk/generator"
    uri = {
        "gdp_growth_df": "/economy/grossdomesticproductgdp/timeseries/ihyq/ukea",
        "unemployment_rate_df": "/employmentandlabourmarket/peoplenotinwork/unemployment/timeseries/mgsx/lms"
    }
    for k, u in uri.items():
        params = {
            "format": "csv",
            "uri": u
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        raw_data[k] = pd.read_csv(StringIO(r.text))

    # House Price Growth (no generator endpoint so scraping .xlsx w/ BeautifulSoup)
    url = "https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/ukhousepriceindexmonthlypricestatistics"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    xlsx_links = [
        a["href"]
        for a in soup.select('a[href]')
        if a["href"].lower().endswith(".xlsx")
    ]
    if not xlsx_links:
        raise RuntimeError("No .xlsx download links found on UK HPI page")

    download_url = urljoin("https://www.ons.gov.uk", xlsx_links[0])

    r = requests.get(download_url, headers=headers, timeout=60)
    r.raise_for_status()

    raw_data["house_price_growth_df"] = pd.read_excel(BytesIO(r.content), sheet_name="1")


    # BoE IADB downloads
    def download_boe_iadb(series_codes, start_date, end_date):
        base_url = "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp"
        params = {
            "csv.x": "yes",
            "SeriesCodes": ",".join(series_codes),
            "UsingCodes": "Y",
            "Datefrom": start_date,
            "Dateto": end_date,
            "CSVF": "TN",
            "VPD": "Y",
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Referer": "https://www.bankofengland.co.uk/statistics/tables",
        }

        r = requests.get(base_url, params=params, headers=headers, timeout=60)
        r.raise_for_status()

        return pd.read_csv(StringIO(r.text))


    # Policy Rate
    raw_data["policy_rate_df"] = download_boe_iadb(["IUMABEDR"], "01/Jan/1990", "now")


    # GILT 10Y
    raw_data["gilt_10y_df"] = download_boe_iadb(["IUMAMNZC"], "01/Jan/1990", "now")

    for name, df in raw_data.items():
        df.to_csv(output_dir / f"{name}.csv", index=False)

    return raw_data

