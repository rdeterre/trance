import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

class Electrical_port:
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

    def variables(self):
        return [self.i, self.v]

    def initialize(self, derivative_order, total_steps):
        if derivative_order < self.min_derivative_order:
            raise Exception("Derivative order cannot be less than %d"
                            % self.min_derivative_order)
        self.i.initialize(derivative_order, total_steps, 0)
        self.v.initialize(derivative_order, total_steps, 0)

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
        # Return useful values
        rel = []
        for i in range(1, self.derivative_order + 1):
            rel.append(self.symbols[-i] - self.values[step_number - i])
        return rel

class Node:
    def __init__(self, name, default_value = 0):
        self.default_value = default_value
        self.name = name
        self.vars = {}
        self.ports = []

    def variables(self):
        vs = []
        for v in self.vars:
            vs.append(self.vars[v])
        for p in self.ports:
            vs += p.variables()
        return vs

    def initialize(self, dt, derivative_order, total_steps):
        if derivative_order < self.min_derivative_order:
            raise Exception("Needs derivative order higher than %d"
                            % self.min_derivative_order)
        self.dt = dt
        for v in self.vars.values():
            v.initialize(derivative_order, total_steps)
        for p in self.ports:
            p.initialize(derivative_order, total_steps)

    def relations(self, step_number):
        rel = []
        for p in self.ports:
            rel += p.relations(step_number)
        return rel;

class Capacitor(Node):
    """
    Model for an ideal Capacitor.
    Relations used are the following :
    1. I(t) = dQ(t)/dt
    2. I(t) = C dV(t)/dt
    3. I_in(t) = I_out(t)
    4. Q(t) = C * V(t)

    Relation 1 translates to the following once discretised :
                    I(t) = (Q(t) - Q(t - dt)) / dt

    Relation 2 translates to :
                  I(t) = C * (V(t) - V(t - dt)) / dt
    """
    def __init__(self, capacitance, name, default_charge = 0):
        Node.__init__(self, name, default_charge)
        self.min_derivative_order = 1
        self.vars['q'] = Variable('q')
        self.c = capacitance
        self.ports = [Electrical_port("%s.p%d" % (self.name, i))
                      for i in range(2)]

    def v(self, time):
        return self.ports[1].v.symbols[time] - self.ports[0].v.symbols[time]

    def relations(self, step_number):
        rel = []
        # Relation 1
        q = self.vars['q']
        rel.append(self.ports[0].i.symbols[0]
                   - (q.symbols[0] - q.symbols[-1]) / self.dt)
        # Relation 2 - Hang in there
        # rel.append(self.ports[0].i.symbols[0] - self.c * (self.v(0) - self.v(-1)) / self.dt)
        # Relation 3 - Relax
        rel.append(self.ports[0].i.symbols[0] + self.ports[1].i.symbols[0])
        # Relation 4
        rel.append(q.symbols[0] - (self.c * self.v(0)))
        # Relations for q
        rel += self.vars['q'].relations(step_number)

        # Relations for old I and V values
        rel += self.ports[0].relations(step_number)
        rel += self.ports[1].relations(step_number)
        return rel

class Current_source(Node):
    """
    Model for an ideal current source.
    """
    def __init__(self, current, name):
        Node.__init__(self, name)
        self.min_derivative_order = 0
        self.i = current
        self.ports = [Electrical_port("%s.p%d" % (self.name, i))
                      for i in range(2)]

    def relations(self, step_number):
        rel = []
        rel.append(self.ports[1].i.symbols[0]
                   + self.ports[0].i.symbols[0])
        rel.append(self.ports[0].i.symbols[0] - self.i)
         # Relations for old I and V values
        rel += self.ports[0].relations(step_number)
        rel += self.ports[1].relations(step_number)
        return rel

class Resistance(Node):
    def __init__(self, resistance, name):
        Node.__init__(self, name)
        self.min_derivative_order = 0
        self.r = resistance
        self.ports = [Electrical_port("%s.p%d" % (self.name, i))
                      for i in range(2)]

    def relations(self, step_number):
        rel = []
        v0 = self.ports[0].v.symbols[0]
        v1 = self.ports[1].v.symbols[0]
        i0 = self.ports[0].i.symbols[0]
        i1 = self.ports[1].i.symbols[0]
        rel.append(i0 + i1)
        rel.append((v1 - v0) + (self.r * i1))
        rel += Node.relations(self, step_number)
        return rel

class Ground(Node):
    def __init__(self, name):
        Node.__init__(self, name)
        self.min_derivative_order = 0
        self.ports = [Electrical_port("%s.p" % self.name)]

    def relations(self, step_number):
        rel = []
        rel.append(self.ports[0].v.symbols[0])
        # Relations for old I and V values
        rel += self.ports[0].relations(step_number)
        return rel

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
            print("Solve time step %d" % st)
            self.solve(st)

    def dprint(self, symbols, rel, results):
        """
        For debug purposes, format and prints on screen solving
        parameters.
        """
        print("------------------------------------SYMBOLS------------------------------------")
        for s in symbols:
            print(s)
        print("-----------------------------------RELATIONS-----------------------------------")
        for r in rel:
            print(r)
        print("------------------------------------RESULTS------------------------------------")
        for r in results:
            print(r)

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

        print("Try to solve %d symbols." % len(symbols))
        results = sp.solve(rel, symbols)
        if not len(results) == len(symbols):
            self.dprint(symbols, rel, results)
            raise Exception("Solver only deduced %d symbols"
                            % len(results))
        for v in var:
            v.values[time_step] = results[v.symbols[0]]

    def initialize(self, dt, total_time_steps, default_value):
        self.total_time_steps = total_time_steps
        for n in self.nodes:
            n.initialize(dt, self.derivative_order,
                         total_time_steps, default_value)
