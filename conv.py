from typing import Any, Dict
import yaml
import json
import toml
import os

with open("graphql.config.yaml", "r", encoding="utf-8") as file:
    x_dict = yaml.safe_load(file)


PARSABLE_DIR = "tests/configs/parsable"
PARSABLE_SINGLE_DIR = "tests/configs/parsable_single"


def dump_dict_in_files(the_dict: Dict[str, Any], the_dir: str):
    with open(
        os.path.join(the_dir, "graphql.config.yaml"), "w", encoding="utf-8"
    ) as file:
        yaml.safe_dump(the_dict, file)

    with open(os.path.join(the_dir, ".graphqlrc.yaml"), "w", encoding="utf-8") as file:
        yaml.safe_dump(the_dict, file)

    with open(
        os.path.join(the_dir, "graphql.config.yml"), "w", encoding="utf-8"
    ) as file:
        yaml.safe_dump(the_dict, file)

    with open(os.path.join(the_dir, ".graphqlrc.yml"), "w", encoding="utf-8") as file:
        yaml.safe_dump(the_dict, file)

    with open(
        os.path.join(the_dir, "graphql.config.json"), "w", encoding="utf-8"
    ) as file:
        file.write(json.dumps(the_dict, indent=4))

    with open(os.path.join(the_dir, ".graphqlrc.json"), "w", encoding="utf-8") as file:
        file.write(json.dumps(the_dict, indent=4))

    with open(
        os.path.join(the_dir, "graphql.config.toml"), "w", encoding="utf-8"
    ) as toml_file:
        toml_file.write(toml.dumps(the_dict))

    with open(
        os.path.join(PARSABLE_DIR, ".graphqlrc.toml"), "w", encoding="utf-8"
    ) as toml_file:
        toml_file.write(toml.dumps(the_dict))


with open("graphql.config.yaml", "r", encoding="utf-8") as file:
    x_dict = yaml.safe_load(file)

dump_dict_in_files(x_dict, PARSABLE_DIR)
dump_dict_in_files(x_dict["projects"]["default"], PARSABLE_SINGLE_DIR)
