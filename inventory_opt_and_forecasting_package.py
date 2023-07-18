import pandas as pd
import random
import numpy as np
from numpy import random
import get_and_post_data as read_data
from datetime import datetime
import simulator_class as sim
import json
import streamlit as st




class forecasts:
    def __init__(self, timarod, periods, number_of_trials, serv_lev):
        self.histogram = self.monte_forecast(timarod, periods, number_of_trials)
        self.serv_level_value = self.serv_lev_value(self.histogram, serv_lev)
        self.df_single_forecast = self.single_forecast(timarod, periods)


    def single_forecast(self, timarod, periods):
        np_timarod = timarod.iloc[:, 0].to_numpy()
        time_series = random.choice(np_timarod, size=(periods))

        return time_series

    def monte_forecast(self, timarod, periods, number_of_trials):
        np_timarod = timarod.iloc[:, 0].to_numpy()
        hist = random.choice(np_timarod, size=(periods, number_of_trials)).sum(axis=0)

        return hist

    def serv_lev_value(self, histogram, serv_lev):
        sorted_histogram = np.sort(histogram)
        line_num = int(serv_lev * len(sorted_histogram))
        serv_lev_val = sorted_histogram[line_num]

        return serv_lev_val

    def histogram_with_cum(self, monte_forecast, bins):
        # create histogram
        hist, bins = np.histogram(monte_forecast, bins=bins, density=False)

        # create cumulative histogram
        cum_hist = np.cumsum(hist) / hist.sum()

        # create Pandas DataFrame
        df = pd.DataFrame({'bin_edges': bins[:-1], 'frequency': hist, 'cumulative_frequency': cum_hist})

        return df

class get_raw_data():
    def __init__(self):
        self.rio_histories = self.get_rio_histories()
        self.rio_items = self.get_rio_items()
        self.rio_item_details = self.get_rio_item_details()
        self.rio_on_order = self.get_rio_on_order()


    def get_rio_histories(self):
        rio_histories = read_data.data_import('data/stocking_items_inv_opt_input1').data_frame
        sim_input_his = rio_histories[['item_number', 'consumption_date', 'qty']]
        sim_input_his = sim_input_his.rename(
            columns={'consumption_date': 'day', 'qty': 'actual_sale', 'item_number': 'item_id'})
        sim_input_his['day'] = pd.to_datetime(sim_input_his['day'])

        #make sure that there are no duplicates in item_id, day
        sim_input_his = sim_input_his.groupby(['item_id', 'day']).agg({"actual_sale":"sum"}).reset_index()

        return sim_input_his

    def get_rio_items(self):
        rio_items = read_data.data_import('data/stocking_items_inv_opt_input2').data_frame
        return rio_items

    def get_rio_item_details(self):
        rio_item_details = read_data.data_import('data/streamlit_rio_items_stocking_items').data_frame
        return rio_item_details

    def get_rio_on_order(self):
        rio_on_order = read_data.data_import('data/stocking_items_deliv_date_on_order').data_frame
        rio_on_order['est_deliv_date'] = rio_on_order['est_deliv_date'].str[0:10]
        return rio_on_order

    def create_rio_his_test_data(self, pn):
        sim_input_his = self.rio_histories[self.rio_histories.item_id.isin([pn])]
        sim_input_his = sim_input_his.reset_index()

        sim_input_his = sim_input_his[['item_id', 'actual_sale', 'day']]
        sim_input_his = self.add_missing_dates_to_sim_input_his(sim_input_his)

        return sim_input_his
        #sim_input_his[['item_id', 'actual_sale', 'day']]


    def create_rio_items_test_data(self, pn):

        rio_items = self.rio_items[self.rio_items.pn.isin([pn])]
        return rio_items

    def create_rio_item_details_test_data(self, pn):
        rio_item_details = self.rio_item_details[self.rio_item_details.item_number.isin([pn])]
        return rio_item_details

    def create_on_order_test_data(self, pn):

        rio_on_order = self.rio_on_order[self.rio_on_order.pn.isin([pn])]
        return rio_on_order

    def add_missing_dates_to_sim_input_his(self, sim_input_his):
        all_pn = sim_input_his['item_id'].unique()
        i = 0

        min_date = sim_input_his['day'].min()
        #max_date = sim_input_his['day'].max()
        max_date = '2023-07-12'

        idx = pd.date_range(min_date, max_date)

        new_sim_input_his = sim_input_his.iloc[:0, :].copy()
        for column in all_pn:
            time_series_for_pn = sim_input_his[sim_input_his['item_id'] == column]
            time_series_for_pn = time_series_for_pn.set_index('day')
            time_series_for_pn = time_series_for_pn.reindex(idx)

            time_series_for_pn['item_id'] = time_series_for_pn['item_id'].fillna(column)
            time_series_for_pn['actual_sale'] = time_series_for_pn['actual_sale'].fillna(0)

            frames = [new_sim_input_his, time_series_for_pn]

            new_sim_input_his = pd.concat(frames)

        new_sim_input_his['day'] = new_sim_input_his.index

        return new_sim_input_his

