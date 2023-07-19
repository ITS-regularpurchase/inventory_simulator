import streamlit as st
from authentication import check_password
import inventory_opt_and_forecasting_package as sim
import part_number_container as pc
import plotly.graph_objects as go
import plotly.offline as pyo

st.set_page_config(
    layout="wide"
)

if check_password():
    if 'data' not in st.session_state:
        st.session_state.data = sim.get_raw_data()
        pn_list = st.session_state.data.rio_items['pn']
        st.session_state.alda = pc.inv_opt_container(pn_list)

    alda = st.session_state.alda

    # data = sim.get_raw_data()
    # pn_list = st.session_state.data.rio_items['pn'].head(300)
    # alda = pc.inv_opt_container(pn_list)
    opt_plan = alda.overview_opt_plan
    mynd = pc.plotly_draw_inv_opt_plan

    filter_rio_items = alda.rio_items.merge(alda.rio_item_details, how='left', left_on='pn', right_on='item_number')
    filter_rio_items = filter_rio_items[['pn', 'actual_stock', 'purchasing_method_x', 'movement_three_year']]
    filter_rio_items = filter_rio_items.rename(columns={'purchasing_method_x': 'purchasing_method'})

    purchase_method_option = tuple(filter_rio_items['purchasing_method'].unique()[0])
    min_3_year_movement = float(filter_rio_items['movement_three_year'].min())
    max_3_year_movement = float(filter_rio_items['movement_three_year'].max())

    col1, col2 = st.columns([0.2, 0.8])

    with col1:
        with st.form("my_form"):
            purch_method = st.selectbox('Purchasing Method', ('low_sale', 'min-max'))
            values = st.slider('Select a range of values', min_3_year_movement, max_3_year_movement,
                               (min_3_year_movement, max_3_year_movement))

            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit")
            if submitted:
                to_filter = filter_rio_items['pn'][(filter_rio_items['purchasing_method'] == purch_method)
                                                   & (filter_rio_items['movement_three_year'] >= values[0])
                                                   & (filter_rio_items['movement_three_year'] < values[1])]
                alda.update_overview_opt_plan(to_filter)

    with col2:
        opt_plan = alda.overview_opt_plan

        st.plotly_chart(mynd.opt_inv_plan(opt_plan), use_container_width=True)

