import streamlit as st
pip install streamlit-aggrid
#import streamlit_authenticator as stauth
from st_aggrid import AgGrid, GridOptionsBuilder
import inventory_opt_and_forecasting_package as inv
import pandas as pd
import plotly.graph_objs as plotly_go
import inv_sim_chart_package as charts
import datetime
import get_data_from_its


inp_data = inv.get_raw_data()
rio_items = inp_data.get_rio_items()
rio_items = rio_items[['pn', 'description', 'actual_stock', 'del_time', 'buy_freq', 'purchasing_method']]
#@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')

st.set_page_config(
    page_title="ITS - Regular purchase simulator",
    page_icon="ice.jpeg",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

def check_password():
    """Returns true if user has the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "RHINO123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
    with st.expander("Comments"):
        st.markdown('gagnauppfærsla:  keyra þarf skrána get_data_from_its.py')
        st.markdown('Þetta er skirfað á fundi 8. jún til að sýn Írenu og Hlyn hvað þetta er allt saman sniðugt')
        st.markdown('15/06/23 - uppfært: pagetitle, pageicon. Bætti við leitarboxi og aðgangsorði - ÍHT')


    st.title('Inventory Simulator Demo')
    if st.button('Update from MXI'):
        now = datetime.datetime.now()
        get_data_from_its.test()
        st.success(f"Síðasta uppfærsla "+str(now))

    builder = GridOptionsBuilder.from_dataframe(rio_items)
    #builder.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=10)
    builder.configure_pagination(enabled=False, paginationPageSize=15)
    builder.configure_selection('single')
    go = builder.build()

    with st.expander("Part number grid"):
        search_term = st.text_input('Enter Partnumber')
        filtered_grid = rio_items[rio_items['pn'].str.contains(search_term,case=False)]
        grid_return = AgGrid(filtered_grid,go, height=400) 
        #grid_return = AgGrid(rio_items, go)

    selected_rows = grid_return['selected_rows']

    with st.expander("Input"):
        lead_time = st.number_input('Lead time', value = 10)
        buy_freq = st.number_input('buy_freq', value = 10)
        number_of_simulations = st.number_input('number of simulations', value=10000)
        service_level = st.number_input('service level', value=0.95)
        number_of_days = st.number_input('number of days', value=365)


    if selected_rows:
        dfs = pd.DataFrame(selected_rows)
        #pn = type(dfs["pn"])
        pn = dfs["pn"].values[0]



        sim_input_his = inp_data.create_rio_his_test_data(pn)
        sim_rio_items = inp_data.create_rio_items_test_data(pn).reset_index()
        sim_rio_on_order = inp_data.create_on_order_test_data(pn)
        rio_item_details = inp_data.create_rio_item_details_test_data(pn)

        periods = number_of_days
        number_of_trials = number_of_simulations
        serv_level = service_level
        sim_rio_items.at[0, 'buy_freq'] = lead_time
        sim_rio_items.at[0, 'del_time'] = buy_freq



        inv_sim = inv.inventory_simulator_with_input_prep(sim_input_his, sim_rio_items, sim_rio_on_order, periods, number_of_trials, serv_level)

        with st.expander("PN Info"):
            col1, col2 , col3= st.columns(3)


            with col1:
                st.text("Purchasing Suggestion:" + dfs["pn"].values[0])
                st.text("Purchasing Suggestion:" + str(inv_sim.sim_result['purchase_qty'][0]))
                st.text("purchasing method:" + str(rio_item_details['purchasing_method'].values[0]))
                st.text("Vendor:" + str(rio_item_details['vendor_name'].values[0]))
                st.text("Comment:" + str(rio_item_details['comment'].values[0]))

            with col2:

                if str(rio_item_details['purchasing_method'].values[0]) != 'min-max':
                    purch_method = 'Low-Sale'
                else:
                    purch_method = str(rio_item_details['purchasing_method'].values[0])

                st.text("Inventory Level:" + str(rio_item_details['stock_units'].values[0]))
                st.text("Unit Price:" + str(rio_item_details['unit_cost'].values[0]))
                st.text("Purchasing Method:" + purch_method)
                st.text("Min:" + str(rio_item_details['min'].values[0]))
                st.text("Max:" + str(rio_item_details['max'].values[0]))
            with col3:
                agg_3_year_movement = rio_item_details['movement_last_year'].values[0]\
                                +rio_item_details['movement_two_year'].values[0]\
                                +rio_item_details['movement_three_year'].values[0]
                agg_3_year_usage =  rio_item_details['usage_last_year'].values[0]\
                                +rio_item_details['usage_two_year'].values[0]\
                                +rio_item_details['usage_three_year'].values[0]
                st.text("Total Movements Last 3 years :" + str(agg_3_year_movement))
                st.text("Total Usage Last 3 years :" + str(agg_3_year_usage))



        df_his = sim_input_his[['day', 'actual_sale']]
        df_his.set_index('day', inplace=True)



        Inventory = plotly_go.Scatter(x=inv_sim.sim_result['sim_date'], y=inv_sim.sim_result['inv'], mode='lines', fill='tozeroy', marker_color='orange', name="Inventory level" )
        Forecast = plotly_go.Bar(x=inv_sim.sim_result['sim_date'], y=inv_sim.sim_result['forecast'], marker_color='red', name="Forecast" )
        Deliveries = plotly_go.Bar(x=inv_sim.sim_result['sim_date'], y=inv_sim.sim_result['deliveries'], marker_color='green', name = 'Deliveries' )
        History = plotly_go.Bar(x=sim_input_his['day'], y=sim_input_his['actual_sale'],
                                marker_color='blue',
                                name = 'History')


        data = [Inventory, Forecast, Deliveries, History]

        layout = plotly_go.Layout(title = 'Simulator result')

        fig = plotly_go.Figure(data = data, layout = layout)




        buy = charts.inv_sim_charts.plotly_draw_histo_with_cum(inv_sim.histo_with_cum_buy, inv_sim.serv_level_value_buy, 'Histogram of lead time')
        lead = charts.inv_sim_charts.plotly_draw_histo_with_cum(inv_sim.histo_with_cum_lead, inv_sim.serv_level_value_lead, 'Histogram of buying frequency')


        with st.expander("Histograms"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Est. usage based on " + str(100 * service_level) + '% service level',
                        value=str(inv_sim.serv_level_value_buy))

                st.plotly_chart(buy, use_container_width=True)

            with col2:
                st.metric(label="Est. usage based on " + str(100 * service_level) + '% service level',
                        value=str(inv_sim.serv_level_value_lead))
                st.plotly_chart(lead, use_container_width=True)



        with st.expander("Inventory Simulation"):
            st.plotly_chart(fig, use_container_width=True)


        with st.expander("Comments"):
            st.markdown('gagnauppfærsla:  keyra þarf skrána get_data_from_its.py')
        

