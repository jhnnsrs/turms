---
sidebar_position: 5
sidebar_label: "Config"
---

# Config

Turms relies on and complies with [graphql-config](https://www.graphql-config.com/docs/user/user-introduction) and searches
your current working dir for the graphql-config file, it currently supports the following formats:

- [x] graphql.config.yaml
- [x] .graphqlrc.yaml
- [x] graphql.config.yml
- [x] .graphqlrc.yml
- [x] graphql.config.toml
- [x] .graphqlrc.toml
- [x] graphql.config.json
- [x] .graphqlrc.json

```yaml
projects:
  default:
    schema: http://api.spacex.land/graphql/
    documents: graphql/**.graphql
    extensions:
      turms: # path for configuration for turms
        out_dir: examples/api
        stylers:
          - type: turms.stylers.capitalize.Capitalizer
          - type: turms.stylers.snake.SnakeNodeName
        plugins:
          - type: turms.plugins.enums.EnumsPlugin
          - type: turms.plugins.inputs.InputsPlugin
          - type: turms.plugins.fragments.FragmentsPlugin
          - type: turms.plugins.operation.OperationsPlugin
          - type: turms.plugins.funcs.OperationsFuncPlugin
        processors:
          - type: turms.processor.black.BlackProcessor
          - type: turms.processor.isort.IsortProcessor
        scalar_definitions:
          uuid: str
          timestamptz: str
          Date: str
```

We recommend this layout to ensure support for multiple graphql projects, but you can also opt in
for a single project configuration.

### Turms Config

Turms config consists about basic settings like scalar_definitions, output paths but provides sections
for the configuration of plugins, processors and styles (see doc) The general structure follow this pattern:

```yaml
projects:
  default:
    schema: http://api.spacex.land/graphql/
    documents: "graphql/**.graphql"
    extensions:
      turms: # Turms section
      stylers: # styler section (every item is a styler, that applies its style in sucession)
        - type: turms.stylers.capitalize.Capitalizer # the path to the styler class (as in python modules)
      plugins: # plugin section (every item is a plugin, that generates its part of the AST tree)
        - type: "turms.plugins.enums.EnumsPlugin" # the module path
          skip_underscore: True # a configuration item of this specific plugin (enum)
        - type: "turms.plugins.fragments.FragmentPlugin" # the module path
          fragment_bases: # a configuration item of this specific plugin (fragment)
            - pydantic.BaseModel
      stylers: # styler section (every item is a styler, that applies its style in sucession)
        - type: turms.stylers.capitalize.Capitalizer # the path to the styler class (as in python modules)
```

## Central Config

As pydantic lovers, configuration is handled by pydantic models, here is an example
of the configuration

```yaml file="turms section"
projects:
  default:
    schema: # A url for intrsopection, or glob if loading locally
    documents: # A glob of documents for the generation of queries, subs, fragments
    extensions:
      turms:
        out_dir: # str = "api" the root of the generated schema
        generated_name:  #str = "schema.py"
        object_bases: #List[str] = ["pydantic.BaseModel"] The base class for objects
        interface_bases: # Optional[List[str]] = None (A different base clas for interfaces. Defaults to object_bases
        always_resolve_interfaces: # bool = True (if to false, the abstract base for interfaces is part of the union)
        scalar_definitions = #{} A map of grpahql scalars and their python equivalent
        freeze: bool = False # SHould we generate frozen (fake immutability) classes
        additional_bases = {} # A map of graphql (input)type and additional bases (see traits)

```

You can (and actually have to) define python equivalents for graphql scalars that are not
part of the standard library (str, int, bool, float). You can easily do this by providing
scalar definitions:

```yaml
scalar_definitions:
  $GRAPHQL_TYPE: path.to.your.scalar
  DateTime: datetime.datetime
```

The scalar can adhere to the pydantic Field specification to provide validators.
