# The script MUST contain a function named azureml_main
# which is the entry point for this module.

import pandas as pd
import datetime
import math
import json
from scipy.stats import norm
import copy
import sys

def update_inventory(curr_inv, day_nr, outgoing, incoming, initial_shelf_life, backorder):
    # Make sure that the inventory is sorted correctly
    curr_inv.sort(key=lambda x: x[0])

    # Throw away expired inventory
    expired = 0
    while len(curr_inv) > 0 and curr_inv[0][0] < day_nr:
        tmp = curr_inv.pop(0)
        expired += tmp[1]

    # Use the current inventory to satisfy outgoing orders
    outgoing_remaining = outgoing
    while outgoing_remaining > 0 and len(curr_inv) > 1:  # skip the last element, that is used for negative inventory
        current_slice = min(outgoing_remaining, curr_inv[0][1])

        outgoing_remaining = outgoing_remaining - current_slice
        curr_inv[0][1] = curr_inv[0][1] - current_slice

        if curr_inv[0][1] == 0:
            curr_inv.pop(0)

    # Calculate lost sale or update backorders
    lost_sale = 0
    if outgoing_remaining > 0:
        if backorder:
            curr_inv[-1][1] = curr_inv[-1][1] - outgoing_remaining
        else:
            lost_sale = outgoing_remaining

    # Add the incoming inventory
    if incoming > 0:
        if curr_inv[-1][1] < 0:  # start by satisfying backorders if we have those
            backorder_slice = min(incoming, -1*curr_inv[-1][1])
            incoming = incoming - backorder_slice
            curr_inv[-1][1] = curr_inv[-1][1] + backorder_slice

        curr_inv.append( [initial_shelf_life + day_nr, incoming] )
        curr_inv.sort(key=lambda x: x[0])

    # Calculate the total current inventory
    total_inventory = 0
    for tmp in curr_inv:
        total_inventory += tmp[1]

    return curr_inv, total_inventory, lost_sale, expired



def calc_inv_at_next_delivery(current_inventory, forecast, deliveries, other_deliveries, index_from, index_this_delivery, index_next_delivery, backorder):
    currentinv = copy.deepcopy(current_inventory)

    # start with the current deliveries at the end of the current day
    currentinv, _, _, _ = update_inventory(currentinv, index_from, 0, deliveries[index_from] + other_deliveries[index_from],index_next_delivery - index_from + 1, backorder) 

    # calculate the inventory position before our delivery arrives
    # here we get lost sales if the inventory goes below zero unless we have backorder as True
    for i in range(index_from+1, index_this_delivery+1):
        currentinv,  inv_at_this_deliv, _, _ = update_inventory(currentinv, i, forecast[i], deliveries[i] + other_deliveries[i],index_next_delivery - index_from + 1, backorder) 

    # calculate the inventory position after our purchase arrives until the next purchase arrives
    # we will then want to adjust the purchase quantity so this will be equal to the safetystock
    for i in range(index_this_delivery+1, index_next_delivery+1):
        currentinv, current_total, _, _ = update_inventory(currentinv, i, forecast[i], deliveries[i] + other_deliveries[i],index_next_delivery - index_from + 1, True) 
    
    # return the inventory position at next delivery
    return current_total, inv_at_this_deliv


def calc_inv_at_next_delivery_with_bypass(current_inventory, totalforecast, deliveries, other_deliveries, index_from, index_this_delivery, index_to):
    # calculate the current total inventory
    currentinv = copy.deepcopy(current_inventory)
    _, current_total, _, _ = update_inventory(currentinv, index_from, 0, 0, index_to - index_from + 1, False)
    inv_at_this_deliv = current_total

    # calculate the deliveries until the next purchase arrives (the one after our current purchase)
    for i in range(index_from, index_to+1):
        current_total = current_total + deliveries[i] + other_deliveries[i]
        if i == index_this_delivery:
            inv_at_this_deliv = current_total

    # here the forecast is just a lump sum    
    return current_total - totalforecast, inv_at_this_deliv


