'''
Do a slow torque ramp towards a small position change. Used to estimate internal play and stiffness
'''

import time, datetime
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import threading

import asyncio
from actuator import Actuator

abs_start_time = time.monotonic_ns()
e_stop = False

async def do_torque_ramp(actuator: Actuator, duration, max_torque):
    # ramp up till max torque in either direction 
    ramp_duration = duration/2

    states = []
    succes = True

    try:
        print(f'Ramping to {max_torque} Nm in {ramp_duration} seconds.', end=' ', flush=True)
        start_time = time.monotonic_ns()
        while not e_stop:
            pct_done = (time.monotonic_ns() - start_time) / (ramp_duration*1e9)
            if pct_done > 1.0:
                break
            torque = max_torque * pct_done
            result = await actuator.set_position(feedforward_torque=torque, kp_scale=0.0, kd_scale=0.0, velocity_limit=0.5)
            states.append(actuator.state_to_dict(result, time.monotonic_ns()))
            await asyncio.sleep(0.001)
            
        if states[-1]['FAULT'] != 0:
            print(f'fault code: {states[-1]["FAULT"]}, STOPPING')
            raise Exception('Fault detected')

        #ramp down torque
        print(f'\tand back down', end=' ', flush=True)
        start_time = time.monotonic_ns()
        while not e_stop:
            pct_done = (time.monotonic_ns() - start_time) / (ramp_duration*1e9)
            if pct_done > 1.0:
                break
            torque = max_torque * (1-pct_done)
            result = await actuator.set_position(feedforward_torque=torque, kp_scale=0.0, kd_scale=0.0, velocity_limit=0.02)
            states.append(actuator.state_to_dict(result, time.monotonic_ns()))
            await asyncio.sleep(0.001)

    except Exception as e:
        print(f'torqueramp failed. Error: {e}')
        succes = False

    finally:
        if e_stop:
            print(f'Emergency stop detected, stopping motor')
            succes = False
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
        asyncio.run(actuator.m.set_stop())
        asyncio.run(actuator.set_position_bounds('nan', 'nan'))

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d__%H-%M-%S')
        filename = f'test_data/{timestamp}__torquerampfailed__{test_name}.csv'
        test_df.to_csv(filename, index=False)

        print(f'Ramp failed, still saved data to {filename}')
        test_df.plot(x='TIME', y='TORQUE')
        plt.show()
        exit()
        
    # test_df['TORQUE_smooth'] = test_df['TORQUE'].rolling(window=20, center=True).mean()
    return test_df


def e_stop_detector():
    global e_stop
    while True:
        inp = input('type q to stop: ')
        if inp == 'q':
            e_stop = True
            break
        time.sleep(0.05)
    


if __name__ == '__main__':
    STIFFNESS_TEST_TORQUE = 120.0          # Nm at output
    STIFFNESS_TEST_DURATION = 10.0
    STIFFNESS_TEST_REPETITIONS = 2

    # STORED_DATA = ['POSITION', 'TORQUE', 'CONTROL_TORQUE', 'Q_CURRENT', 'FAULT', 
    STORED_DATA = [ 'POSITION', 'TORQUE', 'CONTROL_TORQUE', 'Q_CURRENT',
                    'FAULT', 'TRAJECTORY_COMPLETE',
                    'TEMPERATURE', 'MOTOR_TEMPERATURE',
    ]


    print('\nStarting torque ramp test')
    print(f'torque test: {STIFFNESS_TEST_TORQUE}Nm, {STIFFNESS_TEST_DURATION}s, {STIFFNESS_TEST_REPETITIONS} repetitions')
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
    MAX_DEVIATION = 0.3    # measured in output revolutions    
    result = asyncio.run(actuator.set_position())
    asyncio.run(actuator.m.set_stop())
    cur_pos = actuator.state_to_dict(result)['POSITION']
    print(f'Current position: {cur_pos}, setting bounds to {cur_pos-MAX_DEVIATION} to {cur_pos+MAX_DEVIATION}')
    asyncio.run(actuator.set_position_bounds(cur_pos-MAX_DEVIATION, cur_pos+MAX_DEVIATION))


    #start emergency stop
    e_stop_thread = threading.Thread(target=e_stop_detector, daemon=True)
    e_stop_thread.start()


    # move to a repeatable position:
    succes, states = asyncio.run(do_torque_ramp(actuator, duration=2.0, max_torque=-3.0))
    if not succes:
        print('Failed to move to repeatable position, is output fixed?')
        exit()

    print('Starting tests\n')
    abs_start_time = time.monotonic_ns()
    all_states = []

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


    df['MOTOR_TEMPERATURE'] = df['MOTOR_TEMPERATURE'] * 0.442 - 1.62

    # plot
    fig, ax = plt.subplots(4, 1, figsize=(10, 14), sharex=True)
    df.plot(x='TIME', y=['POSITION'], ax=ax[0])
    df.plot(x='TIME', y=['TORQUE', 'CONTROL_TORQUE'], ax=ax[1])
    df.plot(x='TIME', y=['Q_CURRENT'], ax=ax[2])
    df.plot(x='TIME', y=['TEMPERATURE', 'MOTOR_TEMPERATURE'], ax=ax[3])

    plt.show()
    
    print('Done')

