import math
import time, datetime

from threading import Thread
import asyncio
from actuator import Actuator



continue_flag = True
async def run_at_speed(actuator, speed, filename):
    print_time = time.time()
    print_interval = 10
    torques = []
    last_torq_avg = 1.0
    test_start_time = time.time()

    direction_change_interfal = 120
    direction_change_time = time.time()
    direction = 1

    print(f'Starting run-in test at {speed} rps, time: {test_start_time}, saving to {filename}')

    with open(filename, 'w') as f:
        result = await actuator.set_position(math.nan, speed, accel_limit=50)
        state = actuator.state_to_dict(result, time.time_ns())
        f.write(';'.join(state.keys()) + '\n')


        while continue_flag:
            if time.time() - direction_change_time > direction_change_interfal:
                direction_change_time = time.time()
                direction *= -1
                print(f'Changing direction to {direction}')
            result = await actuator.set_position(math.nan, speed*direction, accel_limit=2)
            state = actuator.state_to_dict(result, time.time_ns())
            state['DIRECTION'] = direction
            f.write(';'.join(map(str, state.values())) + '\n')
            torques.append(state['TORQUE'] * direction)

            if time.time() - print_time > print_interval:
                torq_avg = sum(torques) / len(torques)
                if last_torq_avg == 0:
                    torq_change = 0
                else:
                    torq_change = (torq_avg-last_torq_avg)/last_torq_avg * 100
                torques = []
                last_torq_avg = torq_avg
                time_elapsed = time.time() - test_start_time
                print(f'Time: {time_elapsed:.1f}s,\t torque_avg: {torq_avg:7.3f},\t torq_change:{torq_change:7.3f}%,\t temp_moteus: {state["TEMPERATURE"]}C, \t temp_motor:~{state["MOTOR_TEMPERATURE"] *0.442 - 1.62:.2f}C')
                print_time = time.time()

    
    await actuator.slow_down()
    await actuator.stop_and_zero()


def start_run_in(actuator, speed, filename):
    asyncio.run(run_at_speed(actuator, speed, filename))


if __name__ == '__main__':
    TOP_SPEED = 0.35
    
    STORED_DATA = ['POSITION', 'VELOCITY', 'TORQUE', 'Q_CURRENT', 'TEMPERATURE', 'MOTOR_TEMPERATURE']	

    test_name = input('Enter test name: ')
    actuator = Actuator(1, STORED_DATA)
    
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d__%H-%M-%S')
    filename = f'test_data/{timestamp}_run-in_{test_name}_{TOP_SPEED}rps.csv'

    # start thread to collect data
    run_in_thread = Thread(target=start_run_in, args=(actuator, TOP_SPEED, filename), daemon=True)  
    run_in_thread.start()

    while True:
        key = input('send q to stop:\n')
        if key == 'q':
            continue_flag = False
            break

    run_in_thread.join()

    print('Run-in test done, saved to', filename)

