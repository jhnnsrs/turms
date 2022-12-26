---
sidebar_position: 1
sidebar_label: "Document Code Generation"
title: "Generating Code from Documents"
---

Clients using a GraphQL API, generally can do so by calling specific operations on
the graphQL schema (like a mutation, query, subscription). These operations are defined
in the standard graphql SDL, and then together with the variables are send to the graphql
api.

```gql

fragment Continent on Continent {
  code
  name
}

query get_countries($filter: CountryFilterInput) {
  countries(filter: $filter) {
    code
    name
    continent {
      ...Continent
    }
  }
}

```

You can do this in `vanilla` python by just sending the query as a string, and the
variables as json to the graphql api and deseralizing the JSON-response to a python 
dictionary. However this approach can be very error prone and can lead to run-time
errors especially in larger projects.

```python

t = """
fragment Continent on Continent {
  code
  name
}

query get_countries($filter: CountryFilterInput) {
  countries(filter: $filter) {
    code
    name
    continent {
      ...Continent
    }
  }
}
"""

server_reponse = client.post(t, variables={"filter": {"code": "eq": "22"}})
continent_name = server_response["data"]["countries"][0]["continent"]["name"] # nested dictionaries

```

Additionally you will not get any help from your IDE about the types and their nullability.
With turms you can easily generate typed operations from you SDL query, that will give you
both runtime checks and IDE type support.

## How to use turms for client-side document generation

Client side code is often structured around the graphql documents (not the schema), as the documents
describe which data you want to retrieve from the API. Your documents are nothing more than
SDL code describing your operations and (resuable) fragments, and are stored in your development
enviroment (most often in a seperate folder).

With turms installed we can now specify in the config where these documents are stored, and the
schema it should use to infer the types from and use a modfieid battery of plugins to generate our python code from it:

```yaml
projects:
  default:
    schema: https://countries.trevorblades.com/
    documents: "your_documents/*.graphql" #a glob pattern where your documents are stored
    extensions:
      turms:
        out_dir: "your_library" # the folder where we will generate schema.py with all the generated code
        stylers: # stylers to convert graphQL naming style to python
          - type: turms.stylers.capitalize.CapitalizeStyler
          - type: turms.stylers.snake_case.SnakeCaseStyler
        plugins: # the plugins to use
          - type: "turms.plugins.enums.EnumsPlugin" #creates python enums from graphql enums
          - type: "turms.plugins.inputs.InputsPlugin" # creates input types from grahqlinputtypes
          - type: turms.plugins.fragments.FragmentsPlugin # scans your documents for fragments and generates them
          - type: turms.plugins.operations.OperationsPlugin # scans your documents for queries, mutation, subscription
        processors:
          - type: turms.processors.black.BlackProcessor # enfores black styling
          - type: turms.processors.isort.IsortProcessor # sorts the imports
        scalar_definitions:
          uuid: str
          UUID: str # mapping UUID scalar to st
          Callback: str
          Any: typing.Any
          QString: str
          ID: str
```

In this configuration turms will generated pydantic classes, from your documents, mapping to the defined GraphQL scalar types to their respective python types.

:::note

You might wonder, why we are not using pure dataclasses. This is mainly due turms support for graphql interfaces and unions, where we need to cast a returned type to the right datatype, somethign that is not possible with dataclasses by default, but easily done with pydantic and it deserialization.
:::

From the document in one turms will now generate the following generated code:

```python
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class StringQueryOperatorInput(BaseModel):
    eq: Optional[str]
    ne: Optional[str]
    in_: Optional[List[Optional[str]]] = Field(alias="in")
    nin: Optional[List[Optional[str]]]
    regex: Optional[str]
    glob: Optional[str]


class CountryFilterInput(BaseModel):
    code: Optional[StringQueryOperatorInput]
    currency: Optional[StringQueryOperatorInput]
    continent: Optional[StringQueryOperatorInput]


class ContinentFilterInput(BaseModel):
    code: Optional[StringQueryOperatorInput]


class LanguageFilterInput(BaseModel):
    code: Optional[StringQueryOperatorInput]


class Continent(BaseModel):
    typename: Optional[Literal["Continent"]] = Field(alias="__typename")
    code: str
    name: str


class Get_countriesCountries(BaseModel):
    typename: Optional[Literal["Country"]] = Field(alias="__typename")
    code: str
    name: str
    continent: Continent


class Get_countries(BaseModel):
    countries: List[Get_countriesCountries]

    class Arguments(BaseModel):
        filter: Optional[CountryFilterInput] = None

    class Meta:
        document = "fragment Continent on Continent {\n  code\n  name\n}\n\nquery get_countries($filter: CountryFilterInput) {\n  countries(filter: $filter) {\n    code\n    name\n    continent {\n      ...Continent\n    }\n  }\n}"

```

In this example we can see that turms not only generated typed models for the query but also for the
arguments and the input types (if there were enums also all enums would have been generated).

Now you can simple import these dataclasses and use them for (de-)serialization:

```python

from your_library.schema import Get_countries, CountryFilterInput, StringQueryOperatorInput


variables = Get_countries.Arguments(filter=CountryFilterInput(code=StringQueryOperatorInput(eq="DE"))))

t = client.post(Get_countries.Meta.document, variables.json())
countries = Get_countries(**t)

for i in countries.countries:
    print(i.name)
```

Additionally when using the "Funcs Plugin", we can even reduce this boilerplate code, down to function
calls like this:

```
from your_library.schema import get_countries, CountryFilterInput, StringQueryOperatorInput

countries = get_countries(filter=CountryFilterInput(code=StringQueryOperatorInput(eq="DE")))

for i in countries.countries:
    print(i.name)

```

:::note

If you don't like the verbosity of the nested, input types, you can also use pydantics validation
capabilite and pass the nested dictionary directly, pydantic will still do its runtime checking magic
and give you serialization error.

:::


## Example project

In the example project (here)[https://github.com/jhnnsrs/turms/tree/master/examples/pydantic-basic]. We illustrate the necessary configuration to use code generation in a schema first approach.



