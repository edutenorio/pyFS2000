import numpy as np
import logging
import os

from .base import ListedMixin, FS2000Entity
from .load_base import LoadCalcMixin


class LoadCombination(ListedMixin, LoadCalcMixin, FS2000Entity):
    type = 'LCOMB'
    parameters = ['LCOMB', 'DESC']
    paramdefaults = [0, '']

    def __init__(self, model, *args, **kwargs):
        """
        Creates a load combination within the model.
        """
        self._LCOMB, self._DESC = 0, ''
        self._lc_fact_pairs = []
        super().__init__(model, *args, **kwargs)
    
    def __str__(self):
        return f'LCOMB {self.pk}: {self._DESC}'

    def __repr__(self):
        result = f'LCOMB {self.pk}: {self._DESC}\n'
        result += f'{"Load Case":<9} {"Factor":>10}'
        for lc, factor in self._lc_fact_pairs:
            result += f'\n{lc:^9} {factor:>10.4f}'
        return result

    def read_from_file(self, filename):
        logger = logging.getLogger('FS2000')
        fname, fext = os.path.splitext(filename)
        name_valid = fext.startswith('.C') and fext[2:].isnumeric()
        if not name_valid:
            logger.error(f'Invalid combindation file name: {filename}')
            raise ValueError(f'Invalid combindation file name: {filename}')
        # Set primary key from file name
        self.set_pk(int(fext[2:]))
        # Read file
        with open(filename, 'r') as f:
            lines = f.read().split('\n')
            f.close()
        n: int = int(lines[0])
        self._lc_fact_pairs.clear()
        for i in range(1, n+1):
            parts = lines[i].split()
            lc, factor = int(parts[0]), float(parts[1])
            self._lc_fact_pairs.append((lc, factor))
        self._DESC = lines[n+1].strip()
    
    def calculate(self):
        if self._calculated:
            return
        self._reset_res()
        load_list = []
        for lc, factor in self.lc_fact_pairs:
            load = self._model.LoadCaseList.get(lc)
            if not load:
                logger = logging.getLogger('FS2000')
                logger.error(f"Error in combinadion {self.pk}: Load case {lc} not found in model.")
                raise ValueError(f"Error in combinadion {self.pk}: Load case {lc} not found in model.")
            load.calculate()
            # Manualy factor the load results
            load._fres *= factor
            load._mres *= factor
            load_list.append(load)
        self.calculate_from_list(load_list)
        # Reset the calculated flag of the load cases that were factored
        for load in load_list:
            load._calculated = False

    @property
    def lc_fact_pairs(self):
        return self._lc_fact_pairs

    @lc_fact_pairs.setter
    def lc_fact_pairs(self, value):
        if not isinstance(value, list):
            raise ValueError("load_factor_pairs must be a list of (load, factor) tuples.")
        for pair in value:
            if (not isinstance(pair, tuple) or len(pair) != 2 or
                not hasattr(pair[0], 'calculate') or
                not isinstance(pair[1], (int, float))):
                raise ValueError("Each item must be a tuple: (load, numeric factor).")
        self._lc_fact_pairs = value

