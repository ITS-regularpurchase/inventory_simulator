# python
import sqlalchemy
import get_data_from_its as its
import pandas as pd
import random
import monte_carlo_forecast as mcf
import numpy as np
import inventory_simulator as invsim
import datetime as dt
import pymysql
#-----------------------------------------------------------------------------------------------------
# Hér náum við í input gögn frá ITS fyrir simulator
df_his = its.query_to_data_frame('ml_cus.v_stocking_items_inv_opt_input1') #########
df_his = df_his.rename(columns={'consumption_date': 'date', 'item_number': 'pn', 'qty': 'qty'})

rio_items = its.query_to_data_frame('ml_cus.v_stocking_items_inv_opt_input2')
rio_items.actual_stock = rio_items.actual_stock.astype(int)
rio_items_ideal_stock = rio_items.ideal_stock.astype(int)

deliv_date_on_order = its.query_to_data_frame('ml_cus.v_stocking_items_deliv_date_on_order')



del_time = rio_items[['pn', 'del_time']]
buy_freq = rio_items[['pn', 'buy_freq']]

rio_items = rio_items[rio_items['del_time'] > 0]
del_time = del_time[del_time['del_time'] > 0]
rio_items = rio_items[rio_items['buy_freq'].notnull()]

#Tryggjum að jafn mörg pn séu í del_time og historical_data
df_his = pd.merge(df_his,del_time,how='inner',left_on=['pn'],right_on=['pn'])
df_his = df_his.iloc[:,[0,1,2]]

#-----------------------------------------------------------------------------------------------------
# Hér undirbúum við gögn fyrir simulator
#Hér eru gögn gerð tilbúinn fyrir spá
historical_data = mcf.his_ready_forecast(df_his)
print("Buið að keyra ready")
#Hér spáum við fyrir gögnum
forecast_data = mcf.monte_carlo_forecast(historical_data, 726, 0.4)
print("forecast_data")
#Hér setjum við rétta innkaupadagsetningu inn
order_days = mcf.order_days(726, rio_items.iloc[:,0], rio_items.iloc[:,6])
print("búið að setja rétt innkaupdags inn")
#Hér hermum við lead time með x% öryggi
lead_forecast = mcf.lead_and_buy_caluculation(historical_data, 300, 0.97, del_time, 0.4)

lead_forecast
print("Buið að keyra lead time")
#Hér hermum við buy freq með x% öryggi
buy_forecast = mcf.lead_and_buy_caluculation(historical_data, 300, 0.97, buy_freq, 0.4)
print("Buið að keyra buy freq")

#Forecast tafla gerð tilbúinn fyrir gagnagrunn
forecast_data_table= pd.melt(forecast_data.reset_index(), id_vars='index')
forecast_data_table.rename(columns={'index': 'period', 'variable': 'item_number', 'value':'qty'}, inplace=True)


#----------------------------------------------------------------------------------------------------

#Skrifum allar töflur í sqlite gagnagrunn
#Byrjum á að útbúa grunninn
# Import create_engine
from sqlalchemy import create_engine, Table, select

# Create an engine that connects to the census.sqlite file: engine
sqlite_engine = create_engine('sqlite:///quick_analysis.db')

sqlite_con = sqlite_engine.connect()



#gögnum skilað í sql gagnagrunn til að útbúa sql fyrir input fyrir simulatorinn
df_his.to_sql(name='historical_data', con=sqlite_con, if_exists = 'replace', index=False)

lead_forecast.forecast = lead_forecast.forecast.astype(int)
lead_forecast.nu_of_periods = lead_forecast.nu_of_periods.astype(int)
lead_forecast.to_sql(name='lead_forecast', con=sqlite_con, if_exists = 'replace', index=False)

buy_forecast.forecast = buy_forecast.forecast.astype(int)
buy_forecast.nu_of_periods = buy_forecast.nu_of_periods.astype(int)
buy_forecast.to_sql(name='buy_forecast', con=sqlite_con, if_exists = 'replace', index=False)
forecast_data_table.to_sql(name='forecast_data', con=sqlite_con, if_exists = 'replace', index=False)
rio_items.to_sql(name='rio_items', con=sqlite_con, if_exists = 'replace', index=False)
order_days.to_sql(name='order_days', con=sqlite_con, if_exists = 'replace', index=False)
deliv_date_on_order.to_sql(name='deliv_date_on_order', con=sqlite_con, if_exists = 'replace', index=False)


#--------------------------------------------------------------------------------------------------------
## Hér hefst loka undirbúningur fyrir að keyra simulator
#1.. náum í gögn úr gagnagrunni
print('Keyrsla úr grunni hefst')
connection2 = sqlite_engine.connect() 
stmt = 'SELECT * FROM v_inv_sim_input'
result_proxy = connection2.execute(stmt)
results = result_proxy.fetchall()

print('Búið að ná í gögn úr grunni')


inv_sim_input = pd.DataFrame(results) 


#2.. renamum dálka to sameinum extra params 2 og extra params 2 í 1 dálk

inv_sim_input["extra_params"] = inv_sim_input[5] + inv_sim_input[6]
inv_sim_input = inv_sim_input.drop(inv_sim_input.columns[[5,6]], axis=1) 
inv_sim_input.rename(columns={0: 'item_id', 1: 'day', 2:'forecast', 3:'actual_sale', 4: 'order_day', 7:'delivery'}, inplace=True)

#3.. Keyrum simulatorinn
print('gögn sett í dataframe og keyrsla á simulator hefst')
dataframe_result = invsim.run_inventory_simulator(inv_sim_input)

print('simulator keyrslu lokið')


#4..keyrum niðurstöður í gagnagrunn
dataframe_result.to_sql(name='inv_sim_result', con=sqlite_con, if_exists = 'replace', index=False)


