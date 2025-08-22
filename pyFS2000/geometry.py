import logging
import os
from dotenv import load_dotenv
import numpy as np
from icecream import ic

from .aux_functions import str_or_blank
from .base import ListedMixin, CalculatedMixin, FS2000Entity
from .exceptions import SectionTypeInvalid

load_dotenv()

def find_default_libraries(section_format_keys):
    fs2000_path = os.getenv("FS2000_DIR", r'C:\Program Files (x86)\FS2000')
    if not os.path.exists(fs2000_path):
        return []
    lib_files = [f.upper() for f in os.listdir(fs2000_path) if
                 os.path.splitext(f)[1].upper().startswith('.PR') and f[-1].upper() in section_format_keys]
    return lib_files

class Geometry(ListedMixin, CalculatedMixin, FS2000Entity):
    """Defines an FS2000 Geometry code."""
    type = 'GTAB'
    parameters = ['CODE', 'TYPE', 'NAME', 'DESIGNATION', 'GTYPE', 'GOFY', 'GOFZ', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6',
                  'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'C13', 'C14', 'C15', 'C16', 'C17', 'C18', 'C19', 'C20',
                  'CORRALL', 'MILLTOL', 'CONTDEN', 'INSULT', 'INSULDEN', 'LININGT', 'LININGDEN']
    paramdefaults = [0, 0, '', '', '', 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    # default_libraries = ['UB.PRI', 'UC.PRI', 'RSJ.PRI', 'PFC.PRC', 'RHS.PRB', 'SHS.PRB', 'RST.PRT', 'TUB.PRT',
    #                      'TUC.PRT', 'RSA.PRA', 'EA.PRL', 'UEA.PRL', 'DEA.PRD', 'DUA.PRD', 'HEA.PRI', 'HEB.PRI',
    #                      'HEM.PRI', 'IPE.PRI', 'IPN.PRI', 'WS_.PRI', 'HP_.PRI', 'MS_.PRI', 'SS_.PRI', 'CS_.PRB',
    #                      'MC_.PRB', 'HS_.PRB', 'WT_.PRT', 'MT_.PRT', 'ST_.PRT', 'AA_.PRA', 'AS_.PRL', 'DE_.PRD',
    #                      'DU_.PRD']
    section_format_keys = ['I', 'C', 'B', 'T', 'A', 'L', 'R', 'D', '1', '2']
    default_libraries = find_default_libraries(section_format_keys)
    default_libraries_name = [x.split('.')[0] for x in default_libraries]
    model_libraries_name = [f'MD{x}' for x in section_format_keys]

    def __init__(self, model, *args, **kwargs):
        """
        Creates a geometry property code within the model.
        """
        self._TYPE, self._NAME, self._DESIGNATION, self._GTYPE = 0, '   ', '         ', ' '
        self._GOFY, self._GOFZ = 0, 0
        self._C1, self._C2, self._C3, self._C4, self._C5, self._C6 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        self._C7, self._C8, self._C9, self._C10, self._C11, self._C12, self._C13 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        self._C14, self._C15, self._C16, self._C17, self._C18, self._C19, self._C20 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        self._CORRALL, self._MILLTOL, self._CONTDEN, self._INSULT = 0.0, 0.0, 0.0, 0.0
        self._INSULDEN, self._LININGT, self._LININGDEN = 0.0, 0.0, 0.0
        self._gtabp_defined = False
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        self.calculate()
        return f'Code Name Desig\'n       OD      Wall t    Area   Iz-Inertia Iy-Inertia Ix-Inertia(J)\n' \
               f'{self.pk:^4d}  {self._NAME:>3s} {self._DESIGNATION:<9s}  {self._C1:8.5f} {self._C2:8.5f} ' \
               f'{self._C3:9.3E}  {self._C4:9.3E}  {self._C5:9.3E}  {self._C6:9.3E}'

    def __str__(self):
        self.calculate()
        s = f'GTAB1,{self.pk},{self._TYPE},{self._NAME},{self._DESIGNATION},{self._GTYPE},{self._GOFY},{self._GOFZ}'
        s += f'\nGTAB2,{self.pk},{self._C1},{self._C2},{self._C3},{self._C4},{self._C5},{self._C6}'
        s += f'\nGTAB3,{self.pk},{self._C7},{self._C8},{self._C9},{self._C10},{self._C11}'
        s += f'\nGTAB4,{self.pk},{self._C12},{self._C13},{self._C14},{self._C15}'
        s += f'\nGTAB5,{self.pk},{self._C16},{self._C17},{self._C18},{self._C19},{self._C20}'
        if self._gtabp_defined:
            s += f'\nGTABP,{self.pk},{self._CORRALL},{self._MILLTOL},{self._CONTDEN},{self._INSULT},{self._INSULDEN},' \
                 f'{self._LININGT},{self._LININGDEN}'
        return s

    def commit(self, replace=True, update_items=None):
        super().commit()
        # Update active constants
        self._model.ACTGEOM = self.pk

    def set_to_pipe(self):
        """
        Set the TYPE, NAME, DESIGNMATION and GTYPE parameters to pipe.
        """
        self._TYPE = 3
        self._NAME = 'PIP'
        self._DESIGNATION = '0        '
        self._GTYPE = 'P'

    def calculate_pipe(self):
        # Calculate pipe properties
        if self._TYPE != 3:
            return
        if np.isclose(self._C1, 0.0):
            return
        od, wt = self._C1, self._C2
        _id = od - 2 * wt
        self._C3 = np.pi * (od ** 2 - _id ** 2) / 4
        self._C4 = np.pi * (od ** 4 - _id ** 4) / 64
        self._C5 = self._C4
        self._C6 = 2 * self._C4
        self._C7 = self._C3 / 2
        self._C8 = self._C3 / 2
        self._C9 = (od ** 3 - _id ** 3) / 6
        self._C10 = self._C9
        self._C11 = 2 * (od ** 3 - _id ** 3) / 3
        self._C12, self._C13 = od / 2, 0.0
        self._C14, self._C15 = 0.0, od / 2
        self._C16, self._C17, self._C18, self._C19 = 0.0, 0.0, 0.0, 0.0
        self._C20 = np.pi * (od ** 4 - _id ** 4) / (16 * od) if not np.isclose(od, 0.0) else 0.0
        self.TYPE = 3
        self.NAME = 'PIP'
        self.DESIGNATION = ' 0'
        self.GTYPE = 'P'

    def calculate(self):
        if self._calculated:
            return
        super().calculate()

    @property
    def CODE(self):
        return self.pk

    @property
    def TYPE(self):
        """
        Type of geometry data
            3  = Pipe
            10 = Compression only (non-linear)
            11 = Tension only (non-linear)
            Any other number implies beam data
        """
        return self._TYPE

    @TYPE.setter
    def TYPE(self, value):
        self._TYPE = int(value)
        if self._TYPE == 3:
            self.set_to_pipe()

    @property
    def NAME(self):
        """3 Character Name"""
        return self._NAME

    @NAME.setter
    def NAME(self, value):
        self._NAME = str_or_blank(str(value), length=3)

    @property
    def DESIGNATION(self):
        """Up to 9 numeric characters"""
        return self._DESIGNATION

    @DESIGNATION.setter
    def DESIGNATION(self, value):
        self._DESIGNATION = str_or_blank(str(value), length=9)

    @property
    def GTYPE(self):
        """Beam type for Virtual views"""
        return self._GTYPE

    @GTYPE.setter
    def GTYPE(self, value):
        self._GTYPE = str_or_blank(str(value), length=1)

    @property
    def GOFY(self):
        """Graphic y-offset for virtual views"""
        return self._GOFY

    @GOFY.setter
    def GOFY(self, value):
        self._GOFY = float(value)

    @property
    def GOFZ(self):
        """Graphic z-offset for virtual views"""
        return self._GOFZ

    @GOFZ.setter
    def GOFZ(self, value):
        self._GOFZ = float(value)

    @property
    def C1(self):
        return self._C1

    @C1.setter
    def C1(self, value):
        """Pipe OD (for Pipe data)"""
        self._C1 = float(value)
        if np.isclose(self._C2, 0.0):
            self._C2 = self._C1 / 2
        self.calculate_pipe()

    @property
    def C2(self):
        """Pipe Wall Thickness (for Pipe data)"""
        return self._C2

    @C2.setter
    def C2(self, value):
        self._C2 = float(value)
        self.calculate_pipe()

    @property
    def C3(self):
        """Area"""
        # self.calculate()
        return self._C3

    @C3.setter
    def C3(self, value):
        self._C3 = float(value)
        # self._calculated = False

    @property
    def C4(self):
        """Izz - Moment of inertia"""
        # self.calculate()
        return self._C4

    @C4.setter
    def C4(self, value):
        self._C4 = float(value)
        # self._calculated = False

    @property
    def C5(self):
        """Iyy - Moment of inertia"""
        # self.calculate()
        return self._C5

    @C5.setter
    def C5(self, value):
        self._C5 = float(value)
        # self._calculated = False

    @property
    def C6(self):
        """J - Polar moment of inertia"""
        # self.calculate()
        return self._C6

    @C6.setter
    def C6(self, value):
        self._C6 = float(value)
        # self._calculated = False

    @property
    def C7(self):
        """Ay - Shear area"""
        # self.calculate()
        return self._C7

    @C7.setter
    def C7(self, value):
        self._C7 = float(value)
        # self._calculated = False

    @property
    def C8(self):
        """Az - Shear area"""
        # self.calculate()
        return self._C8

    @C8.setter
    def C8(self, value):
        self._C8 = float(value)
        # self._calculated = False

    @property
    def C9(self):
        """Plastic Modulus zz axis"""
        # self.calculate()
        return self._C9

    @C9.setter
    def C9(self, value):
        self._C9 = float(value)
        # self._calculated = False

    @property
    def C10(self):
        """Plastic Modulus yy axis"""
        # self.calculate()
        return self._C10

    @C10.setter
    def C10(self, value):
        self._C10 = float(value)
        # self._calculated = False

    @property
    def C11(self):
        """Plastic Torsional Modulus"""
        # self.calculate()
        return self._C11

    @C11.setter
    def C11(self, value):
        self._C11 = float(value)
        # self._calculated = False

    @property
    def C12(self):
        """Stress point 1 y co-ordinate"""
        # self.calculate()
        return self._C12

    @C12.setter
    def C12(self, value):
        self._C12 = float(value)

    @property
    def C13(self):
        """Stress point 1 z co-ordinate"""
        # self.calculate()
        return self._C13

    @C13.setter
    def C13(self, value):
        self._C13 = float(value)

    @property
    def C14(self):
        """Stress point 2 y co-ordinate"""
        # self.calculate()
        return self._C14

    @C14.setter
    def C14(self, value):
        self._C14 = float(value)

    @property
    def C15(self):
        """Stress point 2 z co-ordinate"""
        # self.calculate()
        return self._C15

    @C15.setter
    def C15(self, value):
        self._C15 = float(value)

    @property
    def C16(self):
        """Stress point 3 y co-ordinate"""
        # self.calculate()
        return self._C16

    @C16.setter
    def C16(self, value):
        self._C16 = float(value)

    @property
    def C17(self):
        """Stress point 3 z co-ordinate"""
        # self.calculate()
        return self._C17

    @C17.setter
    def C17(self, value):
        self._C17 = float(value)

    @property
    def C18(self):
        """Stress point 4 y co-ordinate"""
        # self.calculate()
        return self._C18

    @C18.setter
    def C18(self, value):
        self._C18 = float(value)

    @property
    def C19(self):
        """Stress point 4 z co-ordinate"""
        # self.calculate()
        return self._C19

    @C19.setter
    def C19(self, value):
        self._C19 = float(value)

    @property
    def C20(self):
        """Elastic Torsional Modulus"""
        # self.calculate()
        return self._C20

    @C20.setter
    def C20(self, value):
        self._C20 = float(value)
        # self._calculated = False

    @property
    def has_pipeprops(self):
        """True if the geometry has pipe extended properties defined"""
        return self._gtabp_defined

    @property
    def CORRALL(self):
        """Corrosion Tolerance"""
        return self._CORRALL

    @CORRALL.setter
    def CORRALL(self, value):
        self._CORRALL = float(value)
        self._gtabp_defined = True
        self._calculated = False

    @property
    def MILLTOL(self):
        """Mill Tolerance %"""
        return self._MILLTOL

    @MILLTOL.setter
    def MILLTOL(self, value):
        self._MILLTOL = float(value)
        self._gtabp_defined = True
        self._calculated = False

    @property
    def CONTDEN(self):
        """Contents Density"""
        return self._CONTDEN

    @CONTDEN.setter
    def CONTDEN(self, value):
        self._CONTDEN = float(value)
        self._gtabp_defined = True
        self._calculated = False

    @property
    def INSULT(self):
        """Insulation Thickness"""
        return self._INSULT

    @INSULT.setter
    def INSULT(self, value):
        self._INSULT = float(value)
        self._gtabp_defined = True
        self._calculated = False

    @property
    def INSULDEN(self):
        """Insulation Density"""
        return self._INSULDEN

    @INSULDEN.setter
    def INSULDEN(self, value):
        self._INSULDEN = float(value)
        self._gtabp_defined = True
        self._calculated = False

    @property
    def LININGT(self):
        """Internal Lining Thickness"""
        return self._LININGT

    @LININGT.setter
    def LININGT(self, value):
        self._LININGT = float(value)
        self._gtabp_defined = True
        self._calculated = False

    @property
    def LININGDEN(self):
        """Internal Lining Density"""
        return self._LININGDEN

    @LININGDEN.setter
    def LININGDEN(self, value):
        self._LININGDEN = float(value)
        self._gtabp_defined = True
        self._calculated = False

    @property
    def weyy(self):
        """Elastic Modulus yy axis"""
        self.calculate()
        zmax = max(np.abs([self._C13, self._C15, self._C17, self._C19]))
        if not np.isclose(zmax, 0.0):
            return self._C5 / zmax
        else:
            return 0.0

    @property
    def wezz(self):
        """Elastic Modulus zz axis"""
        self.calculate()
        ymax = max(np.abs([self._C12, self._C14, self._C16, self._C18]))
        if not np.isclose(ymax, 0.0):
            return self._C4 / ymax
        else:
            return 0.0

    # Fancy names for properties
    @property
    def od(self):
        """Pipe OD"""
        return self._C1

    @od.setter
    def od(self, value):
        self.C1 = value

    @property
    def wt(self):
        """Pipe wall thickness"""
        return self._C2

    @wt.setter
    def wt(self, value):
        self.C2 = value

    @property
    def ax(self):
        """Area"""
        self.calculate()
        return self._C3

    @property
    def izz(self):
        """Izz - Moment of inertia"""
        self.calculate()
        return self._C4

    @property
    def iyy(self):
        """Iyy - Moment of inertia"""
        self.calculate()
        return self._C5

    @property
    def j(self):
        """J - Polar moment of inertia"""
        self.calculate()
        return self._C6

    @property
    def ay(self):
        """Ay - Shear area"""
        self.calculate()
        return self._C7

    @property
    def az(self):
        """Az - Shear area"""
        self.calculate()
        return self._C8

    @property
    def wpzz(self):
        """Plastic Modulus zz axis"""
        self.calculate()
        return self._C9

    @property
    def wpyy(self):
        """Plastic Modulus yy axis"""
        self.calculate()
        return self._C10

    @property
    def wpxx(self):
        """Plastic Torsional Modulus"""
        self.calculate()
        return self._C11

    @property
    def c1y(self):
        """Stress point 1 y co-ordinate"""
        return self._C12

    @property
    def c1z(self):
        """Stress point 1 z co-ordinate"""
        return self._C13

    @property
    def c2y(self):
        """Stress point 2 y co-ordinate"""
        return self._C14

    @property
    def c2z(self):
        """Stress point 2 z co-ordinate"""
        return self._C15

    @property
    def c3y(self):
        """Stress point 3 y co-ordinate"""
        return self._C16

    @property
    def c3z(self):
        """Stress point 3 z co-ordinate"""
        return self._C17

    @property
    def c4y(self):
        """Stress point 4 y co-ordinate"""
        return self._C18

    @property
    def c4z(self):
        """Stress point 4 z co-ordinate"""
        return self._C19

    @property
    def wexx(self):
        """Elastic Torsional Modulus"""
        self.calculate()
        return self._C20

    @property
    def insul_area(self):
        """External insulation cross-section area"""
        if not self._gtabp_defined:
            return 0.0
        insul_ir = self._C1 / 2
        insul_or = insul_ir + self._INSULT
        return np.pi * (insul_or ** 2 - insul_ir ** 2)

    @property
    def lining_area(self):
        """Internal lining cross-section area"""
        if not self._gtabp_defined:
            return 0.0
        lining_or = self._C1 / 2 - self._C2
        lining_ir = lining_or - self.LININGT
        return np.pi * (lining_or ** 2 - lining_ir ** 2)

    @property
    def cont_area(self):
        """Internal contents cross-section area"""
        cont_r = self._C1 / 2 - self._C2 - self._LININGT
        return np.pi * (cont_r ** 2)

    @property
    def insul_mass(self):
        """External insulation mass per unit length"""
        if not self._gtabp_defined:
            return 0.0
        insul_ir = self._C1 / 2
        insul_or = insul_ir + self._INSULT
        return np.pi * (insul_or ** 2 - insul_ir ** 2) * self._INSULDEN

    @property
    def lining_mass(self):
        """Internal lining mass per unit length"""
        if not self._gtabp_defined:
            return 0.0
        lining_or = self._C1 / 2 - self._C2
        lining_ir = lining_or - self.LININGT
        return np.pi * (lining_or ** 2 - lining_ir ** 2) * self._LININGDEN

    @property
    def cont_mass(self):
        """Internal contents mass per unit length"""
        cont_r = self._C1 / 2 - self._C2 - self._LININGT
        return np.pi * (cont_r ** 2) * self._CONTDEN

    def get_dimensions(self):
        """Get the section dimensions for the specific section type.
        --- Work in progress ---"""
        logger = logging.getLogger('FS2000')
        # NAME can be 'PIP' for pipe, 'USD' for user defined or one of the default or model defined list
        if self._NAME == 'PIP':
            return {'FORMAT': 'P',
                    'UNIT': '"m"' if self._model.is_SI() else '"in"',
                    'OD': self._C1, 'WT': self._C2}
        filepath = None
        if self._NAME.strip() in self.default_libraries_name:
            filename = self.default_libraries[self.default_libraries_name.index(self._NAME.strip())]
            filepath = self._model.SystemPath.joinpath(filename)
        elif self._NAME in self.model_libraries_name:
            filename = f'{self._model.NAME}.PR{self._NAME[2]}'
            filepath = self._model.ModelDir.joinpath(filename)
        if filepath is None:
            return None
        section_format = str(filepath)[-1]
        # result = {'FORMAT': section_format}
        if section_format not in self.section_format_keys:
            raise SectionTypeInvalid(f'Section format "{section_format}" not defined.')
        if not filepath.exists():
            logger.warning(f'Section file "{filepath.name}" not found.')
            return None
        file = open(filepath, 'r')
        lines = file.read().split('\n')
        file.close()
        # Read section units
        # section_unit = '"in"' if 'INCH' in lines[0] else '"mm"'
        section_unit = 'in' if 'INCH' in lines[0] else 'mm'
        # Read header for properties
        headers = lines[1].split()
        # Read lines to look for the section designation
        vals = []
        section_found = False
        for line in lines[2:]:
            vals = line.split()
            vals[0] = vals[0] if vals[0][0] != '-' else vals[0][1:]
            if vals[0] == self._DESIGNATION.strip():
                section_found = True
                break
        if not section_found:
            logger.warning(f'Section "{self._DESIGNATION}" not found in file "{filepath.name}".')
            return None
        # return dict(zip(['FORMAT', 'UNIT'] + headers,
        #                 [section_format, section_unit, f'"{self._NAME} {vals[0]}"'] + [float(x) for x in vals[1:]]))
        return dict(zip(['FORMAT', 'UNIT'] + headers,
                        [section_format, section_unit, f'{self._NAME} {vals[0]}'] + [float(x) for x in vals[1:]]))
