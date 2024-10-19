
import time, datetime
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import asyncio
from actuator import Actuator


async def record_trajectory(actuator, commands):
    states = []
    start_time = time.monotonic_ns()
    for i, command in enumerate(commands):
        count = 2
        print(f'Command {i+1}/{len(commands)}: {command}')
        while True:

            result = await actuator.set_position(**command)
            state = actuator.state_to_dict(result, time.monotonic_ns())
            states.append(state)

            if state['FAULT'] != 0:
                print(f'Fault detected: {state["FAULT"]}')
                df = pd.DataFrame(states)
                return df
            
            count = max(0, count-1)
            if count == 0:
                if state['TRAJECTORY_COMPLETE']:
                    break

            await asyncio.sleep(0.001)
    
    await actuator.slow_down()
    await actuator.m.set_stop()
    # await actuator.stop_and_zero()

    df = pd.DataFrame(states)
    return df


if __name__ == '__main__':
    print('Starting Trajectory test')
    test_name = input('Enter name: ')

    STORED_DATA = [ 'POSITION', 'CONTROL_POSITION', 'COMMAND_POSITION',
                    'VELOCITY', 'CONTROL_VELOCITY', 'COMMAND_VELOCITY',
                    'TORQUE', 'CONTROL_TORQUE', 'Q_CURRENT',
                    'FAULT', 'TRAJECTORY_COMPLETE',
                    'TEMPERATURE', 'MOTOR_TEMPERATURE',

    ]
    actuator = Actuator(stored_data=STORED_DATA)


    # generate trajectory waypoint commands
    commands = [{'position': 0.0, 'velocity': 0.0, 'accel_limit': 0.5,  'velocity_limit': 1.0}]
    pos_offset = -0.6

    # max_velocity = 1.6
    # for accel in [1.0, 3.0, 6.0, 8.0, 10, 12, 14, 16]:
    #     for pos in [0.0, 0.07, 0.14, 0.21, 0.35, 0.5, 0.7, 0.0, 0.4, 0.0]:
    max_velocity = 1.1
    for accel in [1.0, 3.0, 6.0, 8.0, 10, 1.0]:
        for pos in [0.0, 0.07, 0.14, 0.21, 0.5, 0.2, 0.4, 0.0]:
            commands.append({
                'position': pos+pos_offset,
                'velocity': 0.0, 
                'accel_limit': accel,  
                'velocity_limit': max_velocity
            })
    commands.append({'position': 0.0, 'velocity': 0.0, 'accel_limit': 0.5,  'velocity_limit': 1.0})

    # record trajectory
    df = asyncio.run(record_trajectory(actuator, commands))
    df['TIME'] = (df['TIME'] - df['TIME'].iloc[0]) / 1e9
    
    # save data
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d__%H-%M-%S')
    filename = f'test_data/{timestamp}_trajectory_{test_name}.csv'
    print(f'Saving data to {filename}')
    df.to_csv(filename, index=False)

    print(f'Done, datarate was {len(df)/df["TIME"].iloc[-1]:.2f} Hz')

    # plot
    fig, ax = plt.subplots(4, 1, figsize=(10, 14), sharex=True)
    df.plot(x='TIME', y=['POSITION', 'COMMAND_POSITION', 'CONTROL_POSITION'], ax=ax[0])
    df.plot(x='TIME', y=['VELOCITY', 'COMMAND_VELOCITY', 'CONTROL_VELOCITY'], ax=ax[1])
    df.plot(x='TIME', y=['TORQUE', 'CONTROL_TORQUE'], ax=ax[2])
    df.plot(x='TIME', y=['Q_CURRENT'], ax=ax[3])
    # df.plot(x='TIME', y=['TEMPERATURE', 'MOTOR_TEMPERATURE'], ax=ax[4])

    plt.show()


