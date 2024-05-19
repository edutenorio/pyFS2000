from datetime import datetime

import numpy as np

from .base import ListedMixin, CalculatedMixin, FS2000Entity
from .entity_list import EntityList
from .loads import Load


class LoadCase(ListedMixin, CalculatedMixin, FS2000Entity):
    type = 'LOAD'
    parameters = ['LCASE', 'LDESC', 'LDATE', 'LTIME']
    paramdefaults = [0, '', '01/01/1900', '00:00:00']

    def __init__(self, model, *args, **kwargs):
        """
        Creates a load case within the model.
        """
        self._LCASE, self._LDESC = 0, ''
        self._ldatetime = datetime.now()
        self._LDATE, self._LTIME = self._ldatetime.strftime('%d/%m/%Y'), self._ldatetime.strftime('%H:%M:%S')
        self._load_list = []
        self._fres, self._mres = np.zeros(3), np.zeros(3)
        self._fx_cent, self._fy_cent, self._fz_cent = np.zeros(3), np.zeros(3), np.zeros(3)
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        return f'LCASE {self.pk} - {self.LDESC}'

    def calculate(self):
        if self._calculated:
            return
        self._fres, self._mres = np.zeros(3), np.zeros(3)
        self._fx_cent, self._fy_cent, self._fz_cent = np.zeros(3), np.zeros(3), np.zeros(3)
        for load in self._load_list:
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
    def LoadList(self):
        """List of loads in the load case"""
        return self._load_list

    @property
    def LCASE(self):
        """Load Case Number"""
        return self.pk

    @property
    def LDESC(self):
        """Load Case Description"""
        return self._LDESC

    @LDESC.setter
    def LDESC(self, value):
        self._LDESC = str(value)

    @property
    def LDATE(self):
        """Current Date of Load Case"""
        return self._LDATE

    @LDATE.setter
    def LDATE(self, value):
        value = value.replace('.', '/').replace('-', '/')
        d, m, y = [int(x) for x in value.split('/')]
        d, m = (d, m) if m <= 12 else (m, d)
        value = f'{d:02d}/{m:02d}/{y:04d}'
        date = datetime.strptime(value, '%d/%m/%Y')
        time = datetime.strptime(self._LTIME, '%H:%M:%S')
        self._ldatetime = datetime(date.year, date.month, date.day, time.hour, time.minute, time.second)
        self._LDATE = self._ldatetime.strftime('%d/%m/%Y')

    @property
    def LTIME(self):
        """Current time of Load Case"""
        return self._LTIME

    @LTIME.setter
    def LTIME(self, value):
        date = datetime.strptime(self._LDATE, '%d/%m/%Y')
        time = datetime.strptime(value, '%H:%M:%S')
        self._ldatetime = datetime(date.year, date.month, date.day, time.hour, time.minute, time.second)
        self._LTIME = self._ldatetime.strftime('%H:%M:%S')
