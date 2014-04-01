from trance import *

"""
    +-------+
  +-+-+   +-+--+
  |Vol|   |Res |
  +-+-+   +-+--+
    +---+---+
      +-+-+
      |Gnd|
      +---+
"""
vol = Voltage_source(voltage=1, name="vol")
res = Resistance(resistance=1e3, name="res")
gnd = Ground(name="gnd")

l1 = Electrical_link([
    vol.ports[0],
    res.ports[0],
    gnd.ports[0]
])

l2 = Electrical_link([
    vol.ports[1],
    res.ports[1]
])

sim = Simulation()

sim.add_nodes([vol, res, gnd])
sim.add_links([l1, l2])

sim.simulate(dt = 0.1, total_time = 1)

plt.plot(res.ports[0].i.values)
plt.show()
