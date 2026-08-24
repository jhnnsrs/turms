"""The 2.0 plugin config keys, and the deprecated spellings they replaced.

Plugin options had drifted into three different naming schemes for the same
concept (``types_bases`` / ``inputtype_bases`` / ``fragment_bases``, and
``add_documentation`` vs ``extract_documentation``). 2.0 converges them on
``<kind>_bases`` and ``extract_documentation``; the old spellings keep working
for one release so existing graphql.config.yaml files still load.
"""

import warnings

import pytest

from turms.plugins.fragments import FragmentsPluginConfig
from turms.plugins.inputs import InputsPluginConfig
from turms.plugins.objects import ObjectsPluginConfig
from turms.plugins.strawberry import StrawberryPluginConfig

RENAMES = [
    (ObjectsPluginConfig, "types_bases", "object_bases", ["x.Y"]),
    (InputsPluginConfig, "inputtype_bases", "input_bases", ["x.Y"]),
    (StrawberryPluginConfig, "inputtype_bases", "input_bases", ["x.Y"]),
    (FragmentsPluginConfig, "add_documentation", "extract_documentation", False),
]


@pytest.mark.parametrize("cls,old,new,value", RENAMES)
def test_deprecated_key_still_loads_and_warns(cls, old, new, value):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        config = cls(**{old: value})

    assert getattr(config, new) == value
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


@pytest.mark.parametrize("cls,old,new,value", RENAMES)
def test_setting_both_spellings_is_an_error(cls, old, new, value):
    with pytest.raises(ValueError, match="not both"):
        cls(**{old: value, new: value})


@pytest.mark.parametrize("cls,old,new,value", RENAMES)
def test_new_key_needs_no_warning(cls, old, new, value):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        config = cls(**{new: value})

    assert getattr(config, new) == value
    assert not [w for w in caught if issubclass(w.category, DeprecationWarning)]


def test_bases_options_share_one_convention():
    """Every plugin that takes base classes spells the option ``<kind>_bases``."""
    assert "object_bases" in ObjectsPluginConfig.model_fields
    assert "input_bases" in InputsPluginConfig.model_fields
    assert "input_bases" in StrawberryPluginConfig.model_fields
    assert "fragment_bases" in FragmentsPluginConfig.model_fields

    for cls in (ObjectsPluginConfig, InputsPluginConfig, StrawberryPluginConfig):
        assert "types_bases" not in cls.model_fields
        assert "inputtype_bases" not in cls.model_fields


def test_plugin_type_defaults_point_at_real_classes():
    """``type`` defaults are the dotted path turms imports to build the plugin."""
    from turms.helpers import import_string

    for cls in (
        ObjectsPluginConfig,
        InputsPluginConfig,
        StrawberryPluginConfig,
        FragmentsPluginConfig,
    ):
        import_string(cls().type)
