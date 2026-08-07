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

st.write("Use the page navigation in the sidebar above to filter by year and position, then explore an analysis page. Your filters carry over as you navigate between pages.")
