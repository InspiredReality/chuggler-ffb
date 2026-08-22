import streamlit as st
from dashboard_common import configure_page, inject_custom_css

configure_page("Fantasy Football Dashboard")
inject_custom_css()

if "selected_app" not in st.session_state:
    st.session_state["selected_app"] = None

selected_app = st.session_state["selected_app"]

if selected_app is not None:
    if st.sidebar.button("🔄 Switch App", use_container_width=True):
        st.session_state["selected_app"] = None
        st.rerun()
    st.sidebar.markdown("---")

if selected_app == "chuggler":
    pages = [
        st.Page("app_pages/chuggler/home.py", title="Home", icon="🏈", default=True),
        st.Page("app_pages/chuggler/position_analysis.py", title="Position Analysis", icon="📊"),
        st.Page("app_pages/chuggler/player_analysis.py", title="Player Analysis", icon="👤"),
        st.Page("app_pages/chuggler/team_analysis.py", title="Team Analysis", icon="🏆"),
        st.Page("app_pages/chuggler/draft_analysis.py", title="Draft Analysis", icon="📈"),
        st.Page("app_pages/chuggler/advanced_metrics.py", title="Advanced Metrics", icon="🎯"),
    ]
elif selected_app == "dynasty":
    pages = [
        st.Page("app_pages/dynasty/home.py", title="Home", icon="🏈", default=True),
        st.Page("app_pages/dynasty/position_analysis.py", title="Position Analysis", icon="📊"),
        st.Page("app_pages/dynasty/player_analysis.py", title="Player Analysis", icon="👤"),
        st.Page("app_pages/dynasty/team_analysis.py", title="Team Analysis", icon="🏆"),
        st.Page("app_pages/dynasty/draft_analysis.py", title="Draft Analysis", icon="📈"),
        st.Page("app_pages/dynasty/advanced_metrics.py", title="Advanced Metrics", icon="🎯"),
    ]
else:
    pages = [st.Page("app_pages/landing.py", title="Home", icon="🏈", default=True)]

nav = st.navigation(pages)
nav.run()
