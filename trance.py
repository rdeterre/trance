import sympy as sp

class Node:
    node_count = 0;
    def __init__(self, time_step):
        self.node_count = Node.node_count++
        self.dt = time_step

class Port:
    port_count = 0
    def __init__(self):
        self.port_count = Node.port_count++

class Electrical_port(Port):
    def __init__(self):
        self.ni = sp.Symbol('ni{0}'.format(port_count))
        self.nv = sp.Symbol('nv{0}'.format(port_count))
        self.ni = sp.Symbol('ni{0}'.format(port_count))
        self.nv = sp.Symbol('nv{0}'.format(port_count))

class Capacitor(Node):
    """
    Model for an ideal Capacitor.
    Relations used are the following :
    1. I(t) = dQ(t)/dt
    2. I(t) = C dV(t)/dt
    3. I_in(t) = I_out(t)

    Relation 1 translates to the following once discretised :
                    I(t) = (Q(t) - Q(t - dt)) / dt

    Relation 2 translates to :
                  I(t) = C * (V(t) - V(t - dt)) / dt
    """
    def __init__(self, capacitance):
        self.nq = sp.Symbol('nq{0}'.format(node_count))
        self.oq = sp.Symbol('oq{0}'.format(node_count))
        self.c = capacitance
        self.minus_port = Electrical_port()
        self.plus_port  = Electrical_port()

    def relations(self):
        rel = []
        rel.append(self.minus_port.ni = (self.nq - self.oq) / self.dt)
        rel.append(self.minus_port.ni = self.c * (self.nv - self.ov) / self.dt)
        rel.append(self.minus_port.ni + self.plus_port.ni)
        return rel

class Current_source(Node):
    """
    Model for an ideal current source
    """
    def __init__(self, current):
        self.i = current
        self.in_port = Electrical_port()
        self.out_port = Electrical_port()

    def relations(self):
        rel = []
        rel.append(self.in_port.i + self.out_port.i)
        return rel

class Electrical_link:
    def __init__(self):
        self.ports = []

    def relations(self):
        rel = []
        for n in self.ports[1:]:
            rel.append(self.ports[0].ni = n.ni)
            rel.append(self.ports[0].oi = n.oi)
            rel.append(self.ports[0].nv = n.nv)
            rel.append(self.ports[0].ov = n.ov)
        return rel

if __name__ == "__main__":
    """
        +-----------------+
        |                 v
    +---+----+       +---------+
    |        |       |         |
    |  Capa  |       |Cur. src.|
    |        |       |         |
    +--------+       +----+----+
        ^                 |
        +-----------------+
    """
    print("This is the Bridge test program.")
    cur = Current_source(1)
    cap = Capactior(1e-3)
    l1 = Electrical_link()
    l1.nodes += [Current_source.in_port, ]
