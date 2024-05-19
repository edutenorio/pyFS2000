import logging
import os
from pathlib import Path
from datetime import datetime

from icecream import ic

# import pandas as pd

from .command import CommandMixin
from .csys import CSys
from .entity_list import EntityList
from .exceptions import ParameterInvalid
from .lists_mixin import ListsMixin
from .node import Node
from .element_offset import ElemOffset
from .element import Element
from .pparam import PParam
from .couple import Couple
from .geometry import Geometry
from .material import Material
from .ctype import CType
from .ic import IC
from .rc import RC
from .rest import Rest


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
    _systempath = Path(r'C:\Program Files (x86)\FS2000')  # Path of the FS2000 folder
    # _descriptor_list = ['NAME', 'TITLE', 'UNIT', 'DATE', 'TIME', 'BY', 'REF', 'DESC']
    # _command_list = []

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
        # self._descriptors = dict(((descriptor, '') for descriptor in self._descriptor_list))
        # self._csys_list = EntityList(CSys)
        # self._node_list = EntityList(Node)
        # self._element_list = EntityList(Element)
        self._elemoffset_list = EntityList(ElemOffset)
        self._pparam_list = EntityList(PParam)
        self._couple_list = EntityList(Couple)
        self._geometry_list = EntityList(Geometry)
        self._material_list = EntityList(Material)
        self._ctype_list = EntityList(CType)
        self._ic_list = EntityList(IC)
        self._rc_list = EntityList(RC)
        self._rest_list = EntityList(Rest)
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
        # return self._descriptors["NAME"]
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
        # Save .XYZ file path
        self._filepath = Path(os.path.join(filedir, f'{filename}.XYZ'))
        # Load model file (.MDL)
        mdlfile = Path(os.path.join(filedir, f'{filename}.MDL'))
        if not mdlfile.is_file():
            logger.error(f'File not found: "{mdlfile}"')
            raise FileNotFoundError(mdlfile)
        self.reset()
        logger.debug(f'Opening model file: "{mdlfile}"')
        self.cmd(mdlfile.read_text())
        logger.info(f'Model loaded from "{mdlfile}"')
        # Read loads
        lfiles = [Path(os.path.join(filedir, f'{f_}{e_}')) for f_, e_ in
                  [os.path.splitext(f) for f in os.listdir(filedir)] if
                  f_.upper() == filename.upper() and e_[:2].upper() == '.L' and e_[2:].isnumeric()]
        for lfile in lfiles:
            self.cmd(lfile.read_text())
        # Read load combinations
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
    def header(self):
        return self.__repr__()

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
    def _get_actcsys(self):
        """Active coordinate system"""
        return self._ACTCSYS

    def _set_actcsys(self, value):
        self._ACTCSYS = int(value)

    def _get_actn(self):
        """Active reference node"""
        return self._ACTN

    def _set_actn(self, value):
        self._ACTN = int(value)
        self._ACTN1 = self._ACTN

    def _get_actn1(self):
        """
        N2 node of last element or last node defined, used for element defaults
        """
        return self._ACTN1

    def _get_actn3(self):
        """Active third node for local element rotation definition"""
        return self._ACTN3

    def _set_actn3(self, value):
        self._ACTN3 = int(value)

    def _get_actrot(self):
        """Active local element rotation angle"""
        return self._ACTROT

    def _set_actrot(self, value):
        self._ACTROT = int(value)

    def _get_actgeom(self):
        """Active geometrical property table code"""
        return self._ACTGEOM

    def _set_actgeom(self, value):
        self._ACTGEOM = int(value)

    def _get_actmat(self):
        """Active material Property table code"""
        return self._ACTMAT

    def _set_actmat(self, value):
        self._ACTMAT = int(value)

    def _get_actrelz(self):
        """Active hinge Definition - local z-axis"""
        return self._ACTRELZ

    def _set_actrelz(self, value):
        self._ACTRELZ = int(value)

    def _get_actrely(self):
        """Active hinge Definition - local y-axis"""
        return self._ACTRELY

    def _set_actrely(self, value):
        self._ACTRELY = int(value)

    def _get_acttype(self):
        """Active element type"""
        return self._ACTTYPE

    def _set_acttype(self, value):
        self._ACTTYPE = int(value)

    def _get_actcon(self):
        """Active element CO constant"""
        return self._ACTCON

    def _set_actcon(self, value):
        self._ACTCON = int(value)

    def _get_actspconst(self):
        """Active spring/couple constant"""
        return self._ACTSPCONST

    def _set_actspconst(self, value):
        self._ACTSPCONST = int(value)

    ACTCSYS = property(_get_actcsys, _set_actcsys)
    ACTN = property(_get_actn, _set_actn)
    ACTN1 = property(_get_actn1)
    ACTN3 = property(_get_actn3, _set_actn3)
    ACTROT = property(_get_actrot, _set_actrot)
    ACTGEOM = property(_get_actgeom, _set_actgeom)
    ACTMAT = property(_get_actmat, _set_actmat)
    ACTRELZ = property(_get_actrelz, _set_actrelz)
    ACTRELY = property(_get_actrely, _set_actrely)
    ACTTYPE = property(_get_acttype, _set_acttype)
    ACTCON = property(_get_actcon, _set_actcon)
    ACTSPCONST = property(_get_actspconst, _set_actspconst)

    # Groups
    def _get_egroup(self):
        """Current group to which elements will be assigned"""
        return self._EGROUP

    def _set_egroup(self, value):
        self._EGROUP = int(value)

    def _get_grpset(self):
        """Current group set"""
        return self._GRPSET

    def _set_grpset(self, value):
        self._GRPSET = int(value)

    def _get_ngroup(self):
        """Current group to which nodes will be assigned"""
        return self._NGROUP

    def _set_ngroup(self, value):
        self._NGROUP = int(value)

    EGROUP = property(_get_egroup, _set_egroup)
    GRPSET = property(_get_grpset, _set_grpset)
    NGROUP = property(_get_ngroup, _set_ngroup)

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






    # Properties as pandas DataFrames
    # def _get_dataframe(self, entity_type):
    #     # return pd.DataFrame([[getattr(x, p) for p in entity_type.get_parameters()]
    #     #                      for x in getattr(self, entity_type.get_list_name())],
    #     #                     columns=entity_type.get_parameters()).set_index(entity_type.get_parameters()[0])
    #     return pd.DataFrame([[getattr(x, p) for p in entity_type.parameters]
    #                          for x in getattr(self, entity_type._list_name)],
    #                         columns=entity_type.parameters).set_index(entity_type.parameters[0])

    # dfCSystems = property(_get_dfcsystems)
    # def df_nodes(self):
    #     """Get the nodes as a Pandas DataFrame"""
    #     return self._get_dataframe(Node)
    #
    # def df_elements(self):
    #     """Get the elements as a Pandas DataFrame"""
    #     return self._get_dataframe(Element)
    #
    # def df_offsets(self):
    #     """Get the element offsets as a Pandas DataFrame"""
    #     return self._get_dataframe(ElemOffset)
    #
    # def df_pparams(self):
    #     """Get the pipework coefficient parameters as a Pandas DataFrame"""
    #     return self._get_dataframe(PParam)
    #
    # def df_couples(self):
    #     """Get the couple elements as a Pandas DataFrame"""
    #     return self._get_dataframe(Couple)
    #
    # def df_geometries(self):
    #     """Get the geometries as a Pandas DataFrame"""
    #     return self._get_dataframe(Geometry)
    #
    # def df_materials(self):
    #     """Get the materials as a Pandas DataFrame"""
    #     return self._get_dataframe(Material)
    #
    # def df_ctypes(self):
    #     """Get the couple types as a Pandas DataFrame"""
    #     return  self._get_dataframe(CType)
    #
    # def df_ics(self):
    #     """Get the integer constant tables as a Pandas DataFrame"""
    #     return self._get_dataframe(IC)
    #
    # def df_rcs(self):
    #     """Get the real constant tables as a Pandas DataFrame"""
    #     return self._get_dataframe(RC)
    #
    # def df_rests(self):
    #     """Get the restraints as a Pandas DataFrame"""
    #     return self._get_dataframe(Rest)
