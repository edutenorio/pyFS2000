import numpy as np
from icecream import ic

from .aux_functions import getattr_nest
from .exceptions import EntityNotFound, TypeInvalid


class EntityList(list):
    _lookup_operators = ['eq', 'ne', 'lt', 'gt', 'le', 'ge', 'range', 'in', 'contains', 'icontains', 'startswith',
                         'istartswith', 'endswith', 'iendswith', 'exact', 'iexact', 'isnull', 'isnone', 'func']

    def __init__(self, entity_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_type = entity_type
        self.pkmax = max([x.pk for x in self]) if len(self) > 0 else 0

    def __repr__(self):
        return '[ ' + ',\n'.join([x.__repr__() for x in self]) + ' ]'

    def __str__(self):
        return '\n'.join([x.__str__() for x in self])

    def _validade_type(self, __object):
        if not isinstance(__object, self._entity_type):
            raise TypeInvalid(f'Invalid type "{__object.__class__.__name__}". '
                              f'Only "{self._entity_type.__name__}" allowed in list.')

    def __add__(self, other):
        for item in other:
            self._validade_type(item)
        new_list = super().__add__(other)
        return EntityList(self._entity_type, new_list)

    def __mul__(self, n):
        new_list = super().__mul__(n)
        return EntityList(self._entity_type, new_list)

    def __rmul__(self, n):
        new_list = super().__rmul__(n)
        return EntityList(self._entity_type, new_list)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            try:
                iter(value)
            except TypeError:
                raise TypeError('can only assign an iterable')
            for v in value:
                self._validade_type(v)
            super().__setitem__(key, value)
            return
        self._validade_type(value)
        super().__setitem__(key, value)

    def __getitem__(self, item):
        if isinstance(item, slice):
            indices = range(*item.indices(len(self)))
            new_list = [self[i] for i in indices]
            return EntityList(self._entity_type, new_list)
        return super().__getitem__(item)

    def copy(self):
        return EntityList(self._entity_type, self)

    def append(self, __object) -> None:
        self._validade_type(__object)
        super().append(__object)
        self.pkmax = __object.pk if __object.pk > self.pkmax else self.pkmax

    def extend(self, __iterable) -> None:
        __iterable_pkmax = 0
        for __object in __iterable:
            self._validade_type(__object)
            __iterable_pkmax = __object.pk if __object.pk > __iterable_pkmax else __iterable_pkmax
        super().extend(__iterable)
        self.pkmax = __iterable_pkmax if __iterable_pkmax > self.pkmax else self.pkmax

    def insert(self, __index, __object) -> None:
        self._validade_type(__object)
        super().insert(__index, __object)
        self.pkmax = __object.pk if __object.pk > self.pkmax else self.pkmax

    def add(self, __object):
        """Add object and sort the list."""
        self._validade_type(__object)
        super().append(__object)
        self.pkmax = __object.pk if __object.pk > self.pkmax else self.pkmax
        self.sort()

    def replace(self, __object):
        """
        Replace the existing object with the new one.

        Raises EntityNotFound if the value is not present.
        """
        self._validade_type(__object)
        if __object not in self:
            raise EntityNotFound(f'Entity not found: {__object}')
        idx = self.index(__object)
        del self[idx]
        self.insert(idx, __object)

    def add_or_replace(self, __object) -> None:
        """Add object or replace if it already exists. Sort the list at the end."""
        if __object not in self:
            self.add(__object)
        else:
            self.replace(__object)

    def remove(self, __value) -> None:
        """
        Remove first occurrence of value, but doesn't raise ValueError if the
         value is not present.
         """
        if __value not in self:
            return
        super().remove(__value)

    def sort_by(self, attr: str, reverse: bool = False):
        """Sorts the list by the specified attribute, in-place"""
        attr_list = attr.split('__')
        self.sort(key=lambda x: getattr_nest(x, attr_list), reverse=reverse)

    @property
    def entity_type(self):
        return self._entity_type

    def get(self, pk):
        """Return an instance of the object with the primary key = pk, or None"""
        try:
            idx = self.index(pk)
            return self[idx]
        except ValueError:
            return None

    @staticmethod
    def _meet_lookup_criteria(entity, attr_list, op, lookup_value):
        # Apply an external boolean funcion
        if len(attr_list) == 1 and op == 'func':
            return lookup_value(getattr_nest(entity, attr_list))
        # Get attributes
        attr_value = getattr_nest(entity, attr_list)
        # Null filters
        if op in ['isnull', 'isnone']:
            return (attr_value is None) == lookup_value
        # List filter
        if op == 'range':
            return (attr_value >= lookup_value[0]) and (attr_value <= lookup_value[1])
        if op == 'in':
            return attr_value in lookup_value
        # String filter
        if op == 'exact':
            return lookup_value == attr_value
        if op == 'iexact':
            return lookup_value.lower() == attr_value.lower()
        if op == 'contains':
            return lookup_value in attr_value
        if op == 'icontains':
            return lookup_value.lower() in attr_value.lower()
        if op in ['startswith', 'endswith']:
            return getattr(attr_value, op)(lookup_value)
        if op in ['istartswith', 'iendswith']:
            return getattr(attr_value.lower(), op)(lookup_value.lower)
        # Equality check for numeric values
        if np.isreal(lookup_value):
            equal = np.isclose(float(attr_value), float(lookup_value))
            if op == 'eq':
                return equal
            if op == 'ne':
                return not equal
            if op == 'lt':
                return attr_value < lookup_value
            if op == 'gt':
                return attr_value > lookup_value
            if op == 'le':
                return (attr_value < lookup_value) or equal
            if op == 'ge':
                return (attr_value > lookup_value) or equal
        if op in ['eq', 'ne', 'lt', 'gt', 'le', 'ge']:
            return getattr(attr_value, f'__{op}__')(lookup_value)

    def _filter(self, positive, **kwargs):
        filtered_list = self.copy()
        for kw in kwargs:
            lookups = kw.split('__')
            # Check if the last lookup is one of the following
            if lookups[-1] in self._lookup_operators:
                op = lookups[-1]
                attr_list = lookups[:-1]
            else:
                op = 'eq'
                attr_list = lookups
            if positive:
                filtered_list = [entity for entity in filtered_list if
                                 self._meet_lookup_criteria(entity, attr_list, op, kwargs[kw])]
            else:
                filtered_list = [entity for entity in filtered_list if
                                 not self._meet_lookup_criteria(entity, attr_list, op, kwargs[kw])]
        return EntityList(self._entity_type, filtered_list)

    def filter(self, **kwargs):
        """Filter instances that match the given criteria.

        The keywords shall be the entity attributes, e.g.:
        ElementList.filter(TYPE=6) -> a list with all type 6 elements

        A set of lookups can be used with __ to lookup a dependency or to apply
        one of the following criteria:
            eq : is equal to a value
            ne : is not equal to a value
            lt : is less than a value
            gt : is greater than a value
            le : is less than or equal to a value
            ge : is greater than or equal to a value
            range : is between two values, inclusive
            in : matches on of the values
            contains : contains the value
            icontains : same as contains, but case-insensitive
            startswith : starts with the value
            istartswith : same as starts with, but case-insensitive
            endswith : ends with the value
            iendswith : same as ends with, but case-insensitive
            exact : matches exactly the value
            iexact : same as exact, but case-insensitive
            isnull : whether the attribute is null
            isnone : same as isnull, more pyhtonic
            func : apply an external function to elements of the list

        e.g.
        NodeList.filter(X__lt=0, Z_lt=0) -> all nodes with X < 0 and Z < 0
        NodeList.filter(X__range=(-0.5,0.5)) -> all nodes with -0.5 <= X <= 0.5
        ElementList.filter(N1__Y__lt=0) -> All elements with first node Y < 0
        ElementList.filter(TYPE__in=[2,3]) -> All bend type elements
        NodeList.filter(func=lambda n: n.X**2+n.Z**2 == 25) -> Nodes w/ r=5.0
        """
        return self._filter(positive=True, **kwargs)

    def exclude(self, **kwargs):
        """Filter instances that DO NOT match the given criteria.
        Refer to filter() for the query documentation.
        """
        return self._filter(positive=False, **kwargs)

    def order_by(self, attr: str, reverse: bool = False):
        """Returns a copy of the list sorted by the specified attribute"""
        new_list = self.copy()
        new_list.sort(key=lambda x: getattr_nest(x, attr.split('__')), reverse=reverse)
        return new_list

    def first(self):
        """Returns the first element of the list, or None if empty"""
        return self[0] if len(self) > 0 else None

    def last(self):
        """Returns the last element of the list, or None if empty"""
        return self[-1] if len(self) > 0 else None

    def count(self, __value=None) -> int:
        """
        Return number of occurrences of value, or the list length if value is
        not specified."""
        if __value is None:
            return len(self)
        return super().count(__value)

    def min(self, attr: str):
        """Returns the minimum value for the attribute"""
        if len(self) == 0:
            return None
        value_array = np.array([getattr_nest(x, attr.split('__')) for x in self])
        return value_array.min(initial=None)

    def max(self, attr: str):
        """Returns the maximum value for the attribute"""
        if len(self) == 0:
            return None
        value_array = np.array([getattr_nest(x, attr.split('__')) for x in self])
        return value_array.max(initial=None)

    def mid(self, attr: str):
        """Returns the mid value for the attribute = (max+min)/2"""
        if len(self) == 0:
            return None
        value_array = np.array([getattr_nest(x, attr.split('__')) for x in self])
        return (value_array.max(initial=None) + value_array.min(initial=None)) / 2

    def ptp(self, attr: str):
        """Returns the peak-to-peak value for the attribute = max-min"""
        if len(self) == 0:
            return None
        value_array = np.array([getattr_nest(x, attr.split('__')) for x in self])
        return np.ptp(value_array)

    def sum(self, attr: str):
        """Returns the sum of the values for the attribute"""
        if len(self) == 0:
            return None
        value_array = np.array([getattr_nest(x, attr.split('__')) for x in self])
        return value_array.sum()

    def average(self, attr: str, weights=None):
        """Returns the weighted average value for the attribute =
        sum(value*weight) / sum(weight)"""
        if len(self) == 0:
            return None
        value_array = np.array([getattr_nest(x, attr.split('__')) for x in self])
        return np.average(value_array, weights=weights)

    def mean(self, attr: str):
        """Returns the arithmetic mean value for the attribute"""
        if len(self) == 0:
            return None
        value_array = np.array([getattr_nest(x, attr.split('__')) for x in self])
        return value_array.mean()

    def std(self, attr: str):
        """Returns the standard deviation for the attribute"""
        if len(self) == 0:
            return None
        value_array = np.array([getattr_nest(x, attr.split('__')) for x in self])
        return value_array.std()

    def var(self, attr: str):
        """Returns the variance for the attribute"""
        if len(self) == 0:
            return None
        value_array = np.array([getattr_nest(x, attr.split('__')) for x in self])
        return value_array.var()

    def median(self, attr):
        """Returns the median value for the attribute = value at [count//2]"""
        if len(self) == 0:
            return None
        value_array = np.array([getattr_nest(x, attr.split('__')) for x in self])
        return np.median(value_array)

    def percentile(self, attr: str, q: np.array or float, method='linear') -> np.array or float:
        """Returns the q-th percentile(s) for the attribute"""
        if len(self) == 0:
            return None
        value_array = np.array([getattr_nest(x, attr.split('__')) for x in self])
        if np.__version__ < '1.22.0':
            return np.percentile(value_array, q, interpolation=method)
        return np.percentile(value_array, q, method=method)
