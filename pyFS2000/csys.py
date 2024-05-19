import logging

from icecream import ic
from numpy import array, dot, cross, matmul, cos, radians, sin
from numpy.linalg import norm, inv

from .aux_functions import cylindrical_to_cartesian, spherical_to_cartesian, conical_to_cartesian
from .aux_functions import cartesian_to_cylindrical, cartesian_to_spherical, cartesian_to_conical
from .base import FS2000Entity, ListedMixin, CalculatedMixin
from .exceptions import ParameterInvalid


class CSys(ListedMixin, CalculatedMixin, FS2000Entity):
    """Defines an FS2000 coordinate system."""
    type = 'CSYS'
    parameters = ['NO', 'TYPE', 'T1', 'T2', 'T3', 'RX', 'RY', 'RZ', 'P1', 'P2', 'N3']
    paramdefaults = [0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1]
    _pkbounds = (6, 20)

    def __init__(self, model, *args, **kwargs):
        """Create a new coordinate system.

        Syntaxes:
        s1 = CSys(model, cmd)
            cmd is a command line of the form:
            'CSYS, No, Type, T1, T2, T3, RX, RY, RZ, P1, P2, N3'

        s2 = CSys(model, t1=0, t2=0, t3=5.0, ry=60)
            Define a coordinate system using keywords Valid keywords are (not
            case sensitive):
            'CSYS','T1','TX','T2','TY','T3','TZ','RX','RY','RZ','P1','P2','N3'
            Obs. 'T1' and 'TX' have same meaning. Same for 'T2'/'TY' and
            'T3'/'TZ'
            Any keyword not defined will recieve default values.
            """
        # Check for alternative keyword definitions of T1/TX, T2/TY, T3/TZ before calling the constructor
        corresp = {'TX': 'T1', 'TY': 'T2', 'TZ': 'T3'}
        for kw in kwargs:
            if kw in corresp.keys():
                # If 'TX' is passed as keyword parameter, it will be assigned to 'T1' and 'TX' will be deleted.
                # Same for 'TY' to 'T2' and 'TZ' to 'T3'.
                value = kwargs.pop(kw)
                kwargs[corresp[kw.upper()]] = value
        # Internal parameters
        self._TYPE = 0
        self._T1, self._T2, self._T3 = 0.0, 0.0, 0.0
        self._RX, self._RY, self._RZ = 0.0, 0.0, 0.0
        self._P1, self._P2, self._N3 = 0.0, 0.0, 0
        self._o = array([0, 0, 0], dtype=float)  # System origin, in global coordinates
        self._i = array([1, 0, 0], dtype=float)  # Canonical vector i, in global coordinates
        self._j = array([0, 1, 0], dtype=float)  # Canonical vector j, in global coordinates
        self._k = array([0, 0, 1], dtype=float)  # Canonical vector k, in global coordinates
        self._Tl2g = array([[1, 0, 0, 0],
                            [0, 1, 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]], dtype=float)  # Transformation matrix local to global
        self._Tg2l = array([[1, 0, 0, 0],
                            [0, 1, 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]], dtype=float)  # Transformation matrix global to local
        # Call base class constructor
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        r = f'CSYS={self.pk:>2d}, ' \
            f'Type={["0-Cartesian", "1-Cylindrical", "2-Spherical", "3-Conical"][self._TYPE]:^13s}, '
        if self._N3 == -1:
            r += f'3-nodes: [{self._T1:>4d},{self._T2:>4d},{self._T3:>4d}]'
        else:
            r += f'Origin: [{self._T1:>9.4f},{self._T2:>9.4f},{self._T3:>9.4f}], ' \
                 f'Rotations = [{self._RX:>7.2f},{self._RY:>7.2f},{self._RZ:>7.2f}]'
        if self._TYPE == 3:
            r += f' , R0={self._P1:>9.4f}, Theta={self._P2:>6.2f}'
        return r

    def calculate(self):
        """Calculate the transformation matrices."""
        if self.calculated:
            return
        # Set origin of the system
        if self._N3 == -1:
            # 3-node definition. These nodes should be defined in the global coordinate system
            p0 = self._model.get_node(self._T1).xyzg
            px = self._model.get_node(self._T2).xyzg
            py = self._model.get_node(self._T3).xyzg
            self._o[0], self._o[1], self._o[2] = p0[0], p0[1], p0[2]
            # Define the canonical vector 'i'
            self._i = (px - p0) / norm(px - p0)
            # Define the vector 'j' and make sure it is perpendicular to 'i' and unitary
            self._j = (py - p0) / norm(py - p0)
            self._j = self._j - dot(self._j, self._i) * self._i
            self._j /= norm(self._j)
            # Define vector 'k' as the cross product between 'i' and 'j'
            self._k = cross(self._i, self._j)
            # Transformation Matrix : global to local
            m1 = array([[1, 0, 0, -self._o[0]],
                        [0, 1, 0, -self._o[1]],
                        [0, 0, 1, -self._o[2]],
                        [0, 0, 0, 1]])
            m2 = array([[self._i[0], self._i[1], self._i[2], 0],
                        [self._j[0], self._j[1], self._j[2], 0],
                        [self._k[0], self._k[1], self._k[2], 0],
                        [0, 0, 0, 1]])
            self._Tg2l = matmul(m2, m1)
            # Transformation matrtix : local to global
            self._Tl2g = inv(self._Tg2l)
        else:
            # Definition by XYZ-coordinates and Y-Z-X rotations
            self._o[0], self._o[1], self._o[2] = self._T1, self._T2, self._T3
            m1 = array([[1, 0, 0, -self._o[0]],
                        [0, 1, 0, -self._o[1]],
                        [0, 0, 1, -self._o[2]],
                        [0, 0, 0, 1]])
            rx, ry, rz = radians([self._RX, self._RY, self._RZ])
            m2 = array([[cos(ry), 0, -sin(ry), 0],
                        [0, 1, 0, 0],
                        [sin(ry), 0, cos(ry), 0],
                        [0, 0, 0, 1]])
            m3 = array([[cos(rz), sin(rz), 0, 0],
                        [-sin(rz), cos(rz), 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
            m4 = array([[1, 0, 0, 0],
                        [0, cos(rx), sin(rx), 0],
                        [0, -sin(rx), cos(rx), 0],
                        [0, 0, 0, 1]])
            # Canonical vectors
            m_ijk = matmul(m4, matmul(m3, m2))
            self._i[0], self._i[1], self._i[2] = m_ijk[0][0], m_ijk[0][1], m_ijk[0][2]
            self._j[0], self._j[1], self._j[2] = m_ijk[1][0], m_ijk[1][1], m_ijk[1][2]
            self._k[0], self._k[1], self._k[2] = m_ijk[2][0], m_ijk[2][1], m_ijk[2][2]
            # Transformation Matrix : global to local
            self._Tg2l = matmul(m_ijk, m1)
            # Transformation matrtix : local to global
            self._Tl2g = inv(self._Tg2l)
        # Set calculated flag to True
        super().calculate()

    # Properties
    @property
    def NO(self):
        """Co-ordinate system number"""
        return self.pk

    @property
    def TYPE(self):
        """
        Co-ordinate system type (0-Cartesian, 1-Cylindrical,
        2-Spherical, 3-Conical)
        """
        return self._TYPE

    @TYPE.setter
    def TYPE(self, value):
        if value not in [0, 1, 2, 3]:
            logging.error(f'Invalid CSYS type {self._TYPE}. Should be 0, 1, 2 or 3.')
            raise ParameterInvalid(f'Invalid CSYS type {self._TYPE}. Should be 0, 1, 2 or 3.')
        self._TYPE = value

    @property
    def T1(self):
        """
        Co-ordinate X of origin in Global Cartesian, or node 1 of 3 that define
        the x-y plane if N3=-1
        """
        return self._T1

    @T1.setter
    def T1(self, value):
        self._T1 = value

    @property
    def T2(self):
        """
        Co-ordinate Y of origin in Global Cartesian, or node 2 of 3 that define
        the x-y plane if N3=-1
        """
        return self._T2

    @T2.setter
    def T2(self, value):
        self._T2 = value

    @property
    def T3(self):
        """
        Co-ordinate Z of origin in Global Cartesian, or node 3 of 3 that define
        the x-y plane if N3=-1
        """
        return self._T3

    @T3.setter
    def T3(self, value):
        self._T3 = value

    @property
    def RX(self):
        """Rotationnal orientation around X-axis (degrees). Not used if N3=-1"""
        return self._RX

    @RX.setter
    def RX(self, value):
        self._RX = value

    @property
    def RY(self):
        """Rotationnal orientation around Y-axis (degrees). Not used if N3=-1"""
        return self._RY

    @RY.setter
    def RY(self, value):
        self._RY = value

    @property
    def RZ(self):
        """Rotationnal orientation around Z-axis (degrees). Not used if N3=-1"""
        return self._RZ

    @RZ.setter
    def RZ(self, value):
        self._RZ = value

    @property
    def P1(self):
        """For conical systems, P1 is the radius at Z=0"""
        return self._P1

    @P1.setter
    def P1(self, value):
        self._P1 = value

    @property
    def P2(self):
        """For conical systems, P2 is the cone angle"""
        return self._P2

    @P2.setter
    def P2(self, value):
        self._P2 = value

    @property
    def N3(self):
        """
        If N3 = -1 then T1, T2, T3 are used to identify 3 nodes that define
        the x-y plane
        """
        return self._N3

    @N3.setter
    def N3(self, value):
        self._N3 = value

    @property
    def i(self):
        """Canonical Vector i in global coordinates"""
        self.calculate()
        return self._i

    @property
    def j(self):
        """Canonical Vector j in global coordinates"""
        self.calculate()
        return self._j

    @property
    def k(self):
        """Canonical Vector k in global coordinates"""
        self.calculate()
        return self._k

    # Public functions
    def local_to_global(self, point, dim=3):
        """Convert a point in local coordinates to global cartesian system."""
        self.calculate()
        # Set a vector with the point coordinates in local coordinate system
        pl = array([point[0], point[1], point[2], 1], dtype=float)
        # Converto to cartesian
        if self._TYPE == 0:
            # Cartesian (do nothing)
            pass
        elif self._TYPE == 1:
            pl = cylindrical_to_cartesian(pl)
        elif self._TYPE == 2:
            pl = spherical_to_cartesian(pl)
        elif self._TYPE == 3:
            pl = conical_to_cartesian(pl, self._P1, self._P2)
        # Calculate transformation in cartesian coordinates
        pg = matmul(self._Tl2g, pl)
        # Return global coordinates
        return pg[:dim]

    def global_to_local(self, point, dim=3):
        """
        Convert a point in global cartesian coordinates to system local
        coordinates.
        """
        # Calculate coordinate system parameters if not calculated yet
        if not self.calculated:
            self.calculate()
        # Set a vector with the point coordinates (assumes global is always cartesian)
        pg = array([point[0], point[1], point[2], 1], dtype=float)
        # Calculate transformation in cartesian coordinates
        pl = matmul(self._Tg2l, pg)
        # Transform to system type
        if self._TYPE == 0:
            # Cartesian (do nothing)
            pass
        elif self._TYPE == 1:
            pl = cartesian_to_cylindrical(pl)
        elif self._TYPE == 2:
            pl = cartesian_to_spherical(pl)
        elif self._TYPE == 3:
            pl = cartesian_to_conical(pl, self._P1, self._P2)
        # Return local coordinates
        return pl[:dim]