def inventory_simulator(initial_inv, leadtime, safetystock, forecast, sales, purchases, other_deliveries, backorder, leadtimeforecast, buyfreqforecast, bypass_forecast, min_order_qty, package_size, initial_shelf_life, use_minmax, minmax_min, minmax_max):
    T = len(purchases)

    # prepare initial values and empty datasets
    purchase_qty = [0] * T
    deliveries = [0] * T
    purchase_dates = [i for i,j in enumerate(purchases) if j > 0.5]
    lost_sales = [0] * T
    expired = [0] * T

    salesandforecast = forecast
    salesandforecast[:len(sales)] = sales

    inv = [0] * T
    purchase_index = 0

    stockoutdays = 0
    daysbelowsafety = 0

    # tryggja að backorder sé True eða False (ekki tala)
    backorder = backorder > 0.5

    current_inventory = copy.deepcopy(initial_inv)

    # ----- iterate over the days
    for t in range(T-leadtime):    
        # the forecast is calculated at the start of each day, resulting in lost sale if we down have the items in stock

        current_inventory, curr_inv_pos, lost_sales[t], expired[t] = update_inventory(current_inventory, t, salesandforecast[t], 0, initial_shelf_life, backorder)

        # check if this is an order day and if the remaining time is long enough to calculate the purchase quantity
        if (purchase_index+1 < len(purchase_dates)) and (t == purchase_dates[purchase_index]) and (purchase_dates[purchase_index+1]+leadtime+1 < T):
            # calculate the inventory position when the next delivery after this will arrive
            if bypass_forecast:
                inv_pos_at_next_delivery, inv_pos_at_this_delivery = calc_inv_at_next_delivery_with_bypass(current_inventory, leadtimeforecast + buyfreqforecast, deliveries, other_deliveries, t, t + leadtime, purchase_dates[purchase_index+1] + leadtime)
            else:
                inv_pos_at_next_delivery, inv_pos_at_this_delivery = calc_inv_at_next_delivery(current_inventory, forecast, deliveries, other_deliveries, t, t + leadtime, purchase_dates[purchase_index+1] + leadtime, backorder)

            # calculate the purchase quantity
            current_purchase_qty = 0
            if use_minmax:
                if curr_inv_pos <= minmax_min:
                    #current_purchase_qty = max(0,int(minmax_max - curr_inv_pos))
                    current_purchase_qty = max(0,min(int(minmax_max - inv_pos_at_this_delivery),minmax_max))

            elif inv_pos_at_next_delivery < safetystock:
                current_purchase_qty = int(safetystock - inv_pos_at_next_delivery + 0.5)


            if current_purchase_qty > 0:
                if current_purchase_qty < min_order_qty and current_purchase_qty > 0:
                    current_purchase_qty = min_order_qty

                if package_size > 1 and current_purchase_qty > 0:
                    numpackages = current_purchase_qty // package_size
                    if current_purchase_qty % package_size > 0:
                        numpackages = numpackages + 1
                    current_purchase_qty = numpackages * package_size

                purchase_qty[t] = current_purchase_qty
                deliveries[t+leadtime] = current_purchase_qty

        # deliveries arrive at the end of the day
        current_inventory, inv[t], _, _ = update_inventory(current_inventory, t, 0, deliveries[t] + other_deliveries[t], initial_shelf_life, backorder)
        
        # check if we have more order days
        if (purchase_index < len(purchase_dates)) and (t == purchase_dates[purchase_index]):
            purchase_index = purchase_index + 1


    # ---- clean up the days after we stop purchasing (because of time horizon)
    for t in range(T-leadtime,T):
        current_inventory, inv[t], lost_sales[t], expired[t] = update_inventory(current_inventory, t, salesandforecast[t], deliveries[t] + other_deliveries[t], initial_shelf_life, backorder)

    return inv, purchase_qty, deliveries, lost_sales, expired




def get_key_value_or_default(the_extra_params, the_key, the_defaultvalue, func = lambda x: x):
    if the_key in the_extra_params.keys():
        return func(the_extra_params[the_key])
    else:
        return the_defaultvalue



