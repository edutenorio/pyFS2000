import logging
import os
from pathlib import Path
from datetime import datetime
from icecream import ic
from dotenv import load_dotenv

from .command import CommandMixin
from .csys import CSys
from .exceptions import ParameterInvalid
from .lists_mixin import ListsMixin

load_dotenv()


class Model(CommandMixin, ListsMixin):
    """
    Class to represent an FS2000 Model

    It holds lists of all the FS2000 model entities such as nodes, elements, etc

    Entities should be created or deleted using the same command lines as in the
    FS2000 program, using the 'cmd' function.

    Example, to create a node with number 15 and coordinates (2.5,0,5.5):
    m1 = Model(NAME='Any_Model_Name')
    m1.cmd('N,15,2.5,0,5.5')
    """
    _systempath = Path(os.getenv("FS2000_DIR"), r'C:\Program Files (x86)\FS2000')  # Path of the FS2000 folder

    def __init__(self, filename: str = None):
        """
        Initiate a Model object

        Parameters
        ----------
        filename : str or None
            If specified, the model will be created with the file data.
        """
        super().__init__()
        # Model definition
        self._reformat = False
        self._fsversion = 'FS2000 Version Unknown'
        self._NAME, self._TITLE, self._UNIT, self._udef = 'NEWMOD', 'Model', 'S.I.', 0
        self._BY, self._REF, self._DESC = 'User', 'A', 'B'
        self._datetime = datetime.now()
        self._DATE, self._TIME = self._datetime.strftime('%d/%m/%Y'), self._datetime.strftime('%H:%M:%S')

        # General model parameters and objects
        self._filepath = Path('')  # File path to load from and save to
        # Other parameters
        self._ACTCSYS = 0  # Active coordinate system
        self._ACTN = 0  # Reference node
        self._ACTN1 = 0  # N2 node of last element or last node defined, used for element defaults
        self._ACTN3 = 0  # Third node for local element rotation definition (Default = 0)
        self._ACTROT = 0  # Local element rotation angle (default = 0)
        self._ACTGEOM = 1  # Geometrical property table code (default = 1)
        self._ACTMAT = 1  # Material Property table code (default = 1)
        self._ACTRELZ = 0  # Hinge Definition - local z axis  (0, 1, 2, or 3) (default = 0)
        self._ACTRELY = 0  # Hinge Definition - local y axis  (0, 1, 2, or 3)  (default = 0)
        self._ACTTYPE = 0  # Element type (default = 0)
        self._ACTCON = 0  # Element CO constant (default = 0)
        self._ACTSPCONST = 0  # Spring/Couple constant (default = 0)
        self._EGROUP = 0  # Current group to which elements will be assigned
        self._GRPSET = 0  # Current group set
        self._NGROUP = 0  # Current group to which nodes will be assigned
        self._NMAX = 0  # Maximum node label defined in the model
        self._CSYSMAX = 5  # Maximum coordinate system defined in the model
        self._EMAX = 0  # Maximum element label defined in the model
        self._SCMAX = 0  # Maximum spring/couple element label defined in the model
        self._GEOMMAX = 0  # Maximum geometry property code defined in the model
        self._MATMAX = 0  # Maximum material property code defined in the model
        self._CTYPEMAX = 0  # Maximum couple type property code defined in the model
        self._ICMAX = 0  # Maximum integer constant table code defined in the model
        self._RCMAX = 0  # Maximum real constant table code defined in the model
        # self._RESTMAX = 0  # Maximum node restraint table code defined in the model
        # self._PPARAMMAX = 0  # Maximum pipework coefficient code defined in the model
        # self._EOFMAX = 0  # Maximum element offset key defined in the model
        self._LASTNODE = None  # Last node defined
        self._LASTELEM = None  # Last element defined
        self._LASTSC = None  # Last couple element defined
        self._ACTLCASE = None  # Active load case
        # Default Coordinate Systems
        CSys(self, pk=0, TYPE=0).commit()
        CSys(self, pk=1, TYPE=1).commit()
        CSys(self, pk=2, TYPE=2).commit()

    def reset(self):
        self.__init__()

    def __repr__(self):
        return f'FS2000 Model\n' \
               f'------------\n' \
               f'Model Name        : {self._NAME}\n' \
               f'Model Description : {self._TITLE}\n' \
               f'Units Description : {self._UNIT}\n' \
               f'Created By        : {self._BY}\n' \
               f'Ref No            : {self._REF}\n' \
               f'Add\'l Description : {self._DESC}'

    def __str__(self):
        return self._NAME

    def _set_active_constant(self, active_constant, value):
        setattr(self, f'_{active_constant}', value)

    def _get_filename_split(self, filename: str = None):
        """
        Return the path, file name and extension of a given filename.
        If none, return the same for self._filepath."""
        if filename is not None:
            filedir = os.path.dirname(filename)
            filename, fileext = os.path.splitext(os.path.basename(filename))
            return filedir, filename, fileext
        filedir = os.path.dirname(self._filepath)
        filename = f'{self._NAME}'
        fileext = '.XYZ'
        return filedir, filename, fileext

    def load(self, filename: str = None):
        """
        Load an FS2000 model from a disk. The current model entities will be
        cleared.

        filename : str (optional), default = None
            Name of the file to be loaded. If None or not specified, the current
            model name will be used to look for "<NAME>.XYZ" in the current
            working directory. If a file name is specified, it will override the
            current model.
        """
        logger = logging.getLogger('FS2000')
        filedir, filename, fileext = self._get_filename_split(filename)
        # Load model file (.MDL)
        mdlfile = Path(os.path.join(filedir, f'{filename}.MDL'))
        if not mdlfile.is_file():
            logger.error(f'Model file not found: "{mdlfile}"')
            raise FileNotFoundError(mdlfile)
        # Reset model
        self.reset()
        logger.debug(f'Opening model file: "{mdlfile}"')
        # Save .XYZ file path after reset
        self._filepath = Path(os.path.join(filedir, f'{filename}.XYZ'))
        # Execute mdl file lines as commands
        self.cmd(mdlfile.read_text())
        logger.info(f'Model loaded from "{mdlfile}"')
        # Read loads
        lfiles = [Path(os.path.join(filedir, f'{f_}{e_}')) for f_, e_ in
                  [os.path.splitext(f) for f in os.listdir(filedir)] if
                  f_.upper() == filename.upper() and e_[:2].upper() == '.L' and e_[2:].isnumeric()]
        for lfile in lfiles:
            self.cmd(lfile.read_text())
        # Read load combinations - to be implemented
        return self

    def save(self):
        """
        Save the model to disk. Current directory and descriptor NAME will be
        used to create the file name:
        <WORKING DIR>/<NAME>.MDL

        To save with a different name, use the "save_as" function.
        """
        filedir, filename, fileext = os.path.dirname(self._filepath), f'{self._NAME}', '.MDL'
        self.save_as(filename, filedir)

    def save_as(self, new_name, filedir=None):
        """
        Rename the model and save to disk

        new_name : str
            Name of the new model. The NAME descriptor will be updated to match

        filedir : str (optional)
            Path to save the model at. If not specified, the model will be saved
            in the current working directory.
        """
        # Create directory if not exists
        dirpath = Path(filedir if filedir is not None else '.')
        if not dirpath.exists():
            dirpath.mkdir(parents=True, exist_ok=True)
        # Update model name
        self._NAME = new_name
        self._filepath = Path(os.path.join(dirpath, f'{new_name}.XYZ'))
        # Write to the file
        logging.debug(f'Saving model to file \'{self._filepath}\'')
        mdl_filepath = Path(os.path.join(dirpath, f'{new_name}.MDL'))
        with open(mdl_filepath, 'w') as f:
            # REFORMAT flag
            if self._reformat:
                f.write('REFORMAT\n')
            # Model Definition
            f.write(f'{self._fsversion}\n')
            for descriptor in ['NAME', 'TITLE', 'UNIT', 'DATE', 'TIME', 'BY', 'REF', 'DESC']:
                f.write(f'{descriptor},{getattr(self, descriptor)}\n')
            # Write model elements
            for vec in [self._csys_list[3:], self._node_list, self._element_list, self._pparam_list,
                        self._elemoffset_list, self._couple_list, self._geometry_list, self._material_list,
                        self._ctype_list, self._ic_list, self._rc_list, self._rest_list]:
                for obj in vec:
                    f.write(f'{str(obj)}\n')
            # End of data
            f.write('END OF DATA\n')
            # Close file
            f.close()
        # Log
        logger = logging.getLogger('FS2000')
        logger.info(f'Model saved to "{self._filepath}"')

    # Descriptors and Version properties
    def is_SI(self):
        """
        Returns True if the Systeme International is used (International System
        of Units).
        """
        return self._udef == 0

    @staticmethod
    def get_active_model():
        filename = os.path.join(Model._systempath, 'MODEL.NAM')
        if not os.path.exists(filename):
            raise FileNotFoundError(f'FS2000 MODEL.NAM file not found in {Model._systempath}.')
        f = open(filename, 'r')
        lines = f.read().split('\n')
        f.close()
        if len(lines) < 3:
            raise ValueError(f'FS2000 MODEL.NAM file in {Model._systempath} is corrupted.')
        return {'FILE': f'{lines[0].strip()}.XYZ', 'NAME': lines[1].strip(), 'PATH': lines[2].strip()}

    # Model Definition
    @property
    def NAME(self):
        """Model Name"""
        return self._NAME

    @NAME.setter
    def NAME(self, value):
        self._NAME = str(value)

    @property
    def TITLE(self):
        """Model Description"""
        return self._TITLE

    @TITLE.setter
    def TITLE(self, value):
        self._TITLE = str(value)

    @property
    def UNIT(self):
        """Unit System"""
        return self._UNIT

    @UNIT.setter
    def UNIT(self, value):
        unit = value
        if ('SI' in unit) or ('S.I.' in unit):
            self._UNIT = unit
            self._udef = 0
            return
        if ('US' in unit) or ('U.S.' in unit):
            self._UNIT = unit
            self._udef = 1
            return
        raise ParameterInvalid(f'Unit system description invalid: {unit}.')

    @property
    def UDEF(self):
        """Unit System Definition: 0 - SI, 1 - US Units"""
        return self._udef

    @UDEF.setter
    def UDEF(self, value):
        udef = int(value)
        if udef not in [0, 1]:
            raise ParameterInvalid(f'Unit definition through UDEF should be 0 or 1, not {udef}.')
        self._udef = udef

    @property
    def DATE(self):
        """Current Date of the Model"""
        return self._DATE

    @DATE.setter
    def DATE(self, value):
        value = value.replace('.', '/').replace('-', '/')
        d, m, y = [int(x) for x in value.split('/')]
        d, m = (d, m) if m <= 12 else (m, d)
        value = f'{d:02d}/{m:02d}/{y:04d}'
        date = datetime.strptime(value, '%d/%m/%Y')
        time = datetime.strptime(self._TIME, '%H:%M:%S')
        self._datetime = datetime(date.year, date.month, date.day, time.hour, time.minute, time.second)
        self._DATE = self._datetime.strftime('%d/%m/%Y')

    @property
    def TIME(self):
        """Current Time of the Model"""
        return self._TIME

    @TIME.setter
    def TIME(self, value):
        date = datetime.strptime(self._DATE, '%d/%m/%Y')
        time = datetime.strptime(value, '%H:%M:%S')
        self._datetime = datetime(date.year, date.month, date.day, time.hour, time.minute, time.second)
        self._TIME = self._datetime.strftime('%H:%M:%S')

    @property
    def BY(self):
        """Created by"""
        return self._BY

    @BY.setter
    def BY(self, value):
        self._BY = str(value)

    @property
    def REF(self):
        """Reference No"""
        return self._REF

    @REF.setter
    def REF(self, value):
        self._REF = str(value)

    @property
    def DESC(self):
        """Additional Description"""
        return self._DESC

    @DESC.setter
    def DESC(self, value):
        self._DESC = str(value)

    @property
    def FS2000Version(self):
        """FS2000 Version"""
        return self._fsversion

    @FS2000Version.setter
    def FS2000Version(self, value):
        fsversion = str(value)
        self._fsversion = fsversion if 'FS2000 VERSION' in fsversion else f'FS2000 VERSION {fsversion}'

    @property
    def SystemPath(self):
        r"""FS2000 folder. Default is 'C:\Program Files (x86)\FS2000'"""
        return self._systempath

    @SystemPath.setter
    def SystemPath(self, value):
        self._systempath = value

    @property
    def FilePath(self):
        """Model file path. Read only, to change it, use the 'save_as' function"""
        return self._filepath
    
    @property
    def ModelDir(self):
        """Current Model directory"""
        return self._filepath.parent

    # Active Constants properties
    @property
    def ACTCSYS(self):
        """Active coordinate system"""
        return self._ACTCSYS

    @ACTCSYS.setter
    def ACTCSYS(self, value):
        self._ACTCSYS = int(value)

    @property
    def ACTN(self):
        """Active reference node"""
        return self._ACTN

    @ACTN.setter
    def ACTN(self, value):
        self._ACTN = int(value)
        self._ACTN1 = self._ACTN

    @property
    def ACTN1(self):
        """
        N2 node of last element or last node defined, used for element defaults
        """
        return self._ACTN1

    @property
    def ACTN3(self):
        """Active third node for local element rotation definition"""
        return self._ACTN3

    @ACTN3.setter
    def ACTN3(self, value):
        self._ACTN3 = int(value)

    @property
    def ACTROT(self):
        """Active local element rotation angle"""
        return self._ACTROT

    @ACTROT.setter
    def ACTROT(self, value):
        self._ACTROT = int(value)

    @property
    def ACTGEOM(self):
        """Active geometrical property table code"""
        return self._ACTGEOM

    @ACTGEOM.setter
    def ACTGEOM(self, value):
        self._ACTGEOM = int(value)

    @property
    def ACTMAT(self):
        """Active material Property table code"""
        return self._ACTMAT

    @ACTMAT.setter
    def ACTMAT(self, value):
        self._ACTMAT = int(value)

    @property
    def ACTRELZ(self):
        """Active hinge Definition - local z-axis"""
        return self._ACTRELZ

    @ACTRELZ.setter
    def ACTRELZ(self, value):
        self._ACTRELZ = int(value)

    @property
    def ACTRELY(self):
        """Active hinge Definition - local y-axis"""
        return self._ACTRELY

    @ACTRELY.setter
    def ACTRELY(self, value):
        self._ACTRELY = int(value)

    @property
    def ACTTYPE(self):
        """Active element type"""
        return self._ACTTYPE

    @ACTTYPE.setter
    def ACTTYPE(self, value):
        self._ACTTYPE = int(value)

    @property
    def ACTCON(self):
        """Active element CO constant"""
        return self._ACTCON

    @ACTCON.setter
    def ACTCON(self, value):
        self._ACTCON = int(value)

    @property
    def ACTSPCONST(self):
        """Active spring/couple constant"""
        return self._ACTSPCONST

    @ACTSPCONST.setter
    def ACTSPCONST(self, value):
        self._ACTSPCONST = int(value)

    # Groups
    @property
    def EGROUP(self):
        """Current group to which elements will be assigned"""
        return self._EGROUP

    @EGROUP.setter
    def EGROUP(self, value):
        self._EGROUP = int(value)

    @property
    def GRPSET(self):
        """Current group set"""
        return self._GRPSET

    @GRPSET.setter
    def GRPSET(self, value):
        self._GRPSET = int(value)

    @property
    def NGROUP(self):
        """Current group to which nodes will be assigned"""
        return self._NGROUP

    @NGROUP.setter
    def NGROUP(self, value):
        self._NGROUP = int(value)

    # Max defined elements
    @property
    def CSYSMAX(self):
        """Maximum coordinate system label defined in the model"""
        return self._csys_list.pkmax

    @CSYSMAX.setter
    def CSYSMAX(self, value):
        self._csys_list.pkmax = int(value)

    @property
    def NMAX(self):
        """Maximum node label defined in the model"""
        return self._node_list.pkmax

    @NMAX.setter
    def NMAX(self, value):
        self._node_list.pkmax = int(value)

    @property
    def EMAX(self):
        """Maximum element label defined in the model"""
        return self._element_list.pkmax

    @EMAX.setter
    def EMAX(self, value):
        self._element_list.pkmax = int(value)

    @property
    def SCMAX(self):
        """Maximum spring/couple element label defined in the model"""
        return self._couple_list.pkmax

    @SCMAX.setter
    def SCMAX(self, value):
        self._couple_list.pkmax = int(value)

    @property
    def GEOMMAX(self):
        """Maximum geometry property code defined in the model"""
        return self._geometry_list.pkmax

    @GEOMMAX.setter
    def GEOMMAX(self, value):
        self._geometry_list.pkmax = int(value)

    @property
    def MATMAX(self):
        """Maximum material property code defined in the model"""
        return self._MATMAX

    @MATMAX.setter
    def MATMAX(self, value):
        self._material_list.pkmax = int(value)
        
    @property
    def CTYPEMAX(self):
        """Maximum couple type property code defined in the model"""
        return self._CTYPEMAX
    
    @CTYPEMAX.setter
    def CTYPEMAX(self, value):
        self._ctype_list.pkmax = int(value)
    
    @property
    def ICMAX(self):
        """Maximum integer constant table code defined in the model"""
        return self._ICMAX
    
    @ICMAX.setter
    def ICMAX(self, value):
        self._ic_list.pkmax = int(value)

    # SCMAX = property(_get_scmax)
    # MATMAX = property(_get_matmax)
    # CTYPEMAX = property(_get_ctypemax)
    # ICMAX = property(_get_icmax)
    # RCMAX = property(_get_rcmax)
    # RESTMAX = property(_get_restmax)
    # PPARAMMAX = property(_get_pparammax)
    # EOFMAX = property(_get_eofmax)

    # Last defined elements
    @property
    def LASTNODE(self):
        """Last node defined"""
        return self._LASTNODE

    @property
    def LASTELEM(self):
        """Last element defined"""
        return self._LASTELEM

    @property
    def LASTSC(self):
        """Last couple element defined"""
        return self._LASTSC

    @property
    def ACTLCASE(self):
        """Active Load Case"""
        return self._ACTLCASE

    @ACTLCASE.setter
    def ACTLCASE(self, value):
        self._ACTLCASE = int(value)
