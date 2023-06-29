import streamlit as st
from authentication import check_password

if check_password():
    st.title("This is for rotable parts :rotating_light:")