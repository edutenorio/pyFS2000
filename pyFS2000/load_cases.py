from datetime import datetime

import numpy as np

from .base import ListedMixin, FS2000Entity
from .load_base import LoadCalcMixin
from .entity_list import EntityList
from .loads import Load


class LoadCase(ListedMixin, LoadCalcMixin, FS2000Entity):
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
        super().__init__(model, *args, **kwargs)

    def __str__(self):
        return f'LCASE {self.pk}: {self.LDESC}'

    # def __repr__(self):
    #     return f'LCASE {self.pk} - {self.LDESC}'

    def calculate(self):
        self.calculate_from_list(self._load_list)

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
