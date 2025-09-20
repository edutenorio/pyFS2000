import numpy as np

from .base import CalculatedMixin

class LoadCalcMixin(CalculatedMixin):
    def __init__(self, *args, **kwargs):
        self._fres, self._mres = np.zeros(3), np.zeros(3)
        self._fx_cent, self._fy_cent, self._fz_cent = np.zeros(3), np.zeros(3), np.zeros(3)
        super().__init__(*args, **kwargs)

    @property
    def fres(self):
        self.calculate()
        return self._fres

    @property
    def mres(self):
        self.calculate()
        return self._mres

    @property
    def fx_cent(self):
        self.calculate()
        return self._fx_cent

    @property
    def fy_cent(self):
        self.calculate()
        return self._fy_cent

    @property
    def fz_cent(self):
        self.calculate()
        return self._fz_cent

    def _reset_res(self):
        self._fres, self._mres = np.zeros(3), np.zeros(3)
        self._fx_cent, self._fy_cent, self._fz_cent = np.zeros(3), np.zeros(3), np.zeros(3)
        self._calculated = False

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

    def summary_str(self) -> str:
        """Summary of load results as a formatted string"""
        self.calculate()
        result = f'{"":<22} {"Fx":>11}      {"Fy":>11}      {"Fz":>11}\n'
        result += f'{"Total Forces":<22} {self._fres[0]*0.001:>11.3f} kN   {self._fres[1]*0.001:>11.3f} kN   {self._fres[2]*0.001:>11.3f} kN\n'
        result += f'{"Centroid Position":<22} {"X":>11}      {"Y":>11}      {"Z":>11}\n'
        result += f'{"X Dir Loads":<22} {self._fx_cent[0]:>11.4f} m    {self._fx_cent[1]:>11.4f} m    {self._fx_cent[2]:>11.4f} m\n'
        result += f'{"Y Dir Loads":<22} {self._fy_cent[0]:>11.4f} m    {self._fy_cent[1]:>11.4f} m    {self._fy_cent[2]:>11.4f} m\n'
        result += f'{"Z Dir Loads":<22} {self._fz_cent[0]:>11.4f} m    {self._fz_cent[1]:>11.4f} m    {self._fz_cent[2]:>11.4f} m\n'
        result += f'{"":<22} {"Mx":>11}      {"My":>11}      {"Mz":>11}\n'
        result += f'{"Total Moment at origin":<22} {self._mres[0]*0.001:>11.4f} kN*m {self._mres[1]*0.001:>11.4f} kN*m {self._mres[2]*0.001:>11.4f} kN*m'
        return result

    def calculate_from_list(self, load_list):
        """Calculate resultant from a list of loads"""
        if self._calculated:
            return
        self._reset_res()
        for load in load_list:
            if not hasattr(load, 'calculate'):
                raise ValueError("All items in load_list must have a 'calculate' method.")
            if (not hasattr(load, '_fres')) or (not hasattr(load, '_mres')) or (not hasattr(load, '_fx_cent')) or (not hasattr(load, '_fy_cent')) or (not hasattr(load, '_fz_cent')):
                raise ValueError("All items in load_list must have 'fres', 'mres', 'fx_cent', 'fy_cent', and 'fz_cent' attributes.")
            load.calculate()
            self._fres += load.fres
            self._mres += load.mres
            self._fx_cent += load.fres[0] * load.fx_cent
            self._fy_cent += load.fres[1] * load.fy_cent
            self._fz_cent += load.fres[2] * load.fz_cent
        # Calculate centre of force
        self._fx_cent = self._fx_cent / self._fres[0] if not np.isclose(self._fres[0], 0.0) else np.zeros(3)
        self._fy_cent = self._fy_cent / self._fres[1] if not np.isclose(self._fres[1], 0.0) else np.zeros(3)
        self._fz_cent = self._fz_cent / self._fres[2] if not np.isclose(self._fres[2], 0.0) else np.zeros(3)
        # Update flag
        super().calculate()

    @staticmethod
    def global_moment(force, position):
        """Calculate global moment from force and position"""
        fx, fy, fz = force
        x, y, z = position
        return np.array([y * fz - z * fy, -x * fz + z * fx, x * fy - y * fx])