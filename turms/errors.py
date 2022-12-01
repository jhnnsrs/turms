class TurmsError(Exception):
    """Base class for all Turms errors"""

    pass


class RegistryError(Exception):
    """Base class for all registry errors"""

    pass


class NoScalarFound(RegistryError):
    """Raised when no scalar is found for a given type. Needs to provided by additional scalars"""

    pass


class NoInputTypeFound(RegistryError):
    """Raised when no input type is found for a given type. Often raised if the input plugin is not loaded, and operations
    use input tyes"""

    pass


class NoEnumFound(RegistryError):
    """Raised when no enum is found for a given type. Often raised if the enum plugin is not loaded, and operations or fragments
    use enums"""

    pass


class GenerationError(TurmsError):
    """Base class for all generation errors"""

    pass
