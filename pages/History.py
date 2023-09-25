import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np
from datetime import datetime, timedelta, date
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px
        
df = pd.read_csv('data/History.csv')
df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

columns=["PART_NUMBER","date","move_type","qty","location_no","LOC"]
builder = GridOptionsBuilder.from_dataframe(df[columns])
builder.configure_pagination(enabled=False, paginationPageSize=15)
builder.configure_column("date", type=["customDateTimeFormat"], custom_format_string='yyyy-MM-dd')
builder.configure_selection('single')
go = builder.build()

today=datetime.now() #today=datetime.now().date()
one_year_ago = today - timedelta(days=365)
st.write("Last update on data 28.08.2023 - 14:43")

with st.form("My_form"):
        col1, col2 = st.columns(2)
        with col1:
                start_date = st.date_input("Start Date", one_year_ago)
                start_date=pd.to_datetime(start_date)
        with col2:
                end_date = st.date_input("End Date", today)
                end_date=pd.to_datetime(end_date)
        search_term = st.text_input('Enter Partnumber')
        modify = st.checkbox("KEF")
        submitted= st.form_submit_button("Submit")

filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date) & (df['PART_NUMBER']==search_term)]

if modify:
        Location_value='KEF'
else:
        Location_value = st.selectbox('**Location**', options=['All'] + [column for column in df['LOC'].unique()], index=0, key='location')


if Location_value == 'All':
        RESUL=filtered_df
        RESUL=df[(df['date'] >= start_date) & (df['date'] <= end_date) & (df['PART_NUMBER']==search_term) ]
else:
        RESUL=df[(df['date'] >= start_date) & (df['date'] <= end_date) & (df['PART_NUMBER']==search_term) & ((df['LOC']==Location_value) | (df['LOC'] == "UNK"))]


tab1, tab2, tab3 = st.tabs(["Grid", "Bar",'Stackbar - filtered'])
with tab1:
    grid_return = AgGrid(RESUL[columns].sort_values(by='date'),go,fit_columns_on_grid_load=True) 
    usage=filtered_df["qty"].sum()
    days= end_date-start_date
with tab2:
       st.bar_chart(RESUL.set_index('date')['qty'])
with tab3:
       selected_type = st.multiselect("Select Types to include", RESUL['move_type'].unique())
       filtered_df = RESUL[RESUL['move_type'].isin(selected_type)]

       fig=px.bar(filtered_df,
                  x='date',
                  y='qty',
                  color='move_type',
                  title='Stacked Bar Chart for Selected Move Types',
                  labels={'Value': 'Values'})
       st.plotly_chart(fig)
       
        


#######TEXTI#############
text = f"""
PN: {search_term}\n
Notkun: {usage}\n
Tímabil: {days.days} dagar"""
centered_text = "Usage info"
########################


# Use the st.markdown() function with HTML/CSS to create a box
st.markdown(
    f"""
    <div style="display: flex; justify-content: center;">
        {centered_text}
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown( 
    f"""
    <div style="border: 2px solid #e0e0e0; padding: 10px; border-radius: 5px;">
        {text}
    </div>
    """,
    unsafe_allow_html=True
)
        
        

