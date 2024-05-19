from .base import ListedMixin, FS2000Entity


class IC(ListedMixin, FS2000Entity):
    """Defines an FS2000 IC (Constants) code properties."""
    type = 'IC'
    parameters = ['CODE', 'IC0', 'IC1', 'IC2', 'IC3', 'IC4', 'IC5', 'IC6']
    paramdefaults = [0, 0, 0, 0, 0, 0, 0, 0]

    def __init__(self, model, *args, **kwargs):
        """Creates an IC (constants) code within the model"""
        self._IC0, self._IC1, self._IC2, self._IC3, self._IC4, self._IC5, self._IC6 = 0, 0, 0, 0, 0, 0, 0
        # Call base constructor
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        return f'Code    IC0       IC1       IC2       IC3       IC4       IC5       IC6\n' \
               f'{self.pk:^4d} {self._IC0:^9d} {self._IC1:^9d} {self._IC2:^9d} {self._IC3:^9d} {self._IC4:^9d} ' \
               f'{self._IC5:^9d} {self._IC6:^9d}'

    # Properties
    @property
    def CODE(self):
        return self.pk

    @property
    def IC0(self):
        """Integer Constant IC0"""
        return self._IC0

    @IC0.setter
    def IC0(self, value):
        self._IC0 = int(value)

    @property
    def IC1(self):
        """Integer Constant IC1"""
        return self._IC1

    @IC1.setter
    def IC1(self, value):
        self._IC1 = int(value)

    @property
    def IC2(self):
        """Integer Constant IC2"""
        return self._IC2

    @IC2.setter
    def IC2(self, value):
        self._IC2 = int(value)

    @property
    def IC3(self):
        """Integer Constant IC3"""
        return self._IC3

    @IC3.setter
    def IC3(self, value):
        self._IC3 = int(value)

    @property
    def IC4(self):
        """Integer Constant IC4"""
        return self._IC4

    @IC4.setter
    def IC4(self, value):
        self._IC4 = int(value)

    @property
    def IC5(self):
        """Integer Constant IC5"""
        return self._IC5

    @IC5.setter
    def IC5(self, value):
        self._IC5 = int(value)

    @property
    def IC6(self):
        """Integer Constant IC6"""
        return self._IC6

    @IC6.setter
    def IC6(self, value):
        self._IC6 = int(value)
