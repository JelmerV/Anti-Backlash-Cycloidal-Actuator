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


async def do_torque_ramp(actuator: Actuator, duration, max_torque):
    # ramp up till max torque in either direction 
    ramp_duration = duration/2

    states = []
    succes = True

    try:
        print(f'Ramping to {max_torque} Nm in {ramp_duration} seconds')
        start_time = time.time()
        while True:
            pct_done = (time.time() - start_time) / (ramp_duration)
            if pct_done > 1.0:
                break
            torque = max_torque * pct_done
            result = await actuator.set_position(feedforward_torque=torque, kp_scale=0.0, kd_scale=0.0)
            states.append(actuator.state_to_dict(result, time.time()-abs_start_time))
            
        if states[-1]['FAULT'] != 0:
            print(f'fault code: {states[-1]["FAULT"]}, STOPPING')
            raise Exception('Fault detected')

        #ramp down torque
        print(f'reached max torque, ramping back down')
        start_time = time.time()
        while True:
            pct_done = (time.time() - start_time) / (ramp_duration)
            if pct_done > 1.0:
                break
            torque = max_torque * (1-pct_done)
            result = await actuator.set_position(feedforward_torque=torque, kp_scale=0.0, kd_scale=0.0)
            states.append(actuator.state_to_dict(result, time.time()-abs_start_time))

    except Exception as e:
        print(f'torqueramp failed. Error: {e}')
        succes = False

    finally:
        print(f'Done. stopping motor')
        await actuator.m.set_stop()
            
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
        return
        
    test_df['TORQUE_smooth'] = test_df['TORQUE'].rolling(window=20, center=True).mean()
    return test_df



if __name__ == '__main__':
    test_name = input('Enter test name: ')
    abs_start_time = time.time()

    STORED_DATA = ['POSITION', 'TORQUE', 'CONTROL_TORQUE', 'Q_CURRENT', 'FAULT']	
    actuator = Actuator(1, STORED_DATA)
    all_states = []


    #for safety, configure motion limits
    MAX_DEVIATION = 0.20    
    result = asyncio.run(actuator.set_position())
    cur_pos = actuator.state_to_dict(result)['POSITION']
    print(f'Current position: {cur_pos}, setting bounds to {cur_pos-MAX_DEVIATION} to {cur_pos+MAX_DEVIATION}')
    asyncio.run(actuator.set_position_bounds(cur_pos-MAX_DEVIATION, cur_pos+MAX_DEVIATION))

    # set position to zero
    asyncio.run(actuator.m.set_output_exact(position=0.0))


    # do multiple low torque ramps for the play calculations
    last_max_time = 0
    for i in range(5):
        test_df = torque_ramp_test(actuator, test_duration=8, max_torque=0.2)
        test_df['test_nr'] = i
        all_states.append(test_df)
        print(f'small ramp {i} done')

    # do a high torque ramp for the stiffness calculations
    for i in range(3):
        test_df = torque_ramp_test(actuator, test_duration=20, max_torque=3.0)
        test_df['test_nr'] = i+10
        all_states.append(test_df)
        print(f'large ramp ramp {i} done')
        

    # restore old bounds config
    asyncio.run(actuator.set_position_bounds('nan', 'nan'))


    # store the data
    df = pd.concat(all_states)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'data/{timestamp}_torqueramp_{test_name}.csv'
    print(f'Test done succesful. Saving to {filename}')
    df.to_csv(filename, index=False)

    fig, axs = plt.subplots(2, 1, sharex=True)
    df.plot(x='TIME', y=['TORQUE', 'TORQUE_smooth', 'CONTROL_TORQUE'], ax=axs[0])
    df.plot(x='TIME', y='POSITION', ax=axs[1])

    df['position [deg]'] = df['POSITION'] * 360
    df.plot(x='TORQUE_smooth', y='position [deg]', kind='scatter')
    plt.show()
    
    print('Done')

