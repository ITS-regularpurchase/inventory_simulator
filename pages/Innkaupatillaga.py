import streamlit as st
import pandas as pd
import numpy as np
from authentication import check_password


st.set_page_config(
    page_title="History",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        # 'Get Help': "mailto:sigurduroli@icelandair.is?subject=st.help&body=Mig vantar aðstoð með ...",
        # 'Report a bug': "mailto:sigurduroli@icelandair.is?subject=st.bug&body=Það er villa í ...",
        'About': "### Inventory Simulator \n ## Tengiliður: *sigurduroli@icelandair.is* \n\n---"
    }
)

st.header("Hér er gott að fara í gegnum innkaupatillögu")

if check_password():
    body = "helo"
    pn = st.text_input("Part number")
    
    usg_1 = ord(pn[0]) * np.random.randint(3, 4) if len(pn) else "0"
    usg_3 = ord(pn[0]) * np.random.randint(1, 2) if len(pn) else "0"
    avail = ord(pn[0]) * np.random.randint(2, 3) if len(pn) else "0"
    price = ord(pn[0]) * np.random.randint(8, 30) if len(pn) else "0"
    
    usg1_col, usg3_col, avail_col, price_col = st.columns(4)
    
    with usg1_col:
        st.title(usg_1, anchor=False)
        st.write("Notkun síðasta ár")
        
    with usg3_col:
        st.title(usg_3, anchor=False)
        st.write('Meðalnotkun síðustu 3 ár')
        
    with avail_col:
        st.title(avail, anchor=False)
        st.write('Available')
        
    with price_col:
        st.title(price, anchor=False)
        st.write('Verð í USD')
    
    line_chart = pd.DataFrame(np.random.randn(20, 3), columns=["col1", "col2", "col3"])

    st.line_chart(
        line_chart, x="col1", y=["col2", "col3"]
    )