from scipy.integrate import solve_ivp
import numpy as np
import matplotlib.pyplot as plt

h0 = 4
h1 = 5
C0 = 110
C1 = 15.7


def target(t):
    if t < 50:
        return 150
    if t < 130:
        return 20*(t - 50)/(130-50) + 150
    elif t < 215:
        return 240
    else:
        return 0

last_pid_check = -2.0
next_turn_on = -1.0
turn_on_delay = 0.0
next_turn_off = np.inf
turn_off_delay = 0.0
def pid(t, T, dT, iT):
    err = target(t) - T
    #print('err', err)

    P = 1.0 * err + 0.0002 * iT - 1.0*dT
    P = max(P, 0.0)
    P = min(P, 1.0)

    return P, err

P = 0.0

def fun(t, y):
    global last_pid_check, next_turn_on, turn_on_delay, next_turn_off, turn_off_delay, P
    dy = np.zeros_like(y)

    Qq_a = h0 * (y[1] - y[0])
    Qa_e = h1 * (20 - y[1])

    dy[1] = (-Qq_a + Qa_e)/C1
    err = target(t) - y[1]
    if t - last_pid_check > 0.2:
        TPM, err = pid(t, y[1], dy[1], y[2])
        last_pid_check = t
        turn_on_delay = TPM * 1.0
        turn_off_delay = (1 - TPM) * 1.0
    
    if t > next_turn_on:
        next_turn_off = t + turn_on_delay
        next_turn_on = np.inf
        P = 1200

    if t > next_turn_off:
        next_turn_on = t + turn_off_delay
        next_turn_off = np.inf
        P = 0.0

    print(turn_on_delay, turn_off_delay)
    dy[0] = (P + Qq_a)/C0
    dy[2] = err

    return dy

sol = solve_ivp(fun, [0, 400], [20, 20, 0.0], rtol=1e-10, atol=1e-10, max_step=1e-2)

#plt.plot(sol.t, sol.y[0])
plt.plot(sol.t, sol.y[1])
plt.grid()
plt.show()