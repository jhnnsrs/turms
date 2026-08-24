---
sidebar_position: 2
sidebar_label: "InputType"
---

# InputType

InputType generates python objects from Graphql InputTypes

### Default Configuration

```yaml
project:
  default:
    schema: ...
    extensions:
      turms:
        plugins:
          - type: turms.plugins.inputs.InputsPlugin
            input_bases: #List[str] = ["pydantic.BaseModel"]
            skip_underscore: #bool = True
```

## `@oneOf` input unions

Input types annotated with the spec [`@oneOf` directive](https://github.com/graphql/graphql-spec/pull/825)
(exactly one field must be provided, and it must be non-null) are generated as
pydantic unions. `@oneOf` is the spec-blessed outcome of the GraphQL input-union
RFC and is the recommended way to model polymorphic inputs (it supersedes the
turms-specific `unionElementOf` directive for new schemas).

When every field of the `@oneOf` input is a distinct input object type — the
*tagged input-union* pattern, where the field name acts as the tag —

```graphql
input CatInput { name: String!, meow: Boolean }
input DogInput { name: String!, bark: Boolean }

input PetInput @oneOf {
  cat: CatInput
  dog: DogInput
}
```

turms generates a direct union of the member models, so you pass a member
instance where the union is expected:

```python
PetInput = Annotated[Union[CatInput, DogInput], WrapSerializer(_serialize_pet_input)]

find_pet(pet=CatInput(name="whiskers"))
# serialized variables: {"pet": {"cat": {"name": "whiskers"}}}
```

The attached serializer restores the tagged wire form `{fieldName: value}` that
`@oneOf` servers expect, preserving the client's usual
`dict(by_alias=True, exclude_unset=True)` serialization.

In every other case — scalar or enum fields, or the same member type
appearing under two fields — turms falls back to one wrapper class per field,
unioned under
the input type's name. Each wrapper carries its single field as required, so it
serializes to the tagged wire form without any custom serializer:

```python
class FindUserInputEmail(BaseModel):
    """'email' variant of the @oneOf input 'FindUserInput'"""
    email: str

FindUserInput = Union[FindUserInputId, FindUserInputEmail, FindUserInputUsername]

find_user(input=FindUserInputEmail(email="x@y.z"))
# serialized variables: {"input": {"email": "x@y.z"}}
```

Caveats:

- graphql-core 3.2 (the currently pinned range) does not know the directive, so
  SDL schemas must declare it: `directive @oneOf on INPUT_OBJECT`. graphql-core
  3.3+ exposes it natively.
- Introspected schemas carry no `@oneOf` information on graphql-core 3.2, so
  detection silently no-ops there — the input is generated as a plain optional-
  fields model.
- Fields of a `@oneOf` input must be nullable and must not declare defaults
  (per spec); turms raises a `GenerationError` otherwise.
- Listing a `@oneOf` input in the funcs plugin's `expand_input_types` cannot
  enforce that exactly one parameter is provided and logs a warning.
