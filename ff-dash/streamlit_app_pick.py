import streamlit as st
from dashboard_common import (
    configure_page,
    inject_custom_css,
    load_all_data,
    render_sidebar_filters,
    apply_filters,
    render_data_summary,
)

configure_page("Fantasy Football Dashboard")
inject_custom_css()

st.title("🏈 Fantasy Football Analytics Dashboard")

master_df, adp_df = load_all_data()

if master_df.empty:
    st.error("❌ No data found! Make sure your CSV files are in the 'data' folder.")
    st.stop()

selected_years, selected_positions = render_sidebar_filters(master_df)

if not selected_years or not selected_positions:
    st.warning("⚠️ Please select at least one year and position.")
    st.stop()

filtered_df = apply_filters(master_df, selected_years, selected_positions)
render_data_summary(filtered_df)

st.write("Use the sidebar to filter by year and position, then explore an analysis page below. Your filters carry over as you navigate between pages.")

st.page_link("pages/1_📊_Position_Analysis.py", label="Position Analysis", icon="📊")
st.page_link("pages/2_👤_Player_Analysis.py", label="Player Analysis", icon="👤")
st.page_link("pages/3_🏆_Team_Analysis.py", label="Team Analysis", icon="🏆")
st.page_link("pages/4_📈_Draft_Analysis.py", label="Draft Analysis", icon="📈")
st.page_link("pages/5_🎯_Advanced_Metrics.py", label="Advanced Metrics", icon="🎯")
