import sympy as sp
import numpy as np

class Node:
    def __init__(self, time_step):
        self.dt = time_step

class Port:
    pass

class Electrical_port(Port):
    def __init__(self):
        self.i = Variable('i', 0)
        self.v = Variable('v', 0)

class Variable:
    variable_count = 0
    def __init__(self, name, derivative_order):
        self.name = name
        self.der_order = derivative_order
        self.symbols = [sp.Symbol(name + "_" str(variable_count++) + "_" + str(i) for i in range(derivative_order + 1))]
        self.values = []

    def relations(self, step_number):
        # Fill values with void until 'step_number - 1'
        while len(self.values) < step_number:
            print("Fill element %d of %s variable" %{len(self.values), name})
            self.values.append(np.nan)

        # Return useful values
        rel = []
        for i in range(1, derivative_order):
            if not self.values[step_number - i].isNan():
                rel.append(self.symbols[-i] - self.values[step_number - i])
        return rel

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
        self.q = Variable('q', 1)
        self.c = capacitance
        self.ports = [Electrical_port() for i in range(2)]

    def v(self, time):
        """
        Associations are  V(t - n * dt) -> v(-n) 
        """
        return self.ports[1].symbols[time] - self.ports[0].symbols[time]
        
    def relations(self, step_number):
        rel = []
        # Relation 1
        rel.append(self.ports[0].i.symbols[0] - (self.q.symbols[0] - self.q.symbols[-1]) / self.dt)
        # Relation 2 - Hang in there
        rel.append(self.ports[0].i.symbols[0] - self.c * (self.v(0) - self.v(-1)) / self.dt)
        # Relation 3 - Relax
        rel.append(self.ports[0].symbols[0] = self.ports[1].symbols[0])
        # Relations for q
        rel += self.q.relations(step_number)
        return rel

class Current_source(Node):
    """
    Model for an ideal current source
    """
    def __init__(self, current):
        self.i = current
        self.ports = [Electrical_port() for i in range(2)]

    def relations(self):
        rel = []
        rel.append(self.ports[1].symbols[0] + self.ports[0].symbols[0])
        return rel

class Electrical_link:
    def __init__(self):
        self.ports = []

    def i_sum(self):
        sum = 0
        for n in self.ports:
            sum += n.symbols[0]
        return sum

    def relations(self):
        rel = []
        for n in self.ports[1:]:
            rel.append(self.ports[0].nv - n.nv)
            rel.append(self.ports[0].ov - n.ov)
        rel.append(self.i_sum())
        return rel

def solve(time_step, elements):
    # Concatenate relations.
    rel = []
    var = []
    for e in elements:
        rel += e.relations
        var += e.variables

    # TODO : Check that.
    results = sp.solve(rel, var)
    # TODO : Check that also.
    for e in elements:
        e.assign(time_step, results)

if __name__ == "__main__":
    """
        +-----------------+
        |                 v
    +---+----+       +---------+
    |  Capa  |       |Cur. src.|
    +--------+       +----+----+
        ^                 |
        +-----------------+
    """
    print("This is the Bridge test program.")
    cur = Current_source(1)
    cap = Capactior(1e-3)
    l1 = Electrical_link()
    l1.nodes += [Current_source.in_port, ]
