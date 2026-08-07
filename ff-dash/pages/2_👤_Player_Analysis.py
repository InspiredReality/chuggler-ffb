import streamlit as st
import plotly.express as px
from dashboard_common import (
    configure_page,
    inject_custom_css,
    load_all_data,
    render_sidebar_filters,
    apply_filters,
    render_data_summary,
    create_player_rank_analysis,
    calculate_avg_points_per_player,
    create_player_tiers_by_position,
)

configure_page("Player Analysis", page_icon="👤")
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

st.header("👤 Player Analysis")

ranked_players = create_player_rank_analysis(filtered_df)

st.subheader("🎯 Player Performance by Rank (Multi-Year View)")
st.write("Each dot represents one player's season. Players who played multiple years have multiple dots.")

if not ranked_players.empty:
    fig_scatter = px.scatter(
        ranked_players,
        x='overall_rank',
        y='player_fantasy_pts',
        color='position',
        hover_data=['player_name_full', 'year', 'week'],
        title='Fantasy Points vs Overall Rank by Position',
        labels={
            'overall_rank': 'Overall Rank (1 = Best)',
            'player_fantasy_pts': 'Total Fantasy Points for Season',
            'position': 'Position'
        },
        height=500
    )

    fig_scatter.update_layout(
        xaxis_title="Overall Rank (1 = Highest Scoring Player)",
        yaxis_title="Total Fantasy Points for Season",
        showlegend=True
    )

    fig_scatter.update_xaxes(autorange="reversed")

    st.plotly_chart(fig_scatter, use_container_width=True, key="player-rank-scatter")

    col1, col2, col3 = st.columns(3)

    with col1:
        top_scorer = ranked_players.loc[ranked_players['player_fantasy_pts'].idxmax()]
        st.metric(
            "🏆 Highest Single Season",
            f"{top_scorer['player_name_full']}",
            f"{top_scorer['player_fantasy_pts']:.1f} pts ({top_scorer['year']})"
        )

    with col2:
        multi_year_players = ranked_players['player_name_full'].value_counts()
        most_consistent = multi_year_players.max()
        st.metric("📅 Max Years Played", most_consistent, f"by {multi_year_players.idxmax()}")

    with col3:
        avg_top10 = ranked_players[ranked_players['overall_rank'] <= 10]['player_fantasy_pts'].mean()
        st.metric("🎯 Top 10 Avg Points", f"{avg_top10:.1f}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏅 Top 20 Players by Average Points")
    player_avg = calculate_avg_points_per_player(filtered_df)
    top_20 = player_avg.head(20)

    fig3 = px.scatter(top_20, x='games_played', y='avg_points_per_week',
                     color='position', size='avg_points_per_week',
                     hover_data=['player_name_full'],
                     title='Top Players: Avg Points vs Games Played')
    st.plotly_chart(fig3, use_container_width=True, key="top-players-scatter")

    st.dataframe(top_20[['player_name_full', 'position', 'avg_points_per_week', 'games_played']],
                use_container_width=True)

with col2:
    st.subheader("🏆 Player Tiers (Natural Breakpoints)")
    st.write("Tier 1 = Elite, Tier 4 = Replacement Level")

    if len(filtered_df) > 50:  # Only if enough data
        tiers = create_player_tiers_by_position(filtered_df)
        if not tiers.empty and 'tier' in tiers.columns:

            tier_counts = tiers.groupby(['position', 'tier']).size().reset_index(name='count')
            fig4 = px.bar(tier_counts, x='position', y='count',
                         color='tier',
                         title='Player Tier Distribution by Position',
                         color_discrete_map={
                             'Tier 1': '#1f77b4',  # Blue
                             'Tier 2': '#ff7f0e',  # Orange
                             'Tier 3': '#2ca02c',  # Green
                             'Tier 4': '#d62728'   # Red
                         })
            st.plotly_chart(fig4, use_container_width=True, key="tier-distribution")

            tier_stats = tiers.groupby(['position', 'tier']).agg({
                'player_fantasy_pts': ['mean', 'count']
            }).round(1)
            tier_stats.columns = ['Avg Points', 'Player Count']
            st.dataframe(tier_stats, use_container_width=True)
        else:
            st.info("Insufficient data for tier analysis")
    else:
        st.info("Need more data for tier analysis")
