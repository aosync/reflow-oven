import time
import machine as mc

cs = mc.Pin(17, mode=mc.Pin.OUT, value=1)
run = mc.Pin(15, mode=mc.Pin.OUT, value=0)
max6675_0 = mc.SPI(0)
filteredTemp = 0
alpha = 0.4

temp0 = 0.0
temp1 = 0.0
temp2 = 0.0

while True:
    cs(0)
    data = int.from_bytes(max6675_0.read(2))
    cs(1)
    
    if data & 0x0004:
        print('ERROR THERMOCOUPLE SHORTED')
    
    temp0 = temp1
    temp1 = temp2
    temp2 = (data >> 3) * 0.25

    temp = sorted([temp0, temp1, temp2])[1]

    filteredTemp = temp #alpha * temp + (1 - alpha) * filteredTemp
    print('Temp is', filteredTemp)

    if filteredTemp > 200.0:
        print('halt')
        run(0)
    else:
        print('run')
        run(1)

    time.sleep(0.25)