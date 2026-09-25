from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from .metrics import calculate_metrics

def build_report(results: pd.DataFrame) -> dict:
    by_gw=[]
    if not results.empty:
        for gw, frame in results.groupby("GW", sort=True):
            item={"GW":int(gw)}
            item.update(calculate_metrics(frame))
            by_gw.append(item)
    return {"summary":calculate_metrics(results),"gameweeks":by_gw,"rows":int(len(results))}

def save_report(results, output_dir):
    path=Path(output_dir); path.mkdir(parents=True,exist_ok=True)
    results.to_csv(path/"backtest_player_results.csv",index=False)
    report=build_report(results)
    (path/"backtest_report.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    return report
