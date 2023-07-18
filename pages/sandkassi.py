import streamlit as st

i=10

def telja():
    st.session_state.teljari = st.session_state.teljari+1
    st.session_state.mu = st.session_state.teljari**2 + 1

def reste_session_var():
    st.session_state.teljari = 0
    st.session_state.mu = 0


if 'teljari' not in st.session_state:
    st.session_state.teljari = 0

if 'mu' not in st.session_state:
    st.session_state.mu = 0


st.button('alda', on_click = telja)
st.button('alda kalda', on_click = reste_session_var)
st.write(st.session_state.teljari)
st.write(st.session_state.mu)
