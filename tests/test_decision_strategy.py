from decision_strategy import choose_transfer_action, confidence_score, chip_advisor
def test_hit_needs_margin():
    assert choose_transfer_action(2,6,2,hit_cost=4)=="HOLD"
def test_high_confidence():
    assert confidence_score(decision_margin=1,minutes_certainty=1,fixture_certainty=1,signal_agreement=1)["label"]=="HIGH"
def test_blank_gameweek_chip():
    assert chip_advisor(free_transfers=1,net_gain=0,squad_health_status="HEALTHY",blank_gameweek=True)["recommended_chip"]=="FREE_HIT"
