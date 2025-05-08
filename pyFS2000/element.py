import logging

import numpy as np
import scipy.spatial.transform.rotation as rot

from .aux_functions import calc_ijk
from .base import FS2000Entity, ListedMixin, CalculatedMixin
from .exceptions import ParameterInvalid


class Element(ListedMixin, CalculatedMixin, FS2000Entity):
    """Defines an FS2000 model beam element."""
    type = 'E'
    parameters = ['ELEM', 'N1', 'N2', 'N3', 'ROT', 'GEOM', 'MAT', 'RELZ', 'RELY', 'TAPER', 'TYPE', 'CO', 'BENDRAD']
    paramdefaults = [0, 0, 0, 0, 0.0, 1, 1, 0, 0, 0, 0, 0, 0.0]

    def __init__(self, model, *args, **kwargs):
        """Create an element within the model."""
        self._N1, self._N2, self._N3, self._ROT, self._GEOM, self._MAT = 0, 0, 0, 0.0, 1, 1
        self._RELZ, self._RELY, self._TAPER, self._TYPE, self._CO, self._BENDRAD = 0, 0, 0, 0, 0, 0.0
        self._p1, self._p2, self._p3 = None, None, None
        self._i, self._j, self._k = None, None, None
        self._off1, self._off2 = np.zeros(3), np.zeros(3)
        self._bendang, self._length, self._bendcent, self._cog = 0.0, 0.0, np.zeros(3), np.zeros(3)
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        self.calculate()
        bend_comp = '' if np.isclose(self._BENDRAD, 0.0) else f'  Bend Radius = {self._BENDRAD:.4f}  ' \
                                                              f'Angle = {np.degrees(self._bendang):.2f}'
        return f'Elem Nod1 Nod2 Nod3    Rot    Length Geom Tapered Mat RelZ RelY Type CO\n' \
               f'{self.pk:>4} {self._N1:>4} {self._N2:>4} {self._N3 if self._N3 > 0 else "":>4} {self._ROT:>6.1f} ' \
               f'{self._length:>9.4f} {self._GEOM:>4} {self._TAPER if self._TAPER > 0 else "":>7} {self._MAT:>3} ' \
               f'{self._RELZ:>4} {self._RELY:>4} {self._TYPE:>4} {self._CO:>2}{bend_comp}'

    def commit(self, replace=True, update_items=None):
        super().commit()
        # Update active constants
        self._model._ACTN1 = self._N2
        self._model._ACTN3 = self._N3
        self._model._ACTROT = self._ROT
        self._model._ACTGEOM = self._GEOM
        self._model._ACTMAT = self._MAT
        self._model._ACTRELZ = self._RELZ
        self._model._ACTRELY = self._RELY
        self._model._ACTTYPE = self._TYPE
        self._model._ACTCON = self._CO
        self._model._LASTELEM = self

    def calculate(self):
        """
        Calculate element properties: local coordinate system, bend radius,
        length.
        """
        if self._calculated:
            return
        # Update calculated flage
        super().calculate()
        # Get logger
        logger = logging.getLogger('FS2000')
        # Local coordinate system
        # Check if nodes N1 and N2 exist
        if (self._N1 in self._model.NodeList) and (self._N2 in self._model.NodeList):
            # Calculate and save initial and final end point coordinates, and reference point coordinates if any
            self._p1, self._p2 = self._model.NodeList.get(self._N1).xyzg, self._model.NodeList.get(self._N2).xyzg
            self._p3 = self._model.NodeList.get(self._N3).xyzg if self._N3 > 0 else None
            # Calculate and save local CS vectors with no offsets
            self._i, self._j, self._k, self._ROT = calc_ijk(self._p1, self._p2, self._p3, self._ROT)
            # Apply offsets
            eof = self._model.ElemOffsetList.get(self.pk)
            if eof is not None:
                off = [np.array([0, 0, 0]), np.array([0, 0, 0])]
                # Element End id Code: 1 - First node only, 2 - Second node only, 3 - Both nodes
                node_offset_options = [[1, 3], [2, 3]]
                # Node offsets
                for node_end in [0, 1]:
                    if eof.NOEF in node_offset_options[node_end]:
                        if getattr(eof, f'_EREF{node_end + 1}') == 0:
                            # Global coordinates
                            off[node_end] = np.array([getattr(eof, f'_X{node_end + 1}'),
                                                      getattr(eof, f'_Y{node_end + 1}'),
                                                      getattr(eof, f'_Z{node_end + 1}')])
                        else:
                            # Local coordinates, may be from the element itself or another element
                            # eref = self if getattr(eof, f'EREF{node_end+1}') == self.pk else \
                            #     self._model.get_element(getattr(eof, f'EREF{node_end+1}'))
                            eref = self._model.ElementList.get(getattr(eof, f'EREF{node_end + 1}'))
                            if eref != self:
                                eref.calculate()
                            xi = getattr(eof, f'X{node_end + 1}')
                            yi = getattr(eof, f'Y{node_end + 1}')
                            zi = getattr(eof, f'Z{node_end + 1}')
                            off[node_end] = xi * eref.localX + yi * eref.localY + zi * eref.localZ
                # Save calculated offsets
                self._off1, self._off2 = off[0], off[1]
                # Recalculate and save offseted p1 and p2
                self._p1, self._p2 = self._p1 + self._off1, self._p2 + self._off2
                # Recalculate and save local CS vectors
                self._i, self._j, self._k, self._ROT = calc_ijk(self._p1, self._p2, self._p3, self._ROT)
        else:
            # Attribute defaults
            self._p1, self._p2, self._p3 = np.zeros(3), np.zeros(3), np.zeros(3)
            self._i = np.array([1, 0, 0], dtype=float)
            self._j = np.array([0, 1, 0], dtype=float)
            self._k = np.array([0, 0, 1], dtype=float)
            # Raise warning
            if (self._N1 not in self._model.NodeList) and (self._N2 not in self._model.NodeList):
                txt = f'Undefined nodes {self._N1} and {self._N2} in element {self.pk}.'
            else:
                txt = f'Undefined node {self._N1 if self._N1 not in self._model.NodeList else self._N2} ' \
                      f'in element {self.pk}'
            logger.warning(txt)
        # Bend angle (if applicable)
        if self._TYPE in [2, 3]:
            # logger.debug('Calculating element {} bend angle.'.format(self.pk))
            # Find end points
            if self._TYPE == 3:
                # If element is type 3, the third node is the bend centre
                pc1, pc2 = self._p1 - self._p3, self._p2 - self._p3
                # Check sizes
                if not (np.isclose(np.linalg.norm(pc1), np.linalg.norm(pc2), atol=1.0E-4) and
                        (np.isclose(np.linalg.norm(pc1), self._BENDRAD, atol=1.0E-4)) and
                        (np.isclose(np.linalg.norm(pc2), self._BENDRAD, atol=1.0E-4))):
                    logger.warning(f'Bend radius does not match node distances in element {self.pk}. '
                                   f'BENDRAD={self._BENDRAD}, dist1={np.linalg.norm(pc1)}, '
                                   f'dist2={np.linalg.norm(pc2)}')
                # Calculate the angle between the two vectors
                self._bendang = np.arccos(np.dot(pc1, pc2) / (np.linalg.norm(pc1) * np.linalg.norm(pc2)))
            else:
                # If element is type 2, the third node is the intersection of the tangents
                pi1, pi2 = self._p1 - self._p3, self._p2 - self._p3
                # Check distances
                if not np.isclose(np.linalg.norm(pi1), np.linalg.norm(pi2), atol=1.0E-4):
                    logger.warning(f'Bend tangent distances do not match in element {self.pk}: '
                                   f'tan1={np.linalg.norm(pi1)}, tan2={np.linalg.norm(pi2)}')
                # Calculate the angle between two vectors. The bend angle is equal to pi minus the angle
                # between the tangents
                self._bendang = np.pi - np.arccos(np.dot(pi1, pi2) / (np.linalg.norm(pi1) * np.linalg.norm(pi2)))
            if self._bendang > np.pi / 2:
                logger.warning(f'FS2000 restricts the bend angle between 0 and 90 degress. '
                               f'Calculated value is {np.degrees(self._bendang):.2f}. Watch out for consistency.')
            # Bend centre
            if self._TYPE == 3:
                # If type is 3, P3 is already the bend centre
                self._bendcent = self._p3
            else:
                # Otherwise, it has to be calculated
                a, b = self._p1 - self._p3, self._p2 - self._p3
                c = np.cross(b, a)
                a, b, c = a / np.linalg.norm(a), b / np.linalg.norm(b), c / np.linalg.norm(c)
                r = rot.Rotation.from_rotvec(np.pi / 2 * c)
                ap, bp = r.apply(a), r.apply(b)
                # System
                # p1 + r1*ap = p2 + r2*bp = centre
                # ap*r1 - bp*r2 = p2 - p1
                # [ [ ap[0], -bp[0] ]       [ [r1]      [ [ p2[0]-p1[0] ]
                #   [ ap[1], -bp[1] ]    *    [r2] ]  =   [ p2[1]-p1[1] ]
                #   [ ap[2], -bp[2] ] ]                   [ p2[2]-p1[2] ] ]
                mat_a = np.array([[ap[0], -bp[0]], [ap[1], -bp[1]], [ap[2], -bp[2]]])
                delta_p = np.array(
                    [[self._p2[0] - self._p1[0]], [self._p2[1] - self._p1[1]], [self._p2[2] - self._p1[2]]])
                mat_r = np.linalg.lstsq(mat_a, delta_p, rcond=None)[0]
                r1, r2 = mat_r[0][0], mat_r[1][0]
                self._bendcent = self._p1 + ap * r1  # could be p2 + bp * r2, supposed to be equivalent
        # Element length and C.o.G.
        if self._TYPE in [2, 3]:
            self._length = self._BENDRAD * self._bendang
            # Bend cog in local coordinate x-y, origin in bend centre, x in direction of p1, y perpendicular
            # in direction of p2
            x, y = self._p1 - self._bendcent, self._p2 - self._bendcent
            py = np.dot(y, x) / np.dot(x, x) * x                 # projection of y in x
            y = y - py                                           # now y is perpendicular to x
            x, y = x / np.linalg.norm(x), y / np.linalg.norm(y)  # Now both vectors are unitary
            x_cog = self._BENDRAD * np.sin(self._bendang) / self._bendang        # CoG x-coordinate in x-y plane
            y_cog = self._BENDRAD * (1 - np.cos(self._bendang)) / self._bendang  # CoG y-coordinate in x-y plane
            self._cog = x_cog * x + y_cog + y  # CoG in global coordinates
        else:
            self._length = np.linalg.norm(self._p2 - self._p1)
            self._cog = (self._p1 + self._p2) / 2

    @property
    def length(self):
        """Element length (considering offsets and bends)"""
        self.calculate()
        return self._length

    @property
    def bendang(self):
        """Angle of a bend element, in degrees"""
        self.calculate()
        if self._TYPE not in [2, 3]:
            return 0.0
        return np.degrees(self._bendang)

    @property
    def ELEM(self):
        """Element number"""
        return self.pk

    @property
    def N1(self):
        """Start node of element"""
        return self._model.NodeList.get(self._N1)

    @N1.setter
    def N1(self, value):
        self._N1 = int(value)
        self._calculated = False

    @property
    def N2(self):
        """End node of element"""
        return self._model.NodeList.get(self._N2)

    @N2.setter
    def N2(self, value):
        self._N2 = int(value)
        self._calculated = False

    @property
    def N3(self):
        """Third node of element used to define local rotation"""
        return self._model.NodeList.get(self._N3)

    @N3.setter
    def N3(self, value):
        self._N3 = int(value)
        self._calculated = False

    @property
    def ROT(self):
        """Local element rotation angle"""
        return self._ROT

    @ROT.setter
    def ROT(self, value):
        # if self._N3 > 0:
        #     logger = logging.getLogger('FS2000')
        #     logger.warning('ROT definition will be meaningless when third node N3 is defined')
        self._ROT = float(value)
        self._calculated = False

    @property
    def GEOM(self):
        """Geometrical property table code"""
        return self._model.GeometryList.get(self._GEOM)

    @GEOM.setter
    def GEOM(self, value):
        self._GEOM = int(value)
        self._calculated = False

    @property
    def MAT(self):
        """Material Property table code"""
        return self._model.MaterialList.get(self._MAT)

    @MAT.setter
    def MAT(self, value):
        self._MAT = int(value)
        self._calculated = False

    @property
    def RELZ(self):
        """Hinge Definition - local-z axis"""
        return self._RELZ

    @RELZ.setter
    def RELZ(self, value):
        value_error, relz = False, 0
        try:
            relz = int(value)
        except ValueError:
            value_error = True
        if (relz not in [0, 1, 2, 3]) or value_error:
            raise ParameterInvalid(f'Invalid RELZ value: {value}. Should be (0, 1, 2 or 3)')
        self._RELZ = relz

    @property
    def RELY(self):
        """Hinge Definition - local-y axis"""
        return self._RELY

    @RELY.setter
    def RELY(self, value):
        value_error, rely = False, 0
        try:
            rely = int(value)
        except ValueError:
            value_error = True
        if (rely not in [0, 1, 2, 3]) or value_error:
            raise ParameterInvalid(f'Invalid RELY value: {value}. Should be (0, 1, 2 or 3)')
        self._RELY = rely

    @property
    def TAPER(self):
        """
        This is used to identify tapered beams by defining the geom property
        code at the end node of an element.
        A +ve value signifies a Type A Taper,
        A -ve value signifies a Type B Taper.
        Default is 0, no taper
        """
        return self._TAPER

    @TAPER.setter
    def TAPER(self, value):
        self._TAPER = int(value)
        self._calculated = False

    @property
    def TYPE(self):
        """Element Type"""
        return self._TYPE

    @TYPE.setter
    def TYPE(self, value):
        value_error, t = False, 0
        try:
            t = int(value)
        except ValueError:
            value_error = True
        if (t not in [0, 2, 3, 6, 7, 8, 15, 16]) or value_error:
            raise ParameterInvalid(f'Invalid Element TYPE value: {value}. Should be (0, 2, 3, 6, 7, 8, 15 or 16)')
        self._TYPE = t
        self._calculated = False

    @property
    def CO(self):
        """Additional CO constant"""
        return self._CO

    @CO.setter
    def CO(self, value):
        self._CO = int(value)
        self._calculated = False

    @property
    def BENDRAD(self):
        """Bend radius for Type 2 and Type 3 elements"""
        return self._BENDRAD

    @BENDRAD.setter
    def BENDRAD(self, value):
        self._BENDRAD = float(value)
        self._calculated = False

    @property
    def bendcent(self):
        """Bend Centre for Type 2 and Type 3 elements"""
        # Return None if element is not a bend
        if self._TYPE not in [2, 3]:
            return None
        self.calculate()
        return self._bendcent

    @property
    def p1(self):
        """Effective initial point coordinates (considering offsets)"""
        self.calculate()
        return self._p1

    @property
    def p2(self):
        """Effective final point coordinates (considering offsets)"""
        self.calculate()
        return self._p2

    @property
    def p3(self):
        """Reference point coordinates"""
        self.calculate()
        return self._p3

    @property
    def cog(self):
        """Element Centre of Gravity"""
        self.calculate()
        return self._cog

    @property
    def localX(self):
        """Element Local-X direction vector"""
        self.calculate()
        return self._i

    @property
    def localY(self):
        """Element Local-X direction vector"""
        self.calculate()
        return self._j

    @property
    def localZ(self):
        """Element Local-X direction vector"""
        self.calculate()
        return self._k
