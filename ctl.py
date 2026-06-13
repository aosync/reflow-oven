import matplotlib.pyplot as plt
import serial
import time

octl = serial.Serial('/dev/ttyACM0')
time.sleep(0.5)

i = 205
while True:
    octl.reset_input_buffer()
    octl.write(b's %u\r\n' % i)
    octl.flush()

    out = octl.readline().decode('utf-8').strip('\r\n')
    print(out)

    octl.reset_input_buffer()
    octl.write(b'z\r\n')
    octl.flush()

    out = octl.readline().decode('utf-8').strip('\r\n')
    print(out)
    time.sleep(1.0)
    i += 1
