import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np
from datetime import datetime, timedelta, date
from st_aggrid import AgGrid, GridOptionsBuilder
from streamlit_elements import elements, mui, html
        
df = pd.read_csv('data/history.csv')
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


grid_return = AgGrid(RESUL[columns].sort_values(by='date'),go,fit_columns_on_grid_load=True) 
usage=filtered_df["qty"].sum()
days= end_date-start_date

with elements("Usage info"):
        col1, col2 = st.columns(2)
            with col1:
                    st.text( "PN: "+ search_term)
                    st.text(f"Notkun: {usage}")
                    st.text(f"Tímabil: {days.days} dagar")
        

with st.expander("Usage info"):
            col1, col2 = st.columns(2)
            with col1:
                    st.text( "PN: "+ search_term)
                    st.text(f"Notkun: {usage}")
                    st.text(f"Tímabil: {days.days} dagar")

