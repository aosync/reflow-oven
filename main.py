import time
import machine as mc
import asyncio
import sys

# Pins
cs = mc.Pin(17, mode=mc.Pin.OUT, value=1)
run = mc.Pin(15, mode=mc.Pin.OUT, value=0)
max6675_0 = mc.SPI(0)

# Variables
filt_temp = [0.0, 0.0, 0.0]
ts = [0.0, 0.0, 0.0]
alpha = 0.5
target = 0
i_err = 0.0
pwm_window = 220

# PID output
oven_on_delay = 0.0
oven_off_delay = 0.0
power = 0.0

def pid_coefs(T):
    Kp = (1/4 - 1/12)/(250 - 50)*(T - 50) + 1/16
    Ki = (0.002 - 0.0003)/(250 - 50)*(T - 50) + 0.0003
    #Ki = 0.0007
    Kd = (0.4 - 1.0)/(250 - 50)*(T - 50) + 0.7
    return Kp, Ki, Kd

def pid():
    global oven_on_delay, oven_off_delay, i_err, power

    # Calculate PID output
    err = target - filt_temp[2]

    h0 = time.ticks_diff(ts[2], ts[1]) / 1000
    h1 = time.ticks_diff(ts[1], ts[0]) / 1000

    if h0 <= 0 or h1 <= 0:
        return
    
    #d_err = (2*h0 + h1)/(h0*(h0 + h1))*filt_temp[2] - (h0 + h1)/(h0*h1)*filt_temp[1] + h0/(h1*(h0 + h1)) * filt_temp[0]
    d_err = (filt_temp[2] - filt_temp[1]) / h0
    i_err_last = i_err
    i_err = i_err + (2 * target - filt_temp[2] - filt_temp[1])/2*h0

    Kp, Ki, Kd = pid_coefs(filt_temp[2])
    
    # Clamp integral term
    if Ki * i_err > 1.0:
        i_err = 1.0 / Ki
    elif Ki * i_err < -1.0:
        i_err = -1.0 / Ki
    
    # Calculate output
    P = Kp * err + Ki * i_err - Kd * d_err
    #print(Kp, Ki, Kd)
    #print(Ki * i_err)
    #print(P)
    #P = 0.15 * err + 0.0008 * i_err - 0.7 * d_err
    P = max(P, 0.0)
    P = min(P, 1.0)

    if P == 0.0 and Ki * i_err < 0:
        i_err = i_err_last
    if P == 1.0 and Ki * i_err > 0:
        i_err = i_err_last

    power = 2 * P - 1
    oven_on_delay = int(P * pwm_window)
    oven_off_delay = int((1 - P) * pwm_window)

async def max6675_reading():
    temp = [0.0, 0.0, 0.0]
    while True:
        # Read MAX6675 data
        cs(0)
        data = int.from_bytes(max6675_0.read(2))
        ts[0] = ts[1]
        ts[1] = ts[2]
        ts[2] = time.ticks_ms()
        cs(1)
    
        # Check if data correct
        #if data & 0x0004:
        #    print('ERROR THERMOCOUPLE SHORTED')
        
        temp[0] = temp[1]
        temp[1] = temp[2]
        temp[2] = (data >> 3) * 0.25
        
        filt_temp[0] = filt_temp[1]
        filt_temp[1] = filt_temp[2]
        filt_temp[2] = alpha * sorted(temp)[1] + (1 - alpha) * filt_temp[2]
        
        #print('%0.1f/%0.1f' % (filt_temp[2], target))
        pid()
        await asyncio.sleep_ms(225)

async def oven_delta_sigma():
    MAINS_FREQ = 50
    MAINS_PERIOD_MS = int(1000 / MAINS_FREQ + 0.5)

    fire = 0
    res = 0
    while True:
        res += power - fire
        fire = 1 if res >= 0 else -1
        
        if fire == 1:
            run(1)
        else:
            run(0)

        await asyncio.sleep_ms(MAINS_PERIOD_MS)


async def oven_pwm():
    while True:
        run(1)
        await asyncio.sleep_ms(oven_on_delay)
        run(0)
        await asyncio.sleep_ms(oven_off_delay)

async def serial_if():
    global target

    # Define the stdin asyncio reader
    stdin = asyncio.StreamReader(sys.stdin.buffer)

    # Interface loop
    while True:
        cmd = (await stdin.readline()).decode('utf-8').strip('\r\n').split(' ')
        
        if cmd[0] == 's':
            if len(cmd) >= 2:
                target = float(cmd[1])
            print('0', target)
        elif cmd[0] == 'v':
            print('0', filt_temp[2])
        elif cmd[0] == 'z':
            print('0', filt_temp[2], target)
        else:
            print('1')

async def main():
    await asyncio.gather(
        max6675_reading(),
        oven_delta_sigma(),
        serial_if()
    )

try:
    asyncio.run(main())
except KeyboardInterrupt:
    run(0)
    #print('End')
# while True:
    # cs(0)
    # data = int.from_bytes(max6675_0.read(2))
    # cs(1)
    
    # if data & 0x0004:
    #     print('ERROR THERMOCOUPLE SHORTED')
    
    # temp0 = temp1
    # temp1 = temp2
    # temp2 = (data >> 3) * 0.25

    # temp = sorted([temp0, temp1, temp2])[1]

    # filteredTemp = temp #alpha * temp + (1 - alpha) * filteredTemp
    # print('Temp is', filteredTemp)

#     if filteredTemp > 200.0:
#         print('halt')
#         run(0)
#     else:
#         print('run')
#         run(1)

#     time.sleep(0.25)