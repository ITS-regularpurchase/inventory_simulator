import time
import streamlit as st
import pandas as pd
import numpy as np
from verdlisti_df import verdlisti
from authentication import check_password
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode

st.set_page_config(
    page_title="Pricelist",
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



if check_password():
    st.title('Verðlisti - Icelandair :airplane:')
    current_time = time.strftime("%H:%M:%S")
    st.write(current_time)


    currency = st.sidebar.radio(options=('Default', 'USD', 'EUR'), label='Gjaldmiðill')
    st.sidebar.write('---')
    vendor_choice = st.sidebar.selectbox('**Veldu birgja**', options=['Allir'] + [vendor for vendor in verdlisti().df['Vendor'].unique()], index=0, key='vendor')
    
    @st.cache_data(show_spinner="Sæki verðlista...")
    def load_data():
        df = verdlisti()
        return df
    
    #Success message
    success = st.empty()

    with success.container():
        pl = load_data()
        if pl is not None:
            st.success('Verðlisti sóttur!')
        time.sleep(5)

    success.empty()

    
    with st.expander('Verðlisti'):
        if currency == 'Default':
            if vendor_choice != 'Allir':
                st.write(f'#### Vörur frá *{vendor_choice}*:')
                st.write(pl.show_only(vendor_choice))
            else:
                st.dataframe(pl.df, use_container_width=True)
        
        else:
            st.write(f"#### *Verð í {currency}:*")
            st.dataframe(pl.change_currency(currency), use_container_width=True)

    with st.expander('Leita PNR'):    
        this_search = st.text_input('Leita PNR', key='search')
            
        duplicate = pl.df[pl.df.duplicated(subset='PNR', keep=False)].sort_values(by=['PNR', 'Price'], ascending=True)
        
        if this_search:
            st.write(duplicate.change_currency(currency)[duplicate['PNR'] == this_search].style.highlight_min(subset='Price', color='lightgreen', axis=0))
        else:
            st.write(duplicate)
    
    #Configure AgGrid
    cols = list(pd.read_csv('data/verdlisti.csv', sep=';', nrows=1))
    builder = GridOptionsBuilder.from_dataframe(pd.read_csv('data/verdlisti.csv', sep=';', usecols=[i for i in cols if i != 'SPQ']))
    pl_df = pd.read_csv('data/verdlisti.csv', sep=';', usecols=[i for i in cols if i != 'SPQ'])
    pl_go = builder.build()
    
    
            
    with st.expander('AgGrid PN Search'):
        search = st.text_input('Leita PNR', key='ag_search')
        display_values = np.where((pl_df['PNR'].str.contains(search, case=False)) & (pl_df['Vendor'].str.contains(vendor_choice, case=False) if vendor_choice != 'Allir' else True))
        pl_display = AgGrid(pl_df.loc[display_values], gridOptions=pl_go, height=500, columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW)
        
        
    
    st.write('---')
    st.caption("*Icelandair Technical Services*")
    