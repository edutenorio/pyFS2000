import logging

import numpy as np
from icecream import ic

from .base import CalculatedMixin, FS2000Entity
from .load_base import LoadCalcMixin
from .exceptions import ParameterInvalid


class Load(LoadCalcMixin, FS2000Entity):
    def __init__(self, model, loadcase, *args, **kwargs):
        self._loadcase = loadcase
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        return self.__str__()

    def commit(self):
        self._loadcase.LoadList.append(self)
        self._loadcase._calculated = False



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
        load_list = []
        for element in self._model.ElementList:
            mass_per_length = element.GEOM.ax * element.MAT.DENS
            if element.GEOM.has_pipeprops:
                mass_per_length += element.GEOM.insul_mass + element.GEOM.lining_mass + element.GEOM.cont_mass
            udl = LoadUDL(self._model, self._loadcase, ELEM=element.pk, COORD=1)
            udl.UDX, udl.UDY, udl.UDZ = mass_per_length * np.array([self._GX, self._GY, self._GZ])
            load_list.append(udl)
        self.calculate_from_list(load_list)

    @property
    def GX(self):
        """Acceleration in global-X direction"""
        return self._GX

    @GX.setter
    def GX(self, value):
        self._GX = float(value)
        self._calculated = False

    @property
    def GY(self):
        """Acceleration in global-Y direction"""
        return self._GY

    @GY.setter
    def GY(self, value):
        self._GY = float(value)
        self._calculated = False

    @property
    def GZ(self):
        """Acceleration in global-Z direction"""
        return self._GZ

    @GZ.setter
    def GZ(self, value):
        self._GZ = float(value)
        self._calculated = False


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
        self._calculated = False

    @property
    def TY(self):
        """Prescribed displacement in Y-direction"""
        return self._TY

    @TY.setter
    def TY(self, value):
        self._TY = float(value)
        self._calculated = False

    @property
    def TZ(self):
        """Prescribed displacement in Z-direction"""
        return self._TZ

    @TZ.setter
    def TZ(self, value):
        self._TZ = float(value)
        self._calculated = False

    @property
    def RX(self):
        """Prescribed rotation in X-direction"""
        return self._RX

    @RX.setter
    def RX(self, value):
        self._RX = float(value)
        self._calculated = False

    @property
    def RY(self):
        """Prescribed rotation in Y-direction"""
        return self._RY

    @RY.setter
    def RY(self, value):
        self._RY = float(value)
        self._calculated = False

    @property
    def RZ(self):
        """Prescribed rotation in Z-direction"""
        return self._RZ

    @RZ.setter
    def RZ(self, value):
        self._RZ = float(value)
        self._calculated = False


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
        self._mres = np.array([mx, my, mz]) + LoadCalcMixin.global_moment([fx, fy, fx], [x, y, z])
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
        self._calculated = False

    @property
    def FX(self):
        """Concentrated Force in X-direction"""
        return self._FX

    @FX.setter
    def FX(self, value):
        self._FX = float(value)
        self._calculated = False

    @property
    def FY(self):
        """Concentrated Force in Y-direction"""
        return self._FY

    @FY.setter
    def FY(self, value):
        self._FY = float(value)
        self._calculated = False

    @property
    def FZ(self):
        """Concentrated Force in Z-direction"""
        return self._FZ

    @FZ.setter
    def FZ(self, value):
        self._FZ = float(value)
        self._calculated = False

    @property
    def MX(self):
        """Concentrated moment (couple) in X-direction"""
        return self._MX

    @MX.setter
    def MX(self, value):
        self._MX = float(value)
        self._calculated = False

    @property
    def MY(self):
        """Concentrated moment (couple) in Y-direction"""
        return self._MY

    @MY.setter
    def MY(self, value):
        self._MY = float(value)
        self._calculated = False

    @property
    def MZ(self):
        """Concentrated moment (couple) in Z-direction"""
        return self._MZ

    @MZ.setter
    def MZ(self, value):
        self._MZ = float(value)
        self._calculated = False

    @property
    def NMASS(self):
        """Concentrated nodal mass"""
        return self._NMASS

    @NMASS.setter
    def NMASS(self, value):
        self._NMASS = float(value)
        self._calculated = False


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
        self._mres = LoadCalcMixin.global_moment([fx, fy, fz], [x, y, z])
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
        self._calculated = False

    @property
    def UDX(self):
        """Load intensity in global X"""
        return self._UDX

    @UDX.setter
    def UDX(self, value):
        self._UDX = float(value)
        self._calculated = False

    @property
    def UDY(self):
        """Load intensity in global Y"""
        return self._UDY

    @UDY.setter
    def UDY(self, value):
        self._UDY = float(value)
        self._calculated = False

    @property
    def UDZ(self):
        """Load intensity in global Z"""
        return self._UDZ

    @UDZ.setter
    def UDZ(self, value):
        self._UDZ = float(value)
        self._calculated = False

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
        self._calculated = False


class LoadPUDL(Load):
    type = 'PUDL'
    parameters = ['CODE', 'DIR', 'LOAD', 'COORD']
    paramdefaults = [0, 1, 0.0, 1]

    def __init__(self, model, loadcase, *args, **kwargs):
        self._CODE, self._DIR, self._LOAD, self._COORD = self.paramdefaults
        super().__init__(model, loadcase, *args, **kwargs)

    def calculate(self):
        if self._calculated:
            return
        # Create a UDL load list from all elements with the specified geometric property
        load_list = []
        for element in self._model.ElementList.filter(GEOM=self._CODE):
            load = LoadUDL(self._model, self._loadcase, ELEM=element.pk, COORD=self._COORD)
            if self._COORD == 1:
                load.UDX = self._LOAD if self._DIR == 1 else 0.0
                load.UDY = self._LOAD if self._DIR == 2 else 0.0
                load.UDZ = self._LOAD if self._DIR == 3 else 0.0
            elif self._COORD == 3:
                projection = [element.localX, element.localY, element.localZ][self._DIR - 1][self._DIR - 1]
                load.UDX = self._LOAD * projection if self._DIR == 1 else 0.0
                load.UDY = self._LOAD * projection if self._DIR == 2 else 0.0
                load.UDZ = self._LOAD * projection if self._DIR == 3 else 0.0
            load_list.append(load)
        self.calculate_from_list(load_list)
        # Update flag
        super().calculate()

    @property
    def CODE(self):
        """Element Geometric Property"""
        return self.model.GeometryList.get(self._CODE)

    @CODE.setter
    def CODE(self, value):
        self._CODE = int(value)
        self._calculated = False

    @property
    def DIR(self):
        """Load direction (global), 1 = X, 2 = Y, 3 = Z"""
        return self._DIR

    @DIR.setter
    def DIR(self, value):
        if int(value) not in [1, 2, 3]:
            raise ParameterInvalid(f'Invalid direction {int(value)}. It should be 1 for X, 2 for Y or 3 for Z')
        self._DIR = int(value)
        self._calculated = False

    @property
    def LOAD(self):
        """Load magnitude"""
        return self._LOAD

    @LOAD.setter
    def LOAD(self, value):
        self._LOAD = float(value)
        self._calculated = False

    @property
    def COORD(self):
        """Co-ordinate system (default = global) 1 Global,  3 Projected Global"""
        return self._COORD

    @COORD.setter
    def COORD(self, value):
        if int(value) not in [1, 3]:
            raise ParameterInvalid('Invalid corrdinate system. It should be 1 for Global or 2 for Projected Global')
        self._COORD = int(value)
        self._calculated = False
