import logging
import numpy as np

from numpy.linalg import norm

from .aux_functions import calc_ijk
from .base import ListedMixin, CalculatedMixin, FS2000Entity


class Couple(ListedMixin, CalculatedMixin, FS2000Entity):
    """Defines an FS2000 couple element."""
    type = 'SC'
    parameters = ['ELEM', 'N1', 'N2', 'ROT', 'REFELEM', 'SPCONST', 'SCCSYS']
    paramdefaults = [0, 0, 0, 0.0, 0, 0, 0]

    def __init__(self, model, *args, **kwargs):
        """Creates a couple within the model."""
        # Internal variables
        self._N1, self._N2, self._ROT = 0, 0, 0.0
        self._REFELEM, self._SPCONST, self._SCCSYS = 0, 0, 0
        self._p1, self._p2 = None, None
        self._i, self._j, self._k = None, None, None
        # Call base class constructor
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        self.calculate()
        # Temporary until couple type implementation
        sctype = self._model.CTypeList.get(self._SPCONST)
        k1, k2, k3, k4, k5, k6 = sctype.K1, sctype.K2, sctype.K3, sctype.K4, sctype.K5, sctype.K6
        tp, co = sctype.TYPE, sctype.CO
        return f'SpCp  Nod1  Nod2    Rot RefElem CSys StiffCode    K1       K2       K3       K4       K5       ' \
               f'K6    Type CO\n{self.pk:^4d} {self._N1:>5d} {self._N2:>5d} {self._ROT:>6.1f} {self._REFELEM:^7d} ' \
               f'{self._SCCSYS:^4d} {self._SPCONST:^9d} {k1:>8.2E} {k2:>8.2E} {k3:>8.2E} {k4:>8.2E} {k5:>8.2E} ' \
               f'{k6:>8.2E} {tp:^4d} {co:^3d}'

    def commit(self):
        super().commit()
        # Update active constants
        self._model._ACTN1 = self._N2
        self._model._ACTROT = self._ROT
        self._model._ACTSPCONST = self._SPCONST
        self._model._LASTSC = self



    #
    # def create_sccopy(self, cmd):
    #     """
    #     Create a couple element from the command:
    #     SCCOPY, E1, E2, EINC, NTIMES, EST, NINC
    #         The SCCOPY command is used to copy an existing pattern of
    #         spring/couples using a pattern of existing nodes. The element
    #         numbering pattern will be preserved.
    #         E1     : First spring element in existing element pattern
    #                  (default=1)
    #         E2     : Last spring element in existing element pattern
    #                  (default=E1)
    #         EINC   : Element increment in existing element pattern (default=1)
    #         NTIMES : No of copies required
    #         EST    : First spring element (default=SCMAX+1)
    #         NINC   : Node increment between existing node sets (default=1)
    #     """
    #     cmd_vals = self._cmd_split(cmd, 7)
    #     e1 = try_int(cmd_vals[1], 1)
    #     e2 = try_int(cmd_vals[2], e1)
    #     einc = try_int(cmd_vals[3], 1)
    #     ntimes = try_int(cmd_vals[4], 1)
    #     est = try_int(cmd_vals[5], self._model.SCMAX + 1)
    #     ninc = try_int(cmd_vals[6], 1)
    #     # List couple elements
    #     couples = []
    #     for sc in range(e1, e2 + 1, einc):
    #         if sc in self._model.Couples:
    #             couples.append(self._model.get_couple(sc))
    #             # couples[-1]._calculate()
    #     for i in range(1, ntimes + 1):
    #         for sc in couples:
    #             # Create new couple element with same attributes then existing couple element
    #             new_attributes = dict()
    #             new_attributes['ELEM'] = est
    #             new_attributes['N1'] = sc.N1 + i * ninc
    #             new_attributes['N2'] = sc.N2 + i * ninc
    #             for attribute in ['ROT', 'REFELEM', 'SPCONST', 'SCCSYS']:
    #                 new_attributes[attribute] = getattr(sc, '_' + attribute)
    #             logging.debug('Copying couple element {}'.format(sc))
    #             Couple(self._model, **new_attributes)
    #             # Increment couple element number
    #             est += 1
    #
    # def create_scdel(self, cmd):
    #     """
    #     Delete couple elements from the command:
    #     SCDEL, E1, E2, EINC
    #         The SCDEL command is used to delete an existing pattern of
    #         spring/couples.
    #         E1   : First element in existing element pattern (no default) or
    #                Group No
    #         E2   : Last element in existing element pattern (default = E1)
    #         EINC : Element increment in existing element pattern (default = 1)
    #
    #         Using Groups If E1 is defined as a negative value (define E2 and
    #         EINC=0) then it will be interpreted as a Group No in the current
    #         Group SET. See GRPSET command.
    #     """
    #     logging.debug('No new couple element created')
    #     cmd_vals = self._cmd_split(cmd, 4)
    #     try:
    #         e1 = int(cmd_vals[1])
    #     except ValueError:
    #         logging.error('No default values for E1 in SCDEL command: {}'.format(cmd))
    #         raise NoDefault('No default values for E1 in SCDEL command: {}'.format(cmd))
    #     e2 = try_int(cmd_vals[2], e1)
    #     einc = try_int(cmd_vals[3], 1)
    #     if e1 < 0:
    #         logging.warning('Element group still to be implemented. SCDEL command will do nothing.')
    #     else:
    #         for sc in range(e1, e2 + 1, einc):
    #             if sc in self._model.Couples:
    #                 logging.debug('Removing couple element {}'.format(sc))
    #                 self._model.Couples.remove(sc)

    def calculate(self):
        """Calculate couple element properties: local coordinate system."""
        if self._calculated:
            return
        n1, n2 = self._model.NodeList.get(self._N1), self._model.NodeList.get(self._N2)
        self._p1 = n1.xyzg if n1 is not None else None
        self._p2 = n1.xyzg if n2 is not None else None
        # Check if there is a coordinate system specified, it will override any local cs defined
        if self._SCCSYS > 0:
            # Use defined coordinate system
            csys = self._model.CSysList.get(self._SCCSYS)
            self._i, self._j, self._k = csys.i, csys.j, csys.k
        # Check if there is a reference element associated, and just use the element coordinate system
        elif self._REFELEM > 0:
            e = self._model.ElementList.get(self._REFELEM)
            self._i, self._j, self._k = e.localX, e.localY, e.localZ
        # Otherwise, calculate the local coordinate system by the nodes
        else:
            # Check if N1 and N2 exist
            if (n1 is None) or (n2 is None):
                # If any of the nodes does not exist, use global coodinate system
                self._i = np.array([1, 0, 0], dtype=float)
                self._j = np.array([0, 1, 0], dtype=float)
                self._k = np.array([0, 0, 1], dtype=float)
            else:
                # Check if nodes N1 and N2 are the same, or coincident
                if np.isclose(np.linalg.norm(self._p2 - self._p1), 0.0):
                    # Use global coordinate system
                    self._i = np.array([1, 0, 0], dtype=float)
                    self._j = np.array([0, 1, 0], dtype=float)
                    self._k = np.array([0, 0, 1], dtype=float)
                else:
                    # Determine local coordinate system as you would for a beam element
                    self._i, self._j, self._k, self._ROT = calc_ijk(self._p1, self._p2, None, self._ROT)
        # Update flag
        super().calculate()

    # Properties
    @property
    def ELEM(self):
        """Couple element number"""
        return self.pk

    @property
    def N1(self):
        """Start node of couple element"""
        return self._model.NodeList.get(self._N1)

    @N1.setter
    def N1(self, value):
        self._N1 = int(value)
        self._calculated = False

    @property
    def N2(self):
        """End node of couple element"""
        return self._model.NodeList.get(self._N2)

    @N2.setter
    def N2(self, value):
        self._N2 = int(value)
        self._calculated = False

    @property
    def ROT(self):
        """Local couple element rotation angle"""
        return self._ROT

    @ROT.setter
    def ROT(self, value):
        self._ROT = float(value)
        self._calculated = False

    @property
    def REFELEM(self):
        """Reference element for local coordinate system"""
        return self._model.ElementList.get(self._REFELEM)

    @REFELEM.setter
    def REFELEM(self, value):
        self._REFELEM = int(value)
        self._calculated = False

    @property
    def SPCONST(self):
        """Spring constant property table code"""
        return self._model.CTypeList.get(self._SPCONST)

    @SPCONST.setter
    def SPCONST(self, value):
        self._SPCONST = int(value)
        self._calculated = False

    @property
    def SCCSYS(self):
        """Reference coordinate system"""
        return self._model.CSysList.get(self._SCCSYS)

    @SCCSYS.setter
    def SCCSYS(self, value):
        self._SCCSYS = int(value)
        self._calculated = False

    @property
    def p1(self):
        """Effective initial point coordinates"""
        self.calculate()
        return self._p1

    @property
    def p2(self):
        """Effective final point coordinates"""
        self.calculate()
        return self._p2

    @property
    def localX(self):
        """Couple element Local-X direction vector"""
        self.calculate()
        return self._i

    @property
    def localY(self):
        """Couple element Local-Y direction vector"""
        self.calculate()
        return self._j

    @property
    def localZ(self):
        """Couple element Local-Y direction vector"""
        self.calculate()
        return self._k
