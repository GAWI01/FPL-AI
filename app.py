import streamlit as st

from data_loader import DataLoaderError, load_players, validate_current_data


st.set_page_config(
    page_title="FPL-AI",
    page_icon="⚽",
    layout="wide",
)


st.title("⚽ FPL-AI")
st.caption("FPL Decision Engine")

st.divider()


# -------------------------------------------------------------------
# DATA
# -------------------------------------------------------------------

try:
    validate_current_data()
    players = load_players()

except DataLoaderError as exc:
    st.error(f"Datafeil: {exc}")
    st.stop()


# -------------------------------------------------------------------
# OVERVIEW
# -------------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Spillere", len(players))

with col2:
    st.metric("Gameweek", "GW3")

with col3:
    st.metric("Free Transfers", "1")

with col4:
    st.metric("Wildcard", "Available")


st.divider()


# -------------------------------------------------------------------
# AI DECISION CENTER
# -------------------------------------------------------------------

st.header("🧠 AI Decision Center")

left, right = st.columns(2)

with left:
    st.subheader("My Team")
    st.info("FPL-laget kobles inn her.")

with right:
    st.subheader("AI Recommendation")
    st.info("Prediction engine kobles inn her.")


st.divider()


# -------------------------------------------------------------------
# PLAYER INTELLIGENCE
# -------------------------------------------------------------------

st.header("📊 Player Intelligence")

st.caption(
    "Dette er foreløpig rå/canonical spillerdata. "
    "Prediction engine kommer senere."
)


display_columns = [
    "name",
    "position",
    "team",
    "price",
    "status",
    "form",
    "points_per_game",
    "total_points",
    "minutes",
    "expected_goals",
    "expected_assists",
]


available_columns = [
    column
    for column in display_columns
    if column in players.columns
]


st.dataframe(
    players[available_columns],
    use_container_width=True,
    hide_index=True,
)


st.divider()

st.caption("FPL-AI — local development")