import logging
import numpy as np

from .aux_functions import str_or_blank
from .base import ListedMixin, CalculatedMixin, FS2000Entity
from .exceptions import ParameterInvalid, VectorSizeError, ArgumentError


class Material(ListedMixin, CalculatedMixin, FS2000Entity):
    """Defines an FS2000 Material code."""
    type = 'MTAB'
    parameters = ['CODE', 'E', 'G', 'POIS', 'DENS', 'ALPHA', 'YIELD', 'MATNAM', 'ULT', 'ULTSTR', 'COLDALLST',
                  'QUALFACT', 'PRESSCOEFF', 'PT_VEC', 'TEMP_VEC', 'ALPHA_VEC', 'E_VEC', 'ALLSTRESS_VEC']
    MAX_TPTS = 15  # Maximum number of points for temperature-dependent properties
    paramdefaults = [0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, '        ', 0.0, 0.0, 0.0, 0.0, 0.0,
                     np.arange(1, MAX_TPTS+1, dtype=int), np.zeros(MAX_TPTS, dtype=float),
                     np.zeros(MAX_TPTS, dtype=float), np.zeros(MAX_TPTS, dtype=float), np.zeros(MAX_TPTS, dtype=float)]

    def __init__(self, model, *args, **kwargs):
        """
        Creates a material property code within the model.
        """
        # Internal variables
        self._mtabp_defined = False
        self._mtabt_defined = False
        self._npts = 0  # Number of points for temperature-dependent properties
        self._E, self._G, self._POIS, self._DENS, self._ALPHA, self._YIELD = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        self._MATNAM, self._ULT, self._ULTSTR, self._COLDALLST = '        ', 0.0, 0.0, 0.0
        self._QUALFACT, self._PRESSCOEFF = 0.0, 0.0
        self._PT_VEC, self._TEMP_VEC = np.arange(1, self.MAX_TPTS+1, dtype=int), np.zeros(self.MAX_TPTS, dtype=float)
        self._ALPHA_VEC, self._E_VEC = np.zeros(self.MAX_TPTS, dtype=float), np.zeros(self.MAX_TPTS, dtype=float),
        self._ALLSTRESS_VEC = np.zeros(self.MAX_TPTS, dtype=float)
        # Call base constructor
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        e_str = f'{self._E:8.2E}'.replace('+', '')
        g_str = f'{self._G:8.2E}'.replace('+', '')
        gamma_str = f'{self._DENS}'.replace('+', '')
        fy_str = f'{self._YIELD:8.2E}'.replace('+', '')
        fu_str = f'{self._ULT:8.2E}'.replace('+', '')
        return f'Code   Name     EMod   Poiss   GMod   ExpCoef  Densit  Yield Ultimate\n' \
               f'{self.pk:^4d} {self._MATNAM:<8s} {e_str:7s} {self._POIS:6.4f} {g_str:7s} {self._ALPHA:8.2E} ' \
               f'{gamma_str:7s} {fy_str:7s} {fu_str:7s}'

    def __str__(self):
        s = f'MTAB, {self.pk},{self._E},{self._G},{self._POIS},{self._DENS},{self._ALPHA},{self._YIELD},' \
            f'{self._MATNAM},{self._ULT}'
        if self._mtabp_defined:
            s += f'\nMTABP,{self.pk},{self._ULTSTR},{self._COLDALLST},{self._QUALFACT},{self._PRESSCOEFF}'
        if self._mtabt_defined:
            for i in range(0, self._npts):
                s += f'\nMTABT,{self.pk},{self._PT_VEC[i]},{self._TEMP_VEC[i]},{self._ALPHA_VEC[i]},' \
                     f'{self._E_VEC[i]},{self._ALLSTRESS_VEC[i]}'
        return s

    def commit(self):
        super().commit()
        # Update active constants
        self._model.ACTMAT = self.pk

    def calculate(self):
        if self._calculated:
            return
        # Calculate the shear modulus G if not defined
        if np.isclose(self._G, 0.0) and (not np.isclose(self._E, 0.0)) and (not np.isclose(self._POIS, 0.0)):
            self._G = self._E / (2 * (1 + self._POIS))
        elif (not np.isclose(self._G, 0.0)) and (not np.isclose(self._E, 0.0)) and np.isclose(self._POIS, 0.0):
            # Alternatively calculate the Poisson coefficient if E and G are defined and Poisson is not
            self._POIS = self._E / (2 * self._G) - 1
        elif (not np.isclose(self._G, 0.0)) and np.isclose(self._E, 0.0) and (not np.isclose(self._POIS, 0.0)):
            # It should never happen, but if G and Poisson are defined and E is not, calculate it
            self._E = 2 * self._G * (1 + self._POIS)
        # Update the calculated flag
        super().calculate()

    # Temperature dependant functions
    def _interp_temp(self, temp, vector):
        """Interpolate a specific vector value for a temperature temp"""
        logger = logging.getLogger('FS2000')
        if not self._mtabt_defined:
            logger.warning(f'Temperature dependants properties not defined for material {self.pk}, returning 0')
            return 0
        if (temp < self._TEMP_VEC[0]) or (temp > self._TEMP_VEC[self._npts - 1]):
            logger.warning(
                f'Temperature {temp} out of defined range [{self._TEMP_VEC[0]},{self._TEMP_VEC[self._npts - 1]}]')
        return np.interp(temp, self._TEMP_VEC[:self._npts], vector[:self._npts])

    def get_pt_t(self, temp):
        """Point index for a specific temperature, used for reference only"""
        return self._interp_temp(temp, self._PT_VEC)

    def get_alpha_t(self, temp):
        """Thermal Coefficient of Expansion at a specific temperature 'temp'"""
        return self._interp_temp(temp, self._ALPHA_VEC)

    def get_e_t(self, temp):
        """Young Modulus at a specific temperature 'temp'"""
        return self._interp_temp(temp, self._E_VEC)

    def get_allstress_t(self, temp):
        """De-rated Yield Stress at a specific temperature 'temp'"""
        return self._interp_temp(temp, self._ALLSTRESS_VEC)

    def remove_ext_properties(self):
        """Remove all extended properties (pipe properties and temperature dependant properties)"""
        self._mtabp_defined = False
        self._mtabt_defined = False
        self._ULTSTR, self._COLDALLST, self._QUALFACT, self._PRESSCOEFF = 0.0, 0.0, 0.0, 0.0
        self._PT_VEC, self._TEMP_VEC = np.zeros(self.MAX_TPTS, dtype=int), np.zeros(self.MAX_TPTS, dtype=float)
        self._ALPHA_VEC, self._E_VEC = np.zeros(self.MAX_TPTS, dtype=float), np.zeros(self.MAX_TPTS, dtype=float)
        self._ALLSTRESS_VEC = np.zeros(self.MAX_TPTS, dtype=float)

    def add_t_data(self, temp, expcoeff, elastmod, allowstress):
        """Add a temperature-dependent data row."""
        if self._npts == self.MAX_TPTS:
            raise VectorSizeError(f'Maximum temperature points is {self.MAX_TPTS}.')
        self._TEMP_VEC[self._npts] = temp
        self._ALPHA_VEC[self._npts] = expcoeff
        self._E_VEC[self._npts] = elastmod
        self._ALLSTRESS_VEC[self._npts] = allowstress
        self._npts += 1
        self._mtabt_defined = True

    def _validate_t_data_point(self, i):
        if not self._mtabt_defined:
            raise ArgumentError(f'Temperature-dependent properties not defined for material {self.pk}')
        if i > self._npts:
            raise ArgumentError(f'Temperature point {i} not defined')
        if i < 1:
            raise ArgumentError(f'Invalid temperatre point {i}')

    def edit_t_data(self, i, temp=None, expcoeff=None, elastmod=None, allowstress=None):
        """Edit the temperature-dependent data por point i."""
        self._validate_t_data_point(i)
        self._TEMP_VEC[i - 1] = temp if temp is not None else self._TEMP_VEC[i - 1]
        self._ALPHA_VEC[i - 1] = expcoeff if expcoeff is not None else self._ALPHA_VEC[i - 1]
        self._E_VEC[i - 1] = elastmod if elastmod is not None else self._E_VEC[i - 1]
        self._ALLSTRESS_VEC[i - 1] = allowstress if allowstress is not None else self._ALLSTRESS_VEC[i - 1]

    def remove_t_data(self, i):
        """Remove a temperature-dependent data row for point i"""
        self._validate_t_data_point(i)
        if i < self._npts:
            # Move next point values to the deleted point
            self._TEMP_VEC[i - 1] = self._TEMP_VEC[i]
            self._ALPHA_VEC[i - 1] = self._ALPHA_VEC[i]
            self._E_VEC[i - 1] = self._E_VEC[i]
            self._ALLSTRESS_VEC[i - 1] = self._ALLSTRESS_VEC[i]
        self._npts -= 1

    # Properties
    @property
    def E(self):
        """Modulus of Elasticity"""
        return self._E

    @E.setter
    def E(self, value):
        self._E = float(value)
        self._calculated = False

    @property
    def G(self):
        """Modulus of Rigidity"""
        return self._G

    @G.setter
    def G(self, value):
        self._G = float(value)
        self._calculated = False

    @property
    def POIS(self):
        """Poisson's ratio"""
        return self._POIS

    @POIS.setter
    def POIS(self, value):
        self._POIS = float(value)
        self._calculated = False

    @property
    def DENS(self):
        """Density"""
        return self._DENS

    @DENS.setter
    def DENS(self, value):
        self._DENS = float(value)
        self._calculated = False

    @property
    def ALPHA(self):
        """Thermal Coefficient of Expansion"""
        return self._ALPHA

    @ALPHA.setter
    def ALPHA(self, value):
        self._ALPHA = float(value)

    @property
    def YIELD(self):
        return self._YIELD

    @YIELD.setter
    def YIELD(self, value):
        self._YIELD = float(value)

    @property
    def MATNAM(self):
        """Material Description (up to 8 characters)"""
        return self._MATNAM

    @MATNAM.setter
    def MATNAM(self, value):
        self._MATNAM = str_or_blank(value, length=8)

    @property
    def ULT(self):
        """Ultimate Strength"""
        return self._ULT

    @ULT.setter
    def ULT(self, value):
        self._ULT = float(value)

    @property
    def ULTSTR(self):
        """Ultimate Tensile Strength for extended properties"""
        return self._ULTSTR

    @ULTSTR.setter
    def ULTSTR(self, value):
        self._ULTSTR = float(value)
        self._mtabp_defined = True

    @property
    def COLDALLST(self):
        """Cold Allowable Stress for extended properties"""
        return self._COLDALLST

    @COLDALLST.setter
    def COLDALLST(self, value):
        self._COLDALLST = float(value)
        self._mtabp_defined = True

    @property
    def QUALFACT(self):
        """Quality/Joint Factor for extended properties"""
        return self._QUALFACT

    @QUALFACT.setter
    def QUALFACT(self, value):
        self._QUALFACT = float(value)
        self._mtabp_defined = True

    @property
    def PRESSCOEFF(self):
        """Pressure Coefficient for extended properties"""
        return self._PRESSCOEFF

    @PRESSCOEFF.setter
    def PRESSCOEFF(self, value):
        self._PRESSCOEFF = float(value)
        self._mtabp_defined = True

    @property
    def npts(self):
        """Number of Points for temperature dependant properties"""
        return self._npts

    @property
    def PT_VEC(self):
        """Points for temperature dependant properties"""
        return self._PT_VEC[:self._npts]

    @property
    def TEMP_VEC(self):
        """Temperature vector for temperature dependant properties"""
        return self._TEMP_VEC[:self._npts]

    @property
    def ALPHA_VEC(self):
        """
        Thermal Coefficient of Expansion vector for temperature dependant
        properties
        """
        return self._ALPHA_VEC[:self._npts]

    @property
    def E_VEC(self):
        """Modulus of Elasticity vector for temperature dependant properties"""
        return self._E_VEC[:self._npts]

    @property
    def ALLSTRESS_VEC(self):
        """Allowable Stress vector for temperature dependant properties"""
        return self._ALLSTRESS_VEC[:self._npts]
