import pandas as pd
from data.raw.raw_data import load_raw_macro_data
import stress_test.config as cfg

raw_data = load_raw_macro_data()

gg_df = raw_data["gdp_growth_df"]
ur_df = raw_data["unemployment_rate_df"]
hpgi_df = raw_data["house_price_growth_df"]
pr_df = raw_data["policy_rate_df"]
g10y_df = raw_data["gilt_10y_df"]

gg_df = gg_df.rename(columns={gg_df.columns[0]: "quarter", gg_df.columns[1]: "gdp_growth (%)"})
gg_df = gg_df[gg_df["quarter"].str.contains("Q", na=False)]
gg_df["quarter"] = gg_df["quarter"].astype(str).str.replace(" ", "", regex=False)
gg_df["gdp_growth (%)"] = pd.to_numeric(gg_df["gdp_growth (%)"], errors="coerce")
raw_data["gdp_growth_df"] = gg_df

ur_df = ur_df.rename(columns={ur_df.columns[0]: "quarter", ur_df.columns[1]: "unemployment_rate (%)"})
ur_df = ur_df[ur_df["quarter"].str.contains("Q", na=False)]
ur_df["quarter"] = ur_df["quarter"].astype(str).str.replace(" ", "", regex=False)
ur_df["unemployment_rate (%)"] = pd.to_numeric(ur_df["unemployment_rate (%)"], errors="coerce")
raw_data["unemployment_rate_df"] = ur_df

hpgi_df = hpgi_df.rename(columns={hpgi_df.columns[0]: "month", hpgi_df.columns[1]: "hpg index"})
hpgi_df = hpgi_df.iloc[2:,:2]
hpgi_df = hpgi_df.copy()
hpgi_df["month"] = (
    hpgi_df["month"].astype(str)
    .str.replace(r"\s*\[[rpRP]\]\s*$", "", regex=True)
    .str.strip()
)
hpgi_df["month"] = (
    hpgi_df["month"]
    .str.replace(r"^([A-Za-z]{3})[A-Za-z]*\s+(\d{4})$", r"\1 \2", regex=True)
    .str.title()
)
hpgi_df["month"] = pd.to_datetime(hpgi_df["month"], format="%b %Y", errors="raise")
hpgi_df["hpg index"] = pd.to_numeric(hpgi_df["hpg index"], errors="coerce")
hpgi_df = hpgi_df.dropna(subset=["month", "hpg index"])
hpgi_df = hpgi_df.set_index("month").sort_index()
q_index = hpgi_df["hpg index"].resample("QE").mean()
q_growth = q_index.pct_change(1)

hpg_df = q_growth.to_frame(name="house_price_growth")
hpg_df.index = hpg_df.index.to_period(cfg.FREQUENCY)
hpg_df = hpg_df.reset_index().rename(columns={"month": "quarter", "house_price_growth": "house_price_growth (%)"})
hpg_df["house_price_growth (%)"] = (hpg_df["house_price_growth (%)"] * 100).round(1)
raw_data["house_price_growth_df"] = hpg_df.dropna()



if __name__ == "__main__":
    for name, df in raw_data.items():
        df.to_csv(f"data/processed/{name}.csv", index=False)

