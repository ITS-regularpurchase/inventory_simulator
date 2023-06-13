import pandas as pd

class data_import:
    def __init__(self, file_name):
        self.data_frame = self.import_csv(file_name)

    def import_csv(self, file_name):
        df = pd.read_csv(file_name+'.csv')
        return df