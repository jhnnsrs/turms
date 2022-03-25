import pytest

from turms.helpers import import_string


def test_faulty_import():
    with pytest.raises(ImportError):
        import_string("invalid")

    with pytest.raises(ImportError):
        import_string("turms.plugins.base.RandomClass")
