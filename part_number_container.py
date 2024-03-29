import inventory_opt_and_forecasting_package as sim
import plotly.graph_objects as go
import plotly.offline as pyo
import pandas as pd
import streamlit as st




class inv_opt_container(sim.inventory_simulator_with_input_prep, sim.get_raw_data):
    def __init__(self, pn_list):
        """
        Creates instance variables:
            final_res: 
                Purchasing suggestion for all provided part numbers (pn_list)
            
            container_as_is_info / as_is_container_for_grid: for each part number:
                'pn', 'description', 'lead_time', 'order_freq', 'lead_forecast',
                'buy_forecast', 'bakcorder', 'safety_stock', 'bypass_forecast',
                'current_inventory', 'del_time', 'buy_freq', 'purchasing_method',
                'vendor_name', 'stock_units', 'inv_class_cd', 'service_level', 'min',
                'max', 'comment', 'movement_last_year', 'usage_last_year',
                'movement_two_year', 'usage_two_year', 'movement_three_year',
                'usage_three_year', 'purch_sugg', 'optimal_stock', 'unit_cost',
                'optimal_stock_value', 'current_stock_value',
                'current_vs_optimal_diff_value', 'opt_stock_status',
                'agg_movement_last_3_years'
                
            overview_opt_plan (for all pn) / update_overview_opt_plan (takes in filtered list):
                For each pn:
                    stock value,
                    total qty,
                    qty of nil stock,
                    nil stock % compared to all pn provided
        """
        self.rio_histories = self.get_rio_histories()
        self.rio_items = self.get_rio_items()
        self.rio_item_details = self.get_rio_item_details()
        self.rio_on_order = self.get_rio_on_order()

        self.final_res = self.run_purch_sugg_for_all_pn(pn_list)
        self.overview_opt_plan = self.calc_optimal_evoulouton_stock_value_and_serv_level()
        self.container_as_is_info = self.container_as_is_info
        self.as_is_container_for_grid = self.container_as_is_info


    def run_purch_sugg_for_all_pn(self, pn_list):
        final_res = pd.DataFrame()

        for indx, values in pn_list.items():
            sim_input_his = self.create_rio_his_test_data(values)
            sim_rio_items = self.create_rio_items_test_data(values)
            sim_rio_on_order = self.create_on_order_test_data(values)
            sim_rio_item_details = self.create_rio_item_details_test_data(values)

            sim_object = sim.inventory_simulator_with_input_prep(sim_input_his, sim_rio_items, sim_rio_on_order, sim_rio_item_details, 750,
                                                                 1000, 0.95)

            if not final_res.empty:
                final_res = pd.concat([final_res, sim_object.sim_result], ignore_index=True)
                self.container_as_is_info  =  pd.concat([self.container_as_is_info, sim_object.as_is_info], ignore_index=True)
            else:
                final_res = sim_object.sim_result
                self.container_as_is_info = sim_object.as_is_info


        return final_res

    def calc_optimal_evoulouton_stock_value_and_serv_level(self):
        detail = self.container_as_is_info[['pn', 'unit_cost', 'purchasing_method']]
        final_res = self.final_res[['item_id', 'inv', 'sim_date']]

        inv_plan = final_res.merge(detail, how='inner', left_on='item_id', right_on='pn')
        inv_value = inv_plan.inv * inv_plan.unit_cost
        inv_plan['inv_value'] = inv_value

        inv_plan_grouped = inv_plan[['item_id', 'sim_date', 'inv_value']]
        inv_plan_grouped = inv_plan.groupby("sim_date", as_index=False).agg({"inv_value": "sum"})

        total_number_of_pn = inv_plan.groupby(["sim_date"], as_index=False).agg({"inv": "count"})
        number_of_pn_nill_stock = inv_plan.loc[inv_plan['inv'] <= 0].groupby(["sim_date"], as_index=False).agg(
            {"inv": "count"})

        inv_plan_grouped['total_number_of_pn'] = total_number_of_pn['inv']

        inv_plan_grouped['number_of_pn_nill_stock'] = number_of_pn_nill_stock['inv']
        inv_plan_grouped['number_of_pn_nill_stock'] = inv_plan_grouped['number_of_pn_nill_stock'].fillna(0)

        inv_plan_grouped['service_level'] = 1 - inv_plan_grouped['number_of_pn_nill_stock'] / inv_plan_grouped[
            'total_number_of_pn']

        return inv_plan_grouped

    def update_overview_opt_plan(self, filterd_list):
        detail = self.container_as_is_info #[['pn', 'unit_cost', 'purchasing_method']]
        final_res = self.final_res[['item_id', 'inv', 'sim_date']]

        detail_filter = detail['pn'].isin(filterd_list)
        final_res_filter = final_res['item_id'].isin(filterd_list)

        detail = detail[detail_filter]
        final_res = final_res[final_res_filter]

        inv_plan = final_res.merge(detail, how='inner', left_on='item_id', right_on='pn')
        inv_value = inv_plan.inv * inv_plan.unit_cost
        inv_plan['inv_value'] = inv_value

        inv_plan = inv_plan[['item_id', 'sim_date', 'inv_value', 'inv']]
        inv_plan_grouped = inv_plan.groupby("sim_date", as_index=False).agg({"inv_value": "sum"})

        total_number_of_pn = inv_plan.groupby(["sim_date"], as_index=False).agg({"inv": "count"})
        number_of_pn_nill_stock = inv_plan.loc[inv_plan['inv'] <= 0].groupby(["sim_date"], as_index=False).agg(
            {"inv": "count"})

        inv_plan_grouped['total_number_of_pn'] = total_number_of_pn['inv']
        inv_plan_grouped['number_of_pn_nill_stock'] = number_of_pn_nill_stock['inv']
        inv_plan_grouped['number_of_pn_nill_stock'] = inv_plan_grouped['number_of_pn_nill_stock'].fillna(0)

        inv_plan_grouped['service_level'] = 1 - inv_plan_grouped['number_of_pn_nill_stock'] / inv_plan_grouped[
            'total_number_of_pn']

        self.overview_opt_plan = inv_plan_grouped

    def filter_container_as_is_info(self, filterd_list):
        self.as_is_container_for_grid  = self.container_as_is_info[self.container_as_is_info['pn'].isin(filterd_list)]







