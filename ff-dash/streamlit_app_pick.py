import streamlit as st
from dashboard_common import configure_page, inject_custom_css

configure_page("Fantasy Football Dashboard")
inject_custom_css()

pages = [
    st.Page("app_pages/home.py", title="Home", icon="🏈", default=True),
    st.Page("app_pages/position_analysis.py", title="Position Analysis", icon="📊"),
    st.Page("app_pages/player_analysis.py", title="Player Analysis", icon="👤"),
    st.Page("app_pages/team_analysis.py", title="Team Analysis", icon="🏆"),
    st.Page("app_pages/draft_analysis.py", title="Draft Analysis", icon="📈"),
    st.Page("app_pages/advanced_metrics.py", title="Advanced Metrics", icon="🎯"),
]

nav = st.navigation(pages)
nav.run()
