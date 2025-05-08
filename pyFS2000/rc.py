from .base import ListedMixin, FS2000Entity


class RC(ListedMixin, FS2000Entity):
    """Defines an FS2000 RC (Constants) code properties."""
    type = 'RC'
    parameters = ['CODE', 'RCX1', 'RCY1', 'RCX2', 'RCY2', 'RCX3', 'RCY3', 'RCX4', 'RCY4', 'RCX5', 'RCY5',
                  'RCX6', 'RCY6', 'RCX7', 'RCY7']
    paramdefaults = [0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def __init__(self, model, *args, **kwargs):
        """Creates an RC (constants) code within the model"""
        self._RCX1, self._RCY1, self._RCX2, self._RCY2, self._RCX3, self._RCY3 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        self._RCX4, self._RCY4, self._RCX5, self._RCY5, self._RCX6, self._RCY6 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        self._RCX7, self._RCY7 = 0.0, 0.0
        # Call base constructor
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        return f'Code        1          2          3          4          5          6          7\n' \
               f'{self.pk:^4d} X {self._RCX1:>10.3E} {self._RCX2:>10.3E} {self._RCX3:>10.3E} {self._RCX4:>10.3E} ' \
               f'{self._RCX5:>10.3E} {self._RCX6:>10.3E} {self._RCX7:>10.3E}\n' \
               f'     Y {self._RCY1:>10.3E} {self._RCY2:>10.3E} {self._RCY3:>10.3E} {self._RCY4:>10.3E} ' \
               f'{self._RCY5:>10.3E} {self._RCY6:>10.3E} {self._RCY7:>10.3E}'

    # Properties
    @property
    def RCX1(self):
        """Real Constant x-value of point 1"""
        return self._RCX1

    @RCX1.setter
    def RCX1(self, value):
        self._RCX1 = float(value)

    @property
    def RCY1(self):
        """Real Constant y-value of point 1"""
        return self._RCY1

    @RCY1.setter
    def RCY1(self, value):
        self._RCY1 = float(value)

    @property
    def RCX2(self):
        """Real Constant x-value of point 2"""
        return self._RCX2

    @RCX2.setter
    def RCX2(self, value):
        self._RCX2 = float(value)

    @property
    def RCY2(self):
        """Real Constant y-value of point 2"""
        return self._RCY2

    @RCY2.setter
    def RCY2(self, value):
        self._RCY2 = float(value)

    @property
    def RCX3(self):
        """Real Constant x-value of point 3"""
        return self._RCX3

    @RCX3.setter
    def RCX3(self, value):
        self._RCX3 = float(value)

    @property
    def RCY3(self):
        """Real Constant y-value of point 3"""
        return self._RCY3

    @RCY3.setter
    def RCY3(self, value):
        self._RCY3 = float(value)

    @property
    def RCX4(self):
        """Real Constant x-value of point 4"""
        return self._RCX4

    @RCX4.setter
    def RCX4(self, value):
        self._RCX4 = float(value)

    @property
    def RCY4(self):
        """Real Constant y-value of point 4"""
        return self._RCY4

    @RCY4.setter
    def RCY4(self, value):
        self._RCY4 = float(value)

    @property
    def RCX5(self):
        """Real Constant x-value of point 5"""
        return self._RCX5

    @RCX5.setter
    def RCX5(self, value):
        self._RCX5 = float(value)

    @property
    def RCY5(self):
        """Real Constant y-value of point 5"""
        return self._RCY5

    @RCY5.setter
    def RCY5(self, value):
        self._RCY5 = float(value)

    @property
    def RCX6(self):
        """Real Constant x-value of point 6"""
        return self._RCX6

    @RCX6.setter
    def RCX6(self, value):
        self._RCX6 = float(value)

    @property
    def RCY6(self):
        """Real Constant y-value of point 6"""
        return self._RCY6

    @RCY6.setter
    def RCY6(self, value):
        self._RCY6 = float(value)

    @property
    def RCX7(self):
        """Real Constant x-value of point 7"""
        return self._RCX7

    @RCX7.setter
    def RCX7(self, value):
        self._RCX7 = float(value)

    @property
    def RCY7(self):
        """Real Constant y-value of point 7"""
        return self._RCY7

    @RCY7.setter
    def RCY7(self, value):
        self._RCY7 = float(value)
