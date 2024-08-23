
import math
import asyncio
import moteus
import time


STORED_DATA = {
    'POSITION',  'COMMAND_POSITION', 'CONTROL_POSITION',
    'VELOCITY', 'COMMAND_VELOCITY', 'CONTROL_VELOCITY',
    'TORQUE', 'Q_CURRENT'
}


class Actuator:
    def __init__(self, actuator_id=1, stored_data=STORED_DATA, qr=None):
        self.stored_data = stored_data
        self.m = self.start_actuator(actuator_id)
        self.s = moteus.Stream(self.m, verbose=True)

        asyncio.run(self.store_old_config())


    def prep_query_resolution(self, stored_data=None):
        if stored_data is None:
            stored_data = self.stored_data.copy()

        qr = moteus.QueryResolution()

        if 'TRAJECTORY_COMPLETE' in stored_data:
            qr.trajectory_complete = moteus.INT8            

        for attr in dir(qr):
            if attr.startswith('_'):
                continue
            if attr.upper() in stored_data:
                if getattr(qr, attr) == moteus.IGNORE:
                    setattr(qr, attr, moteus.F32)
                stored_data.remove(attr.upper())
            else:
                setattr(qr, attr, moteus.IGNORE)

        for register in stored_data:
            qr._extra[moteus.Register[register]] = moteus.F32

        return qr

    def start_actuator(self, actuator_id):
        qr = self.prep_query_resolution()
        m = moteus.Controller(id=actuator_id, query_resolution=qr)
        asyncio.run(m.set_stop())      

        return m
    
    async def set_position(self, position=math.nan, velocity=math.nan, **kwargs):
        results = await self.m.set_position(
            position=position,
            velocity=velocity,
            **kwargs,
            query=True,
        )
        return results
    
    async def slow_down(self):
        await self.m.set_position_wait_complete(
            position=math.nan,
            velocity=0.0,
            accel_limit=10.0,
        )
    
    async def stop_and_zero(self):
        await self.m.set_stop()
        await asyncio.sleep(0.05)
        await self.m.set_output_nearest(position=0.0)

    async def store_old_config(self):
        await self.s.write_message(b"tel stop")
        await self.s.flush_read()
        await self.s.command(b"d stop")

        self.old_position_min = await self.read_config_double("servopos.position_min")
        self.old_position_max = await self.read_config_double("servopos.position_max")


    async def read_config_double(self, name):
        response = await self.s.command(f"conf get {name}".encode('utf8'), allow_any_response=True)
        return float(response.decode('utf8'))
    
    async def set_position_bounds(self, upper=None, lower=None):
        upper = upper or self.old_position_max
        lower = lower or self.old_position_min

        await self.s.command(f'conf set servopos.position_min {upper}'.encode('utf8'))
        await self.s.command(f'conf set servopos.position_max {lower}'.encode('utf8'))
        await self.s.command(f'conf write'.encode('utf8'))
        
    def state_to_dict(self, state, timestamp=None):
        state_dict = {'TIME': timestamp or time.time()}
        for register in self.stored_data:
            state_dict[register] = state.values[moteus.Register[register]]
        return state_dict
