'''
Do a slow torque ramp towards a small position change. Used to estimate internal play and stiffness
'''

import time, datetime
import math
from threading import Thread

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import asyncio
from actuator import Actuator
import socket
import array

MINI_40_IP = "192.168.1.1"
MINI_40_PORT = 49152
MINI_40_STARTMSG = b'\x12\x34\x00\x00\x00\x02\x00\x00\x00\x00' # Standard header 0x1234, Command 0x00000002 (2), Number of samples 0x00000000 (0) see sect 9.1 user manual NET F/T

poll_mini40 = True
mini40_data = []

def collect_mini40_data():
    # Start socket
    print('Starting Mini40 polling')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(MINI_40_STARTMSG, (MINI_40_IP, MINI_40_PORT))

    global poll_mini40, mini40_data
    while poll_mini40:
        # Request dat from latest packet
        data, addr = sock.recvfrom(1024)
        state = [time.monotonic_ns()]  # add timestamp

        # 'header info'
        state.append(int.from_bytes(data[0:4], byteorder='big', signed=False))             #0-3         |   rdt_sequence        |   unsigned 32 bit integer
        state.append(int.from_bytes(data[4:8], byteorder='big', signed=False))             #4-7         |   ft_sequence         |   unsigned 32 bit integer
        state.append(int.from_bytes(data[8:12], byteorder='big', signed=False))            #8-11        |   status              |   unsigned 32 bit integer
        # Force X,Y,Z
        state.append(int.from_bytes(data[12:16], byteorder='big', signed=True))             #12-15       |   Force, X-dir        |   signed 32 bit integer
        state.append(int.from_bytes(data[16:20], byteorder='big', signed=True))             #16-19       |   Force, Y-dir        |   signed 32 bit integer
        state.append(int.from_bytes(data[20:24], byteorder='big', signed=True))             #20-23       |   Force, Z-dir        |   signed 32 bit integer
        # Torque X,Y,Z
        state.append(int.from_bytes(data[24:28], byteorder='big', signed=True))            #24-27       |   Torque, X-dir       |   signed 32 bit integer
        state.append(int.from_bytes(data[28:32], byteorder='big', signed=True))            #28-31       |   Torque, Y-dir       |   signed 32 bit integer
        state.append(int.from_bytes(data[32:36], byteorder='big', signed=True))            #32-35       |   Torque, Z-dir       |   signed 32 bit integer

        mini40_data.append(state)

    print('Mini40 polling stopped')
    

async def do_torque_ramp(actuator: Actuator, duration, max_torque):
    # ramp up till max torque in either direction 
    ramp_duration = duration/2

    states = []
    succes = True

    try:
        print(f'Ramping to {max_torque} Nm in {ramp_duration} seconds.', end=' ', flush=True)
        start_time = time.monotonic_ns()
        while True:
            pct_done = (time.monotonic_ns() - start_time) / (ramp_duration)
            if pct_done > 1.0:
                break
            torque = max_torque * pct_done
            result = await actuator.set_position(feedforward_torque=torque, kp_scale=0.0, kd_scale=0.0)
            states.append(actuator.state_to_dict(result, time.perf_counter()))
            
        if states[-1]['FAULT'] != 0:
            print(f'fault code: {states[-1]["FAULT"]}, STOPPING')
            raise Exception('Fault detected')

        #ramp down torque
        print(f'and back down', end=' ', flush=True)
        start_time = time.monotonic_ns()
        while True:
            pct_done = (time.monotonic_ns() - start_time) / (ramp_duration)
            if pct_done > 1.0:
                break
            torque = max_torque * (1-pct_done)
            result = await actuator.set_position(feedforward_torque=torque, kp_scale=0.0, kd_scale=0.0)
            states.append(actuator.state_to_dict(result, time.perf_counter()))

    except Exception as e:
        print(f'torqueramp failed. Error: {e}')
        succes = False

    finally:
        print(f'Done. stopping motor')
        # await actuator.m.set_stop()
            
        return succes, states
    

def main():
    global poll_mini40, mini40_data

    ramp_duration = 5.0
    max_torque = 1.0


    STORED_DATA = ['POSITION', 'TORQUE', 'CONTROL_TORQUE', 'Q_CURRENT', 'FAULT']
    actuator = Actuator(actuator_id=1, stored_data=STORED_DATA)
    
    # set position to zero
    asyncio.run(actuator.m.set_output_nearest(position=0.0))

    #for safety, configure motion limits
    MAX_DEVIATION = 0.10    
    result = asyncio.run(actuator.set_position())
    cur_pos = actuator.state_to_dict(result)['POSITION']
    print(f'Current position: {cur_pos}, setting bounds to {cur_pos-MAX_DEVIATION} to {cur_pos+MAX_DEVIATION}')
    asyncio.run(actuator.set_position_bounds(cur_pos-MAX_DEVIATION, cur_pos+MAX_DEVIATION))
    
    # initialize start time
    abs_start_time = time.monotonic_ns()


    # start force measurements
    mini40_thread = Thread(target=collect_mini40_data)
    mini40_thread.start()

    # do torque ramp
    succes, states = asyncio.run(do_torque_ramp(actuator, ramp_duration, max_torque))

    # stop mini 40 thread
    poll_mini40 = False
    mini40_thread.join()

    
    # stop and restore old bounds config
    asyncio.run(actuator.m.set_stop())
    asyncio.run(actuator.set_position_bounds('nan', 'nan'))
    

    # data to dfs
    columns = ['TIME', 'RDT_SEQUENCE', 'FT_SEQUENCE', 'STATUS', 'FORCE_X', 'FORCE_Y', 'FORCE_Z', 'TORQUE_X', 'TORQUE_Y', 'TORQUE_Z']
    mini40_df = pd.DataFrame(mini40_data, columns=columns)
    mini40_df['TIME'] = mini40_df['TIME'] - abs_start_time
     
    states_df = pd.DataFrame(states)
    states_df['TIME'] = states_df['TIME'] - abs_start_time



    # store the data
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d__%H-%M-%S')
    filename = f'test_data/{timestamp}__torqueconstant'
    print(f'Test done succesful. Saving to {filename}_$.csv')
    mini40_df.to_csv(f'{filename}_mini40.csv', index=False)
    states_df.to_csv(f'{filename}_actuator.csv', index=False)






if __name__ == '__main__':
    main()

