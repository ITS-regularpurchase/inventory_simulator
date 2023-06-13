def test():
    print('Hello World')

def query_to_data_frame(table):
    import sqlalchemy
    from sqlalchemy import engine, MetaData, Table, select
    import pandas as pd
    import urllib
    #import pymysql
    params = urllib.parse.quote_plus("DRIVER={ODBC Driver 17 for SQL Server};SERVER=ICEREKCL20AG;DATABASE=ITS_RHINO_PROD_MX;UID=AM_Admin;PWD=Rhino123")
    engine = engine.create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)
    
    connection = engine.connect()
    
    
    stmt = 'select * from ' + table
    
    df_table = connection.execute(stmt).fetchall()

    col_name = connection.execute(stmt).keys()
    df_table = pd.DataFrame(df_table)
    df_table.columns = col_name
    print('siggi')
    return df_table


#Ath tók simulato viewið út af því það vantaði hreyfingar á min max vörur og setti veiewið streamlit_stocking_items_inv_opt_input1 í staðin
#df_v_stocking_items_inv_opt_input1 = query_to_data_frame('ml_cus.v_stocking_items_inv_opt_input1')
#df_v_stocking_items_inv_opt_input1.to_csv(r'stocking_items_inv_opt_input1.csv')
def update_mxi():
    df_v_stocking_items_inv_opt_input1 = query_to_data_frame('streamlit_stocking_items_inv_opt_input1')
    df_v_stocking_items_inv_opt_input1.to_csv(r'stocking_items_inv_opt_input1.csv')

    df_v_stocking_items_inv_opt_input2 = query_to_data_frame('ml_cus.v_stocking_items_inv_opt_input2')
    df_v_stocking_items_inv_opt_input2.to_csv(r'stocking_items_inv_opt_input2.csv')


    df_v_stocking_items_deliv_date_on_order = query_to_data_frame('ml_cus.v_stocking_items_deliv_date_on_order')
    df_v_stocking_items_deliv_date_on_order.to_csv(r'stocking_items_deliv_date_on_order.csv')

    df_v_stocking_items_deliv_date_on_order = query_to_data_frame('streamlit_rio_items_stocking_items')
    df_v_stocking_items_deliv_date_on_order.to_csv(r'streamlit_rio_items_stocking_items.csv')

