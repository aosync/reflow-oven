import matplotlib.pyplot as plt
import serial
import time
plt.ion()
plt.rcParams['text.usetex'] = False
setpoint = 0.0

def profile(t):
    if t >= 0 and t < 100:
        return 150
    elif t >= 100 and t < 180:
        return (t - 100)/(180 - 100)*20 + 150
    elif t >= 180 and t < 270:
        return 245
    else:
        return 0

octl = serial.Serial('/dev/ttyACM1')
time.sleep(0.5)

fig, ax = plt.subplots()
ax.set_xlabel('Time [s]')
ax.set_ylabel('Temperature [°C]')
T_line, = ax.plot([], [])
S_line, = ax.plot([], [])

ts = []
Ts = []
Ss = []

T_prev = -1
t_start = time.time()
while True:
    now = time.time()
    T_now = profile(now - t_start)
    if T_now != T_prev:
        setpoint = T_now
        octl.reset_input_buffer()
        octl.write(b's %f\r\n' % T_now)
        octl.flush()
        octl.readline()
        T_prev = T_now
    
    octl.reset_input_buffer()
    octl.write(b'v\r\n')
    octl.flush()
    
    out = octl.readline().decode('utf-8').strip('\r\n').split(' ')[1]
    ts.append(time.time() - t_start)
    Ts.append(float(out))
    Ss.append(setpoint)
    
    # Change plot data
    T_line.set_data(ts, Ts)
    S_line.set_data(ts, Ss)

    # Redraw
    ax.relim()
    ax.autoscale_view()
    fig.canvas.draw()
    fig.canvas.flush_events()

    time.sleep(0.25)
