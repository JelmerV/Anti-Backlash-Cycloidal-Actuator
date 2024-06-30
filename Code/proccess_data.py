
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


test_data = {
    'conic initial': [ (
            'test_data/2024-06-27__14-15-42__torqueramp__conic init 1.csv',
            'test_data/2024-06-27__14-22-03__torqueramp__conic init 2.csv',
            'test_data/2024-06-27__14-27-14__torqueramp__conic init 3.csv',
            'test_data/2024-06-27__14-36-29__torqueramp__conic init 4.csv',
            'test_data/2024-06-27__14-41-07__torqueramp__conic init 5.csv',
            'test_data/2024-06-27__14-45-53__torqueramp__conic init 6.csv',
            'test_data/2024-06-27__14-50-50__torqueramp__conic init 7.csv',
            'test_data/2024-06-27__14-55-34__torqueramp__conic init 8.csv',
            'test_data/2024-06-27__15-01-01__torqueramp__conic init 9.csv',
        ), 'test_data/06-27_15-11-19_speedramp_conic init_240s_1.0rps.csv'],
}



def average_test_repetitions(df):
    data = []
    grouped = df.groupby('test_nr')

    for name, group in grouped:
        group = group.drop('test_nr', axis=1)
        group.index = group.index - group.index[0]

        old_len = len(group)
        group = group.resample('0.5ms').mean()
        group = group.interpolate(method='time')
        # print(f'test {name} resampled from {old_len} to {len(group)} samples')

        data.append(group.values)

    # get consistent length
    min_len = min([len(d) for d in data])
    data = [d[:min_len] for d in data]
    # print(f'setting everything to {min_len} samples')

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

    # print(f'Sample rate: {1/(df["Time [s]"].diff().mean())} Hz')
    df['Time [s]'] = pd.to_datetime(df['Time [s]'], unit='s')
    df.set_index('Time [s]', inplace=True)


    print(f"Test output orientation: {df['Deflection [deg]'].mean()} deg")
    df['Deflection [deg]'] -= df['Deflection [deg]'].mean()

    
    TEST_NR_OFFSET = 100
    play_tests = df[df['test_nr'] < TEST_NR_OFFSET].copy()
    stiffness_tests = df[df['test_nr'] >= TEST_NR_OFFSET].copy()
    stiffness_tests['test_nr'] = stiffness_tests['test_nr'] - TEST_NR_OFFSET

    play_test_mean = average_test_repetitions(play_tests)
    stiffness_test_mean = average_test_repetitions(stiffness_tests)


    return play_test_mean, stiffness_test_mean


def load_speeddata(filename):
    print(f'prepping {filename}')
    df_raw = pd.read_csv(filename)

    df = pd.DataFrame()
    df['Time [s]'] = df_raw['TIME']
    df['Motor Speed [rpm]'] = df_raw['VELOCITY']
    df['Motor Torque [Nm]'] = df_raw['TORQUE']

    print(f'Sample rate: {1/(df["Time [s]"].diff().mean())} Hz')
    df['Time [s]'] = pd.to_datetime(df['Time [s]'], unit='s')
    df.set_index('Time [s]', inplace=True)

    return df


if __name__ == '__main__':
    for test_name, (torque_files, speed_file) in test_data.items():
        print(f'Processing {test_name}')

        fig, axs = plt.subplots(1, 2, figsize=(13, 6))
        colors = plt.cm.viridis(np.linspace(0, 1, len(torque_files)))
        for i, torque_file in enumerate(torque_files):
            play_test, stiffness_test = load_torquedata(torque_file)

            ############### analyse play and stiffness ###############
            def get_rising_slopes(df):
                # split data in to positive and negative slopes. remove the hysteresis part
                max_torque_idx = df['Desired Torque [Nm]'].idxmax()
                pos_slope = df.loc[:max_torque_idx]

                # find zero crossing of desired torque
                min_torque_idx = df['Desired Torque [Nm]'].idxmin()
                zero_torque_idx = df['Desired Torque [Nm]'][max_torque_idx:min_torque_idx].abs().idxmin()
                neg_slope = df.loc[zero_torque_idx:min_torque_idx]

                return pos_slope, neg_slope


            # estimate play
            play_pos_slope, play_neg_slope = get_rising_slopes(play_test)
            pos_play = play_pos_slope['Deflection [deg]'].iloc[0]
            neg_play = play_neg_slope['Deflection [deg]'].iloc[0]
            print(f'Play: {neg_play-pos_play} deg ({pos_play} pos, {neg_play} neg)')


            # estimate stiffness
            stiffness_pos_slope, stiffness_neg_slope = get_rising_slopes(stiffness_test)
            stiffness_pos_slope = stiffness_pos_slope[stiffness_pos_slope['Deflection [deg]'] > neg_play]
            stiffness_neg_slope = stiffness_neg_slope[stiffness_neg_slope['Deflection [deg]'] < pos_play]

            # do polyfit
            pos_stifness, pos_offset = np.polyfit(stiffness_pos_slope['Motor Torque [Nm]'], stiffness_pos_slope['Deflection [deg]'], 1)
            neg_stifness, neg_offset  = np.polyfit(stiffness_neg_slope['Motor Torque [Nm]'], stiffness_neg_slope['Deflection [deg]'], 1)

            print(f'Positive stiffness: {pos_stifness} deg/Nm, offset: {pos_offset} deg')
            print(f'Negative stiffness: {neg_stifness} deg/Nm, offset: {neg_offset} deg')

            ##################################

            axs[0].plot(play_test['Motor Torque [Nm]'], play_test['Deflection [deg]'], label=f'play test {i}', color=colors[i])
            axs[1].plot(stiffness_test['Motor Torque [Nm]'], stiffness_test['Deflection [deg]'], label=f'stiffness test {i}', color=colors[i])

        for ax in axs:
            ax.legend()
            ax.set_xlabel('Motor Torque [Nm]')
            ax.set_ylabel('Deflection [deg]')


        speed_data = load_speeddata(speed_file)

        fig, axs = plt.subplots(1, 1, figsize=(10, 10))
        axs.plot(speed_data['Motor Speed [rpm]'], speed_data['Motor Torque [Nm]'])



        plt.show()
        print('done')