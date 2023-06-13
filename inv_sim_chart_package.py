import plotly.graph_objs as go
import plotly.offline as pyo
import inventory_opt_and_forecasting_package as inv
from datetime import datetime

class inv_sim_charts():

    def plotly_draw_all_time_series(self):
        pass

    def plotly_draw_histo_with_cum(histogram_with_cum, serv_value, title):
        hist = go.Bar(x=histogram_with_cum.iloc[:, 0], y=histogram_with_cum.iloc[:, 1], name='Number of Occurances',
                      yaxis='y1')
        cum = go.Scatter(x=histogram_with_cum.iloc[:, 0], y=histogram_with_cum.iloc[:, 2], mode='lines',
                         name='Service Level', yaxis='y2')

        data = [hist, cum]

        layout = go.Layout(title=title,
                           yaxis=dict(title='Number of Occurances'),
                           yaxis2=dict(title='Service Level',
                                       overlaying='y',
                                       side='right'))

        fig = go.Figure(data=data, layout=layout)

        # Set x-axis title
        fig.update_xaxes(title_text="Usage")
        fig.add_vline(x=serv_value, line_width=3, line_dash="dash", line_color="red")

        return fig

if __name__ == '__main__':
    inp_data = inv.get_raw_data()
    start_time = datetime.now()
    print(start_time)

    sim_input_his = inp_data.create_rio_his_test_data('Q4631')
    sim_rio_items = inp_data.create_rio_items_test_data('Q4631')
    sim_rio_on_order = inp_data.create_on_order_test_data('Q4631')
    a = inv.inventory_simulator_with_input_prep(sim_input_his, sim_rio_items, sim_rio_on_order, 750, 5000, 0.97)

    ch = inv_sim_charts
    buy = ch.plotly_draw_histo_with_cum(a.histo_with_cum_buy, a.serv_level_value_buy)
    pyo.plot(buy)

