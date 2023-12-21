import inventory_opt_and_forecasting_package as inv_opt
import plotly.graph_objects as go
import plotly.offline as pyo
import pandas as pd
import streamlit as st


class compare_min_max_low_sale:
    def __init__(self, sim_input_his, sim_rio_items, sim_rio_on_order, sim_rio_item_details, serv_level):
        self.compare_methods(sim_input_his, sim_rio_items, sim_rio_on_order, sim_rio_item_details, serv_level)
        self.low_sale_as_is_info = self.low_sale_result.as_is_info
        self.low_sale_sim_result = self.low_sale_result.sim_result
        self.min_max_as_is_info = self.min_max_result.as_is_info
        self.min_max_sim_result = self.min_max_result.sim_result

    def compare_methods(self, sim_input_his, sim_rio_items, sim_rio_on_order, sim_rio_item_details, serv_level):
        self.min_max_result = inv_opt.inventory_simulator_with_input_prep(sim_input_his, sim_rio_items, sim_rio_on_order,
                                                                     sim_rio_item_details, 750, 5000, serv_level)

        sim_rio_items_low_sale = sim_rio_items.reset_index()
        sim_rio_items_low_sale.loc[0, 'purchasing_method'] = 'low_sale'

        self.low_sale_result = inv_opt.inventory_simulator_with_input_prep(sim_input_his, sim_rio_items_low_sale,
                                                                           sim_rio_on_order, sim_rio_item_details, 750,
                                                                           5000, serv_level)

class run_all_min_max_low_sale:
    def __init__(self, three_year_agg_movement, serv_level):
        self.data = inv_opt.get_raw_data()
        self.pn_list = self.get_all_pn_with_min_max(three_year_agg_movement)

        self.run_all_pn(serv_level)


    def get_all_pn_with_min_max(self, three_year_agg_movement):

        inv_plan = self.data.rio_items.merge(self.data.rio_item_details, how='inner', left_on='pn', right_on='item_number')
        inv_plan['agg_movement_last_3_years'] = inv_plan['movement_three_year'] + inv_plan['movement_two_year'] + \
                                                inv_plan['movement_last_year']

        pn_list = inv_plan['pn'][(inv_plan['purchasing_method_x'].isin(['min-max']))
                                 & (inv_plan['agg_movement_last_3_years'] >= three_year_agg_movement)
                                 & (inv_plan['max_x'] > 0)
                                 ]

        pn_list = pn_list.drop_duplicates()

        return pn_list

    def run_all_pn(self, serv_level):
        self.min_max_final_res = pd.DataFrame()
        self.low_sale_final_res = pd.DataFrame()

        self.min_max_as_is = pd.DataFrame()
        self.low_sale_as_is = pd.DataFrame()

        for indx, values in self.pn_list.items():
            sim_input_his = self.data.create_rio_his_test_data(values)
            sim_rio_items = self.data.create_rio_items_test_data(values)
            sim_rio_on_order = self.data.create_on_order_test_data(values)
            sim_rio_item_details = self.data.create_rio_item_details_test_data(values)

            compare_object = compare_min_max_low_sale(sim_input_his, sim_rio_items, sim_rio_on_order, sim_rio_item_details, serv_level)

            if not self.min_max_final_res.empty:

                self.min_max_final_res = pd.concat([self.min_max_final_res, compare_object.min_max_sim_result], ignore_index=True)
                self.low_sale_final_res = pd.concat([self.low_sale_final_res, compare_object.low_sale_sim_result], ignore_index=True)

                self.min_max_as_is = pd.concat([self.min_max_as_is, compare_object.min_max_as_is_info], ignore_index=True)
                self.low_sale_as_is = pd.concat([self.low_sale_as_is, compare_object.low_sale_as_is_info], ignore_index=True)
                self.total_his = pd.concat([self.total_his, sim_input_his],ignore_index=True)

            else:

                self.min_max_final_res = compare_object.min_max_sim_result
                self.low_sale_final_res = compare_object.low_sale_sim_result

                self.min_max_as_is = compare_object.min_max_as_is_info
                self.low_sale_as_is = compare_object.low_sale_as_is_info

                self.total_his = sim_input_his

    def compare_with_plot(self, low_sale_sim_result, min_max_sim_result, sim_input_his):

        trace0 = go.Scatter(x=low_sale_sim_result['sim_date'], y=low_sale_sim_result['inv'], mode='lines',
                            fill='tozeroy',
                            marker_color='red'
                            , yaxis='y1', name='Low Sale')
        trace1 = go.Scatter(x=min_max_sim_result['sim_date'], y=min_max_sim_result['inv'], mode='lines'
                            , yaxis='y1', name='Min Max'
                            , line=dict(color='green', width=3, dash='solid'))

        trace2 = go.Bar(x=sim_input_his['day'], y=sim_input_his['actual_sale'], marker_color='blue', name='History')

        data = [trace0, trace1, trace2]

        layout = go.Layout(title='Simulator result')

        fig = go.Figure(data=data, layout=layout)



        return fig

if __name__ == '__main__':
    inp_data = inv_opt.get_raw_data()

    pn = 'NAS1611-211'

    sim_input_his = inp_data.create_rio_his_test_data(pn)
    sim_rio_items = inp_data.create_rio_items_test_data(pn)
    sim_rio_item_details = inp_data.create_rio_item_details_test_data(pn)
    sim_rio_on_order = inp_data.create_on_order_test_data(pn)


    a = compare_min_max_low_sale(sim_input_his, sim_rio_items, sim_rio_on_order, sim_rio_item_details, 0.99)

    print(a.low_sale_sim_result)
    print(a.min_max_as_is_info)

    all = run_all_min_max_low_sale(5, 0.97)

    print(all.pn_list)


