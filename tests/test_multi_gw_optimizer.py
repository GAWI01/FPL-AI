import pandas as pd
from optimizer.multi_gw import MultiGWConfig, aggregate_multi_gw_value, optimize_multi_gw

def test_aggregate_multi_gw_sums_weighted_values():
    df=pd.DataFrame({"player_id":[1,1,1],"GW":[2,3,4],"predicted_points":[2.,3.,4.]})
    out=aggregate_multi_gw_value(df, MultiGWConfig(horizon=3, gw_weights=(1.0,0.5,0.25)))
    assert out.loc[out.player_id.eq(1),"optimization_score"].iloc[0] == 4.5

def test_horizon_filters_gameweeks():
    df=pd.DataFrame({"player_id":[1,1,1],"GW":[2,3,5],"predicted_points":[2.,3.,9.]})
    out=aggregate_multi_gw_value(df, MultiGWConfig(horizon=2))
    assert out["optimization_score"].iloc[0] == 5.0

def test_multi_gw_reuses_squad_optimizer():
    rows=[]
    for pos,n in [("GK",2),("DEF",5),("MID",5),("FWD",3)]:
        for i in range(n):
            rows.append({"player_id":len(rows)+1,"name":f"{pos}{i}","position":pos,"team":f"T{len(rows)%6}","price":5.0,"GW":2,"predicted_points":10.0-i})
    df=pd.DataFrame(rows)
    assert len(optimize_multi_gw(df, budget=100))==15
