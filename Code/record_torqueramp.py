'''
Do a slow torque ramp towards a small position change. Used to estimate internal play and stiffness
'''

import time, datetime
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import asyncio
from actuator import Actuator

abs_start_time = time.monotonic_ns()

async def do_torque_ramp(actuator: Actuator, duration, max_torque):
    # ramp up till max torque in either direction 
    ramp_duration = duration/2

    states = []
    succes = True

    try:
        print(f'Ramping to {max_torque} Nm in {ramp_duration} seconds.', end=' ', flush=True)
        start_time = time.monotonic_ns()
        while True:
            pct_done = (time.monotonic_ns() - start_time) / (ramp_duration*1e9)
            if pct_done > 1.0:
                break
            torque = max_torque * pct_done
            result = await actuator.set_position(feedforward_torque=torque, kp_scale=0.0, kd_scale=0.0)
            states.append(actuator.state_to_dict(result, time.monotonic_ns()))
            
        if states[-1]['FAULT'] != 0:
            print(f'fault code: {states[-1]["FAULT"]}, STOPPING')
            raise Exception('Fault detected')

        #ramp down torque
        print(f'\tand back down', end=' ', flush=True)
        start_time = time.monotonic_ns()
        while True:
            pct_done = (time.monotonic_ns() - start_time) / (ramp_duration*1e9)
            if pct_done > 1.0:
                break
            torque = max_torque * (1-pct_done)
            result = await actuator.set_position(feedforward_torque=torque, kp_scale=0.0, kd_scale=0.0)
            states.append(actuator.state_to_dict(result, time.monotonic_ns()))

    except Exception as e:
        print(f'torqueramp failed. Error: {e}')
        succes = False

    finally:
        print(f'\tDone. stopping motor')
        # await actuator.m.set_stop()
            
        return succes, states
    

def torque_ramp_test(actuator: Actuator, test_duration, max_torque):
    ramp_duration = test_duration/2
    pos_succes, pos_states = asyncio.run(do_torque_ramp(actuator, ramp_duration, max_torque))
    test_df = pd.DataFrame(pos_states)
    if pos_succes:
        neg_succes, neg_states = asyncio.run(do_torque_ramp(actuator, ramp_duration, -max_torque))
        test_df = pd.concat([test_df, pd.DataFrame(neg_states)])
    
    if not pos_succes or not neg_succes:
        print('Ramp failed')
        test_df.plot(x='TIME', y='TORQUE')
        plt.show()
        exit()
        
    # test_df['TORQUE_smooth'] = test_df['TORQUE'].rolling(window=20, center=True).mean()
    return test_df



if __name__ == '__main__':    
    PLAY_TEST_TORQUE = 4.0          # Nm at output
    PLAY_TEST_DURATION = 4.0
    PLAY_TEST_REPETITIONS = 5

    STIFFNESS_TEST_TORQUE = 40.0          # Nm at output
    STIFFNESS_TEST_DURATION = 20.0
    STIFFNESS_TEST_REPETITIONS = 3

    STORED_DATA = ['POSITION', 'TORQUE', 'CONTROL_TORQUE', 'Q_CURRENT', 'FAULT']


    print('\nStarting torque ramp test')
    print(f'play test: {PLAY_TEST_TORQUE}Nm, {PLAY_TEST_DURATION}s, {PLAY_TEST_REPETITIONS} repetitions')
    print(f'stiffness test: {STIFFNESS_TEST_TORQUE}Nm, {STIFFNESS_TEST_DURATION}s, {STIFFNESS_TEST_REPETITIONS} repetitions')
    print('')
    test_name = input('Enter test name: ')

    if test_name == '':
        print('No test name given, exiting')
        exit()


    # initialize actuator
    actuator = Actuator(actuator_id=1, stored_data=STORED_DATA)

    # set position to zero
    asyncio.run(actuator.m.set_output_nearest(position=0.0))

    #for safety, configure motion limits
    MAX_DEVIATION = 0.015    # measured in output revolutions    
    result = asyncio.run(actuator.set_position())
    asyncio.run(actuator.m.set_stop())
    cur_pos = actuator.state_to_dict(result)['POSITION']
    print(f'Current position: {cur_pos}, setting bounds to {cur_pos-MAX_DEVIATION} to {cur_pos+MAX_DEVIATION}')
    asyncio.run(actuator.set_position_bounds(cur_pos-MAX_DEVIATION, cur_pos+MAX_DEVIATION))


    # move to a repeatable position:
    succes, states = asyncio.run(do_torque_ramp(actuator, duration=1.0, max_torque=-PLAY_TEST_TORQUE))
    if not succes:
        print('Failed to move to repeatable position, is output fixed?')
        exit()


    abs_start_time = time.monotonic_ns()
    all_states = []

    # do multiple low torque ramps for the play calculations
    last_max_time = 0
    for i in range(PLAY_TEST_REPETITIONS):
        test_df = torque_ramp_test(actuator, test_duration=PLAY_TEST_DURATION, max_torque=PLAY_TEST_TORQUE)
        test_df['test_nr'] = i
        all_states.append(test_df)
        print(f'small ramp {i} done')

    # do a high torque ramp for the stiffness calculations
    for i in range(STIFFNESS_TEST_REPETITIONS):
        test_df = torque_ramp_test(actuator, test_duration=STIFFNESS_TEST_DURATION, max_torque=STIFFNESS_TEST_TORQUE)
        test_df['test_nr'] = i+100
        all_states.append(test_df)
        print(f'large ramp ramp {i} done')
        

    # stop and restore old bounds config
    asyncio.run(actuator.m.set_stop())
    asyncio.run(actuator.set_position_bounds('nan', 'nan'))


    # store the data
    df = pd.concat(all_states)
    df['TIME'] = (df['TIME'] - abs_start_time) / 1e9

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d__%H-%M-%S')
    filename = f'test_data/{timestamp}__torqueramp__{test_name}.csv'
    print(f'Test done succesful. Saving to {filename}')
    df.to_csv(filename, index=False)

    # fig, axs = plt.subplots(2, 1, sharex=True)
    # df.plot(x='TIME', y=['TORQUE', 'CONTROL_TORQUE'], ax=axs[0])
    # df.plot(x='TIME', y='POSITION', ax=axs[1])

    # df['position [deg]'] = df['POSITION'] * 360
    # df.plot(x='TORQUE', y='position [deg]', kind='scatter')
    # plt.show()
    
    print('Done')

