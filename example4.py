from trance import *

"""
    +-------+
  +-+--+   +-+--+
  |Fabb|   |Res |
  +-+--+   +-+--+
    +---+---+
      +-+-+
      |Gnd|
      +---+
"""
fabb = Fabs_battery(20, 1100, 1.2, 0.34, 2.15, 24, 1, "fabb", soc_init=1)
res = Resistance(resistance=1e3, name="res")
gnd = Ground(name="gnd")

l1 = Electrical_link([
    fabb.ports[0],
    res.ports[0],
    gnd.ports[0]
])

l2 = Electrical_link([
    fabb.ports[1],
    res.ports[1]
])

sim = Simulation()

sim.add_nodes([fabb, res, gnd])
sim.add_links([l1, l2])

sim.simulate(dt = 0.0001, total_time = 20)

plt.plot(fabb.vars['soc'].values)
plt.show()
