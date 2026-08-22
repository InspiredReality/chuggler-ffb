import streamlit as st

st.markdown('<h1 class="main-header">🏈 Fantasy Football Analytics Dashboard</h1>', unsafe_allow_html=True)
st.write("Choose an app to get started.")

st.markdown("""
<style>
.st-key-app-picker button {
    height: 5rem;
    font-size: 1.6rem;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

_, center, _ = st.columns([1, 2, 1])
with center:
    with st.container(key="app-picker"):
        if st.button("🏈 Chuggler", use_container_width=True, type="primary"):
            st.session_state["selected_app"] = "chuggler"
            st.rerun()
        if st.button("👑 Dynasty", use_container_width=True):
            st.session_state["selected_app"] = "dynasty"
            st.rerun()
