import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np
import pyodbc
from datetime import datetime, timedelta, date
from st_aggrid import AgGrid, GridOptionsBuilder
############################################################################################################################################
## dataframe to csv

def server_to_csv():
    conn=pyodbc.connect(Driver='{ODBC Driver 17 for SQL Server}',host='ICEREKCL20AG',user='AM_Admin', password='Rhino123', database='MXI_STG')  #ITS_RHINO_PROD_MX'
    cursor=conn.cursor()
    stmt = "SELECT * FROM mxi_cus.v_rio_cus_histories"
    cursor.execute(stmt)

    result=cursor.execute(stmt).fetchall()

    col_name = [column[0] for column in cursor.description]
    rows= cursor.execute(stmt).fetchall()

    list_of_lists = [list(row) for row in rows]

    df = pd.DataFrame(list_of_lists, columns=[column[0] for column in cursor.description])
    df["LOC"] = df['location_no'].str.upper().str[:3]
    columns=["PART_NUMBER","date","move_type","qty","location_no","LOC"]

    csv_path='History.csv'
    df.to_csv(csv_path,index=False)
    print(f"Dataframe has been saved to {csv_path}")
    return df.to_csv(csv_path,index=False)