import math
import time, datetime

from threading import Thread
import asyncio
from actuator import Actuator



continue_flag = True
async def run_at_speed(actuator, speed, filename):
    print_time = time.time()
    print_interval = 5
    torques = []
    last_torq_avg = 1.0

    with open(filename, 'w') as f:
        result = await actuator.set_position(math.nan, speed, accel_limit=50)
        state = actuator.state_to_dict(result, time.time_ns())
        f.write(';'.join(state.keys()) + '\n')


        while continue_flag:
            result = await actuator.set_position(math.nan, speed, accel_limit=50)
            state = actuator.state_to_dict(result, time.time_ns())
            f.write(';'.join(map(str, state.values())) + '\n')
            torques.append(state['TORQUE'])

            if time.time() - print_time > print_interval:
                torq_avg = sum(torques) / len(torques)
                torq_change = (torq_avg-last_torq_avg)/last_torq_avg * 100
                torques = []
                last_torq_avg = torq_avg
                print(f'torque: {state["TORQUE"]:.3f},\t torque_avg: {torq_avg:.3f},\t torq_change:{torq_change:7.4f}%,\t temp_moteus: {state["TEMPERATURE"]}C, \t temp_motor: {state["MOTOR_TEMPERATURE"]:.3f}?')
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
    
    timestamp = datetime.datetime.now().strftime('%m-%d_%H-%M-%S')
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

