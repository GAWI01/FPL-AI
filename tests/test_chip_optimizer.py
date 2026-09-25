import pandas as pd
from optimizer.chip_optimizer import evaluate_chip_scenarios

def squad():
    rows=[]
    for pos,n in [("GK",2),("DEF",5),("MID",5),("FWD",3)]:
        for i in range(n):
            rows.append({"player_id":len(rows)+1,"name":f"{pos}{i}","position":pos,"team":f"T{len(rows)%6}","price":5.0,"predicted_points":4.0})
    return pd.DataFrame(rows)

def pool():
    rows=squad().to_dict("records")
    for i in range(16,21):
        rows.append({"player_id":i,"name":f"Elite{i}","position":"MID","team":f"Z{i}","price":5.0,"predicted_points":10.0})
    return pd.DataFrame(rows)

def test_blank_gameweek_prefers_free_hit_when_available():
    out=evaluate_chip_scenarios(squad(),pool(),available_chips={"FREE_HIT":True,"WILDCARD":False,"BENCH_BOOST":False,"TRIPLE_CAPTAIN":False},blank_gameweek=True)
    assert out["recommended_chip"]=="FREE_HIT"

def test_double_gameweek_exposes_bench_and_triple_captain_scenarios():
    out=evaluate_chip_scenarios(squad(),pool(),available_chips={"FREE_HIT":False,"WILDCARD":False,"BENCH_BOOST":True,"TRIPLE_CAPTAIN":True},double_gameweek=True)
    assert {x["chip"] for x in out["scenarios"]}=={"BENCH_BOOST","TRIPLE_CAPTAIN"}

def test_no_available_chip_returns_none():
    out=evaluate_chip_scenarios(squad(),pool(),available_chips={c:False for c in ["WILDCARD","FREE_HIT","BENCH_BOOST","TRIPLE_CAPTAIN"]})
    assert out["recommended_chip"] is None
