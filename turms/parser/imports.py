from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
import ast


def generate_imports(schema: GraphQLSchema, config: GeneratorConfig):

    imports = []

    additional_bases_imports = {
        item for key, lis in config.additional_bases.items() for item in lis
    }

    for item in additional_bases_imports:
        imports.append(
            ast.ImportFrom(
                module=".".join(item.split(".")[:-1]),
                names=[ast.alias(name=item.split(".")[-1])],
                level=0,
            )
        )

    for key, definition in config.scalar_definitions.items():
        if definition in ["str", "int", "float", "bool", "complex"]:
            continue

        imports.append(
            ast.ImportFrom(
                module=".".join(definition.split(".")[:-1]),
                names=[ast.alias(name=definition.split(".")[-1])],
                level=0,
            )
        )

    for item in config.object_bases:
        imports.append(
            ast.ImportFrom(
                module=".".join(item.split(".")[:-1]),
                names=[ast.alias(name=item.split(".")[-1])],
                level=0,
            )
        )

    for item in config.interface_bases:
        imports.append(
            ast.ImportFrom(
                module=".".join(item.split(".")[:-1]),
                names=[ast.alias(name=item.split(".")[-1])],
                level=0,
            )
        )

    imports += [
        ast.ImportFrom(
            module="pydantic.fields",
            names=[ast.alias(name="Field")],
            level=0,
        ),
        ast.ImportFrom(
            module="typing",
            names=[
                ast.alias(name="Optional"),
                ast.alias(name="List"),
                ast.alias(name="Dict"),
                ast.alias(name="Union"),
                ast.alias(name="Literal"),
            ],
            level=0,
        ),
    ]

    return imports
