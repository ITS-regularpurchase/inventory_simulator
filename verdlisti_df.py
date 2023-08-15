import pandas as pd
import numpy as np
import streamlit as st
# from string import replace

class verdlisti():
    def __init__(self) -> None:
        cols = list(pd.read_csv('data/verdlisti.csv', sep=';', nrows=1))
        self.df = pd.read_csv('data/verdlisti.csv', sep=';', decimal=',', usecols=[i for i in cols if i != 'SPQ'])
        
        
    def change_currency(self, currency: str) -> pd.DataFrame:
        """Changes the currency of all prices in dataframe"""
        exchange_rate = {'ISK': 140, 'USD': 1.0723, 'EUR': 0.94}
        
        if currency == 'USD':
            self.df['Currency'], self.df['Price'] = currency, np.where(self.df['Currency'] == currency, self.df['Price'], np.round(pd.to_numeric(self.df['Price'].str.replace(',','.')) * exchange_rate[currency], 2))
        elif currency == 'EUR':
            self.df['Currency'], self.df['Price'] = currency, np.where(self.df['Currency'] == currency, self.df['Price'], np.round(pd.to_numeric(self.df['Price'].str.replace(',','.')) * exchange_rate[currency], 2))
        return self.df
    
    def sort_by_price(self, amount:int) -> pd.DataFrame:
        """Sorts values by price"""
        self.df = self.df.sort_values(by='Price', ascending=False).head(int(amount))
        return self.df
    
    def show_only(self, vendor) -> pd.DataFrame:
        """Shows only selected vendor"""
        if vendor != 'All':
            self.df = self.df[self.df['Vendor'] == vendor]
        return self.df
    
    def __repr__(self) -> str:
        return self.df.__repr__()