def run_inventory_simulator(invsimdataset):
    current_id = invsimdataset.item_id[0]
    start_pos = 0
    end_pos = 0
    counter = 0

    n = len(invsimdataset.item_id)

    # prepare our datastructures to handle the results
    item_id = [0]*n
    inv = [0]*n
    purchase_qty = [0]*n
    deliveries = [0]*n
    lost_sale = [0]*n
    expired = [0]*n
    sim_date = [None]*n


    resultscounter = 0
    itemcounter = 0

    # take the pandas dataframe and turn each column into a list, much easier that way...
    # also check if some columns are in the dataframe and set the list as None if they are not
    dataset_itemid = invsimdataset['item_id'].values.tolist()
    dataset_forecast = invsimdataset['forecast'].values.tolist()
    dataset_actual_sale = invsimdataset['actual_sale'].values.tolist()
    if 'actual_sale' in invsimdataset.columns:
        dataset_actual_sale = invsimdataset['actual_sale'].values.tolist()
    else:
        dataset_actual_sale = None
    dataset_order_day = invsimdataset['order_day'].values.tolist()
    dataset_delivery = invsimdataset['delivery'].values.tolist()
    dataset_extra_params = invsimdataset['extra_params'].astype(str).tolist()
    if 'variance' in invsimdataset.columns:
        dataset_variance = invsimdataset['variance'].values.tolist()
    else:
        dataset_variance = None


    #iterate through the dataset
    while (end_pos < len(dataset_itemid)):
        # find where the current item ends
        while (end_pos < len(dataset_itemid) and dataset_itemid[end_pos] == current_id):
            end_pos = end_pos + 1

        # prepare the forecast for the item
        the_forecast = dataset_forecast[start_pos:end_pos]
        for i in range(len(the_forecast)):
            if type(the_forecast[i]) == str:
                the_forecast[i] = int(float(the_forecast[i].replace(',','.')))
        the_forecast = [0 if math.isnan(f) else f for f in the_forecast]

        # prepare the actual sale.  Figure out from the data where the actual sale ends
        # Sometimes we have NaN and sometimes a large negative number to indicate no actual sale
        if dataset_actual_sale:
            end_of_sale = end_pos-1
            while (end_of_sale > start_pos) and (math.isnan(dataset_actual_sale[end_of_sale]) or dataset_actual_sale[end_of_sale] < -1000000):
                end_of_sale = end_of_sale - 1

            # Select the range over the actual sale.
            # and set all points without data in that range to 0
            the_sale = dataset_actual_sale[start_pos:end_of_sale]
            the_sale = [0 if (math.isnan(s) or s < -1000000) else s for s in the_sale]
        else:
            # No actual sale so we'll just use the forecast for the whole horizon
            the_sale = []

        # Pick out the purchases and the deliveries
        the_purchases = dataset_order_day[start_pos:end_pos]
        the_deliveries = dataset_delivery[start_pos:end_pos]

        # pick out the json extra parameters.  They are always identical for
        # each item, so we only need the first one.
        json_text = dataset_extra_params[start_pos]
        js = json.loads(json_text)
        js = js['extra_params'][0]

        # we also only need the first value for the variance, if that column is in the dataset
        if dataset_variance:
            the_variance = dataset_variance[start_pos]
        else:
            the_variance = 0

        # pick out the information stored in the json-text
        #initial_inv = get_key_value_or_default(js, 'current_inventory', 0)  # single number for initial inventory
        initial_inv = eval( str(get_key_value_or_default(js, 'current_inventory', "[]")) )  # array as string with (expirationdate, inv) elements
        lead_time = get_key_value_or_default(js, 'lead_time', 0)
        z_value = get_key_value_or_default(js, 'service_level', 1.65, func=lambda x: norm.ppf(x))
        safety_stock = get_key_value_or_default(js, 'safety_stock', z_value * math.sqrt(lead_time) * math.sqrt(the_variance))
        backorder = get_key_value_or_default(js, 'backorder', False)

        # lead_time_forecast and buy_freq_forecast will override the forecast column if the bypass_forecast is set to True
        lead_time_forecast = get_key_value_or_default(js, 'lead_forecast', 0)
        buy_freq_forecast = get_key_value_or_default(js, 'buy_forecast', 0)
        bypass_forecast = get_key_value_or_default(js, 'bypass_forecast', False) # (lead_time_forecast + buy_freq_forecast > 0)

        use_minmax = get_key_value_or_default(js, 'use_minmax', False) 
        minmax_min = get_key_value_or_default(js, 'minmax_min', 0) 
        minmax_max = get_key_value_or_default(js, 'minmax_max', 0) 

        manual_safety_stock = get_key_value_or_default(js, 'manual_safety_stock', -1)
        if manual_safety_stock > 0:
            safety_stock = manual_safety_stock

        min_order_qty = get_key_value_or_default(js, 'min_order_qty', 0)
        package_size = get_key_value_or_default(js, 'package_size', 1) 

        initial_shelf_life = get_key_value_or_default(js, 'initial_shelf_life', end_pos+1)

        if type(initial_inv) == int:
            initial_inv = [ [initial_shelf_life, initial_inv], ]

        if type(initial_inv) != list:
            print('ERROR: the initial inventory must be a list')
            print('Initial inventory: ', initial_inv)
            exit()

        initial_inv.append( [math.inf, 0] )  #initialize the inventory, placeholder at the end for negative inventory/backorders

        #print("item_id: ", current_id, ", initial_inv: ", initial_inv, ", lead_time: ", lead_time, ", z_value: ", z_value, ", safety_stock: ", safety_stock, ", backorder: ", backorder, sep="")

        # Run the inventory simulator for the current item
        inv_results, purchase_qty_results, deliveries_results, lost_sales_results, expired_results = inventory_simulator(initial_inv, lead_time, safety_stock, the_forecast, the_sale, the_purchases, the_deliveries, backorder, lead_time_forecast, buy_freq_forecast, bypass_forecast, min_order_qty, package_size, initial_shelf_life, use_minmax, minmax_min, minmax_max)

        # update the results, add the results for the current item to all the results
        for i in range(len(inv_results)):
            item_id[resultscounter] = invsimdataset.item_id[start_pos]
            inv[resultscounter] = inv_results[i]
            purchase_qty[resultscounter] = purchase_qty_results[i]
            deliveries[resultscounter] = deliveries_results[i]
            lost_sale[resultscounter] = lost_sales_results[i]
            expired[resultscounter] = expired_results[i]
            sim_date[resultscounter] = invsimdataset.day[start_pos + i]
            resultscounter = resultscounter + 1

        # check if we have reached the end of the dataset
        if end_pos < n:
            current_id = invsimdataset.item_id[end_pos]
            start_pos = end_pos

    # prepare a pandas dataframe as a return value.  Start by creating a dictionary with all the data
    # and then turn the dictionary into a pandas dataframe.
    pandasdata = {'item_id': item_id, 'inv': inv, 'purchase_qty': purchase_qty, 'deliveries': deliveries, 'lost_sale': lost_sale, 'expired': expired, 'sim_date': sim_date}
    totalresults = pd.DataFrame(pandasdata, columns = ['item_id', 'inv', 'purchase_qty', 'deliveries', 'lost_sale', 'expired', 'sim_date'])
    
    return totalresults


