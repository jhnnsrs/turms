class RegistryError(Exception):
    pass


class NoScalarFound(RegistryError):
    pass


class NoInputTypeFound(RegistryError):
    pass


class NoEnumFound(RegistryError):
    pass


class GenerationError(Exception):
    pass
