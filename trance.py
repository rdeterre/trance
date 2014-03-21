import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

class Electrical_port():
    def __init__(self, name):
        self.name = name
        self.min_derivative_order = 0
        self.i = Variable('%s.i' % self.name)
        self.v = Variable('%s.v' % self.name)

    def relations(self, step_number):
        rel = []
        rel += self.i.relations(step_number)
        rel += self.v.relations(step_number)
        return rel

    def initialize(self, derivative_order, total_steps,
                   default_value):
        if derivative_order < self.min_derivative_order:
            raise Exception("Derivative order cannot be less than %d"
                            % self.min_derivative_order)
        self.i.initialize(derivative_order, total_steps, default_value)
        self.v.initialize(derivative_order, total_steps, default_value)

class Variable:
    variable_count = 0
    def __init__(self, name):
        self.name = name
        self.variable_count = Variable.variable_count
        self.symbols = []
        Variable.variable_count += 1
        self.values = np.array([])

    def initialize(self, derivative_order, total_steps, default_value):
        self.values = np.zeros(total_steps)
        if default_value != 0:
            for index, x in self.values:
                x = 0
        self.derivative_order = derivative_order
        self.symbols = [sp.Symbol("{0}_{1}_{2}"
                                  .format(self.name,
                                          self.variable_count, i))
                 for i in range(derivative_order + 1)]

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

class Capacitor():
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
    def __init__(self, capacitance, name):
        self.min_derivative_order = 1
        self.name = name
        self.vars = {}
        self.vars['q'] = Variable('q')
        self.c = capacitance
        self.ports = [Electrical_port("%s.p%d" % (self.name, i))
                      for i in range(2)]

    def variables():
        vs = []
        for v in self.vars:
            vs.append(self.vars[v])
        return vs

    def initialize(self, dt, derivative_order, total_steps,
                   default_value):
        if derivative_order < self.min_derivative_order:
            raise Exception("Needs derivative order higher than %d"
                            % self.min_derivative_order)
        self.dt = dt
        for v in self.vars:
            self.vars[v].initialize(derivative_order, total_steps, default_value)
        for p in self.ports:
            p.initialize(derivative_order, total_steps, default_value)
        
    def v(self, time):
        """
        Associations are  V(t - n * dt) -> v(-n) 
        """
        return self.ports[1].v.symbols[time] - self.ports[0].v.symbols[time]
        
    def relations(self, step_number):
        rel = []
        # Relation 1
        q = self.vars['q']
        rel.append(self.ports[0].i.symbols[0] - (q.symbols[0] - q.symbols[-1]) / self.dt)
        # Relation 2 - Hang in there
        rel.append(self.ports[0].i.symbols[0] - self.c * (self.v(0) - self.v(-1)) / self.dt)
        # Relation 3 - Relax
        rel.append(self.ports[0].i.symbols[0] + self.ports[1].i.symbols[0])
        # Relations for q
        rel += self.vars['q'].relations(step_number)

        # Relations for old I and V values
        rel += self.ports[0].relations(step_number)
        rel += self.ports[1].relations(step_number)
        
        return rel

    def variables(self):
        vars = [self.vars['q']]
        for p in self.ports:
            vars.append(p.i)
            vars.append(p.v)
        return vars

class Current_source():
    """
    Model for an ideal current source.
    """
    def __init__(self, current, name):
        self.min_derivative_order = 0
        self.name = name
        self.i = current
        self.ports = [Electrical_port("%s.p%d" % (self.name, i))
                      for i in range(2)]

    def initialize(self, dt, derivative_order, total_steps,
                   default_value):
        if derivative_order < self.min_derivative_order:
            raise Exception("Needs derivative order higher than %d"
                            % self.min_derivative_order)
        for p in self.ports:
            p.initialize(derivative_order, total_steps, default_value)

    def relations(self, step_number):
        rel = []
        rel.append(self.ports[1].i.symbols[0]
                   + self.ports[0].i.symbols[0])
        rel.append(self.ports[0].i.symbols[0] - self.i)

         # Relations for old I and V values
        rel += self.ports[0].relations(step_number)
        rel += self.ports[1].relations(step_number)
        
        return rel

    def variables(self):
        vars = []
        for p in self.ports:
            vars.append(p.i)
            vars.append(p.v)
        return vars

class Voltage_source():
    """
    Model for an ideal voltage source.
    """
    def __init__(self, voltage, name):
        self.min_derivative_order = 0
        self.name = name
        self.v = voltage
        self.ports = [Electrical_port("%s.p" % self.name)]

    def initialize(self, dt, derivative_order, total_steps,
                   default_value):
        if derivative_order < self.min_derivative_order:
            raise Exception("Needs derivative order higher than %d"
                            % self.min_derivative_order)

        self.ports[0].initialize(derivative_order,
                                 total_steps,
                                 default_value)

    def relations(self, step_number):
        rel = []
        rel.append(self.ports[0].v.symbols[0] - self.v)

        # Relations for old I and V values
        rel += self.ports[0].relations(step_number)
        return rel

    def variables(self):
        vars = []
        for p in self.ports:
            vars.append(p.i)
            vars.append(p.v)
        return vars
        

class Electrical_link:
    def __init__(self, ports):
        self.ports = ports

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
        return []

class Simulation:
    def __init__(self):
        self.nodes = []
        self.links = []
        self.derivative_order = 0

    def add_nodes(self, nodes):
        for n in nodes:
            if n.min_derivative_order > self.derivative_order:
                self.derivative_order = n.min_derivative_order
        self.nodes += nodes

    def add_links(self, links):
        self.links += links

    def simulate(self):
        for st in range(self.derivative_order, self.total_time_steps):
            self.solve(st)

    def solve(self, time_step):
        # Concatenate relations.
        rel = []
        var = []
        symbols = []
        for e in self.nodes:
            rel += e.relations(time_step)
            var += e.variables()
        for l in self.links:
            rel += l.relations(time_step)
        for v in var:
            for i in range (self.derivative_order + 1):
                symbols.append(v.symbols[i])
        results = sp.solve(rel, symbols)
        if not len(results) == len(symbols):
            raise Exception("The solver failed to deduce all symbols")
        for v in var:
            v.values[time_step] = v.symbols[0]
            # = np.append(v.values, results[v.symbols[0]])

    def initialize(self, dt, total_time_steps, default_value):
        self.total_time_steps = total_time_steps
        for n in self.nodes:
            n.initialize(dt, self.derivative_order,
                         total_time_steps, default_value)

        
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
    try:
        for i in range(1, 2):
            solve(i, els, 1)
    except TypeError:
        print("Type error while solving")

    plt.plot(cap.q.values)
    plt.show()                  
