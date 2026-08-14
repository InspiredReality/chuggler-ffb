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
    load_adp_for_year,
    adp_file_status,
    build_2026_draft_plan,
    build_league_draft_board,
    render_draft_plan_html,
    calculate_draft_vorp,
    compute_position_value_by_round,
    vorp_cell_style,
    POSITION_COLORS,
)

master_df, adp_df = load_all_data()
draft_df = load_draft_data()

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
    draft_overview_tab, strategy_tab, value_tab, plan_tab = st.tabs([
        "📊 Draft Overview",
        "🧠 Strategy Analysis",
        "💎 Value Analysis",
        "🔮 2026"
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
                draft_df, selected_positions, selected_years
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

            st.write("**🏆 Biggest Steals vs ADP**")
            if not steals.empty:
                steal_display = steals[['player_name', 'pick', 'AVG Draft Position', 'adp_diff', 'season_points', 'team_name', 'year']]
                steal_display.columns = ['Player', 'Your Pick', 'ADP', 'Rounds Later', 'Points', 'Team', 'Year']
                st.dataframe(steal_display)
            else:
                st.info("No significant steals found")

            st.write("**💸 Biggest Reaches vs ADP**")
            if not reaches.empty:
                reach_display = reaches[['player_name', 'pick', 'AVG Draft Position', 'adp_diff', 'season_points', 'team_name', 'year']]
                reach_display.columns = ['Player', 'Your Pick', 'ADP', 'Rounds Early', 'Points', 'Team', 'Year']
                st.dataframe(reach_display)
            else:
                st.info("No significant reaches found")

            # ADP accuracy analysis
            st.subheader("🎯 League vs ADP Accuracy")

            league_vs_adp = draft_df[draft_df['position'].isin(selected_positions)].merge(
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

    with plan_tab:
        st.subheader("🔮 2026 Draft Plan")

        n_teams = int(draft_df.groupby('year')['team_name'].nunique().max())
        qbs_per_team = draft_df[draft_df['position'] == 'QB'].groupby(
            ['year', 'team_name']).size().mean()

        st.write(
            f"Round-by-round targets for your pick slot, built from this league's own draft "
            f"history. Each round shows the position that has actually worked at that pick and "
            f"how confident that read is; the named players come from the 2026 ADP board."
        )

        if qbs_per_team >= 2:
            st.info(
                f"⚡ **This is a superflex/2QB league** — {qbs_per_team:.1f} QBs drafted per team "
                f"per year. QB is the premium position here, and the plan below weights it "
                f"accordingly."
            )

        col_a, col_b = st.columns(2)
        with col_a:
            slot = st.number_input(
                "Your draft slot", min_value=1, max_value=n_teams, value=min(2, n_teams), step=1,
                help="Where you pick in round 1. Snake order is handled automatically.",
            )
        with col_b:
            n_rounds = st.number_input(
                "Rounds", min_value=1, max_value=30,
                value=int(draft_df['round'].max()), step=1,
            )

        adp_2026 = load_adp_for_year(2026)
        has_adp = not adp_2026.empty

        if has_adp:
            st.caption(f"ADP board: {len(adp_2026)} players loaded from `data/ADP_2026.csv`.")
        else:
            status = adp_file_status(2026)
            if status['state'] == 'ok':
                st.error(
                    f"📋 **Found `{status['path']}` but couldn't read it as an ADP board.** "
                    f"Columns present: `{', '.join(status['columns'])}`. Needs a player-name "
                    f"column (`Player`), a position column (`Pos`), and an ADP column "
                    f"(`AVG Draft Position`). Position calls below still work without it."
                )
            elif status['state'] == 'unreadable':
                st.error(
                    f"📋 **`{status['path']}` couldn't be parsed as CSV:** {status.get('error', '')}"
                )
            else:
                st.warning(
                    "📋 **No 2026 ADP board yet.** The position calls below are ready — they "
                    "come from your league's draft history and don't need ADP. Add "
                    "`ff-dash/data/ADP_2026.csv` (columns: `Player`, `Pos`, `AVG Draft "
                    "Position` — same format as the existing ADP files) and this tab will name "
                    "real players at every pick, rookies included."
                )

        plan = build_2026_draft_plan(draft_df, adp_2026, int(slot), n_teams, int(n_rounds))

        your_picks = ", ".join(str(row['overall']) for row in plan)
        st.caption(f"Your picks from slot {int(slot)} in a {n_teams}-team snake: {your_picks}")

        if has_adp:
            st.markdown("---")
            st.subheader("📋 The board, in your league's draft order")
            st.write(
                "Every player, re-ordered by when they actually go **here** rather than by public "
                "ADP. Nobody can predict who'll be on the board at a given pick, so use this to "
                "take the best player available: sort or filter it, find the highest player still "
                "undrafted, and check the round where he's realistically reachable. The "
                "round-by-round plan below is built from exactly this table."
            )

            board_tbl = build_league_draft_board(
                draft_df, adp_2026, int(slot), n_teams, int(n_rounds)
            )

            board_positions = sorted({p[:3].rstrip('0123456789') for p in board_tbl['Pos']})
            pick_filter = st.multiselect(
                "Filter by position", board_positions, default=board_positions,
                key="board_pos_filter",
            )
            shown = board_tbl[
                board_tbl['Pos'].str.replace(r'\d+$', '', regex=True).isin(pick_filter)
            ]
            st.dataframe(
                shown,
                use_container_width=True,
                hide_index=True,
                height=420,
                column_config={
                    'Exp. pick here': st.column_config.NumberColumn(
                        'Exp. pick', help="Where this player typically goes in your league"),
                    'Public ADP': st.column_config.NumberColumn(format="%.1f"),
                    'Wait until': st.column_config.TextColumn(
                        'Wait until Rd',
                        help="Last round of yours where he's still 50%+ likely on the board. "
                             "'take early' means he's usually gone before your first pick."),
                    'Chance there': st.column_config.NumberColumn(
                        '% there', format="%d%%",
                        help="Chance he lasts to that round"),
                },
            )
            st.caption(
                f"{len(board_tbl)} players. “Exp. pick” is calibrated from this league's own "
                "drafts by positional rank on the board — your league's QB1 has gone at pick "
                "2, 1, 2 and 2 in the last four drafts."
            )
            st.markdown("---")

        st.markdown(render_draft_plan_html(plan, has_adp), unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📐 Position value by round")
        st.write(
            "Every cell is measured against the same replacement-level player at that position, "
            "so it answers *what tier of player does this round buy* — not just how a pick "
            "compared to others taken in the same round. A round-10 QB and a round-1 QB are "
            "scored against the same replacement QB."
        )

        vorp_df = calculate_draft_vorp(draft_df, n_teams)
        vorp_tbl, finish_tbl = compute_position_value_by_round(vorp_df)

        st.caption("**Average points above replacement** (green = worth the pick, red = below a freely-available player)")
        st.dataframe(
            vorp_tbl.style.format("{:.0f}", na_rep="—").map(vorp_cell_style),
            use_container_width=True,
        )

        st.caption("**Typical finish within the position** (median — e.g. `8` under QB means that round's QBs usually end up as QB8 that season)")
        st.dataframe(finish_tbl.style.format("{:.0f}", na_rep="—"), use_container_width=True)

        with st.expander("How these numbers are calculated"):
            st.markdown(
                "**Value over replacement (VORP)** is a player's season points minus the "
                "replacement-level score at his position that year — replacement being the last "
                "player who'd realistically be in a starting lineup. In a "
                f"{n_teams}-team superflex that's roughly QB{int(2.0 * n_teams)}, "
                f"RB{int(2.5 * n_teams)}, WR{int(3.5 * n_teams)}, TE{n_teams}, K{n_teams}, "
                f"DEF{n_teams}. Everything below that is free off waivers, so points above it "
                "are what the pick was actually worth.\n\n"
                "This replaced an earlier hit-rate measure that asked whether a pick beat its "
                "own position's average. That bar was cleared by **84% of all round-1 picks** "
                "regardless of position, so it carried almost no information early in the draft. "
                "VORP has no such floor — it asks the same question in round 1 and round 16.\n\n"
                "**Typical finish** is the median positional rank players taken in that round "
                "actually achieved. It's the honest answer to *\"will a round-10 QB outscore QBs "
                "taken in other rounds\"*: read down the QB column and compare.\n\n"
                "Cells with fewer than 3 historical picks are left blank rather than shown as a "
                "one-sample certainty, and in the round-by-round plan above, a position's VORP "
                "is pulled toward that pick's overall average in proportion to sample size "
                "(`n / (n+4)`) so a lucky 3-pick run can't outrank a position with a dozen "
                "observations behind it. Both the shrunk and raw figures are shown.\n\n"
                "⚠️ **K and DEF are overstated here.** Replacement is computed from drafted "
                "players only, and since about one kicker per team gets drafted, the "
                "replacement kicker ends up being the *worst drafted* kicker rather than the "
                "freely-available waiver kicker who scores about the same. Treat K/DEF VORP as "
                "an upper bound — the real edge from picking a kicker early is close to zero.\n\n"
                "Suggestions per round: 1 for rounds 1–3, 2 for rounds 4–7, 3 from round 8 on."
            )
