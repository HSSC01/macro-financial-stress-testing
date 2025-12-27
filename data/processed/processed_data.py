import pandas as pd
from data.raw.raw_data import load_raw_macro_data

raw_data = load_raw_macro_data()

gg_df = raw_data["gdp_growth_df"]
ur_df = raw_data["unemployment_rate_df"]
hpg_df = raw_data["house_price_growth_df"]
pr_df = raw_data["policy_rate_df"]
g10y_df = raw_data["gilt_10y_df"]

if __name__ == "__main__":
    print(gg_df)