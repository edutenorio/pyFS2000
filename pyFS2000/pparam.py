from .base import ListedMixin, FS2000Entity
from .exceptions import ParameterInvalid


class PParam(ListedMixin, FS2000Entity):
    """Defnies an FS2000 Pipework Coefficient properties."""
    type = 'PPARAM'
    parameters = ['ELEM', 'TYPE', 'NODEEND', 'KFLEX', 'SIFI', 'SIFO', 'C1', 'C2']
    paramdefaults = [0, 0, 0, 0.0, 0.0, 0.0, 0, 0]
    _type_helptext = {
        1: ('Bend', 'Welded elbow or pipe bend (both ends welded)'),
        2: ('Bend', 'Welded elbow or pipe bend (one end welded other flanged)'),
        3: ('Bend', 'Welded elbow or pipe bend (both ends flanged)'),
        4: ('Bend', 'Mitre end bend'),
        5: ('Bend', 'Socket Welded Elbow'),
        6: ('Tee/Branch', 'Welding Tee per ANSI B16.9'),
        7: ('Tee/Branch', 'Reinforced fabricated tee with pad or saddle (Header pipe)'),
        8: ('Tee/Branch', 'Unreinforced fabricated tee'),
        9: ('Tee/Branch', 'Extruded welding tee'),
        10: ('Tee/Branch', 'Welded-in contour insert'),
        11: ('Tee/Branch', 'Branch welded on fitting (integrally reinforced)'),
        12: ('Flange/Connectors', 'Buttwelded joint, reducer or weld neck flange'),
        13: ('Flange/Connectors', 'Double-welded slip-on flange'),
        14: ('Flange/Connectors', 'Fillet-welded joint or socket weld flange'),
        15: ('Flange/Connectors', 'Lap joint flange (with ANSI B16.9 lap joint stub)'),
        16: ('Flange/Connectors', 'Screwed pipe joint or screwed flange'),
        17: ('Flange/Connectors', 'Corrogated straight pipe or corrugated or creased bend'),
        18: ('Flange/Connectors', 'User Defined'),
        19: ('Valves', 'Valves Type Components'),
    }
    _nodeend_helptext = {
        1: 'First node only',
        2: 'Second node only',
        3: 'Both nodes',
    }

    def __init__(self, model, *args, **kwargs):
        """Creates a PPARAM pipework coefficient properties within the model."""
        # Internal variables
        self._ELEM, self._TYPE, self._NODEEND = 0, 0, 0
        self._KFLEX, self._SIFI, self._SIFO, self._C1, self._C2 = 0.0, 0.0, 0.0, 0.0, 0.0
        # Call base constructor
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        result = f'Element {self.pk}: {self._type_helptext[self._TYPE][0]} - {self._type_helptext[self._TYPE][1]}'
        result += f' - {self._nodeend_helptext[self._NODEEND]}' if self._TYPE in range(6, 19) else ''
        result += f'\nKflex={self._KFLEX}, SIFi={self.SIFI}, SIFo={self.SIFO}'
        if self._TYPE in range(1, 6):
            result += f', Bend Radius={self._C1}, Mitre angle={self._C2}'
        elif self._TYPE in range(6, 12):
            result += f', Reinforcement thickness={self._C1}, Tee radius={self._C2}'
        elif self._TYPE in range(12, 19):
            result += f', Flange table entry index={self._C1}'
        return result

    # Properties
    @property
    def ELEM(self):
        """Pipe Element"""
        return self._model.ElementList.get(self._ELEM)

    @ELEM.setter
    def ELEM(self, value):
        self._ELEM = int(value)

    @property
    def TYPE(self):
        """Pipework Component type"""
        return self._TYPE

    @TYPE.setter
    def TYPE(self, value):
        value = int(value)
        if value not in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]:
            raise ParameterInvalid(f'Inavlid pipework coefficient type {value}')
        self._TYPE = value

    @property
    def NODEEND(self):
        """Applicable node in element (1-first only, 2-second only, 3-both)"""
        return self._NODEEND

    @NODEEND.setter
    def NODEEND(self, value):
        value = int(value)
        if value not in [1, 2, 3]:
            raise ParameterInvalid(f'Invalid node end {value}. It should be 1, 2 or 3')
        self._NODEEND = value

    @property
    def KFLEX(self):
        """Flexibility Factor"""
        return self._KFLEX

    @KFLEX.setter
    def KFLEX(self, value):
        self._KFLEX = float(value)

    @property
    def SIFI(self):
        """Stress Intensification Factor - inner face"""
        return self._SIFI

    @SIFI.setter
    def SIFI(self, value):
        self._SIFI = float(value)

    @property
    def SIFO(self):
        """Stress Intensification Factor - outer face"""
        return self._SIFO

    @SIFO.setter
    def SIFO(self, value):
        self._SIFO = float(value)

    @property
    def C1(self):
        """Additional constant 1"""
        return self._C1

    @C1.setter
    def C1(self, value):
        self._C1 = float(value)

    @property
    def C2(self):
        """Additional constant 2"""
        return self._C2

    @C2.setter
    def C2(self, value):
        self._C2 = value
