'''This is an accelerometer/gyro mouse module.  I'm intending
to use it in tandem with a stick mouse for fine control.'''

from machine import I2C, Pin
# import struct
from array import array

# i2c = I2C(0, scl=Pin(2), sda=Pin(1))
i2c = I2C(0, scl=Pin(1), sda=Pin(0))

STATE = None

# Mouse movement learnhing stuff:
# gyro: 14.375 LSB/dps; accel full-res: 256 LSB/g (convenient!)
X_SIGN = 1
Y_SIGN = -1
DEADBAND = 22        # 1.5 dps
FULL_SCALE = 1294    # 90 dps
LIMIT = 128          # 0.5 in 1/256 units
SPREAD = 29          # 2.0 dps stability window
MAG_LO = 55696       # (256-20)^2 : |a|-1g within 0.08g, squared, no sqrt
MAG_HI = 76176       # (256+20)^2

_buf = bytearray(6)
_bias = array('i', (0, 0, 0))
WIN_N = 25
_wx = array('h', (0,) * WIN_N)
_wy = array('h', (0,) * WIN_N)
_wz = array('h', (0,) * WIN_N)
_wi = 0
_wfill = 0
_bias_valid = False

# ITG-2305 / ITG-3205 default I2C address is usually 0x68
GYRO_ADDR = 0x68
ADXL_ADDR = 0x53
HMC_ADDR = 0x1E

# HMC Magnetometer Stuff
# CONFIG_A = 0x00
# CONFIG_B = 0x01
# MODE_REG = 0x02
# DATA_X_H = 0x03

# ADXL Stuff:
POWER_CTL = 0x2D
DATA_FORMAT = 0x31
DATAX0 = 0x32

# Gyro ITG Register Addresses
SMPLRT_DIV = 0x15
DLPF_FS = 0x16
GYRO_XOUT_H = 0x1D
PWR_MGM = 0x3E

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
def init_adxl():
    '''Initialize the adxl'''
    # Put sensor into measurement mode
    i2c.writeto_mem(ADXL_ADDR, POWER_CTL, b'\x08')

    # Set data format to Full Resolution, +/- 2g range
    i2c.writeto_mem(ADXL_ADDR, DATA_FORMAT, b'\x08')


###  GYRO Functions ###
def init_gyro():
    '''initialize the gyro'''
    # Wake up device and set internal oscillator
    i2c.writeto_mem(GYRO_ADDR, PWR_MGM, b'\x00')
    # Set full scale range (usually FS_SEL = 3 is 2000 deg/s) and LPF
    i2c.writeto_mem(GYRO_ADDR, DLPF_FS, b'\x18')
    # Set sample rate divider
    i2c.writeto_mem(GYRO_ADDR, SMPLRT_DIV, b'\x04')


# Smart mouse learning/measurement functions
def _s16(hi, lo):
    v = (hi << 8) | lo
    return v - 65536 if v > 32767 else v

def _read_gyro_raw():
    i2c.readfrom_mem_into(GYRO_ADDR, GYRO_XOUT_H, _buf)
    return _s16(_buf[0], _buf[1]), _s16(_buf[2], _buf[3]), _s16(_buf[4], _buf[5])

def _read_adxl_raw():
    i2c.readfrom_mem_into(ADXL_ADDR, DATAX0, _buf)
    # little-endian
    return _s16(_buf[1], _buf[0]), _s16(_buf[3], _buf[2]), _s16(_buf[5], _buf[4])

def _spread_ok(w):
    lo = hi = w[0]
    for i in range(1, WIN_N):
        v = w[i]
        if v < lo: lo = v
        elif v > hi: hi = v
    return hi - lo <= SPREAD

def _mean(w):
    s = 0
    for i in range(WIN_N):
        s += w[i]
    return s // WIN_N

def _update_bias(gx, gy, gz, mag2):
    global _wi, _wfill, _bias_valid
    _wx[_wi] = gx; _wy[_wi] = gy; _wz[_wi] = gz
    _wi = (_wi + 1) % WIN_N
    if _wfill < WIN_N:
        _wfill += 1
        return
    if mag2 < MAG_LO or mag2 > MAG_HI:
        return
    if _spread_ok(_wx) and _spread_ok(_wy) and _spread_ok(_wz):
        if _bias_valid:
            _bias[0] += (_mean(_wx) - _bias[0]) >> 3
            _bias[1] += (_mean(_wy) - _bias[1]) >> 3
            _bias[2] += (_mean(_wz) - _bias[2]) >> 3
        else:
            _bias[0] = _mean(_wx); _bias[1] = _mean(_wy); _bias[2] = _mean(_wz)
            _bias_valid = True

def _to_axis(r, sign):
    if -DEADBAND < r < DEADBAND:
        return 0
    v = sign * r * LIMIT // FULL_SCALE
    if v > LIMIT: return LIMIT
    if v < -LIMIT: return -LIMIT
    return v


def get_num_keys():
    '''Standard pico_keeb input module function that tells
    the main program how many keys this module handles so the main
    program can allocate memory for it.'''
    return 0


def init(not_applicable, state, unused_keys_mv):
    '''Init is a standard function for pico_keeb input modules that 
    we use to store a referenc to the global InputState oject so
    any inputs can be recorded in it each tick without any allocation.
    We also can perform any needed module initialization here, like
    pio state machines as well as other hardware setup (adxl, gyro).'''
    global STATE
    init_adxl()
    init_gyro()
    # init_hmc()
    STATE = state


def update_state():
    '''update_state is a standard function in pico_keeb input modules.'''
    gx, gy, gz = _read_gyro_raw()
    ax, ay, az = _read_adxl_raw()
    _update_bias(gx, gy, gz, ax*ax + ay*ay + az*az)
    if not _bias_valid:
        return
    # axis selection inlined: X from gz (yaw), Y from gx (pitch)
    STATE.mouse_x += _to_axis(gz - _bias[2], X_SIGN)
    STATE.mouse_y += _to_axis(gx - _bias[0], Y_SIGN)


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

    init(0, state, None)
    while True:
        state.clear_deltas()
        update_state()
        print(STATE.mouse_x, STATE.mouse_y, _bias_valid)
        sleep(0.5)
