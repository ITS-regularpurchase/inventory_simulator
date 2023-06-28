import streamlit as st
from authentication import check_password


logged_in = False

while not logged_in:
    logged_in = check_password()

if logged_in:
    st.title("Fyrir Sigga :airplane:")