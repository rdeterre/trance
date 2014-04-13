import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import math

class Electrical_port:
    def __init__(self, name, init_current = 0, init_voltage = 0):
        self.name = name
        self.min_derivative_order = 0
        self.init_current = init_current
        self.init_voltage = init_voltage
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
        self.i.initialize(derivative_order, total_steps, self.init_current)
        self.v.initialize(derivative_order, total_steps, self.init_voltage)

class Variable:
    variable_count = 0
    def __init__(self, name):
        self.name = name
        self.variable_count = Variable.variable_count
        self.symbols = []
        Variable.variable_count += 1
        self.values = np.array([])

    def initialize(self, derivative_order, total_steps, init_value):
        self.values = np.zeros(total_steps)
        if init_value != 0:
            for i in range(derivative_order):
                self.values[i] = init_value
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
    def __init__(self, name, vars = {}, init_values = {}, ports = []):
        self.init_values = init_values
        self.name = name
        self.vars = vars
        self.ports = ports

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
        for v in self.vars.keys():
            if v in self.init_values:
                print("Init %s with init values" % v)
                self.vars[v].initialize(derivative_order, total_steps, self.init_values[v])
            else:
                print("Init %s without init values" % v)
                self.vars[v].initialize(derivative_order, total_steps, 0)
        for p in self.ports:
            p.initialize(derivative_order, total_steps)
        print("Initialize node %s with dt %f" % (self.name, self.dt))


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
    2. I_in(t) = I_out(t)
    3. Q(t) = C * V(t)
    """
    def __init__(self, capacitance, name, init_charge = 0):
        Node.__init__(self,
                      name,
                      vars = {'q': Variable('q')},
                      init_values = {'q': init_charge},
                      ports = [Electrical_port("%s.p%d" % (name, i))
                               for i in range(2)])
        self.min_derivative_order = 1
        self.c = capacitance

    def v(self, time):
        return self.ports[1].v.symbols[time] - self.ports[0].v.symbols[time]

    def relations(self, step_number):
        rel = []

        q = self.vars['q']
        rel.append(self.ports[0].i.symbols[0]
                   - (q.symbols[0] - q.symbols[-1]) / self.dt)
        rel.append(self.ports[0].i.symbols[0] + self.ports[1].i.symbols[0])
        rel.append(q.symbols[0] - (self.c * self.v(0)))
        # Relations for q
        rel += self.vars['q'].relations(step_number)
        # Relations for old I and V values
        rel += self.ports[0].relations(step_number)
        rel += self.ports[1].relations(step_number)
        return rel
T
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

class Voltage_source(Node):
    """
    Model for an ideal voltage source.
    """
    def __init__(self, voltage, name):
        Node.__init__(self, name)
        self.min_derivative_order = 0
        self.v = voltage
        self.ports = [Electrical_port("%s.p%d" % (self.name, i))
                      for i in range(2)]

    def relations(self, step_number):
        rel = []
        rel.append(self.ports[1].v.symbols[0]
                   - self.ports[0].v.symbols[0] - self.v)
        rel.append(self.ports[0].i.symbols[0] + self.ports[1].i.symbols[0])
        # Old I and V values
        rel += self.ports[0].relations(step_number)
        rel += self.ports[1].relations(step_number)
        return rel


class Fabs_battery(Node):
    def __init__(self, Tref, QnomTref, k, ri_oc, voc100_ref, bat_series, bat_parallel, name, soc_init):
        Node.__init__(self,
                      name,
                      vars = {'soc': Variable('soc')},
                      init_values = {'soc': soc_init},
                      ports = [Electrical_port("%s.p%d" % (name, i))
                               for i in range(2)])

        self.Tref = Tref
        self.QnomTref = QnomTref
        self.k = k
        self.ri_oc = ri_oc
        self.voc100_ref = voc100_ref
        self.soc_init = soc_init
        self.bat_series = bat_series
        self.bat_parallel = bat_parallel
        self.min_derivative_order = 1
		

    def relations(self, step_number):
        print("dt : %f" % self.dt)
        rel = []
		# subscript 1 indicates value at t-1, subscript 0 indicates value at t-1
		
		# State of Charge
        soc0 = self.vars['soc'].symbols[0]
        soc1 = self.vars['soc'].symbols[-1]
		
		# Load Amperage demand
        i0 = self.ports[0].i.symbols[0]
        i1 = self.ports[0].i.symbols[-1]
		
		# Battery terminal voltage
        u0 = self.ports[1].v.symbols[0] - self.ports[0].v.symbols[0]
		
		# Duration of discharge in function of amperage demand, when battery is fully charged
        t100_0 = (self.Tref/i0**self.k)*(self.bat_parallel * self.QnomTref/self.Tref)**self.k
        t100_1 = (self.Tref/i1**self.k)*(self.bat_parallel * self.QnomTref/self.Tref)**self.k
		
		# Battery Capacity [Ah] in function of amperage demand when fully charged
        Q100_1 = i1 * t100_1
        Q100_0 = i0 * t100_0
		
		# Battery actual capacity at t in function of amps demand
        Q1 = soc1 * Q100_1
        Q0 = soc0 * Q100_0
        
		# ##### Relations
		# Peukert's law: soc0 = soc1 - i0 * dt / Q1 
        if step_number <= 0:
            Q100_first = i0 * t100_0
            rel.append(-soc0 + self.soc_init - (i0 * self.dt) / Q100_first)
        else:
            rel.append(-soc0 + soc1 - (i0 * self.dt) / Q1)
		
        # Internal Resistance relation (ri is function of soc)
        # Calculate Ri equivalent for string
        # ri = self.ri_oc * (-7.5e-10 * (self.vars['soc'].symbols[0] ** 5) + 4.18e-7 * (self.vars['soc'].symbols[0] ** 4) - 7.9e5 * (self.vars['soc'].symbols[0] ** 3) + 67e-4 * (self.vars['soc'].symbols[0] ** 2) - 0.265 * self.vars['soc'].symbols[0] + 5.128)
        ri = self.ri_oc * self.bat_series
		
        # Shepherd discharge equation: u0 = voc100_1 - ri * i0 - ki * (1 / (1 - ( i0 * dt / Q1)))      with ki:polarization resistance 
        ki = ri/2
        #/!\ voc100_1 SHOULD BE the open voltage at 100%soc of previous timestep
        voc100 = self.voc100_ref * self.bat_series
        if step_number <= 0:
            rel.append(-u0 + voc_100 - ri * i0 - ki * (1 / (1 - (i0 * self.dt / Q100_first))))
        else:
            rel.append(-u0 + voc_100 - ri * i0 - ki * (1 / (1 - (i0 * self.dt / Q1))))
        # Taylor exansion of the equation above.
        # rel.append(- u0 + voc100 - ri * i0 - ki * 1 + i0 * self.dt / Q1)
        
        # current in = current out ???
        rel.append(i0 + self.ports[1].i.symbols[0])
		
        # Caca, a enlever.
        rel += self.vars['soc'].relations(step_number)
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

    def simulate(self, dt, total_time):
        print("Simulate with total time %f and dt %f" % (total_time, dt))
        error = 0.0001
        if not (total_time + error) % dt <= error:
            raise Exception("total_time is not a multiple of dt. Try setting it to %d instead."
                            % (total_time // dt * dt))
        total_time_steps = int(total_time // dt)
        self.initialize(dt, total_time_steps)
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

    def initialize(self, dt, total_time_steps):
        self.total_time_steps = total_time_steps
        for n in self.nodes:
            n.initialize(dt, self.derivative_order, total_time_steps)
