import streamlit as st
import plotly.express as px
from dashboard_common import (
    load_all_data,
    load_draft_data,
    render_sidebar_filters,
    apply_filters,
    render_data_summary,
    analyze_draft_strategy_effectiveness,
    analyze_draft_value_picks,
    create_draft_scatterplot_with_dynamic_trendline,
    create_draft_position_grid_html,
    POSITION_COLORS,
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

st.header("📈 Draft Analysis")

draft_df = load_draft_data()

if draft_df.empty:
    st.info("🔄 Draft data not available yet.")
    st.write("**To generate draft data:**")
    st.code("""
# 1. Run the Yahoo API draft function once to generate CSV:
get_league_draft_results(weekly_stats_df)

# 2. This creates data/draft_results.csv with columns:
# year, round, pick, overall_pick, team_name, player_name, position, season_points

# 3. Dashboard will automatically load the CSV file
    """)

    st.write("**What you'll see once draft data is added:**")
    st.write("- Draft position vs performance scatterplots")
    st.write("- Draft strategy effectiveness analysis")
    st.write("- Biggest steals and reaches vs ADP")
    st.write("- Team drafting performance comparison")

else:
    draft_overview_tab, strategy_tab, value_tab = st.tabs([
        "📊 Draft Overview",
        "🧠 Strategy Analysis",
        "💎 Value Analysis"
    ])

    with draft_overview_tab:
        st.subheader("🏈 Your League Draft Results")

        required_cols = ['pick', 'season_points', 'position', 'player_name', 'year', 'team_name', 'round']
        missing_cols = [col for col in required_cols if col not in draft_df.columns]

        if missing_cols:
            st.error(f"❌ Missing required columns in draft data: {missing_cols}")
            st.write("**Available columns:**", list(draft_df.columns))
            st.write("**Expected columns:**", required_cols)
            st.stop()

        # Draft position vs performance scatterplot
        try:
            fig_league_scatter = create_draft_scatterplot_with_dynamic_trendline(
                draft_df, selected_positions
            )
            st.plotly_chart(fig_league_scatter, use_container_width=True, key="draft-scatterplot")

        except Exception as e:
            st.error(f"❌ Error creating scatterplot: {e}")
            st.write("**Debug info:**")
            st.write("Draft DF info:")
            st.dataframe(draft_df.head())

        # Draft insights
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            best_value = draft_df.loc[draft_df['season_points'].idxmax()]
            st.metric(
                "🏆 Highest Scorer",
                f"{best_value['player_name']}",
                f"Pick {best_value['pick']} → {best_value['season_points']:.0f} pts"
            )

        with col2:
            late_picks = draft_df[draft_df['pick'] > 60]
            if not late_picks.empty:
                best_late = late_picks.loc[late_picks['season_points'].idxmax()]
                st.metric(
                    "💎 Best Late Pick",
                    f"{best_late['player_name']}",
                    f"Pick {best_late['pick']} → {best_late['season_points']:.0f} pts"
                )

        with col3:
            round1_avg = draft_df[draft_df['round'] == 1]['season_points'].mean()
            st.metric(
                "📊 Round 1 Average",
                f"{round1_avg:.0f} points",
                "Expected from early picks"
            )

        with col4:
            team_totals = draft_df.groupby('team_name')['season_points'].sum()
            best_team = team_totals.idxmax()
            best_team_total = team_totals.max()
            st.metric(
                "🏆 Best Drafting Team",
                best_team,
                f"{best_team_total:.0f} total pts"
            )

        # Draft round analysis table
        st.subheader("📊 Your League Performance by Draft Round")
        league_round_analysis = draft_df.groupby('round').agg({
            'season_points': ['mean', 'std', 'count'],
            'player_name': 'nunique'
        }).round(1)
        league_round_analysis.columns = ['Avg Points', 'Std Dev', 'Total Picks', 'Unique Players']
        st.dataframe(league_round_analysis, use_container_width=True)

        # Position-by-slot grid across all years
        st.subheader("🗺️ Position Drafted by Round & Pick")
        st.write("Each cell is one round × pick slot. Rows inside a cell show the position taken at that slot each year (top to bottom) and how many fantasy points that player scored that season. Click a position below to toggle it in the grid.")

        preferred_order = ['QB', 'RB', 'WR', 'TE', 'DEF', 'K']
        grid_positions_available = sorted(draft_df['position'].dropna().unique())
        ordered_grid_positions = [p for p in preferred_order if p in grid_positions_available] + [
            p for p in grid_positions_available if p not in preferred_order
        ]

        grid_cols = st.columns(len(ordered_grid_positions))
        grid_selected_positions = []
        for i, pos in enumerate(ordered_grid_positions):
            color = POSITION_COLORS.get(pos, '#999999')
            with grid_cols[i]:
                st.markdown(
                    f'<div style="width:16px;height:16px;border-radius:3px;background:{color};margin:0 auto 4px auto;"></div>',
                    unsafe_allow_html=True,
                )
                checked = st.checkbox(pos, value=(pos in selected_positions), key=f"grid_pos_{pos}")
            if checked:
                grid_selected_positions.append(pos)

        st.markdown(
            create_draft_position_grid_html(draft_df, grid_selected_positions),
            unsafe_allow_html=True,
        )

    with strategy_tab:
        st.subheader("🧠 Draft Strategy Effectiveness")

        strategy_performance = analyze_draft_strategy_effectiveness(draft_df)

        if not strategy_performance.empty:
            if 'QB' in strategy_performance.columns:
                fig_qb_strategy = px.scatter(
                    strategy_performance,
                    x='QB',
                    y='season_points',
                    hover_data=['team_name', 'year'],
                    title='Early QB Picks vs Total Team Points',
                    labels={
                        'QB': 'QBs Drafted in First 3 Rounds',
                        'season_points': 'Total Team Points'
                    }
                )
                st.plotly_chart(fig_qb_strategy, use_container_width=True, key="qb-strategy")

            if 'RB' in strategy_performance.columns:
                fig_rb_strategy = px.scatter(
                    strategy_performance,
                    x='RB',
                    y='season_points',
                    hover_data=['team_name', 'year'],
                    title='Early RB Picks vs Total Team Points',
                    labels={
                        'RB': 'RBs Drafted in First 3 Rounds',
                        'season_points': 'Total Team Points'
                    }
                )
                st.plotly_chart(fig_rb_strategy, use_container_width=True, key="rb-strategy")

            st.subheader("📊 Strategy Performance Summary")
            if all(col in strategy_performance.columns for col in ['QB', 'RB', 'WR']):
                strategy_summary = strategy_performance.groupby(['QB', 'RB', 'WR']).agg({
                    'season_points': ['mean', 'count']
                }).round(1)
                strategy_summary.columns = ['Avg Points', 'Times Used']
                st.dataframe(strategy_summary)
            else:
                st.info("Need more draft data for strategy analysis")
        else:
            st.info("Draft strategy analysis requires more data")

    with value_tab:
        st.subheader("💎 Draft Value Analysis")

        if not adp_df.empty:
            steals, reaches = analyze_draft_value_picks(draft_df, adp_df, selected_years)

            col1, col2 = st.columns(2)

            with col1:
                st.write("**🏆 Biggest Steals vs ADP**")
                if not steals.empty:
                    steal_display = steals[['player_name', 'pick', 'AVG Draft Position', 'adp_diff', 'season_points', 'team_name', 'year']]
                    steal_display.columns = ['Player', 'Your Pick', 'ADP', 'Rounds Later', 'Points', 'Team', 'Year']
                    st.dataframe(steal_display)
                else:
                    st.info("No significant steals found")

            with col2:
                st.write("**💸 Biggest Reaches vs ADP**")
                if not reaches.empty:
                    reach_display = reaches[['player_name', 'pick', 'AVG Draft Position', 'adp_diff', 'season_points', 'team_name', 'year']]
                    reach_display.columns = ['Player', 'Your Pick', 'ADP', 'Rounds Early', 'Points', 'Team', 'Year']
                    st.dataframe(reach_display)
                else:
                    st.info("No significant reaches found")

            # ADP accuracy analysis
            st.subheader("🎯 League vs ADP Accuracy")

            league_vs_adp = draft_df.merge(
                adp_df[adp_df['year'].isin(selected_years)][['Player', 'AVG Draft Position', 'year']],
                left_on=['player_name', 'year'],
                right_on=['Player', 'year'],
                how='inner'
            )

            if not league_vs_adp.empty:
                league_vs_adp['adp_diff'] = league_vs_adp['pick'] - league_vs_adp['AVG Draft Position']

                fig_adp_diff = px.histogram(
                    league_vs_adp,
                    x='adp_diff',
                    title='League Draft Position vs ADP Difference',
                    labels={'adp_diff': 'Picks Different from ADP (+ = Later, - = Earlier)'}
                )
                st.plotly_chart(fig_adp_diff, use_container_width=True, key="adp-diff-histogram")

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**🌍 Global ADP vs Performance**")
                    if not adp_df.empty:
                        all_years_performance = filtered_df.groupby(['player_name_full', 'position', 'year']).agg({
                            'player_fantasy_pts': 'sum',
                            'week': 'count'
                        }).reset_index()

                        all_years_performance = all_years_performance[all_years_performance['week'] >= 4]

                        adp_df_filtered = adp_df[adp_df['year'].isin(selected_years)]

                        adp_performance = all_years_performance.merge(
                            adp_df_filtered[['Player', 'AVG Draft Position', 'year']],
                            left_on=['player_name_full', 'year'],
                            right_on=['Player', 'year'],
                            how='inner'
                        )

                        if not adp_performance.empty:
                            fig_adp_scatter = px.scatter(
                                adp_performance,
                                x='AVG Draft Position',
                                y='player_fantasy_pts',
                                color='position',
                                hover_data=['player_name_full', 'year'],
                                title='Global ADP vs Performance',
                                labels={
                                    'AVG Draft Position': 'ADP',
                                    'player_fantasy_pts': 'Season Points'
                                },
                                height=400
                            )
                            st.plotly_chart(fig_adp_scatter, use_container_width=True, key="adp-performance-scatter")

                with col2:
                    st.write("**🏈 Your League vs ADP**")
                    fig_league_vs_adp = px.scatter(
                        league_vs_adp,
                        x='AVG Draft Position',
                        y='pick',
                        color='position',
                        hover_data=['player_name', 'year', 'team_name'],
                        title='Your Picks vs Global ADP',
                        labels={
                            'AVG Draft Position': 'Global ADP',
                            'pick': 'Your League Pick'
                        },
                        height=400
                    )
                    min_val = min(league_vs_adp['AVG Draft Position'].min(), league_vs_adp['pick'].min())
                    max_val = max(league_vs_adp['AVG Draft Position'].max(), league_vs_adp['pick'].max())
                    fig_league_vs_adp.add_shape(
                        type="line",
                        x0=min_val, y0=min_val,
                        x1=max_val, y1=max_val,
                        line=dict(color="gray", dash="dash")
                    )
                    st.plotly_chart(fig_league_vs_adp, use_container_width=True, key="league-vs-adp-scatter")
            else:
                st.warning("⚠️ No matching data between draft and ADP files")
        else:
            st.info("ADP data required for value analysis")
