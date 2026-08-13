'''This is an accelerometer/gyro mouse module.  I'm intending
to use it in tandem with a stick mouse for fine control.'''

from input import InputModule
from machine import I2C, Pin
# import struct
from array import array


class InputModuleAdxl(InputModule):
    '''This extends InputModule with functionality to support 
    adxl gyro and accelerometer mouse input.'''

    def get_num_keys(self):
        '''This doesn't handle any keys.'''
        return 0

    def __init__(self, input_state):
        super().__init__(input_state)

        self.i2c = None
        # Mouse movement learnhing stuff:
        # gyro: 14.375 LSB/dps; accel full-res: 256 LSB/g (convenient!)
        self.X_SIGN = 1
        self.Y_SIGN = -1
        self.DEADBAND = 22        # 1.5 dps
        self.FULL_SCALE = 1294    # 90 dps
        self.LIMIT = 128          # 0.5 in 1/256 units
        self.SPREAD = 29          # 2.0 dps stability window
        self.MAG_LO = 55696       # (256-20)^2 : |a|-1g within 0.08g, squared, no sqrt
        self.MAG_HI = 76176       # (256+20)^2

        self._buf = bytearray(6)
        self._bias = array('i', (0, 0, 0))
        self.WIN_N = 25
        self._wx = array('h', (0,) * self.WIN_N)
        self._wy = array('h', (0,) * self.WIN_N)
        self._wz = array('h', (0,) * self.WIN_N)
        self._wi = 0
        self._wfill = 0
        self._bias_valid = False

        # ITG-2305 / ITG-3205 default I2C address is usually 0x68
        self.GYRO_ADDR = 0x68
        self.ADXL_ADDR = 0x53
        self.HMC_ADDR = 0x1E

        # HMC Magnetometer Stuff
        # CONFIG_A = 0x00
        # CONFIG_B = 0x01
        # MODE_REG = 0x02
        # DATA_X_H = 0x03

        # ADXL Stuff:
        self.POWER_CTL = 0x2D
        self.DATA_FORMAT = 0x31
        self.DATAX0 = 0x32

        # Gyro ITG Register Addresses
        self.SMPLRT_DIV = 0x15
        self.DLPF_FS = 0x16
        self.GYRO_XOUT_H = 0x1D
        self.PWR_MGM = 0x3E

    def init(self, keys_bytes_offset, state_machine_num=None):
        '''Initializes the input module.  This is called once at startup.'''
        # super().init(keys_bytes_offset, state_machine_num)
        # self.i2c = I2C(0, scl=Pin(2), sda=Pin(1))
        self.i2c = I2C(0, scl=Pin(1), sda=Pin(0))
        self.init_adxl()
        self.init_gyro()

    ### HMC Functions ###
    # def init_hmc():
    #     '''initialize the sensor'''
    #     # Set sample rate to 15Hz (0x70)
    #     i2c.writeto_mem(HMC_ADDR, CONFIG_A, b'\x70')
    #     # Set default gain to +/- 1.3 Ga (0x20)
    #     i2c.writeto_mem(HMC_ADDR, CONFIG_B, b'\x20')
    #     # Set to Continuous Measurement Mode (0x00)
    #     i2c.writeto_mem(HMC_ADDR, MODE_REG, b'\x00')


    # def read_hmc():
    #     '''Reads values from the sensor'''
    #     # Read 6 bytes starting from X MSB register
    #     data = i2c.readfrom_mem(HMC_ADDR, DATA_X_H, 6)
    #     # HMC5883L is big-endian (>), and layout is X, Z, Y
    #     x, z, y = struct.unpack('>hhh', data)

    #     # Scale factor for default gain (1.3 Ga) is 0.92 mG/LSB
    #     scale = 0.92
    #     return x * scale, y * scale, z * scale


    ### ADXL Functions ###
    def init_adxl(self):
        '''Initialize the adxl'''
        # Put sensor into measurement mode
        self.i2c.writeto_mem(self.ADXL_ADDR, self.POWER_CTL, b'\x08')

        # Set data format to Full Resolution, +/- 2g range
        self.i2c.writeto_mem(self.ADXL_ADDR, self.DATA_FORMAT, b'\x08')


    ###  GYRO Functions ###
    def init_gyro(self):
        '''initialize the gyro'''
        # Wake up device and set internal oscillator
        self.i2c.writeto_mem(self.GYRO_ADDR, self.PWR_MGM, b'\x00')
        # Set full scale range (usually FS_SEL = 3 is 2000 deg/s) and LPF
        self.i2c.writeto_mem(self.GYRO_ADDR, self.DLPF_FS, b'\x18')
        # Set sample rate divider
        self.i2c.writeto_mem(self.GYRO_ADDR, self.SMPLRT_DIV, b'\x04')


    # Smart mouse learning/measurement functions
    def _s16(self, hi, lo):
        v = (hi << 8) | lo
        return v - 65536 if v > 32767 else v

    def _read_gyro_raw(self):
        self.i2c.readfrom_mem_into(self.GYRO_ADDR, self.GYRO_XOUT_H, self._buf)
        return self._s16(self._buf[0], self._buf[1]), \
                self._s16(self._buf[2], self._buf[3]), \
                self._s16(self._buf[4], self._buf[5])

    def _read_adxl_raw(self):
        self.i2c.readfrom_mem_into(self.ADXL_ADDR, self.DATAX0, self._buf)
        # little-endian
        return self._s16(self._buf[1], self._buf[0]), \
                self._s16(self._buf[3], self._buf[2]), \
                self._s16(self._buf[5], self._buf[4])

    def _spread_ok(self, w):
        lo = hi = w[0]
        for i in range(1, self.WIN_N):
            v = w[i]
            if v < lo:
                lo = v
            elif v > hi:
                hi = v
        return hi - lo <= self.SPREAD

    def _mean(self, w):
        s = 0
        for i in range(self.WIN_N):
            s += w[i]
        return s // self.WIN_N

    def _update_bias(self, gx, gy, gz, mag2):
        # global _wi, _wfill, _bias_valid
        self._wx[self._wi] = gx
        self._wy[self._wi] = gy
        self._wz[self._wi] = gz
        self._wi = (self._wi + 1) % self.WIN_N
        if self._wfill < self.WIN_N:
            self._wfill += 1
            return
        if mag2 < self.MAG_LO or mag2 > self.MAG_HI:
            return
        if self._spread_ok(self._wx) and self._spread_ok(self._wy) and self._spread_ok(self._wz):
            if self._bias_valid:
                self._bias[0] += (self._mean(self._wx) - self._bias[0]) >> 3
                self._bias[1] += (self._mean(self._wy) - self._bias[1]) >> 3
                self._bias[2] += (self._mean(self._wz) - self._bias[2]) >> 3
            else:
                self._bias[0] = self._mean(self._wx)
                self._bias[1] = self._mean(self._wy)
                self._bias[2] = self._mean(self._wz)
                self._bias_valid = True

    def _to_axis(self, r, sign):
        if -self.DEADBAND < r < self.DEADBAND:
            return 0
        v = sign * r * self.LIMIT // self.FULL_SCALE
        if v > self.LIMIT:
            return self.LIMIT
        if v < -self.LIMIT:
            return -self.LIMIT
        return v

    def update_state(self):
        '''update_state is a standard function in pico_keeb input modules.'''
        gx, gy, gz = self._read_gyro_raw()
        ax, ay, az = self._read_adxl_raw()
        self._update_bias(gx, gy, gz, ax*ax + ay*ay + az*az)
        if not self._bias_valid:
            return
        # axis selection inlined: X from gz (yaw), Y from gx (pitch)
        self.state.mouse_x += self._to_axis(gz - self._bias[2], self.X_SIGN)
        self.state.mouse_y += self._to_axis(gx - self._bias[0], self.Y_SIGN)


if __name__ == "__main__":
    from time import sleep
    # It's kinda dumb to copy this class here for testing, but I don't want to have
    # main.py on the pico while doing development because the board will try to run it
    # at boot and cause probs.   So here we are!
    class InputState:
        def __init__(self, num_keys):
            self.keys = bytearray(num_keys)
            self.wheel = []
            self.mouse_x = 0
            self.mouse_y = 0
            self.mouse_enable = 0

        def clear_deltas(self):
            self.wheel = []
            self.mouse_x = 0
            self.mouse_y = 0
            self.mouse_enable = 0
    state = InputState(0)

    adxl = InputModuleAdxl(state)
    num_keys = adxl.get_num_keys()
    print("Num keys:", num_keys)
    adxl.init(0, None)
    while True:
        state.clear_deltas()
        adxl.update_state()
        print(state.mouse_x, state.mouse_y, adxl._bias_valid)
        sleep(0.1)
