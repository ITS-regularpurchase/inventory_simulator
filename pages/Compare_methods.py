import streamlit as st
import compare_purch_methods as compare
from st_aggrid import AgGrid, GridOptionsBuilder
from authentication import check_password
import pandas as pd

if check_password():
    st.set_page_config(
        layout="wide")


    if 'result' not in st.session_state:
        st.session_state.result = compare.run_all_min_max_low_sale(5, 0.97)


    all = st.session_state.result

    rio_items = all.min_max_as_is[all.min_max_as_is['buy_forecast']>5]
    builder = GridOptionsBuilder.from_dataframe(rio_items)
    builder.configure_pagination(enabled=False, paginationPageSize=15)
    builder.configure_selection('single')
    go = builder.build()

    grid_return = AgGrid(rio_items, go, height=250)

    selected_rows = grid_return['selected_rows']

    if selected_rows:
        dfs = pd.DataFrame(selected_rows)
        pn = dfs["pn"].values[0]

        plot_min_max = all.min_max_final_res[all.min_max_final_res['item_id'].isin([pn])]
        plot_low_sale = all.low_sale_final_res[all.low_sale_final_res['item_id'].isin([pn])]
        sim_input_his = all.total_his[all.total_his['item_id'].isin([pn])]

        as_is = all.low_sale_as_is[all.low_sale_as_is['pn'].isin([pn])]

        st.text('MIN ' + str(as_is['min'].values[0]))
        st.text('MAX ' + str(as_is['max'].values[0]))

        st.plotly_chart(all.compare_with_plot(plot_low_sale, plot_min_max, sim_input_his), use_container_width=True)


        st.text('Unit Cost ' + str(as_is['unit_cost'].values[0]))
        st.text('current stock value ' + str(as_is['current_stock_value'].values[0]))
        st.text('optimal stock value ' + str(as_is['optimal_stock_value'].values[0]))



