import pandas as pd
from stress_test.data.raw_data import load_raw_macro_data
import stress_test.config as cfg
from pathlib import Path

raw_data = load_raw_macro_data()
processed_data = {}
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

def load_processed_macro_data():
    gg_df = raw_data["gdp_growth_df"]
    ur_df = raw_data["unemployment_rate_df"]
    hpgmi_df = raw_data["house_price_growth_df"] # house price growth monthly index
    prm_df = raw_data["policy_rate_df"] # policy rate monthly
    g10ym_df = raw_data["gilt_10y_df"] # gilt 10 year rate monthly

    # GDP Growth
    gg_df = gg_df.rename(columns={gg_df.columns[0]: "quarter", gg_df.columns[1]: "gdp_growth_qoq (decimal)"})
    gg_df = gg_df[gg_df["quarter"].str.contains("Q", na=False)]
    gg_df["quarter"] = gg_df["quarter"].astype(str).str.replace(" ", "", regex=False)
    gg_df["gdp_growth_qoq (decimal)"] = pd.to_numeric(gg_df["gdp_growth_qoq (decimal)"], errors="coerce") / 100
    gg_df = gg_df.reset_index(drop=True)
    processed_data["gdp_growth_df"] = gg_df

    # Unemployment Rate
    ur_df = ur_df.rename(columns={ur_df.columns[0]: "quarter", ur_df.columns[1]: "unemployment_rate (decimal)"})
    ur_df = ur_df[ur_df["quarter"].str.contains("Q", na=False)]
    ur_df["quarter"] = ur_df["quarter"].astype(str).str.replace(" ", "", regex=False)
    ur_df["unemployment_rate (decimal)"] = pd.to_numeric(ur_df["unemployment_rate (decimal)"], errors="coerce") / 100
    ur_df = ur_df.reset_index(drop=True)
    processed_data["unemployment_rate_df"] = ur_df

    # House Price Growth (monthly index -> quarterly pct change)
    hpgmi_df = hpgmi_df.rename(columns={hpgmi_df.columns[0]: "month", hpgmi_df.columns[1]: "hpg index"})
    hpgmi_df = hpgmi_df.iloc[2:,:2]
    hpgmi_df = hpgmi_df.copy()
    hpgmi_df["month"] = ( # Removing [r] (revised rate) and [p] (provisional rate) from monthly column
        hpgmi_df["month"].astype(str)
        .str.replace(r"\s*\[[rpRP]\]\s*$", "", regex=True)
        .str.strip()
    )
    hpgmi_df["month"] = ( # ONS provides inconsistent month formatting, ensuring Mmm YYYY format for datetime parsing
        hpgmi_df["month"]
        .str.replace(r"^([A-Za-z]{3})[A-Za-z]*\s+(\d{4})$", r"\1 \2", regex=True)
        .str.title()
    )
    hpgmi_df["month"] = pd.to_datetime(hpgmi_df["month"], format="%b %Y", errors="raise")
    hpgmi_df["hpg index"] = pd.to_numeric(hpgmi_df["hpg index"], errors="coerce")
    hpgmi_df = hpgmi_df.dropna(subset=["month", "hpg index"])
    hpgmi_df = hpgmi_df.set_index("month").sort_index()
    hq_index = hpgmi_df["hpg index"].resample("QE").mean()
    hq_growth = hq_index.pct_change(1)

    hpg_df = hq_growth.to_frame(name="house_price_growth_qoq (decimal)")
    hpg_df.index = hpg_df.index.to_period(cfg.FREQUENCY)
    hpg_df = hpg_df.reset_index().rename(columns={"month": "quarter"})
    hpg_df["house_price_growth_qoq (decimal)"] = (hpg_df["house_price_growth_qoq (decimal)"])
    processed_data["house_price_growth_df"] = hpg_df.dropna().reset_index(drop=True)

    # Policy Rate
    prm_df["month"] = (
        prm_df["DATE"]
        .str.replace(r"^\d{1,2}\s+", "", regex=True)
    )
    prm_df["month"] = ( # No visible inconsistencies, but future-proofing in case future errors in dataset
        prm_df["month"]
        .str.replace(r"^([A-Za-z]{3})[A-Za-z]*\s+(\d{4})$", r"\1 \2", regex=True)
        .str.title()
    )
    prm_df["month"] = pd.to_datetime(prm_df["month"], format="%b %Y", errors="raise")
    prm_df = prm_df.sort_values("month").set_index("month")
    pr_df = (prm_df["IUMABEDR"].resample("QE").last().to_frame(name="policy_rate (decimal)"))
    pr_df.index = pr_df.index.to_period(cfg.FREQUENCY)
    pr_df["policy_rate (decimal)"] = pr_df["policy_rate (decimal)"] / 100
    pr_df = pr_df.reset_index().rename(columns={"month": "quarter"})
    processed_data["policy_rate_df"] = pr_df.dropna()

    # GILT 10Y
    g10ym_df["month"] = (
        g10ym_df["DATE"]
        .str.replace(r"^\d{1,2}\s+", "", regex=True)
    )
    g10ym_df["month"] = ( # No visible inconsistencies, but future-proofing in case future errors in dataset
        g10ym_df["month"]
        .str.replace(r"^([A-Za-z]{3})[A-Za-z]*\s+(\d{4})$", r"\1 \2", regex=True)
        .str.title()
    )
    g10ym_df["month"] = pd.to_datetime(g10ym_df["month"], format="%b %Y", errors="raise")
    g10ym_df = g10ym_df.sort_values("month").set_index("month")
    g10y_df = (g10ym_df["IUMAMNZC"].resample("QE").last().to_frame(name="gilt_10y_yield (decimal)"))
    g10y_df.index = g10y_df.index.to_period(cfg.FREQUENCY)
    g10y_df["gilt_10y_yield (decimal)"] = g10y_df["gilt_10y_yield (decimal)"] / 100
    g10y_df = g10y_df.reset_index().rename(columns={"month": "quarter"})
    processed_data["gilt_10y_df"] = g10y_df.dropna()

    for name, df in processed_data.items():
        df.to_csv(output_dir / f"{name}.csv", index=False)

    return processed_data
