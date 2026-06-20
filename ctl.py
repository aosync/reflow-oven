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


octl.setpoint(octl.T())
octl.ramp(1.5, 130)
wait_until(lambda t, T: T >= 130)
octl.ramp(0.4, 170)
wait_until(lambda t, T: T >= 170)
octl.ramp(1.5, 245)
wait_until(lambda t, T: T >= 217)
wait_until(lambda t, T: t >= 60)
octl.ramp(4.5, 20)
wait_until(lambda t, T: T <= 20)