import pandas as pd
import stress_test.data.processed_data as prd
import stress_test.config as cfg
from pathlib import Path


processed_data = prd.load_processed_macro_data()
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

def macro_hist():
    frames = []
    for name, df in processed_data.items():
        d = df.copy()
        d["quarter"] = pd.PeriodIndex(d["quarter"], freq=cfg.FREQUENCY)

        value_cols = [c for c in d.columns if c != "quarter"]
        d = d.set_index("quarter")[value_cols]
        d = d.rename(columns={c: f"{c}" for c in value_cols})
        frames.append(d)

    macro_hist = pd.concat(frames, axis=1, join="outer").sort_index().reset_index()
    macro_hist = macro_hist.dropna().reset_index(drop=True)

    macro_hist.to_csv(output_dir / "macro_hist.csv", index=False)

    return macro_hist

if __name__ == "__main__":
    print("")