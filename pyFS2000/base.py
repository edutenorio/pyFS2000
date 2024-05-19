import logging
from icecream import ic

from .exceptions import ArgumentError, PrimaryKeyBoundError


class ListedMixin:
    """Mixin for listed entities"""
    # _list = list()
    _pkmax_name = ''  # Maximum primary key defined for all objects in class
    _pkbounds = (0, None)

    def __init__(self, model, *args, **kwargs):
        self._list = getattr(model, f'_{self.__class__.__name__.lower()}_list')
        self._pk = kwargs.pop('pk') if 'pk' in kwargs else 0  # Primary key
        self._model = model
        super().__init__(model, *args, **kwargs)

    def set_pk(self, pk: int = None):
        """
        Set a new primary key for the object. If None is passed, get the maximum
        defined object key + 1.
        """
        # pkmax = self.pkmax
        pkmax = self._list.pkmax
        new_pk = int(pk) if pk is not None else pkmax + 1
        if (self._pkbounds[0] is not None) and (new_pk < self._pkbounds[0]):
            raise PrimaryKeyBoundError(f'Primary key {new_pk} should be equal to or greater than {self._pkbounds[0]}.')
        if (self._pkbounds[1] is not None) and (new_pk > self._pkbounds[1]):
            raise PrimaryKeyBoundError(f'Primary key {new_pk} should be less than or equal to {self._pkbounds[1]}.')
        self._pk = int(pk) if pk is not None else pkmax + 1
        setattr(self, f'_{self.parameters[0]}', self._pk)

    # def commit(self, overwrite: bool = True, update_items: list = None):
    def commit(self):
        """
        Consolidate thew newly created object in its respective model list.
        If there is no object with the same key in the list, self will be added.
        If an object with the same primary key already exists in the list, it
        will be replaced by self.
        """
        self._list.add_or_replace(self)

    def __eq__(self, other):
        """
        Return (self.pk == other.pk) if both are objects or
        (self.pk == other) if other is an integer
        """
        return self.pk == other if type(other) is int else self.pk == other.pk

    def __ne__(self, other):
        """
        Return (self.pk != other.pk) if both are objects or
        (self.pk != other) if other is an integer
        """
        return self.pk != other if type(other) is int else self.pk != other.pk

    def __gt__(self, other):
        """
        Return (self.pk > other.pk) if both are objects or
        (self.pk > other) if other is an integer
        """
        return self.pk > other if type(other) is int else self.pk > other.pk

    def __ge__(self, other):
        """
        Return (self.pk >= other.pk) if both are objects or
        (self.pk >= other) if other is an integer
        """
        return self.pk >= other if type(other) is int else self.pk >= other.pk

    def __lt__(self, other):
        """
        Return (self.pk < other.pk) if both are objects or
        (self.pk < other) if other is an integer
        """
        return self.pk < other if type(other) is int else self.pk < other.pk

    def __le__(self, other):
        """
        Return (self.pk <= other.pk) if both are objects or
        (self.pk <= other) if other is an integer
        """
        return self.pk <= other if type(other) is int else self.pk <= other.pk

    def __int__(self):
        return self.pk

    def __float__(self):
        return float(self.pk)

    @property
    def pk(self):
        """Primary key"""
        return self._pk


class CalculatedMixin:
    """Mixin for classes that have calculated parameters"""

    def __init__(self, *args, **kwargs):
        self._calculated = False
        super().__init__(*args, **kwargs)

    def calculate(self):
        self._calculated = True

    @property
    def calculated(self):
        return self._calculated


class FS2000Entity:
    """
    Defines a base class for all FS2000 objects

    It defines a set of variables and functions common to all FS2000 objects
    that should be redefined by each subclass. The following parameters shall be
    redefined by the subclasses:

        type : str
            Identifier of the object type. Example: 'N' node, 'E' element...

        parameters : list of str
            List of the parameters that define the object
            Example: ['NODE', 'X', 'Y', 'Z', 'CSYS'] for Node

        paramdefaults : list of values
            Default values for the parameters defined in _parameters
            Example: [0, 0.0, 0.0, 0.0, 0] for Node
    """
    type = ''
    parameters = []
    paramdefaults = []

    def __init__(self, model, *args, **kwargs):
        """
        Initialize a FS2000 object base class. Should only be called by a
        subclass initializer.

        Parameters:

        model : Model
            Reference to the FS2000 model the object belongs to.


        """
        self._model = model
        if len(args) > 1:
            raise ArgumentError(f'FS2000 entity object takes only one positional argument, {1+len(args)} were given.')
        # Initialize parameters with keywords or default values
        for param, default in zip(self.parameters, self.paramdefaults):
            if param in kwargs:
                setattr(self, f'{param}', kwargs.pop(param))
            else:
                setattr(self, f'_{param}', default)
        if len(kwargs) > 0:
            logger = logging.getLogger('FS2000')
            for key, value in kwargs.items():
                logger.warning(f'Invalid parameter for {self.__class__}: {key}={value}.')

    def __str__(self):
        # Basic string representration of the object. May be overriden for specific cases
        return ','.join([self.type] + [f'{getattr(self, f"_{x}")}' for x in self.parameters])

    @property
    def model(self):
        """Model which the element belongs."""
        return self._model
