import streamlit as st
from verdlisti_df import verdlisti
import time
from authentication import check_password

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

    slider = int(st.sidebar.slider('Hversu margir?', 1, 50, 10))
    top_ten = st.sidebar.checkbox(f'{slider} dýrustu hlutir')
    st.sidebar.write('---')
    currency = st.sidebar.radio(options=('Default', 'USD', 'EUR'), label='Gjaldmiðill')
    st.sidebar.write('---')
    vendor_choice = st.sidebar.selectbox('**Veldu birgja**', options=['All'] + [vendor for vendor in verdlisti().df['Vendor'].unique()], index=0, key='vendor')
    
    @st.cache_data(show_spinner="Sæki verðlista...")
    def load_data():
        df = verdlisti()
        return df
    
    success = st.empty()
    
    with success.container():
        pl = load_data()
        if pl is not None:
            st.success('Verðlisti sóttur!')
        time.sleep(5)
            
    success.empty()

    if top_ten:
        # TODO: fix this
        pl = pl.sort_by_price(int(slider))
        st.dataframe(pl)
    
    with st.expander('Verðlisti'):
        if currency == 'Default':
            if vendor_choice != 'All':
                st.write(f'#### Vörur frá *{vendor_choice}*:')
                st.write(pl.show_only(vendor_choice))
            else:
                st.write(pl.df)
                
        else:
            st.write(f"#### *Verð í {currency}:*")
            st.write(pl.change_currency(currency))
        
    with st.expander('Leita PNR'):    
        this_search = st.text_input('Leita PNR', key='search')
            
        duplicate = pl.df[pl.df.duplicated(subset='PNR', keep=False)].sort_values(by=['PNR', 'Price'], ascending=True)
        
        if this_search:
            st.write(duplicate.change_currency(currency)[duplicate['PNR'] == this_search].style.highlight_min(subset='Price', color='lightgreen', axis=0))
        else:
            st.write(duplicate)
        
        
    
    st.write('---')
    st.caption("*Icelandair Technical Services*")
    