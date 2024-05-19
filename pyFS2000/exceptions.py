"""
Definitions of FS2000 exceptions
"""
import logging


class FS2000Exception(Exception):
    """Basic Exception class for pyFS2000"""
    def __init__(self, *args):
        if len(args) > 0:
            logger = logging.getLogger('FS2000')
            logger.error(args[0])
        super().__init__(*args)


class CommandError(FS2000Exception):
    pass


class ArgumentError(FS2000Exception):
    pass


class PrimaryKeyBoundError(FS2000Exception):
    pass


# class ValidationError(FS2000Exception):
#     pass


# class NotAModelObject(FS2000Exception):
#     pass


# class CopyNotAllowed(FS2000Exception):
#     pass


class NoDefault(FS2000Exception):
    pass


class EntityNotFound(FS2000Exception):
    pass


class ParameterInvalid(FS2000Exception):
    pass


class TypeInvalid(FS2000Exception):
    pass


class SectionTypeInvalid(FS2000Exception):
    pass


class VectorSizeError(FS2000Exception):
    pass
