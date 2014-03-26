from trance import *


"""
    +--------+
  +-+-+   +--+--+
  |Cur|   | Res |
  +-+-+   +--+--+
    +---+----+
      +-+-+
      |Gnd|
      +---+
"""
res = Resistance(resistance=100, name="res")
cap = Capacitor(capacitance=1e-3, name="cap", init_charge=1)
gnd = Ground(name="gnd")

l1 = Electrical_link([
    res.ports[0],
    cap.ports[0],
    gnd.ports[0]
])

l2 = Electrical_link([
    res.ports[1],
    cap.ports[1]
])

sim = Simulation()

sim.add_nodes([res, cap, gnd])
sim.add_links([l1, l2])

sim.simulate(dt = 0.1, total_time = 1)

plt.plot(cap.vars['q'].values)
plt.show()
