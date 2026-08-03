"""Minimal Streamlit test - no external images, no imports beyond streamlit."""

import streamlit as st

st.set_page_config(page_title="Test", layout="wide")
st.title("Hello from WSL2!")
st.write("If you can see this, Streamlit WebSocket is working.")
if st.button("Click me"):
    st.success("Button clicked! Streamlit is fully functional.")
    st.balloons()
