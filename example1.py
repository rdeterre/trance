from trance import *


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
gnd = Ground(name="gnd")

l1 = Electrical_link([
    cur.ports[0],
    cap.ports[0],
    gnd.ports[0]
])

l2 = Electrical_link([
    cur.ports[1],
    cap.ports[1]
])

sim = Simulation()

sim.add_nodes([cur, cap, gnd])
sim.add_links([l1, l2])

sim.simulate(dt = 0.1, total_time_steps = 15)

plt.plot(cap.vars['q'].values)
plt.show()
