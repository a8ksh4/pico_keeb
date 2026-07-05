'''This is an accelerometer/gyro mouse module.  I'm intending
to use it in tandem with a stick mouse for fine control.'''

from machine import I2C, Pin
import struct

# i2c = I2C(0, scl=Pin(2), sda=Pin(1))
i2c = I2C(0, scl=Pin(1), sda=Pin(0))

# Mouse movement learnhing stuff:
GYRO_X_AXIS = 2      # gyro axis index driving cursor X (2 = yaw/Z)
GYRO_Y_AXIS = 0      # gyro axis index driving cursor Y (0 = pitch/X)
X_SIGN = 1
Y_SIGN = -1
DEADBAND_DPS = 1.5   # ignore rates below this (noise + residual bias)
FULL_SCALE_DPS = 90  # rate that maps to full deflection
LIMIT = 0.5          # module output clamp, half of stick module
STILL_ACCEL_TOL = 0.08  # g deviation from 1g considered "at rest"
STILL_GYRO_DPS = 3.0
BIAS_ALPHA = 0.02

gyro_bias = [0.0, 0.0, 0.0]
_win = []            # ring of recent raw gyro samples
WIN_N = 25           # ~0.25-0.5s depending on loop rate
STILL_SPREAD_DPS = 2.0
_bias_valid = False

# ITG-2305 / ITG-3205 default I2C address is usually 0x68
GYRO_ADDR = 0x68
ADXL_ADDR = 0x53
HMC_ADDR = 0x1E

# HMC Magnetometer Stuff
CONFIG_A = 0x00
CONFIG_B = 0x01
MODE_REG = 0x02
DATA_X_H = 0x03

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
def init_hmc():
    '''initialize the sensor'''
    # Set sample rate to 15Hz (0x70)
    i2c.writeto_mem(HMC_ADDR, CONFIG_A, b'\x70')
    # Set default gain to +/- 1.3 Ga (0x20)
    i2c.writeto_mem(HMC_ADDR, CONFIG_B, b'\x20')
    # Set to Continuous Measurement Mode (0x00)
    i2c.writeto_mem(HMC_ADDR, MODE_REG, b'\x00')


def read_hmc():
    '''Reads values from the sensor'''
    # Read 6 bytes starting from X MSB register
    data = i2c.readfrom_mem(HMC_ADDR, DATA_X_H, 6)
    # HMC5883L is big-endian (>), and layout is X, Z, Y
    x, z, y = struct.unpack('>hhh', data)

    # Scale factor for default gain (1.3 Ga) is 0.92 mG/LSB
    scale = 0.92
    return x * scale, y * scale, z * scale


### ADXL Functions ###
def init_adxl():
    '''Initialize the adxl'''
    # Put sensor into measurement mode
    i2c.writeto_mem(ADXL_ADDR, POWER_CTL, b'\x08')

    # Set data format to Full Resolution, +/- 2g range
    i2c.writeto_mem(ADXL_ADDR, DATA_FORMAT, b'\x08')


def read_adxl():
    '''reads the adxl values and scales them gravity normal stuff'''
    # Read 6 bytes of data starting from DATAX0
    data = i2c.readfrom_mem(ADXL_ADDR, DATAX0, 6)
    # Unpack 3 little-endian 16-bit signed integers (x, y, z)
    x, y, z = struct.unpack('<hhh', data)

    # Scale factor for full resolution mode is typically 3.9 mg/LSB (0.0039g)
    scale = 0.0039
    return x * scale, y * scale, z * scale


###  GYRO Functions ###
def init_gyro():
    '''initialize the gyro'''
    # Wake up device and set internal oscillator
    i2c.writeto_mem(GYRO_ADDR, PWR_MGM, b'\x00')
    # Set full scale range (usually FS_SEL = 3 is 2000 deg/s) and LPF
    i2c.writeto_mem(GYRO_ADDR, DLPF_FS, b'\x18')
    # Set sample rate divider
    i2c.writeto_mem(GYRO_ADDR, SMPLRT_DIV, b'\x04')


def read_gyro_word(register):
    '''Reads a 16-bit signed integer'''
    high = i2c.readfrom_mem(GYRO_ADDR, register, 1)[0]
    low = i2c.readfrom_mem(GYRO_ADDR, register + 1, 1)[0]
    value = (high << 8) | low
    if value > 32767:
        value -= 65536
    return value


def read_gyro():
    '''Read raw angular velocity, scale it to degrees per second,
    and return the values.'''
    data = i2c.readfrom_mem(GYRO_ADDR, GYRO_XOUT_H, 6)
    x, y, z = struct.unpack('>hhh', data)

    scale_factor = 14.375
    dps_x = x / scale_factor
    dps_y = y / scale_factor
    dps_z = z / scale_factor
    return dps_x, dps_y, dps_z


# Smart mouse learning/measurement functions
def to_axis(rate, sign):
    if abs(rate) < DEADBAND_DPS:
        return 0.0
    v = sign * rate / FULL_SCALE_DPS
    return max(-LIMIT, min(LIMIT, v))

def _update_bias(g, accel_mag):
    global _bias_valid
    _win.append(g)
    if len(_win) > WIN_N:
        _win.pop(0)
    if len(_win) < WIN_N or abs(accel_mag - 1.0) > STILL_ACCEL_TOL:
        return
    for i in range(3):
        vals = [s[i] for s in _win]
        if max(vals) - min(vals) > STILL_SPREAD_DPS:
            return
    # stable window: snap/track bias to its mean
    for i in range(3):
        m = sum(s[i] for s in _win) / WIN_N
        gyro_bias[i] = m if not _bias_valid else gyro_bias[i] + 0.1 * (m - gyro_bias[i])
    _bias_valid = True


def get_mouse_delta():
    g = read_gyro()
    ax, ay, az = read_adxl()
    _update_bias(g, (ax*ax + ay*ay + az*az) ** 0.5)
    if not _bias_valid:
        return 0.0, 0.0   # no cursor motion until first good bias
    gx = [g[i] - gyro_bias[i] for i in range(3)]
    return to_axis(gx[GYRO_X_AXIS], X_SIGN), to_axis(gx[GYRO_Y_AXIS], Y_SIGN)


def init(not_applicable):
    '''Init is a standard function for pico_keeb input modules that 
    can perform any needede initialization.  We use this for initializing
    pio state machines as well as other hardware.'''
    init_adxl()
    init_gyro()
    init_hmc()


def get_state():
    '''get_state is a standard function in inupt modules.
    It returns a dict with keys a list of states of any buttons/keys,
    and 'wheel' a list of movement directions.'''
    state = {'mouse': get_mouse_delta()}
    return state


if __name__ == "__main__":
    from time import sleep
    init(0)
    while True:
        changes = get_state()
        print(changes)
        print("ADXL:", read_adxl())
        print("GYRO:", read_gyro())
        print("HMC:", read_hmc())
        sleep(1)
