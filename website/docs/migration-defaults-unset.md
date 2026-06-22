---
sidebar_position: 6
sidebar_label: "Migration: Defaults & UNSET"
---

# Migration Guide: the UNSET / "backend owns defaults" model

:::danger Breaking change
This release changes how turms handles **default values** on input fields and
operation variables. Generated models change shape, and your client's executor
**must** now serialize with `exclude_unset=True`. Read the
[What you must change](#what-you-must-change) section before regenerating.
:::

## TL;DR

- GraphQL **schema defaults are no longer baked into the generated client**. A
  field with a default (`Int! = 5`, `Int = 10`, `[Int!] = [1, 2, 3]`) is now
  emitted as **optional, defaulting to `None`** — the literal default is owned by
  the **server**.
- To make this work end-to-end you must serialize variables with
  **`exclude_unset=True`** so fields the caller never touched are omitted on the
  wire and the server applies its own default.
- The convenience functions (`funcs` plugin) and the new
  [`input_funcs`](plugins/inputfuncs) plugin default optional parameters to a new
  **`UNSET` sentinel** and build the payload conditionally, so they distinguish
  *"caller omitted the argument"* (→ omitted → server default) from *"caller
  passed `null`"* (→ sent as `null`).
- The original schema default and any deprecation reason are preserved as
  introspectable **`Annotated` markers** (`GraphQLDefault`, `Deprecated`) and,
  optionally, folded into the field documentation.

## Why the change?

Previously turms baked the schema's default value straight into the pydantic
model:

```python
# OLD
class Filter(BaseModel):
    limit: int = 10          # default copied from the schema
```

This is wrong for a GraphQL client. A baked default means the client **always
sends `10`** when the caller doesn't override it. If the server later changes its
default, or computes the default dynamically, the client silently overrides it.
The client also can't tell the difference between *"use the server default"* and
*"the value happens to be 10"*.

The correct model is **the backend owns its defaults**. The client should only
send a value when the caller explicitly provides one; otherwise it should omit
the field entirely and let the server fill it in.

## What changed in the generated code

### 1. Defaulted fields become optional `= None`

Given this schema:

```graphql
input DefaultInput {
    requiredWithDefault: Int! = 5
    optionalWithDefault: Int = 10
    listWithDefault: [Int!] = [1, 2, 3]
    plainRequired: String!
}
```

**Before:**

```python
class DefaultInput(BaseModel):
    required_with_default: int = Field(alias="requiredWithDefault", default=5)
    optional_with_default: Optional[int] = Field(alias="optionalWithDefault", default=10)
    list_with_default: List[int] = Field(alias="listWithDefault", default_factory=lambda: [1, 2, 3])
    plain_required: str = Field(alias="plainRequired")
```

**After:**

```python
class DefaultInput(BaseModel):
    required_with_default: Annotated[Optional[int], GraphQLDefault('5')] = Field(alias="requiredWithDefault", default=None)
    optional_with_default: Annotated[Optional[int], GraphQLDefault('10')] = Field(alias="optionalWithDefault", default=None)
    list_with_default: Annotated[Optional[List[int]], GraphQLDefault('[1, 2, 3]')] = Field(alias="listWithDefault", default=None)
    plain_required: str = Field(alias="plainRequired")
```

Note that even a **NonNull-with-default** field (`Int! = 5`) becomes
`Optional[...] = None`: because the server supplies the default, the field is no
longer required on the client. A required field **without** a default
(`plainRequired`) is unchanged — still required.

The same transformation applies to **operation variables**
(`$limit: Int = 10`, `$req: Int! = 5`).

### 2. The `GraphQLDefault` / `Deprecated` markers

The schema default isn't lost — it's preserved as an `Annotated` metadata marker
so it stays introspectable:

```python
Annotated[Optional[int], GraphQLDefault('10')]   # default preserved as a string
Annotated[str, Deprecated('use limit instead')]  # deprecation reason preserved
```

By default these marker classes are **generated into the output module**. You can
point turms at your own classes instead via
[`graphql_default_class` / `deprecated_class`](#new-config-options).

`GraphQLDefault` always holds a **string** (`str(default_value)`), and no marker
is emitted for a `null`/absent default.

### 3. The `UNSET` sentinel

The [`funcs`](plugins/funcs) convenience functions and the new
[`input_funcs`](plugins/inputfuncs) factories now default every optional
parameter to a generated `UNSET` sentinel, and assemble the payload
conditionally:

```python
def get_countries(
    filter: Union[Optional[Filter], UnsetType] = UNSET,
    limit: Union[Optional[int], UnsetType] = UNSET,
    rath: Rath = None,
) -> List[GetCountriesCountries]:
    variables: Dict[str, Any] = {}
    if filter is not UNSET:
        variables['filter'] = filter
    if limit is not UNSET:
        variables['limit'] = limit
    return execute(GetCountries, variables, rath).countries
```

This is what lets the client distinguish the three cases:

| Call | On the wire |
| --- | --- |
| `get_countries()` | `{}` — server applies its defaults |
| `get_countries(limit=None)` | `{"limit": null}` — explicit null sent |
| `get_countries(limit=5)` | `{"limit": 5}` |

Like the markers, `UNSET` / `UnsetType` are generated into the module by default
but can be [overridden](#new-config-options) with your own
(`unset_type_class` + `unset_instance`, which must be set together).

## What you must change

### ✅ Update your executor proxy to use `exclude_unset=True`

This is the **one mandatory change** and turms cannot make it for you — the
serialization lives in your own proxy functions, not in generated code. Find
where your proxy dumps the arguments and add `exclude_unset=True`:

```python
# BEFORE
operation.Arguments(**variables).dict(by_alias=True)

# AFTER
operation.Arguments(**variables).dict(by_alias=True, exclude_unset=True)
```

If you skip this step, the `= None` defaults will be sent as explicit `null`s and
**override your server defaults** — the exact bug this change exists to prevent.

See the updated `examples/rath-usage/your_library/proxies.py` and
`examples/gql-usage/your_library/proxies.py` for the full pattern (sync, async,
subscribe, asubscribe).

### ⚠️ Stop relying on client-side default values

If any of your code read a defaulted field expecting the baked value, it now
reads `None`:

```python
# This used to be 10; it is now None until the server resolves it.
DefaultInput(plain_required="x").optional_with_default  # -> None
```

Move that logic to the server, or pass the value explicitly.

### ⚠️ Account for the `Annotated` / `UNSET` symbols

The generated module now contains `GraphQLDefault`, `Deprecated`, `UnsetType`,
and `UNSET`. If you re-export or introspect the generated module, expect these
new names (or override them — see below).

## New config options

These are all set under `extensions.turms` and apply globally:

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `coercible_scalars` | `Dict[str, str]` | `{}` | Global map of scalar → coercible python type for generated function/factory params. Plugins (`funcs`, `input_funcs`) merge their own on top. |
| `graphql_default_class` | dotted path | – | Use your own class as the `GraphQLDefault` marker instead of generating one. |
| `deprecated_class` | dotted path | – | Use your own class as the `Deprecated` marker instead of generating one. |
| `document_field_metadata` | `bool` | `true` | Fold the deprecation reason and default value into the field documentation (in addition to the markers). Set `false` to keep only the plain description. |
| `unset_type_class` | dotted path | – | Import your own UNSET sentinel **type** instead of generating one. Must be set with `unset_instance`. |
| `unset_instance` | dotted path | – | Import your own UNSET sentinel **instance**. Must be set with `unset_type_class`. |

`unset_type_class` and `unset_instance` must be supplied **together** — setting
only one is a config error.

```yaml
extensions:
  turms:
    document_field_metadata: true
    unset_type_class: my_library.sentinels.UnsetType
    unset_instance: my_library.sentinels.UNSET
```

## The new `input_funcs` plugin

This release also ships a new plugin that generates a **factory function per
input type** following the same UNSET model. See its
[reference page](plugins/inputfuncs) for details. In short:

```python
user = user_input(name="alice")          # optionals omitted (unset)
user.dict(by_alias=True, exclude_unset=True)  # -> {"name": "alice"}
```

Add it after the `inputs` plugin:

```yaml
plugins:
  - type: turms.plugins.inputs.InputsPlugin
  - type: turms.plugins.input_funcs.InputFuncsPlugin
```
