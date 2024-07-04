import time, datetime
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import sys

test_files = [
    'test_data/07-04_11-18-44_run-in_split pinwheel_0.5rps.csv',
    'test_data/07-04_11-21-43_run-in_split pinwheel_0.5rps.csv',
    'test_data/07-04_11-26-47_run-in_split pinwheel_0.5rps.csv',
    'test_data/07-04_11-31-57_run-in_split_0.5rps.csv',
    'test_data/07-04_11-32-24_run-in_split_0.5rps.csv',
    'test_data/07-04_11-35-13_run-in_split_0.5rps.csv',
    'test_data/07-04_11-34-18_run-in_split_0.5rps.csv',
    'test_data/07-04_11-42-45_run-in_split_0.5rps.csv',
]

def read_file(filename):
    df = pd.read_csv(filename, sep=';')
    df['TIME'] = pd.to_datetime(df['TIME'] / 1e9, unit='s')
    df['TIME'] = df['TIME'] - df['TIME'][0]
    df.set_index('TIME', inplace=True)
    
    df.drop(['POSITION',], inplace=True, axis=1)
    df['MOTOR_TEMPERATURE'] = df['MOTOR_TEMPERATURE'] * 0.65 - 20
    return df

df = read_file(test_files[0])
for filename in test_files[1:]:
    df2 = read_file(filename)
    df2.index = df2.index + df.index[-1] + pd.Timedelta(1, unit='ms')
    df = pd.concat([df, df2])
    
df['TORQUE_smooth'] = df['TORQUE'].rolling(500, center=True).mean()
print(df.columns)
df.plot()
plt.show()
# input('Press enter to continue')
