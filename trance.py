import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

class Node:
    def __init__(self, time_step, name):
        self.dt = time_step
        self.name = name

class Port:
    def __init__(self, name):
        self.name = name


class Electrical_port(Port):
    def __init__(self, name, derivative_order):
        self.name = name
        self.derivative_order = derivative_order
        self.i = Variable('%s.i' % self.name, derivative_order)
        self.v = Variable('%s.v' % self.name, derivative_order)

    def relations(self, step_number):
        rel = []
        rel += self.i.relations(step_number)
        rel += self.v.relations(step_number)
        return rel

class Variable:
    variable_count = 0
    def __init__(self, name, derivative_order):
        self.name = name
        self.derivative_order = derivative_order
        self.variable_count = Variable.variable_count;
        self.symbols = [sp.Symbol("{0}_{1}_{2}".format(self.name, self.variable_count, i)) for i in range(derivative_order + 1)]
        Variable.variable_count += 1
        self.values = np.array([])

    def relations(self, step_number):
        print("Variable %s has number of elements %d while asking for relation %d"
              % (self.name, len(self.values), step_number))

        if len(self.values) < step_number - 1:
            # Ahh! Missing initial value!
            raise Exception("Variable %s is missing initial value at step #%d"
                            % (self.name, step_number))
        

        # Return useful values
        rel = []
        for i in range(1, self.derivative_order + 1):
            print("Give relation for variable %s" % self.name)
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
    def __init__(self, capacitance, dt, name, derivative_order):
        if derivative_order < 1:
            raise Exception("Derivative order cannot be less than one for Capacitor")
        self.derivative_order = derivative_order
        self.name = name
        self.dt = dt
        self.q = Variable('q', derivative_order)
        self.c = capacitance
        self.ports = [Electrical_port("%s.p%d" % (self.name, i), derivative_order) for i in range(2)]

    def v(self, time):
        """
        Associations are  V(t - n * dt) -> v(-n) 
        """
        return self.ports[1].v.symbols[time] - self.ports[0].v.symbols[time]
        
    def relations(self, step_number):
        rel = []
        # Relation 1
        rel.append(self.ports[0].i.symbols[0] - (self.q.symbols[0] - self.q.symbols[-1]) / self.dt)
        # Relation 2 - Hang in there
        rel.append(self.ports[0].i.symbols[0] - self.c * (self.v(0) - self.v(-1)) / self.dt)
        # Relation 3 - Relax
        rel.append(self.ports[0].i.symbols[0] + self.ports[1].i.symbols[0])
        # Relations for q
        rel += self.q.relations(step_number)

        # Relations for old I and V values
        rel += self.ports[0].relations(step_number)
        rel += self.ports[1].relations(step_number)
        
        return rel

    def variables(self):
        return [self.q]

class Current_source(Node):
    """
    Model for an ideal current source.
    """
    def __init__(self, current, name, derivative_order):
        self.name = name
        self.i = current
        self.ports = [Electrical_port("%s.p%d" % (self.name, i), derivative_order)
                      for i in range(2)]

    def relations(self, step_number):
        rel = []
        rel.append(self.ports[1].i.symbols[0] + self.ports[0].i.symbols[0])
        rel.append(self.ports[0].i.symbols[0] - self.i)

         # Relations for old I and V values
        rel += self.ports[0].relations(step_number)
        rel += self.ports[1].relations(step_number)
        
        return rel

    def variables(self):
        return []

class Voltage_source(Node):
    """
    Model for an ideal voltage source.
    """
    def __init__(self, voltage, name, derivative_order):
        self.name = name
        self.v = voltage
        self.derivative_order = derivative_order
        self.port = Electrical_port("%s.p" % self.name, derivative_order)

    def relations(self, step_number):
        rel = []
        rel.append(self.port.v.symbols[0] - self.v)

        # Relations for old I and V values
        rel += self.port.relations(step_number)
        return rel

    def variables(self):
        return []
        

class Electrical_link:
    def __init__(self):
        self.ports = []

    def i_sum(self):
        sum = 0
        for n in self.ports:
            sum += n.i.symbols[0]
        return sum

    def relations(self, step_number):
        rel = []
        for n in self.ports[1:]:
            rel.append(self.ports[0].v.symbols[0] - n.v.symbols[0])
        rel.append(self.i_sum())
        return rel

    def variables(self):
        var = []
        for p in self.ports:
            var.append(p.i)
            var.append(p.v)
        return var

class NodeSystem:
    def __init__(self):
        self.nodes = []
        self.links = []
        self.derivative_order = 0

    def solve(time_step):
        # Concatenate relations.
        rel = []
        var = []
        symbols = []
        for e in elements:
            rel += e.relations(time_step)
            var += e.variables()
        for v in var:
            for i in range (derivative_order + 1):
                symbols.append(v.symbols[i])
        results = sp.solve(rel, symbols)
        if not len(results) == len(symbols):
            raise Exception("The solver failed to deduce all symbols")
        for v in var:
            v.values = np.append(v.values, results[v.symbols[0]])
        
if __name__ == "__main__":

    """
      +-------+
      |       |
    +-+-+   +-+--+
    |Cur|   |Capa|
    +-+-+   +-+--+
      |       |
      +---+---+
          |
        +-+-+
        |Gnd|
        +---+
    """
    print("This is the Bridge test program.")
    cur = Current_source(1, "cur", 1)
    cap = Capacitor(1e-3, 0.1, "cap", 1)
    gnd = Voltage_source(0, "gnd", 1)
    l1 = Electrical_link()
    l1.ports += [cur.ports[1], cap.ports[0], gnd.port]
    l2 = Electrical_link()
    l2.ports += [cur.ports[0], cap.ports[1]]
    
    # Initial values
    cap.q.values = np.append(cap.q.values, 1)
    cap.ports[0].v.values = np.append(cap.ports[0].v.values, 0)
    cap.ports[0].i.values = np.append(cap.ports[0].i.values, 0)
    cap.ports[1].v.values = np.append(cap.ports[1].v.values, 0)
    cap.ports[1].i.values = np.append(cap.ports[1].i.values, 0)
    cur.ports[0].v.values = np.append(cur.ports[0].v.values, 0)
    cur.ports[0].i.values = np.append(cur.ports[0].i.values, 0)
    cur.ports[1].v.values = np.append(cur.ports[1].v.values, 0)
    cur.ports[1].i.values = np.append(cur.ports[1].i.values, 0)
    gnd.port.i.values = np.append(gnd.port.i.values, 0)
    gnd.port.v.values = np.append(gnd.port.v.values, 0)
    els = [cur, cap, gnd, l1, l2]
    for i in range(1, 2):
        solve(i, els, 1)

    plt.plot(cap.q.values)
    plt.show()                  
