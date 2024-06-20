'''
Do a (very) slow speed ramp and record torque. Used to estimate friction
'''

import time, datetime
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import asyncio
from actuator import Actuator

async def do_speed_ramp(actuator, duration, max_speed):
    # ramp up and down till max speed, then opositre direction

    accel = max_speed / (duration/4)

    states = []
    start_time = time.time()
    speed = max_speed

    print_progress = 0.1

    while True:
        pct_done = (time.time() - start_time) / duration
        if pct_done > 0.25:
            speed = -max_speed
        if pct_done > 0.75:
            speed = 0.0
        if pct_done > 1.0:
            break
        if pct_done > print_progress:
            print(f'{pct_done*100:.0f}% done')
            print_progress += 0.1
        result = await actuator.set_position(math.nan, speed, accel_limit=accel)
        states.append(actuator.state_to_dict(result, time.time()-start_time))

    
    await actuator.slow_down()
    await actuator.stop_and_zero()

    return pd.DataFrame(states)

if __name__ == '__main__':
    TEST_DURATION = 4*60
    TOP_SPEED = 12.0
    
    STORED_DATA = ['POSITION', 'VELOCITY', 'TORQUE', 'Q_CURRENT']	

    test_name = input('Enter test name: ')
    actuator = Actuator(1, STORED_DATA)
    df = asyncio.run(do_speed_ramp(actuator, TEST_DURATION, TOP_SPEED))
    print(f'Done, datarate was {len(df)/TEST_DURATION:.2f} Hz')

    timestamp = datetime.datetime.now().strftime('%m-%d_%H-%M-%S')
    filename = f'test_data/{timestamp}_speedramp_{test_name}_{TEST_DURATION}s_{TOP_SPEED}rps.csv'
    print(f'Saving data to {filename}')
    df.to_csv(filename, index=False)
    df.plot(x='TIME', y=['TORQUE', 'Q_CURRENT'])
    df.plot(x='TIME', y='VELOCITY')
    df.plot(x='VELOCITY', y='TORQUE', kind='scatter')
    plt.show()
    
    