class inventory_simulator_with_input_prep(forecasts, sim.inventory_simulator):
    def __init__(self, sim_input_his, sim_rio_items, sim_rio_on_order, periods, number_of_trials, serv_level):
        #upphafsgildi úr montercarlo spá fyrir buy freq og lead time
        self.histogram_lead = self.monte_forecast(sim_input_his[['actual_sale', 'day']], sim_rio_items.loc[:, 'del_time'].values[0], number_of_trials)
        self.serv_level_value_lead = self.serv_lev_value(self.histogram_lead, serv_level)
        self.histo_with_cum_lead  = self.histogram_with_cum(self.histogram_lead, 20)

        self.histogram_buy = self.monte_forecast(sim_input_his[['actual_sale', 'day']], sim_rio_items.loc[:, 'buy_freq'].values[0], number_of_trials)
        self.serv_level_value_buy = self.serv_lev_value(self.histogram_buy, serv_level)
        self.histo_with_cum_buy = self.histogram_with_cum(self.histogram_buy, 20)

        #Input í simulator
        self.simulator_input_his = self.step_5_crate_input_data_frame(sim_input_his, periods, sim_rio_items,
                                                                      sim_rio_on_order, number_of_trials,
                                                                      serv_level)
        #Output úr simulator
        self.sim_result = self.simulator_final_result()
        self.as_is_info = self.data_collection_in_dataframe_for_constructor(sim_rio_items)


    def calc_lead_and_buy_with_save(self,inv_sim_his, periods, number_of_trials, serv_level):
        timarod = inv_sim_his[['actual_sale', 'day']]
        histogram = self.monte_forecast(timarod, periods, number_of_trials)
        lead_buy_forecast_with_save = self.serv_lev_value(histogram, serv_level)
        return lead_buy_forecast_with_save

    #In this method we add forecast to the dataframe
    def step_1_add_monte_forecast_to_sim_input(self, sim_input_his, periods):
        pn = sim_input_his['item_id'].iloc[0]
        actual_sale = -1000001
        timarod = sim_input_his[['actual_sale']]

        df_single_forecast = self.single_forecast(timarod, periods)
        start_date = sim_input_his['day'].max() + pd.Timedelta(days=1)

        sim_input_his_with_forecast = pd.DataFrame(
            {'day': pd.date_range(start=start_date, periods=periods),
             'item_id': [pn] * periods,
             'actual_sale': [actual_sale] * periods,
             'forecast': df_single_forecast
             })

        sim_input_his_with_forecast = pd.concat([sim_input_his, sim_input_his_with_forecast])
        sim_input_his_with_forecast = sim_input_his_with_forecast.reset_index()

        return sim_input_his_with_forecast

    # In this method we add on order to data frame
    def step_2_add_on_order_to_sim_input(self, sim_rio_on_order, sim_input_his):
        del_dates = sim_rio_on_order['est_deliv_date'].values.tolist()
        del_qty = sim_rio_on_order['est_deliv_qty'].values.tolist()

        input_with_on_order = sim_input_his
        input_with_on_order['delivery'] = 0
        input_with_on_order.loc[input_with_on_order.day.isin(del_dates), 'delivery'] = del_qty

        return input_with_on_order

    def step_3_input_add_extra_params_to_sim_input(self, sim_rio_items, sim_input_his, number_of_trials, serv_level):

        curr_stock = sim_rio_items.loc[:, 'actual_stock'].values[0]
        lead_time = min(365, sim_rio_items.loc[:, 'del_time'].values[0])
        order_freq = sim_rio_items.loc[:, 'buy_freq'].values[0]
        minmax_min = sim_rio_items.loc[:, 'min'].values[0]
        minmax_max = sim_rio_items.loc[:, 'max'].values[0]
        lead_forecast = self.calc_lead_and_buy_with_save(sim_input_his.loc[sim_input_his['actual_sale'] != -1000001.0],
                                                         lead_time, number_of_trials, serv_level)
        buy_forecast = self.calc_lead_and_buy_with_save(sim_input_his.loc[sim_input_his['actual_sale'] != -1000001.0],
                                                        order_freq, number_of_trials, serv_level)
        backorder = 1
        safety_stock = 0
        bypass_forecast = 1

        if sim_rio_items.loc[:, 'purchasing_method'].values[0]=='low_sale':
            dict_item_info = {}

            dict_item_info['current_inventory'] = "[[10000," + str(curr_stock) + "]]"
            dict_item_info['lead_time'] = lead_time
            dict_item_info['order_freq'] = order_freq
            dict_item_info['lead_forecast'] = lead_forecast
            dict_item_info['buy_forecast'] = buy_forecast
            dict_item_info['bakcorder'] = backorder
            dict_item_info['safety_stock'] = safety_stock
            dict_item_info['bypass_forecast'] = bypass_forecast

            extra_params = [dict_item_info]
            extra_params = {"extra_params": [dict_item_info]}
            extra_params = str(extra_params).replace("'", '"')
            sim_input_with_extra = sim_input_his
            sim_input_with_extra['extra_params'] = extra_params

            return sim_input_with_extra

        if sim_rio_items.loc[:, 'purchasing_method'].values[0]== 'min-max':

            dict_item_info = {}

            dict_item_info['current_inventory'] = "[[10000," + str(curr_stock) + "]]"
            dict_item_info['lead_time'] = lead_time
            dict_item_info['order_freq'] = order_freq
            dict_item_info['lead_forecast'] = lead_forecast
            dict_item_info['buy_forecast'] = buy_forecast
            dict_item_info['bakcorder'] = backorder
            dict_item_info['safety_stock'] = safety_stock
            dict_item_info['bypass_forecast'] = bypass_forecast
            dict_item_info['use_minmax'] = safety_stock
            dict_item_info['minmax_min'] = minmax_min
            dict_item_info['minmax_max'] = minmax_max

            extra_params = [dict_item_info]
            extra_params = {"extra_params": [dict_item_info]}
            extra_params = str(extra_params).replace("'", '"')
            sim_input_with_extra = sim_input_his
            sim_input_with_extra['extra_params'] = extra_params

            return sim_input_with_extra

    #In this method we add order day to data frame
    def step_5_add_order_day_to_sim_input(self, sim_rio_items, sim_input_hist):
        sim_input_his_on_order = sim_input_hist
        buy_freq = sim_rio_items.iloc[0]['buy_freq']
        sim_input_his_on_order['order_day'] = 0
        sim_input_his_on_order.loc[::buy_freq, 'order_day'] = 1

        return sim_input_his_on_order

    def step_5_crate_input_data_frame(self, sim_input_his, periods, sim_rio_items, sim_rio_on_order, number_of_trials, serv_level):
        sim_input_his_1 = self.step_1_add_monte_forecast_to_sim_input(sim_input_his, periods)
        sim_input_his_2 = self.step_2_add_on_order_to_sim_input(sim_rio_on_order, sim_input_his_1)
        sim_input_his_3 = self.step_3_input_add_extra_params_to_sim_input(sim_rio_items, sim_input_his_2, number_of_trials, serv_level)
        sim_input_his_4 = sim_input_his_3.loc[sim_input_his_3['actual_sale'] == -1000001.0].reset_index()
        sim_input_his_5 = self.step_5_add_order_day_to_sim_input(sim_rio_items, sim_input_his_4)
        #Hér sýnum við eingögnu datafram sem inniheldur línur þar sem enginn raun sala er en bara spá
        #sim_input_his_5 = sim_input_his_4.loc[sim_input_his_4['actual_sale'] == -1000001.0].reset_index()

        return sim_input_his_5[['index', 'item_id', 'day','forecast','actual_sale', 'order_day', 'delivery', 'extra_params']]

    def data_collection_in_dataframe_for_constructor(self, sim_rio_items):
        #Næ í upplýsingar úr extra params dictionary hluta í simulatoir_input_his
        my_dict = json.loads(self.simulator_input_his['extra_params'][0])
        # convert the dictionary to a Pandas DataFrame
        df = pd.DataFrame.from_dict(my_dict['extra_params'][0], orient='index').T
        #Næ hér í upplýsingar um birgðastöðu þar sem við höfum lista sem geymir birgðstöðu og expiery dags
        df['updated_current_inventory'] = eval(my_dict['extra_params'][0]['current_inventory'])[0][1]

        #Sameina datafream
        sim_rio_items = sim_rio_items.reset_index()
        result = pd.concat([df, sim_rio_items], axis=1)

        #Vel rétta dálka og rename einn dálk
        result = result[
            ['lead_time', 'order_freq', 'lead_forecast', 'buy_forecast', 'bakcorder', 'safety_stock', 'bypass_forecast',
             'updated_current_inventory', 'pn', 'description', 'del_time', 'buy_freq', 'purchasing_method', 'min',
             'max']]
        result = result.rename(columns={'updated_current_inventory': 'current_inventory'})

        return result

    def simulator_final_result(self):
        inp = self.simulator_input_his
        res = self.run_inventory_simulator(self.simulator_input_his)
        final_res = res.merge(inp[['day', 'forecast', 'actual_sale']], left_on='sim_date', right_on='day')
        final_res = final_res.drop(['day'], axis=1)
        return final_res



