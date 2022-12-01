---
sidebar_label: run
title: run
---

#### load\_projects\_from\_configpath

```python
def load_projects_from_configpath(config_path: str,
                                  select: str = None
                                  ) -> Dict[str, GraphQLProject]
```

Loads the configuration from a configuration file

**Arguments**:

- `config_path` _str_ - The path to the config file
  

**Returns**:

- `GraphQLConfig` - The configuration

#### scan\_folder\_for\_configs

```python
def scan_folder_for_configs(folder_path: str = None) -> List[str]
```

Scans a folder for config files

**Arguments**:

- `folder_path` _str_ - The path to the folder
  

**Returns**:

- `List[str]` - The list of config files

#### scan\_folder\_for\_single\_config

```python
def scan_folder_for_single_config(folder_path: str = None) -> List[str]
```

Scans a folder for one single config file

**Arguments**:

- `folder_path` _str_ - The path to the folder
  

**Returns**:

- `str` - The config file

#### gen

```python
def gen(filepath: Optional[str] = None,
        project_name: Optional[str] = None,
        strict: bool = False,
        overwrite_path: Optional[str] = None)
```

Generates  Code according to the config file

**Arguments**:

- `filepath` _str, optional_ - The filepath of  graphqlconfig. Defaults to &quot;graphql.config.yaml&quot;.
- `project` _str, optional_ - The project within that should be generated. Defaults to None.

#### instantiate

```python
def instantiate(module_path: str, **kwargs)
```

Instantiate A class from a file.

Needs to conform to `path.to.module.ClassName`

**Arguments**:

- `module_path` _str_ - The class path you would like to instatiate
  

**Returns**:

- `object` - The instatiated class.

#### generate

```python
def generate(project: GraphQLProject) -> str
```

Genrates the code according to the configugration

The code is generated in the following order:
1. Introspect the schema (either url or locally)
2. Generate the of grapqhl.ast from this schema
3. Instantiate all plugins/parsers/stylers
4. Generate the ast from the ast through the plugins and stylers
5. Parse the Ast with the parsers
6. Generate the code from the ast through ast.unparse
7. Process the code string through the processors

**Arguments**:

- `project` _GraphQLConfig_ - The configuraion for the generation
  

**Returns**:

- `str` - The generated code

#### generate\_ast

```python
def generate_ast(config: GeneratorConfig,
                 schema: GraphQLSchema,
                 plugins: Optional[List[Plugin]] = None,
                 stylers: Optional[List[Styler]] = None) -> List[ast.AST]
```

Generates the ast from the schema

**Arguments**:

- `config` _GeneratorConfig_ - The generaion Config (turms section)
- `schema` _GraphQLSchema_ - The schema to generate the ast from
- `plugins` _List[Plugins], optional_ - The plugins to use. Defaults to [].
- `stylers` _List[Styler], optional_ - The plugins to use. Defaults to [].
  

**Raises**:

- `GenerationError` - Errors involving the generation of the ast
  

**Returns**:

- `List[ast.AST]` - The generated ast (as list, not as module)

