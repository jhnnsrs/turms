from turms.parsers.base import Parser, ParserConfig
from typing import List
import ast
from pydantic_settings import SettingsConfigDict
from pydantic import Field, field_validator, ConfigDict


class PolyfillPluginConfig(ParserConfig):
    model_config = SettingsConfigDict(env_prefix="TURMS_PARSERS_POLYFILL_")
    type: str = "turms.parsers.polyfill.PolyfillPlugin"
    skip_underscore: bool = True
    python_version: str = "3.9"

    @field_validator("python_version", mode="before")
    def validate_python_version(cls, value):
        if isinstance(value, (int, float)):
            value = str(value)

        if value not in ["3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]:
            raise ValueError("Invalid python version")

        return value


def polyfill_python_seven(
    asts: List[ast.AST], config: PolyfillPluginConfig
) -> List[ast.AST]:

    new_nodes = []
    for node in asts:
        if isinstance(node, ast.ImportFrom):
            if node.module == "typing":
                # okay imports
                aliases = {alias.name for alias in node.names}
                need_extensions = aliases.intersection({"Literal"})
                if need_extensions:
                    new_nodes.append(
                        ast.ImportFrom(
                            module="typing_extensions",
                            names=[ast.alias(name=name) for name in need_extensions],
                            level=0,
                        )
                    )

                okay_imports = aliases - need_extensions
                new_nodes.append(
                    ast.ImportFrom(
                        names=[ast.alias(name=name) for name in okay_imports],
                        module="typing",
                        level=0,
                    )
                )
            else:
                new_nodes.append(node)

        else:
            new_nodes.append(node)

    return new_nodes


class PolyfillParser(Parser):
    """The polyfill parser is used to polyfill the generated python code with
    additional imports and code to make it compatible with older python versions.

    Right now it only supports polyfils for python 3.7 and higher"""

    config: PolyfillPluginConfig = Field(default_factory=PolyfillPluginConfig)

    def parse_ast(
        self,
        asts: List[ast.AST],
    ) -> List[ast.AST]:

        if self.config.python_version == "3.7":
            return polyfill_python_seven(asts, self.config)

        return asts  # pragma: no cover
