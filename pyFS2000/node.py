import logging
from icecream import ic
import numpy as np

from .base import FS2000Entity, ListedMixin, CalculatedMixin


class Node(ListedMixin, CalculatedMixin, FS2000Entity):
    """Defines an FS2000 model node."""
    type = 'N'
    parameters = ['NODE', 'X', 'Y', 'Z', 'CSYS']
    paramdefaults = [0, 0.0, 0.0, 0.0, 0]

    def __init__(self, model, *args, **kwargs):
        """Create a node within the model."""
        self._X, self._Y, self._Z, self._CSYS = 0.0, 0.0, 0.0, 0
        self._xg, self._yg, self._zg = 0.0, 0.0, 0.0
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        return f'Node={self.pk:>4d} , [ {self._X:>10.4f},{self._Y:>10.4f},{self._Z:>10.4f} ] , CSYS={self._CSYS:d}'

    def commit(self, replace=True, update_items=None):
        super().commit()
        # Update active constants
        self._model._LASTNODE = self
        self._model._ACTN = self.pk
        self._model._ACTN1 = self.pk
        self._model._ACTCSYS = self._CSYS

    def calculate(self):
        """Calculate node coordinates in global coordinate system."""
        gcoords = self.CSYS.local_to_global(np.array([self._X, self._Y, self._Z, 1.0]))
        self._xg, self._yg, self._zg = gcoords[0], gcoords[1], gcoords[2]
        super().calculate()

    def _update_local_coords(self):
        """Calculate local coordinates when a global coordinate has changed."""
        lcoords = self.CSYS.global_to_local(np.array([self._xg, self._yg, self._zg]))
        self._X, self._Y, self._Z = lcoords

    def convert_to_csys(self, csys):
        """Convert node to a different coordinate system"""
        # Calculate global coordinates to make sure they are up-to-date
        self.calculate()
        new_csys = self._model.CSysList.get(csys)
        self._X, self._Y, self._Z = new_csys.global_to_local(np.array([self._xg, self._yg, self._zg]))
        self._CSYS = new_csys.pk
        self.calculate()

    @property
    def X(self):
        """X-Coordinate in node coordinate system"""
        return self._X

    @X.setter
    def X(self, value):
        self._X = value
        self._calculated = False

    @property
    def Y(self):
        """Y-Coordinate in node coordinate system"""
        return self._Y

    @Y.setter
    def Y(self, value):
        self._Y = value
        self._calculated = False

    @property
    def Z(self):
        return self._Z

    @Z.setter
    def Z(self, value):
        self._Z = value
        self._calculated = False

    @property
    def xyz(self):
        """Vector containing node coordinates in node coordinate system"""
        return np.array([self._X, self._Y, self._Z])

    @xyz.setter
    def xyz(self, value):
        self._X, self._Y, self._Z = float(value[0]), float(value[1]), float(value[2])
        self._calculated = False

    @property
    def CSYS(self):
        """Node coordinate system number."""
        return self._model.CSysList.get(self._CSYS)

    @CSYS.setter
    def CSYS(self, value):
        self._CSYS = int(value)
        self._calculated = False

    @property
    def xg(self):
        """X-Coordinate in global cartesian coordinate system"""
        self.calculate()
        return self._xg

    @xg.setter
    def xg(self, value):
        self.calculate()
        self._xg = value
        self._update_local_coords()
        self._calculated = False

    @property
    def yg(self):
        """Y-Coordinate in global cartesian coordinate system"""
        self.calculate()
        return self._yg

    @yg.setter
    def yg(self, value):
        self.calculate()
        self._yg = value
        self._update_local_coords()
        self._calculated = False

    @property
    def zg(self):
        """Z-Coordinate in global cartesian coordinate system"""
        self.calculate()
        return self._zg

    @zg.setter
    def zg(self, value):
        self.calculate()
        self._zg = value
        self._update_local_coords()
        self._calculated = False

    @property
    def xyzg(self):
        self.calculate()
        return np.array([self._xg, self._yg, self._zg])

    @xyzg.setter
    def xyzg(self, value):
        self.calculate()
        self._xg, self._yg, self._zg = float(value[0]), float(value[1]), float(value[2])
        self._update_local_coords()
        self._calculated = False

    @property
    def NODE(self):
        """Node number"""
        return self.pk

    def distance_to(self, other):
        dx, dy, dz = self.xg - other.xg, self.yg - other.yg, self.zg - other.zg
        return np.sqrt(dx * dx + dy * dy + dz * dz)
