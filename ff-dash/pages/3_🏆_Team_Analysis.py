import streamlit as st
import plotly.express as px
from dashboard_common import (
    configure_page,
    inject_custom_css,
    load_all_data,
    render_sidebar_filters,
    apply_filters,
    render_data_summary,
    create_team_analysis,
)

configure_page("Team Analysis", page_icon="🏆")
inject_custom_css()

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

st.header("🏆 Team Analysis")

if 'team_name' in filtered_df.columns:
    team_stats = create_team_analysis(filtered_df)

    col1, col2 = st.columns(2)

    with col1:
        fig5 = px.histogram(team_stats, x='avg_points_per_week',
                           title='Team Performance Distribution')
        st.plotly_chart(fig5, use_container_width=True, key="team_perf_dist")

    with col2:
        fig6 = px.bar(team_stats.nlargest(10, 'avg_points_per_week'),
                     x='team_name', y='avg_points_per_week',
                     color='year', title='Top 10 Teams')
        st.plotly_chart(fig6, use_container_width=True, key="top_10_teams")

    st.dataframe(team_stats.sort_values('avg_points_per_week', ascending=False),
                use_container_width=True)
else:
    st.info("Team data not available in current dataset")
