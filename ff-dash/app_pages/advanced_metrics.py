import streamlit as st
import plotly.express as px
from dashboard_common import (
    load_all_data,
    render_sidebar_filters,
    apply_filters,
    render_data_summary,
    analyze_positional_scarcity,
    analyze_elite_vs_depth_strategy,
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

st.header("🎯 Advanced Metrics & Draft Strategy")

# Positional Scarcity Analysis
st.subheader("💎 Positional Scarcity Analysis")
st.write("**Key Question:** Which positions have the biggest drop-off from elite to average players?")

scarcity_df = analyze_positional_scarcity(filtered_df)

if not scarcity_df.empty:
    fig_scarcity = px.bar(
        scarcity_df.sort_values('elite_to_starter_drop', ascending=False),
        x='position',
        y='elite_to_starter_drop',
        title='Points Drop-off: Elite (Top 5%) to Average Starter (Top 25%)',
        labels={
            'elite_to_starter_drop': 'Points Drop-off per Game',
            'position': 'Position'
        },
        color='elite_to_starter_drop',
        color_continuous_scale='Reds'
    )
    fig_scarcity.update_layout(height=400)
    st.plotly_chart(fig_scarcity, use_container_width=True, key="fig_scarcity")

    st.subheader("📊 Positional Depth Analysis")

    display_cols = [
        'position', 'elite_avg', 'top10_avg', 'starter_avg', 'mid_avg',
        'elite_to_starter_drop', 'top10_to_starter_drop', 'elite_count'
    ]

    scarcity_display = scarcity_df[display_cols].sort_values('elite_to_starter_drop', ascending=False)

    scarcity_display.columns = [
        'Position', 'Elite Avg (Top 5%)', 'Top 10% Avg', 'Starter Avg (Top 25%)',
        'Mid-Tier Avg', 'Elite→Starter Drop', 'Top10→Starter Drop', '# Elite Players'
    ]

    st.dataframe(scarcity_display, use_container_width=True)

    st.subheader("🧠 Strategic Insights")

    col1, col2, col3 = st.columns(3)

    with col1:
        most_scarce = scarcity_df.loc[scarcity_df['elite_to_starter_drop'].idxmax()]
        st.metric(
            "🏆 Most Scarce Position",
            most_scarce['position'],
            f"{most_scarce['elite_to_starter_drop']} pt drop-off"
        )

    with col2:
        deepest_pos = scarcity_df.loc[scarcity_df['elite_to_starter_drop'].idxmin()]
        st.metric(
            "📊 Deepest Position",
            deepest_pos['position'],
            f"{deepest_pos['elite_to_starter_drop']} pt drop-off"
        )

    with col3:
        most_elite = scarcity_df.loc[scarcity_df['elite_count'].idxmax()]
        st.metric(
            "🎯 Most Elite Options",
            most_elite['position'],
            f"{most_elite['elite_count']} elite players"
        )

    st.subheader("📈 Draft Strategy Implications")

    scarcity_sorted = scarcity_df.sort_values('elite_to_starter_drop', ascending=False)

    st.write("**Based on positional scarcity analysis:**")

    most_scarce_pos = scarcity_sorted.iloc[0]['position']
    second_scarce_pos = scarcity_sorted.iloc[1]['position'] if len(scarcity_sorted) > 1 else "N/A"
    deepest_pos = scarcity_sorted.iloc[-1]['position']

    st.info(f"""
    🎯 **Priority 1:** Target elite {most_scarce_pos}s early - biggest drop-off from elite to average

    🎯 **Priority 2:** Consider elite {second_scarce_pos}s if available

    🎯 **Wait Strategy:** {deepest_pos} position has good depth - can wait until later rounds

    📊 **The Data Says:** Elite {most_scarce_pos}s provide {scarcity_sorted.iloc[0]['elite_to_starter_drop']:.1f} more points per game than average starters
    """)

# Value Above Replacement Analysis
st.subheader("⚡ Value Above Replacement (VAR)")
var_df = analyze_elite_vs_depth_strategy(filtered_df)

if not var_df.empty:
    fig_var = px.bar(
        var_df.sort_values('elite_var', ascending=False),
        x='position',
        y='elite_var',
        title='Elite Player Value Above Replacement Level',
        labels={
            'elite_var': 'Points Above Replacement per Game',
            'position': 'Position'
        }
    )
    st.plotly_chart(fig_var, use_container_width=True, key="fig_var")

    st.dataframe(var_df, use_container_width=True, key="var-df")

# Weekly trends
st.subheader("📅 Weekly Scoring Trends")
weekly_trends = filtered_df.groupby(['week', 'position'])['player_fantasy_pts'].mean().reset_index()
fig7 = px.line(weekly_trends, x='week', y='player_fantasy_pts',
              color='position', title='Average Points by Week and Position')
st.plotly_chart(fig7, use_container_width=True, key="weekly-trends_fig7")
