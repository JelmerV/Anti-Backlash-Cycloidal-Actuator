
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


test_data = {
    'Baseline initial': ('test_data/speedramp_baseline_initial.csv', 'test_data/torqueramp_baseline_initial.csv'),
    'Baseline run-in': ('test_data/speedramp_baseline_final.csv', 'test_data/torqueramp_baseline_final.csv'),
}



def average_data(df):
    data = []
    grouped = df.groupby('test_nr')

    for name, group in grouped:
        group = group.drop('test_nr', axis=1)
        group.index = group.index - group.index[0]

        old_len = len(group)
        group = group.resample('0.5ms').mean()
        group = group.interpolate(method='time')
        print(f'test {name} resampled from {old_len} to {len(group)} samples')

        data.append(group.values)

    # get consistent length
    min_len = min([len(d) for d in data])
    data = [d[:min_len] for d in data]
    print(f'setting everything to {min_len} samples')

    # average data using numpy
    data_mean = np.mean(np.array(data), axis=0)

    new_columns = df.columns.drop('test_nr')
    mean_df = pd.DataFrame(data_mean, columns=new_columns)

    # smooth data
    mean_df = mean_df.rolling(window=100, center=True).mean()
    mean_df = mean_df.bfill().ffill()

    return mean_df


def load_torquedata(filename):
    print(f'prepping {filename}')
    df_raw = pd.read_csv(filename)

    df = pd.DataFrame()
    df['Time [s]'] = df_raw['TIME']
    df['Motor Torque [Nm]'] = df_raw['TORQUE']
    df['Deflection [deg]'] = df_raw['POSITION'] * 360
    df['Desired Torque [Nm]'] = df_raw['CONTROL_TORQUE']
    df['Q_current/5'] = df_raw['Q_CURRENT']/5
    df['test_nr'] = df_raw['test_nr']

    print(f'Sample rate: {1/(df["Time [s]"].diff().mean())} Hz')
    df['Time [s]'] = pd.to_datetime(df['Time [s]'], unit='s')
    df.set_index('Time [s]', inplace=True)


    print(f"Test output orientation: {df['Deflection [deg]'].mean()} deg")
    df['Deflection [deg]'] -= df['Deflection [deg]'].mean()

    
    TEST_NR_OFFSET = 100
    play_tests = df[df['test_nr'] < TEST_NR_OFFSET].copy()
    stiffness_tests = df[df['test_nr'] >= TEST_NR_OFFSET].copy()
    stiffness_tests['test_nr'] = stiffness_tests['test_nr'] - TEST_NR_OFFSET

    play_test_mean = average_data(play_tests)
    stiffness_test_mean = average_data(stiffness_tests)


    return play_test_mean, stiffness_test_mean


def load_speeddata(filename):
    print(f'prepping {filename}')
    df_raw = pd.read_csv(filename)

    df = pd.DataFrame()
    df['Time [s]'] = df_raw['TIME']
    df['Motor Speed [rpm]'] = df_raw['SPEED']
    df['Motor Torque [Nm]'] = df_raw['TORQUE']

    print(f'Sample rate: {1/(df["Time [s]"].diff().mean())} Hz')
    df['Time [s]'] = pd.to_datetime(df['Time [s]'], unit='s')
    df.set_index('Time [s]', inplace=True)

    return df