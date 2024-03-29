---
sidebar_position: 5
sidebar_label: "Turms ❤️ Rath"
---

# Turms ❤️ Rath

### What is raths?

Rath is an apollo like graphql client library for async and sync queries focussing
on linking client side logic in a composable way.

### Design

Rath and Turms are developed independently, but are completely interoperable.

Consider this query

```graphql title="/graphql/get_capsules.graphql"
query get_capsules {
  capsules {
    id
    missions {
      flight
      name
    }
  }
}
```

On running (in your terminal)

```bash
turms gen
```

Turms generates automatically this pydantic schema for you

```python title="/schema/api.py"

class Get_capsulesQueryCapsulesMissions(GraphQLObject):
    typename: Optional[Literal["CapsuleMission"]] = Field(alias="__typename")
    flight: Optional[int]
    name: Optional[str]


class Get_capsulesQueryCapsules(GraphQLObject):
    typename: Optional[Literal["Capsule"]] = Field(alias="__typename")
    id: Optional[str]
    missions: Optional[List[Optional[Get_capsulesQueryCapsulesMissions]]]


class Get_capsulesQuery(GraphQLQuery):
    capsules: Optional[List[Optional[Get_capsulesQueryCapsules]]]

    class Meta:
        domain = "default"
        document = "query get_capsules {\n  capsules {\n    id\n    missions {\n      flight\n      name\n    }\n  }\n}"

```

Which you can than use easily in your rath code

```python
from rath import Rath
from schema.api import Get_capsulesQuery

rath = Rath(...)

with rath:
  typed_answer = GetcapuslesQuery(**rath.execute(GetcapuslesQuery.Meta.document).data) # fully tpyed

```

You can also use the funcs plugin in conjuction with a rath proxy function to
allow fully typed calls to your api like this:

```python
from rath import Rath
from schema.api import get_capsules

rath = Rath(...)

with rath:
 typed_answer = get_capsules()

```
