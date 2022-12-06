# Turms and GQL Usage

This example illustrates how you can use the python library `gql`
with turms and its funcs plugin.

## Install

This example uses poetry to manage dependencies. You can install it
by running the following command:

```bash
poetry install
```

otherwise you can install gql and pydantic by running:

```bash
pip install gql pydantic
```

:::note

Please note that turms is only a development dependency, the required code only
requires pydantic to work

:::

## Test generation

This examples includes a graphql config file that utilized the inputs, enums,
fragments and operations plugin to generate the necessary code for serialization
to and from pydantic types.

Importantly this example also include the `FuncsPlugin` which allows you to
generate functions that can be used to call the graphql operations. These functions
will be importable alongside the generated types, and when will in turn call the
proxy functions defined in the graphql config file.

```yaml
projects:
  default:
    schema: https://countries.trevorblades.com/
    documents: your_documents/*.graphql
    extensions:
      turms:
        out_dir: your_library

        stylers:
          - type: turms.stylers.capitalize.CapitalizeStyler
          - type: turms.stylers.snake_case.SnakeCaseStyler
        plugins:
          - type: turms.plugins.enums.EnumsPlugin
          - type: turms.plugins.inputs.InputsPlugin
          - type: turms.plugins.fragments.FragmentsPlugin
          - type: turms.plugins.operations.OperationsPlugin
          - type: turms.plugins.funcs.FuncsPlugin
            global_args: # global arguments that we want to pass to all functions (here a reference to the gql client)
              - type: gql.Client
                key: client
                description: "The client we want to use to execute the operation"
            definitions:
              - type: subscription # The type of operation we want to generate a function for
                use: your_library.proxies.subscribe # The proxy function we want to use to execute the operation
              - type: query
                use: your_library.proxies.execute
              - type: mutation
                use: your_library.proxies.execute

        processors:
          - type: turms.processors.black.BlackProcessor
          - type: turms.processors.isort.IsortProcessor
        scalar_definitions:
          uuid: str
          UUID: str
          Callback: str
          Any: typing.Any
          QString: str
          ID: str
```

### How to add documents

The documents are the graphql operations that you want to use. You can add them
to the `your_documents` folder and they will be picked up when running
`turms gen`.
