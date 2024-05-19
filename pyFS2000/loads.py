import logging

import numpy as np
from icecream import ic

from .base import CalculatedMixin, FS2000Entity
from .exceptions import ParameterInvalid


class Load(CalculatedMixin, FS2000Entity):
    def __init__(self, model, loadcase, *args, **kwargs):
        self._loadcase = loadcase
        self._fres, self._mres = np.zeros(3), np.zeros(3)
        self._fx_cent, self._fy_cent, self._fz_cent = np.zeros(3), np.zeros(3), np.zeros(3)
        super().__init__(model, *args, **kwargs)
        self._loadcase.LoadList.append(self)
        self._loadcase._calculated = False

    def __repr__(self):
        return self.__str__()

    def sum(self):
        """Load resultant dictionary with centroids"""
        self.calculate()
        result = {
            'fx': self._fres[0], 'fy': self._fres[1], 'fz': self._fres[2],
            'fx_x': self._fx_cent[0], 'fx_y': self._fx_cent[1], 'fx_z': self._fx_cent[2],
            'fy_x': self._fy_cent[0], 'fy_y': self._fy_cent[1], 'fy_z': self._fy_cent[2],
            'fz_x': self._fz_cent[0], 'fz_y': self._fz_cent[1], 'fz_z': self._fz_cent[2],
        }
        return result

    @property
    def fres(self):
        """Resultant force in global coordinate system"""
        self.calculate()
        return self._fres

    @property
    def mres(self):
        """Resultant moment at origin in global coordinate system"""
        self.calculate()
        return self._mres

    @property
    def fx_cent(self):
        """Centroid of resultant of x-direction force"""
        return self._fx_cent

    @property
    def fy_cent(self):
        """Centroid of resultant of y-direction force"""
        return self._fy_cent

    @property
    def fz_cent(self):
        """Centroid of resultant of z-direction force"""
        return self._fz_cent


class LoadAccel(Load):
    type = 'ACCEL'
    parameters = ['GX', 'GY', 'GZ']
    paramdefaults = [0.0, 0.0, 0.0]

    def __init__(self, model, loadcase, *args, **kwargs):
        self._GX, self._GY, self._GZ = 0.0, 0.0, 0.0
        super().__init__(model, loadcase, *args, **kwargs)

    def calculate(self):
        if self._calculated:
            return
        self._fres, self._mres = np.zeros(3), np.zeros(3)
        self._fx_cent, self._fy_cent, self._fz_cent = np.zeros(3), np.zeros(3), np.zeros(3)
        accel = np.array([self._GX, self._GY, self._GZ])
        for element in self._model.ElementList:
            mass = element.length * element.GEOM.ax * element.MAT.DENS
            if element.GEOM.has_pipeprops:
                mass += element.length * (element.GEOM.insul_mass + element.GEOM.lining_mass + element.GEOM.cont_mass)
            f = mass * accel
            c = element.cog
            m = np.array([-f[1] * c[2] + f[2] * c[1], f[0] * c[2] - f[2] * c[0], -f[0] * c[1] + f[1] * c[0]])
            # Update totals
            self._fres += f
            self._mres += m
            self._fx_cent += f[0] * element.cog
            self._fy_cent += f[1] * element.cog
            self._fz_cent += f[2] * element.cog
        # Calculate centre of force
        self._fx_cent = self._fx_cent / self._fres[0] if not np.isclose(self._fres[0], 0.0) else np.zeros(3)
        self._fy_cent = self._fy_cent / self._fres[1] if not np.isclose(self._fres[1], 0.0) else np.zeros(3)
        self._fz_cent = self._fz_cent / self._fres[2] if not np.isclose(self._fres[2], 0.0) else np.zeros(3)
        # Update flag
        super().calculate()

    @property
    def GX(self):
        """Acceleration in global-X direction"""
        return self._GX

    @GX.setter
    def GX(self, value):
        self._GX = float(value)

    @property
    def GY(self):
        """Acceleration in global-Y direction"""
        return self._GY

    @GY.setter
    def GY(self, value):
        self._GY = float(value)

    @property
    def GZ(self):
        """Acceleration in global-Z direction"""
        return self._GZ

    @GZ.setter
    def GZ(self, value):
        self._GZ = float(value)


