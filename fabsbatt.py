from trance import Node, Variable, Electrical_port

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

    def soc(self, step):
        """
        Returns the state of charge of the battery at 't + step * dt'.
        'step' must be an integer.
        """
        return self.vars['soc'].symbols[step]

    def i(self, step):
        """
        Returns the current flowing through the device at 't + step * dt'.
        'step' must be an integer.  The return value is positive when
        current comes in through port 0.
        """
        return self.ports[0].i.symbols[step]

    def u(self, step):
        """
        Returns the voltage across the ports of the device at 't + step * dt'.
        'step' must be an integer. The return value is positive when voltage at
        port 1 is higher that at port 0.
        """
        return self.ports[1].v.symbols[step] - self.ports[0].v.symbols[step]

    def t100(self, i):
        """
        Returns discharge time for a fully charged battery sourcing current 'i'.
        """
        return (self.Tref/i**self.k) * \
            (self.bat_parallel * self.QnomTref/self.Tref)**self.k

    def q100(self, i):
        """
        Returns the capacity of a fully charged battery sourcing current 'i'.
        """
        return i * self.t100(i)

    def q(self, step):
        """
        Returns the actual battery capacity at time 't + step * dt'. 'step' must
        be an integer.
        """
        return self.soc(step) * self.q100(self.i(step))

    def relations(self, step_number):
        print("dt : %f" % self.dt)
        rel = []

        ###### Relations
        # Peukert's law: soc0 = soc1 - i0 * dt / Q1
        if step_number <= 0:
            # Q100_first = i0 * t100_0
            # Q100_first = q100(i(0))
            rel.append(-self.soc(0) + self.soc_init - \
                       (self.i(0) * self.dt) / self.q100(self.i(0)))
        else:
            rel.append(-self.soc(0) + self.soc(-1) - \
                       (self.i(0) * self.dt) / self.q(-1))

        # Internal Resistance relation (ri is function of soc)
        # Calculate Ri equivalent for string
        # ri = self.ri_oc * (-7.5e-10 * (self.vars['soc'].symbols[0] ** 5) + 4.18e-7 * (self.vars['soc'].symbols[0] ** 4) - 7.9e5 * (self.vars['soc'].symbols[0] ** 3) + 67e-4 * (self.vars['soc'].symbols[0] ** 2) - 0.265 * self.vars['soc'].symbols[0] + 5.128)
        ri = self.ri_oc * self.bat_series

        # Shepherd discharge equation: u0 = voc100_1 - ri * i0 - ki * (1 / (1 - ( i0 * dt / Q1)))      with ki:polarization resistance
        ki = ri/2
        #/!\ voc100_1 SHOULD BE the open voltage at 100%soc of previous timestep
        voc100 = self.voc100_ref * self.bat_series
        if step_number <= 0:
            rel.append(-self.u(0) + voc100 - ri * self.i(0) - \
                       ki * (1 / (1 - (self.i(0) * self.dt / self.q100(self.i(0))))))
        else:
            rel.append(-self.u(0) + voc100 - ri * self.i(0) - ki * (1 / (1 - (self.i(0) * self.dt / self.q(-1)))))
        # Taylor exansion of the equation above.
        # rel.append(- u0 + voc100 - ri * i0 - ki * 1 + i0 * self.dt / Q1)

        # current in = current out ???
        rel.append(self.i(0) + self.ports[1].i.symbols[0])

        # Caca, a enlever.
        rel += self.vars['soc'].relations(step_number)
        rel += self.ports[0].relations(step_number)
        rel += self.ports[1].relations(step_number)
        return rel
