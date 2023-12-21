import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import inventory_opt_and_forecasting_package as sim
import part_number_container as pc
import plotly.graph_objects as go
import plotly.offline as pyo
from authentication import check_password
import pandas as pd

if check_password():
    st.set_page_config(
        page_title="Ex-stream-ly Cool App",
        page_icon="🧊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://www.extremelycoolapp.com/help',
            'Report a bug': "https://www.extremelycoolapp.com/bug",
            'About': "# This is a header. This is an *extremely* cool app!"
        }
    )




    if 'data' not in st.session_state:
        st.session_state.data = sim.get_raw_data()
        pn_list = st.session_state.data.rio_items['pn']
        st.session_state.alda = pc.inv_opt_container(pn_list)


    alda = st.session_state.alda

    rio_items = alda.as_is_container_for_grid[['pn', 'description', 'current_inventory', 'purch_sugg', 'min', 'max', 'del_time', 'buy_freq',
                 'purchasing_method', 'agg_movement_last_3_years', 'optimal_stock', 'unit_cost', 'optimal_stock_value']]
    builder = GridOptionsBuilder.from_dataframe(rio_items)
    builder.configure_pagination(enabled=False, paginationPageSize=15)
    builder.configure_selection('single')
    go = builder.build()


    opt_plan = alda.overview_opt_plan
    mynd = pc.plotly_draw_inv_opt_plan


    filter_rio_items = alda.container_as_is_info

    purchase_method_option = filter_rio_items['purchasing_method'].unique()
    over_under_stock = filter_rio_items['opt_stock_status'].unique()

    min_3_year_movement = float(filter_rio_items['agg_movement_last_3_years'].min())
    max_3_year_movement = float(filter_rio_items['agg_movement_last_3_years'].max())

    min_opt_value = float(filter_rio_items['current_vs_optimal_diff_value'].min())
    max_opt_value = float(filter_rio_items['current_vs_optimal_diff_value'].max())


    col1, col2= st.columns([0.2,0.8])

    with col1:
        with st.form("my_form"):
            selected_purch_method = st.multiselect('Purchasing Method', purchase_method_option)
            selected_over_and_understock = st.multiselect('Purchasing Method', over_under_stock)

            minmax = st.slider('Movement filter', min_3_year_movement, max_3_year_movement , (min_3_year_movement, max_3_year_movement))

            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit")
            if submitted:
                to_filter = filter_rio_items['pn'][(filter_rio_items['purchasing_method'].isin(selected_purch_method))
                  & (filter_rio_items['opt_stock_status'].isin(selected_over_and_understock))
                  & (filter_rio_items['movement_three_year'] >= minmax[0])
                  & (filter_rio_items['movement_three_year'] <= minmax[1])
                ]
                alda.update_overview_opt_plan(to_filter)
                alda.filter_container_as_is_info(to_filter)

    with col2:
        tab1, tab2, tab3 = st.tabs(["Overview", "Grid", "Owl"])

        with tab1:
            opt_plan = alda.overview_opt_plan
            st.plotly_chart(mynd.opt_inv_plan(opt_plan), use_container_width=True)

        with tab2:
            alda.as_is_container_for_grid =  alda.as_is_container_for_grid[['pn', 'description' ,'current_inventory', 'purch_sugg', 'min', 'max', 'del_time', 'buy_freq', 'purchasing_method'
            , 'agg_movement_last_3_years', 'optimal_stock', 'unit_cost', 'optimal_stock_value']]
            # 'current_stock_value', 'opt_stock_status']]
            st.dataframe(alda.as_is_container_for_grid)

        with tab3:
            grid_return = AgGrid(rio_items, go, height=400)

            selected_rows = grid_return['selected_rows']
            st.text(selected_rows)

            if selected_rows:
                dfs = pd.DataFrame(selected_rows)
                # pn = type(dfs["pn"])
                pn = dfs["pn"].values[0]





