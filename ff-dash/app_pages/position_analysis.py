import streamlit as st
import plotly.express as px
from dashboard_common import (
    load_all_data,
    render_sidebar_filters,
    apply_filters,
    render_data_summary,
    calculate_avg_points_per_position,
    calculate_position_volatility,
)

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

st.header("📊 Position Analysis")

col1, col2 = st.columns(2)

with col1:
    avg_by_pos = calculate_avg_points_per_position(filtered_df)
    fig1 = px.bar(avg_by_pos, x='position', y='mean_points',
                 color='year', barmode='group',
                 title='Average Points by Position')
    st.plotly_chart(fig1, use_container_width=True, key="avg_points_pos")

with col2:
    vol_by_pos = calculate_position_volatility(filtered_df)
    fig2 = px.line(vol_by_pos, x='position', y='coeff_of_variation',
                  color='year', markers=True,
                  title='Position Volatility (Coefficient of Variation)')
    st.plotly_chart(fig2, use_container_width=True, key="pos_volatility")

st.subheader("Position Summary")
summary = filtered_df.groupby('position').agg({
    'player_fantasy_pts': ['mean', 'std', 'count'],
    'player_name_full': 'nunique'
}).round(2)
summary.columns = ['Avg Points', 'Std Dev', 'Total Games', 'Unique Players']
st.dataframe(summary, use_container_width=True)