# The entry point function can contain up to two input arguments:
#   Param<dataframe1>: a pandas.DataFrame
#   Param<dataframe2>: a pandas.DataFrame
def azureml_main(dataframe1 = None, dataframe2 = None):

    # Execution logic goes here
    #print('Input pandas.DataFrame #1:\r\n\r\n{0}'.format(dataframe1))

    # If a zip file is connected to the third input port is connected,
    # it is unzipped under ".\Script Bundle". This directory is added
    # to sys.path. Therefore, if your zip file contains a Python file
    # mymodule.py you can import it using:
    # import mymodule
    dataframe_result = run_inventory_simulator(dataframe1)

    # Return value must be of a sequence of pandas.DataFrame
    return dataframe_result

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print('Syntax: python3 inventory_simulator.py <csv_filename>')
        exit()

    thefilename = sys.argv[1]
    x = pd.read_csv(thefilename)
    y = azureml_main(x)

    out_item_id = y.item_id.values.tolist()
    out_inv = y.inv.values.tolist()
    out_purchase_qty = y.purchase_qty.values.tolist()
    out_deliveries = y.deliveries.values.tolist()
    out_lost_sale = y.lost_sale.values.tolist()
    out_expired = y.expired.values.tolist()
    out_sim_date = y.sim_date.values.tolist()

    in_forecast = x['forecast'].values.tolist()
    in_order_day = x['order_day'].values.tolist()
    in_delivery = x['delivery'].values.tolist()

    print('day,item,inv,out,purchaseqty,in,lost,expired,date,order,otherdeliv')
    for i in range(len(out_item_id)):
        print(i,out_item_id[i],out_inv[i],in_forecast[i],out_purchase_qty[i],out_deliveries[i],out_lost_sale[i],out_expired[i],out_sim_date[i], in_order_day[i], in_delivery[i], sep=',')
