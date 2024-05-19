from icecream import ic

from .base import ListedMixin, CalculatedMixin, FS2000Entity
from .exceptions import TypeInvalid


class CType(ListedMixin, CalculatedMixin, FS2000Entity):
    """Defines an FS2000 Couple Type code properties."""
    type = 'STAB'
    parameters = ['CODE', 'K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'TYPE', 'CO']
    paramdefaults = [0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0]

    def __init__(self, model, *args, **kwargs):
        """
        Creates a copuple type code within the model
        """
        self._K1, self._K2, self._K3, self._K4, self._K5, self._K6 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        self._TYPE, self._CO = 0, 0
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        k1_str = f'{self._K1:10.3E}'.replace('+', '')
        k2_str = f'{self._K2:10.3E}'.replace('+', '')
        k3_str = f'{self._K3:10.3E}'.replace('+', '')
        k4_str = f'{self._K4:10.3E}'.replace('+', '')
        k5_str = f'{self._K5:10.3E}'.replace('+', '')
        k6_str = f'{self._K6:10.3E}'.replace('+', '')
        return f'Code     K1        K2        K3        K4        K5        K6    Type  CO\n' \
               f'{self.pk:^4d} {k1_str} {k2_str} {k3_str} {k4_str} {k5_str} {k6_str} {self._TYPE:^4d} {self._CO:^4d}'

    def __str__(self):
        return f'STAB,{self.pk},{self._K1},{self._K2},{self._K3},{self._K4},{self._K5},{self._K6},{self._TYPE},' \
               f'{self._CO}'

    def commit(self):
        super().commit()
        self._model.ACTSPCONST = self.pk

    @property
    def K1(self):
        """Couple Constant k1"""
        return self._K1

    @K1.setter
    def K1(self, value):
        self._K1 = value

    @property
    def K2(self):
        """Couple Constant k2"""
        return self._K2

    @K2.setter
    def K2(self, value):
        self._K2 = value

    @property
    def K3(self):
        """Couple Constant k3"""
        return self._K3

    @K3.setter
    def K3(self, value):
        self._K3 = value

    @property
    def K4(self):
        """Couple Constant k4"""
        return self._K4

    @K4.setter
    def K4(self, value):
        self._K4 = value

    @property
    def K5(self):
        """Couple Constant k5"""
        return self._K5

    @K5.setter
    def K5(self, value):
        self._K5 = value

    @property
    def K6(self):
        """Couple Constant k6"""
        return self._K6

    @K6.setter
    def K6(self, value):
        self._K6 = value

    @property
    def TYPE(self):
        """Couple Element Type"""
        return self._TYPE

    @TYPE.setter
    def TYPE(self, value):
        type_ = int(value)
        if type_ not in [0, 1, 3, 4, 5, 6, 7, 8, 10, 11, 12, 14, 15, 16, 20]:
            raise TypeInvalid(f'Couple Type {type_} is not valid.')
        self._TYPE = type_

    @property
    def CO(self):
        """Couple Additional CO constant"""
        return self._CO

    @CO.setter
    def CO(self, value):
        self._CO = int(value)
