import matplotlib.pyplot as plt
import serial
import time
plt.ion()
plt.rcParams['text.usetex'] = False
setpoint = 0.0

class Oven:
    def __init__(self, serial_path='/dev/ttyACM1'):
        self.serial = serial.Serial(serial_path)
        time.sleep(0.5)
    
    def send(self, msg):
        self.serial.reset_input_buffer()
        self.serial.write(bytes('%s\r\n' % msg, 'utf-8'))
        self.serial.flush()
    
    def recv(self):
        r = self.serial.readline().decode('utf-8').strip('\r\n').split(' ')
        print(r)
        return r

    def T(self):
        # Send command
        self.send('v')

        # Receive response        
        return float(self.recv()[1])
    
    def summary(self):
        # Send command
        self.send('z')

        # Receive response
        r = self.recv()
        return float(r[1]), float(r[2])

    def setpoint(self, sp=None):
        # Send command
        if sp is None:
            self.send('s')
        else:
            self.send('s %f' % sp)
        
        # Receive response
        return float(self.recv()[1])

    def ramp(self, rate, target):
        # Send command
        self.send('r %f %f' % (rate, target))

        # Receive response
        return float(self.recv()[1])



octl = Oven('/dev/ttyACM1')

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

def wait_until(cond, delay=0.25):
    wait_start = time.time()
    while True:
        T, sp = octl.summary()
        now = time.time()
        ts.append(now - t_start)
        Ts.append(T)
        Ss.append(sp)

        if cond(now - wait_start, T):
            break

        # Change plot data
        T_line.set_data(ts, Ts)
        S_line.set_data(ts, Ss)

        # Redraw
        ax.relim()
        ax.autoscale_view()
        fig.canvas.draw()
        fig.canvas.flush_events()

        time.sleep(delay)

def profile_leaded(speed=0.5, temp=0.5):
    liq = 183
    soak = (140, 160)
    soak_duration = 60 * speed + 120 * (1 - speed)
    peak = 230 * temp + 210 * (1 - temp)
    tal = 45 * speed + 75 * (1 - speed)
    return liq, soak, soak_duration, peak, tal

def profile_leadfree(speed=0.5, temp=0.5):
    liq = 217
    soak = (150, 200)
    soak_duration = 60 * speed + 120 * (1 - speed)
    peak = 250 * temp + 235 * (1 - temp)
    tal = 45 * speed + 90 * (1 - speed)
    return liq, soak, soak_duration, peak, tal

def profile_lt(speed=0.5, temp=0.5):
    liq = 138
    soak = (90, 120)
    soak_duration = 30 * speed + 90 * (1 - speed)
    peak = 190 * temp + 165 * (1 - temp)
    tal = 45 * speed + 90 * (1 - speed)
    return liq, soak, soak_duration, peak, tal

liq, soak, soak_duration, peak, tal = profile_leadfree()

octl.setpoint(octl.T())
octl.ramp(1.5, soak[0])
wait_until(lambda t, T: T >= soak[0])
octl.ramp((soak[1] - soak[0]) / soak_duration, soak[1])
wait_until(lambda t, T: T >= soak[1])
octl.ramp(1.2, peak)
wait_until(lambda t, T: T >= liq)
wait_until(lambda t, T: t >= tal)
octl.ramp(4.5, 20)
wait_until(lambda t, T: T <= 20)