from trance import *

if __name__ == "__main__":
    """
      +-------+
    +-+-+   +-+--+
    |Cur|   |Capa|
    +-+-+   +-+--+
      +---+---+
        +-+-+
        |Gnd|
        +---+
    """
    cur = Current_source(current=1, name="cur")
    cap = Capacitor(capacitance=1e-3, name="cap")
    gnd = Voltage_source(voltage=0, name="gnd")

    l1 = Electrical_link([
        cur.ports[0]
        cap.ports[0]
        gnd.port
    ])

    l2 = Electrical_link([
        cur.ports[1]
        cap.ports[1]
    ])

    sim = Simulation()

    sim.add_elements([cur, cap, gnd, l1, l2])

    sim.initialize(dt = 0.1, total_time_steps=20, default_value=0)

    cap.q.values[sim.derivative_order - 1] = 1

    sim.simulate()

    plt.plot(cap.q.values)
    plt.show()

