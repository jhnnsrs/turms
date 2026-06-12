---
sidebar_position: 1
sidebar_label: "Traits"
title: "Traits"
---

Traits are just mixins. Generated code shouldn't be edited — but it can be **extended**. If you
want to attach extra logic to a specific type in your schema, list your own classes under
`additional_bases` and turms will inject them as base classes of every generated model for that
GraphQL type:

```yaml
projects:
  default:
    schema: ...
    extensions:
      turms:
        additional_bases:
          Country:
            - myapp.traits.CountryTrait
```

```python
# myapp/traits.py
from pydantic import BaseModel, field_validator


class CountryTrait(BaseModel):
    @field_validator("code", check_fields=False)
    @classmethod
    def code_must_be_upper(cls, v: str) -> str:
        if not v.isupper():
            raise ValueError("country codes are uppercase")
        return v

    @property
    def flag_url(self) -> str:
        return f"https://flagcdn.com/{self.code.lower()}.svg"
```

The trait is applied **everywhere the GraphQL type appears** — object types, fragments, and even
the deeply nested classes generated inside operation results:

```python
class GetCountriesCountries(CountryTrait, BaseModel):
    code: str
    name: str
```

Traits are prepended to the base list, so their method resolution order beats the generated
defaults.

## Why use traits?

- **Validators**: enforce domain invariants the moment data arrives from the API. Use
  `field_validator(..., check_fields=False)` (the field is declared on the generated subclass,
  not the mixin) or `model_validator` for cross-field rules.

- **Add-in logic**: add computed properties and methods that travel with the data — conversion
  helpers (`.to_numpy()`, `.as_tuple()`), URLs, business logic. Even in complex nested documents
  every selection of that type carries the logic.

- **Instance checks**: since traits become real base classes, `isinstance(obj, CountryTrait)`
  works across all generated variants of the type, however deeply nested the selection was.
