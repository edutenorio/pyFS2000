import logging

from .base import ListedMixin, FS2000Entity
from .exceptions import ParameterInvalid


class Rest(ListedMixin, FS2000Entity):
    """Defined an FS2000 Restrain code properties."""
    type = 'REST'
    parameters = ['NODE', 'X', 'Y', 'Z', 'RX', 'RY', 'RZ']
    paramdefaults = [0, 0, 0, 0, 0, 0, 0]
    _parameter_error_text = 'Restrain should be 1 (fixed) or 0 (free)'

    def __init__(self, model, *args, **kwargs):
        """Creates a node restrain code within the model"""
        self._X, self._Y, self._Z, self._RX, self._RY, self._RZ = 0, 0, 0, 0, 0, 0
        # Call base constructor
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        return f'Node   Tx   Ty   Tz   Rx   Ry   Rz\n' \
               f'{self.pk:^4d}    ' \
               f'{"X" if self._X else "-"}    {"X" if self._Y else "-"}    {"X" if self._Z else "-"}    ' \
               f'{"X" if self._RX else "-"}    {"X" if self._RY else "-"}    {"X" if self._RZ else "-"}'

    # def create_restcopy(self, cmd):
    #     """
    #     Create a node restraint property code from the command:
    #     RESTCOPY, NODE, N1, N2, NINC
    #         The RESTOPY command is used to copy a node restraint to a pattern of
    #         existing nodes.
    #         NODE : Node to be copied (no default)
    #         N1   : First node in existing node pattern (no default)
    #         N2   : Last node in existing node pattern (default = N1)
    #         NINC : Node increment in existing node pattern (default = 1)
    #     """
    #     cmd_vals = self._cmd_split(cmd, 5)
    #     # Read parameters
    #     node = try_int(cmd_vals[1])
    #     n1 = try_int(cmd_vals[2])
    #     n2 = try_int(cmd_vals[3], n1)
    #     ninc = try_int(cmd_vals[4], 1)
    #     # Find the source node restraint
    #     if node in self._model.Rests:
    #         rest = self._model.get_rest(node)
    #         # Create the rests
    #         for n in range(n1, n2 + 1, ninc):
    #             # Check if node exists for warning
    #             if not (n in self._model.Nodes):
    #                 logging.warning(f'Creating node restraint for non-existing node {n}.')
    #             # Check if node restraint exists
    #             if n in self._model.Rests:
    #                 # Modifiy existing
    #                 existing = self._model.get_rest(n)
    #                 existing._X, existing._Y, existing._Z = rest.X, rest.Y, rest.Z
    #                 existing._RX, existing._RY, existing._RZ = rest.RX, rest.RY, rest.RZ
    #             else:
    #                 # Create new restraint
    #                 Rest(self._model, node=n, X=rest.X, Y=rest.Y, Z=rest.Z, RX=rest.RX, RY=rest.RY, RZ=rest.RZ)
    #     else:
    #         # If source node restraint is not found, just issue a warning and do nothing
    #         logging.warning(f'No node restraint defined for node {node} to be copied from in command: {cmd}')

    # Properties
    @property
    def NODE(self):
        """Restrained node number"""
        return self.pk

    @property
    def X(self):
        """X-Translation restraint in global co-ordinate system"""
        return self._X

    @X.setter
    def X(self, value):
        value = int(value)
        if value not in [0, 1]:
            raise ParameterInvalid(self._parameter_error_text)
        self._X = value

    @property
    def Y(self):
        """Y-Translation restraint in global co-ordinate system"""
        return self._Y

    @Y.setter
    def Y(self, value):
        value = int(value)
        if value not in [0, 1]:
            raise ParameterInvalid(self._parameter_error_text)
        self._Y = value

    @property
    def Z(self):
        """Z-Translation restraint in global co-ordinate system"""
        return self._Z

    @Z.setter
    def Z(self, value):
        value = int(value)
        if value not in [0, 1]:
            raise ParameterInvalid(self._parameter_error_text)
        self._Z = value

    @property
    def RX(self):
        """X-Rotation restraint in global co-ordinate system"""
        return self._RX

    @RX.setter
    def RX(self, value):
        value = int(value)
        if value not in [0, 1]:
            raise ParameterInvalid(self._parameter_error_text)
        self._RX = value

    @property
    def RY(self):
        """Y-Rotation restraint in global co-ordinate system"""
        return self._RY

    @RY.setter
    def RY(self, value):
        value = int(value)
        if value not in [0, 1]:
            raise ParameterInvalid(self._parameter_error_text)
        self._RY = value

    @property
    def RZ(self):
        """Z-Rotation restraint in global co-ordinate system"""
        return self._RZ

    @RZ.setter
    def RZ(self, value):
        value = int(value)
        if value not in [0, 1]:
            raise ParameterInvalid(self._parameter_error_text)
        self._RZ = value