if __name__ == '__main__':
    inp_data = get_raw_data()
    start_time = datetime.now()
    print(start_time)

    sim_input_his = inp_data.create_rio_his_test_data('Q4631')
    sim_rio_items = inp_data.create_rio_items_test_data('Q4631')
    sim_rio_item_details = inp_data.create_rio_item_details_test_data('Q4631')
    sim_rio_on_order = inp_data.create_on_order_test_data('Q4631')
    a = inventory_simulator_with_input_prep(sim_input_his, sim_rio_items, sim_rio_on_order, 750, 5000, 0.97)

    #for index, row in inp_data.rio_items.head(5).iterrows():
      #  sim_input_his = inp_data.create_rio_his_test_data(row['pn'])
       # sim_rio_items = inp_data.create_rio_items_test_data(row['pn'])
       # sim_rio_on_order = inp_data.create_on_order_test_data(row['pn'])

      #  a = inventory_simulator_with_input_prep(sim_input_his, sim_rio_items, sim_rio_on_order, 750, 5000, 0.97)
      #  print('siggi'+ str(index))

    #print(sim_rio_items)
    #print(a.simulator_input_his[:1])


    print('-----------------------------------------------------------------------------------------------')
    print('-----------------------------------------------------------------------------------------------')
    print(a.sim_result)
    print(a.as_is_info.columns)