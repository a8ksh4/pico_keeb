'''This is an accelerometer/gyro mouse module.  I'm intending
to use it in tandem with a stick mouse for fine control.'''


import time
from machine import I2C, Pin
import struct

# i2c = I2C(0, scl=Pin(2), sda=Pin(1))
i2c = I2C(0, scl=Pin(1), sda=Pin(0))



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
    # x = read_gyro_word(GYRO_XOUT_H)
    # y = read_gyro_word(GYRO_XOUT_H + 2)
    # z = read_gyro_word(GYRO_XOUT_H + 4)
    data = i2c.readfrom_mem(GYRO_ADDR, GYRO_XOUT_H, 6)
    x, y, z = struct.unpack('>hhh', data)

    scale_factor = 14.375
    dps_x = x / scale_factor
    dps_y = y / scale_factor
    dps_z = z / scale_factor
    return dps_x, dps_y, dps_z


def init(pio_machine_num):
    '''Init is a standard function for input modules that 
    can perform any needede initialization.  Probably this
    is on ly needed to assign unique state machine nums.'''
    # init_adxl()
    # init_gyro()
    # init_hmc()


def get_state():
    '''get_state is a standard function in inupt modules.
    It returns a dict with keys a list of states of any buttons/keys,
    and 'wheel' a list of movement directions.'''
    state = {'mouse': (0, 0)}
    return state