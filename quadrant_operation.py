import sys
import ast
import time
import board
import busio
from adafruit_pca9685 import PCA9685

# Throw an error if not all args are passed
if len(sys.argv) < 3:
    raise ValueError("Pass the Q value ('LOW', 'MEDIUM', 'HIGH') and the list of active_channels, e.g. 'quadrant_operation.py LOW [0,0,0,1]'")

# Read value of Q and active_channels
Q = sys.argv[1].upper()
active_channels = ast.literal_eval(sys.argv[2])

# Throw an error if the format is not valid
if not isinstance(active_channels, list) or len(active_channels) != 4:
    raise ValueError("Please pass 4 values, e.g. '[0,0,0,1]'")

# PWM pins on the PCA9685
SOL_1 = 9
SOL_2 = 5
SOL_3 = 6
SOL_4 = 3

# Actuator channels
AVAILABLE_CHANNELS = [SOL_1, SOL_2, SOL_3, SOL_4]
CHANNELS = [ch for ch, active_channel in zip(AVAILABLE_CHANNELS, active_channels) if active_channel == 1]

print(f'Activating Qs: {CHANNELS}')

# Settings
Q_DICT = {'LOW': 4, 'MEDIUM': 8, 'HIGH': 16}
PWM_FREQ_HZ = 400
TAPS_PER_SECOND = Q_DICT[Q]
ON_MS = 120
KICK_MS = 50            
KICK_DUTY_PERCENT = 5
HOLD_DUTY_PERCENT = 30
OFF = 0

# Off-time between hits
PERIOD_MS = 1000.0 / TAPS_PER_SECOND  
REST_MS = max(0, int(PERIOD_MS) - ON_MS)

# Kick/hold time
T_KICK_MS = min(KICK_MS, ON_MS)
T_HOLD_MS = max(0, ON_MS - T_KICK_MS)

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = PWM_FREQ_HZ

# Helper functions to manage kicks
def duty(percent):
    percent = max(0.0, min(100.0, float(percent)))
    return int((percent / 100.0) * 0xFFFF)

def set_channel_duty(ch, percent):
    pca.channels[ch].duty_cycle = duty(percent)

def kick_phase():
    for ch in CHANNELS:
        set_channel_duty(ch, KICK_DUTY_PERCENT)

def hold_phase():
    for ch in CHANNELS:
        set_channel_duty(ch, HOLD_DUTY_PERCENT)

def all_off():
    for ch in CHANNELS:
        set_channel_duty(ch, OFF)

# Operate the set up CHANNELS until KeyboardInterrupt
try:
    while True:
        # 1) Kick all at kick duty power
        kick_phase()
        time.sleep(T_KICK_MS / 1000.0)

        # 2) Hold all at reduced duty
        if T_HOLD_MS > 0:            
            hold_phase()
            time.sleep(T_HOLD_MS / 1000.0)

        # All channels off
        all_off()

        # Rest until next tap        
        if REST_MS > 0:
            time.sleep(REST_MS / 1000.0)

except KeyboardInterrupt:
    all_off()
    pca.deinit()