class LoadND(Load):
    type = 'ND'
    parameters = ['NODE', 'TX', 'TY', 'TZ', 'RX', 'RY', 'RZ']
    paramdefaults = [0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def __init__(self, model, loadcase, *args, **kwargs):
        self._NODE, self._TX, self._TY, self._TZ, self._RX, self._RY, self._RZ = 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        super().__init__(model, loadcase, *args, **kwargs)

    @property
    def TX(self):
        """Prescribed displacement in X-direction"""
        return self._TX

    @TX.setter
    def TX(self, value):
        self._TX = float(value)

    @property
    def TY(self):
        """Prescribed displacement in Y-direction"""
        return self._TY

    @TY.setter
    def TY(self, value):
        self._TY = float(value)

    @property
    def TZ(self):
        """Prescribed displacement in Z-direction"""
        return self._TZ

    @TZ.setter
    def TZ(self, value):
        self._TZ = float(value)

    @property
    def RX(self):
        """Prescribed rotation in X-direction"""
        return self._RX

    @RX.setter
    def RX(self, value):
        self._RX = float(value)

    @property
    def RY(self):
        """Prescribed rotation in Y-direction"""
        return self._RY

    @RY.setter
    def RY(self, value):
        self._RY = float(value)

    @property
    def RZ(self):
        """Prescribed rotation in Z-direction"""
        return self._RZ

    @RZ.setter
    def RZ(self, value):
        self._RZ = float(value)


class LoadNF(Load):
    type = 'NF'
    parameters = ['NODE', 'FX', 'FY', 'FZ', 'MX', 'MY', 'MZ', 'NMASS']
    paramdefaults = [0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def __init__(self, model, loadcase, *args, **kwargs):
        self._NODE, self._FX, self._FY, self._FZ, self._MX, self._MY, self._MZ = 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        self._NMASS = 0.0
        super().__init__(model, loadcase, *args, **kwargs)

    def calculate(self):
        if self._calculated:
            return
        fx, fy, fz, mx, my, mz = self._FX, self._FY, self._FZ, self._MX, self._MY, self._MZ
        x, y, z = self.model.NodeList.get(self._NODE).xyzg
        self._fres = np.array([fx, fy, fz], dtype=float)
        self._mres = np.array([mx - fy * z + fz * y, my + fx * z - fz * x, mz - fx * y + fy * z], dtype=float)
        self._fx_cent = np.array([x, y, z], dtype=float)
        self._fy_cent = np.array([x, y, z], dtype=float)
        self._fz_cent = np.array([x, y, z], dtype=float)
        # Update flag
        super().calculate()

    @property
    def NODE(self):
        """Node"""
        return self.model.NodeList.get(self._NODE)

    @NODE.setter
    def NODE(self, value):
        self._NODE = int(value)

    @property
    def FX(self):
        """Concentrated Force in X-direction"""
        return self._FX

    @FX.setter
    def FX(self, value):
        self._FX = float(value)

    @property
    def FY(self):
        """Concentrated Force in Y-direction"""
        return self._FY

    @FY.setter
    def FY(self, value):
        self._FY = float(value)

    @property
    def FZ(self):
        """Concentrated Force in Z-direction"""
        return self._FZ

    @FZ.setter
    def FZ(self, value):
        self._FZ = float(value)

    @property
    def MX(self):
        """Concentrated moment (couple) in X-direction"""
        return self._MX

    @MX.setter
    def MX(self, value):
        self._MX = float(value)

    @property
    def MY(self):
        """Concentrated moment (couple) in Y-direction"""
        return self._MY

    @MY.setter
    def MY(self, value):
        self._MY = float(value)

    @property
    def MZ(self):
        """Concentrated moment (couple) in Z-direction"""
        return self._MZ

    @MZ.setter
    def MZ(self, value):
        self._MZ = float(value)

    @property
    def NMASS(self):
        """Concentrated nodal mass"""
        return self._NMASS

    @NMASS.setter
    def NMASS(self, value):
        self._NMASS = float(value)


class LoadUDL(Load):
    type = 'UDL'
    parameters = ['ELEM', 'UDX', 'UDY', 'UDZ', 'COORD']
    paramdefaults = [0, 0.0, 0.0, 0.0, 1]

    def __init__(self, model, loadcase, *args, **kwargs):
        self._ELEM, self._UDX, self._UDY, self._UDZ, self._COORD = 0, 0.0, 0.0, 0.0, 1
        super().__init__(model, loadcase, *args, **kwargs)

    def calculate(self):
        if self._calculated:
            return
        element = self.model.ElementList.get(self._ELEM)
        if self._COORD == 1:
            # Global
            fx, fy, fz = self._UDX * element.length, self._UDY * element.length, self._UDZ * element.length
        elif self._COORD == 3:
            # Projected global
            fx = self._UDX * element.length * element.localX[0]
            fy = self._UDY * element.length * element.localY[1]
            fz = self._UDZ * element.length * element.localZ[2]
        else:
            logger = logging.getLogger('FS2000')
            logger.warning(f'Invalid UDL coordinate system {self._COORD}. '
                           f'It should be 1 for global or 3 for projected global')
            return
        x, y, z = element.cog
        self._fres = np.array([fx, fy, fz], dtype=float)
        self._mres = np.array([-fy * z + fz * y, fx * z - fz * x, -fx * y + fy * z], dtype=float)
        self._fx_cent = np.array([x, y, z], dtype=float)
        self._fy_cent = np.array([x, y, z], dtype=float)
        self._fz_cent = np.array([x, y, z], dtype=float)
        # Update flag
        super().calculate()

    @property
    def ELEM(self):
        """Element"""
        return self.model.ElementList.get(self._ELEM)

    @ELEM.setter
    def ELEM(self, value):
        self._ELEM = int(value)

    @property
    def UDX(self):
        """Load intensity in global X"""
        return self._UDX

    @UDX.setter
    def UDX(self, value):
        self._UDX = float(value)

    @property
    def UDY(self):
        """Load intensity in global Y"""
        return self._UDY

    @UDY.setter
    def UDY(self, value):
        self._UDY = float(value)

    @property
    def UDZ(self):
        """Load intensity in global Z"""
        return self._UDZ

    @UDZ.setter
    def UDZ(self, value):
        self._UDZ = float(value)

    @property
    def COORD(self):
        """Coordinate system - 1=Global, 3=Projected Global"""
        return self._COORD

    @COORD.setter
    def COORD(self, value):
        if int(value) not in [1, 3]:
            raise ParameterInvalid(f'UDL coordinate system {int(value)} invalid. '
                                   f'It should be 1 for global or 3 for projected global')
        self._COORD = int(value)


class LoadPUDL(Load):
    type = 'UDL'
    parameters = ['CODE', 'DIR', 'LOAD', 'COORD']
    paramdefaults = [0, 1, 0.0, 1]

    def __init__(self, model, loadcase, *args, **kwargs):
        self._CODE, self._DIR, self._LOAD, self._COORD = self.paramdefaults
        super().__init__(model, loadcase, *args, **kwargs)

    def calculate(self):
        if self._calculated:
            return
        self._fres, self._mres = np.zeros(3), np.zeros(3)
        self._fx_cent, self._fy_cent, self._fz_cent = np.zeros(3), np.zeros(3), np.zeros(3)
        for element in self._model.ElementList.filter(GEOM=self._CODE):
            f = np.zeros(3)
            if self._COORD == 1:
                f[self._DIR - 1] = self._LOAD * element.length
            elif self._COORD == 3:
                projection = [element.localX, element.localY, element.localZ][self._DIR - 1][self._DIR - 1]
                f[self._DIR - 1] = self._LOAD * element.length * projection
            c = element.cog
            m = np.array([-f[1] * c[2] + f[2] * c[1], f[0] * c[2] - f[2] * c[0], -f[0] * c[1] + f[1] * c[0]])
            # Update totals
            self._fres += f
            self._mres += m
            self._fx_cent += f[0] * element.cog
            self._fy_cent += f[1] * element.cog
            self._fz_cent += f[2] * element.cog
        # Calculate centre of force
        self._fx_cent = self._fx_cent / self._fres[0] if not np.isclose(self._fres[0], 0.0) else np.zeros(3)
        self._fy_cent = self._fy_cent / self._fres[1] if not np.isclose(self._fres[1], 0.0) else np.zeros(3)
        self._fz_cent = self._fz_cent / self._fres[2] if not np.isclose(self._fres[2], 0.0) else np.zeros(3)
        # Update flag
        super().calculate()

    @property
    def CODE(self):
        """Element Geometric Property"""
        return self.model.GeometryList.get(self._CODE)

    @CODE.setter
    def CODE(self, value):
        self._CODE = int(value)

    @property
    def DIR(self):
        """Load direction (global), 1 = X, 2 = Y, 3 = Z"""
        return self._DIR

    @DIR.setter
    def DIR(self, value):
        if int(value) not in [1, 2, 3]:
            raise ParameterInvalid(f'Invalid direction {int(value)}. It should be 1 for X, 2 for Y or 3 for Z')
        self._DIR = int(value)

    @property
    def LOAD(self):
        """Load magnitude"""
        return self._LOAD

    @LOAD.setter
    def LOAD(self, value):
        self._LOAD = float(value)

    @property
    def COORD(self):
        """Co-ordinate system (default = global) 1 Global,  3 Projected Global"""
        return self._COORD

    @COORD.setter
    def COORD(self, value):
        if int(value) not in [1, 3]:
            raise ParameterInvalid('Invalid corrdinate system. It should be 1 for Global or 2 for Projected Global')
        self._COORD = int(value)