class plotly_draw_inv_opt_plan:
    def opt_inv_plan(opt_plan):
        trace0 = go.Scatter(x=opt_plan['sim_date'], y=opt_plan['inv_value'], mode='lines', fill='tozeroy',
                            marker_color='red'
                            , yaxis='y1', name='Inventory value')
        trace1 = go.Scatter(x=opt_plan['sim_date'], y=opt_plan['service_level'], mode='lines'
                            , yaxis='y2', name='service level'
                            , line=dict(color='green', width=3, dash='solid'))

        data = [trace0, trace1]

        layout = go.Layout(title='Simulator result',
                           yaxis=dict(title='Invenotory Value'),
                           yaxis2=dict(title='Service Level',
                                       overlaying='y',
                                       tickformat=',.1%',
                                       side='right'))

        fig = go.Figure(data=data, layout=layout)

        return fig


class streamlit_inv_opt_container():
    pass




if __name__ == '__main__':
    data = sim.get_raw_data()
    pn_list = data.rio_items['pn']

    to_filter = data.rio_items['pn'].head(50)

    alda = inv_opt_container(pn_list.head(20))
    
    print(alda.overview_opt_plan)

    # print(alda.overview_opt_plan)

    #print(alda.update_overview_opt_plan(to_filter))

    # print(alda.container_as_is_info)

    # alda.container_as_is_info.to_excel("as_is_info.xlsx")
   





  


