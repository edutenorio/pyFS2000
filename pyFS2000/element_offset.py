import logging

from .base import ListedMixin, FS2000Entity
from .exceptions import ParameterInvalid


class ElemOffset(ListedMixin, FS2000Entity):
    """Defines element offsets for an FS2000 beam element."""
    type = 'EOF'
    parameters = ['ELEM', 'NOEF', 'EREF1', 'X1', 'Y1', 'Z1', 'EREF2', 'X2', 'Y2', 'Z2']
    paramdefaults = [0, 0, 0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0]

    def __init__(self, model, *args, **kwargs):
        """
        Create an element offset within the model.
        """
        self._ELEM, self._NOEF = 0, 0
        self._EREF1, self._X1, self._Y1, self._Z1 = 0, 0.0, 0.0, 0.0
        self._EREF2, self._X2, self._Y2, self._Z2 = 0, 0.0, 0.0, 0.0
        # Call base class constructor
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        return f'Element    OffsetOpt    Ref.Element  X-Offset  Y-Offset  Z-Offset\n' \
               f'{self._ELEM:^7d} ' \
               f'{["0-No offset", "1-1st Node Only", "2-2nd Node Only", "3-Both Nodes"][self._NOEF]:^15s}   ' \
               f'{self._EREF1:^7d}  {self._X1:>10.4f}{self._Y1:>10.4f}{self._Z1:>10.4f}\n                          ' \
               f'{self._EREF2:^7d}  {self._X2:>10.4f}{self._Y2:>10.4f}{self._Z2:>10.4f}'

    def _reset_element_calculated_flag(self):
        element = self._model.ElementList.get(self._ELEM)
        if element is not None:
            element._calculated = False

    # Properties
    @property
    def ELEM(self):
        """Element which the offset refers to"""
        return self._model.ElementList.get(self._ELEM)

    @ELEM.setter
    def ELEM(self, value):
        self._ELEM = int(value)
        self._reset_element_calculated_flag()

    @property
    def NOEF(self):
        """
        Element End ID code (1-first node only, 2-second node only,
        3-both nodes). Assign zero to delete offset
        """
        return self._NOEF

    @NOEF.setter
    def NOEF(self, value):
        value = int(value)
        if value not in [0, 1, 2, 3]:
            raise ParameterInvalid(f'Invalid element offset ID code {value} for element {self._ELEM}')
        # Set element calculated flag to False
        self._reset_element_calculated_flag()
        # Remove offset if NOEF is zero
        if value == 0:
            self._model.ElemOffsetList.remove(self)
            return
        # Update NOEF
        self._NOEF = value

    @property
    def EREF1(self):
        """
        Reference element for coordinate system for offsets x1, y1, z1 for
        First Node (0 is global)
        """
        return self._model.ElementList.get(self._EREF1)

    @EREF1.setter
    def EREF1(self, value):
        self._EREF1 = int(value)
        self._reset_element_calculated_flag()

    @property
    def X1(self):
        """Element end offset X for first node"""
        return self._X1

    @X1.setter
    def X1(self, value):
        self._X1 = float(value)
        self._reset_element_calculated_flag()

    @property
    def Y1(self):
        """Element end offset Y for first node"""
        return self._Y1

    @Y1.setter
    def Y1(self, value):
        self._Y1 = float(value)
        self._reset_element_calculated_flag()

    @property
    def Z1(self):
        """Element end offset Z for first node"""
        return self._Z1

    @Z1.setter
    def Z1(self, value):
        self._Z1 = float(value)
        self._reset_element_calculated_flag()

    @property
    def EREF2(self):
        """
        Reference element for coordinate system for offsets x2, y2, z2 for
        Second Node (0 is global)
        """
        return self._model.ElementList.get(self._EREF2)

    @EREF2.setter
    def EREF2(self, value):
        self._EREF2 = int(value)
        self._reset_element_calculated_flag()

    @property
    def X2(self):
        """Element end offset X for second node"""
        return self._X2

    @X2.setter
    def X2(self, value):
        self._X2 = float(value)
        self._reset_element_calculated_flag()

    @property
    def Y2(self):
        """Element end offset Y for second node"""
        return self._Y2

    @Y2.setter
    def Y2(self, value):
        self._Y2 = float(value)
        self._reset_element_calculated_flag()

    @property
    def Z2(self):
        """Element end offset Z for second node"""
        return self._Z2

    @Z2.setter
    def Z2(self, value):
        self._Z2 = float(value)
        self._reset_element_calculated_flag()
