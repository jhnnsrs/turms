from typing import Dict, Tuple, Type

from graphql.validation.rules import ASTValidationRule

# Spec Section: "Executable Definitions"
from graphql.validation.rules.executable_definitions import ExecutableDefinitionsRule

# Spec Section: "Operation Name Uniqueness"
from graphql.validation.rules.unique_operation_names import UniqueOperationNamesRule

# Spec Section: "Lone Anonymous Operation"
from graphql.validation.rules.lone_anonymous_operation import LoneAnonymousOperationRule

# Spec Section: "Subscriptions with Single Root Field"
from graphql.validation.rules.single_field_subscriptions import (
    SingleFieldSubscriptionsRule,
)

# Spec Section: "Fragment Spread Type Existence"
from graphql.validation.rules.known_type_names import KnownTypeNamesRule

# Spec Section: "Fragments on Composite Types"
from graphql.validation.rules.fragments_on_composite_types import (
    FragmentsOnCompositeTypesRule,
)

# Spec Section: "Variables are Input Types"
from graphql.validation.rules.variables_are_input_types import (
    VariablesAreInputTypesRule,
)

# Spec Section: "Leaf Field Selections"
from graphql.validation.rules.scalar_leafs import ScalarLeafsRule

# Spec Section: "Field Selections on Objects, Interfaces, and Unions Types"
from graphql.validation.rules.fields_on_correct_type import FieldsOnCorrectTypeRule

# Spec Section: "Fragment Name Uniqueness"
from graphql.validation.rules.unique_fragment_names import UniqueFragmentNamesRule

# Spec Section: "Fragment spread target defined"
from graphql.validation.rules.known_fragment_names import KnownFragmentNamesRule

# Spec Section: "Fragments must be used"
from graphql.validation.rules.no_unused_fragments import NoUnusedFragmentsRule

# Spec Section: "Fragment spread is possible"
from graphql.validation.rules.possible_fragment_spreads import (
    PossibleFragmentSpreadsRule,
)

# Spec Section: "Fragments must not form cycles"
from graphql.validation.rules.no_fragment_cycles import NoFragmentCyclesRule

# Spec Section: "Variable Uniqueness"
from graphql.validation.rules.unique_variable_names import UniqueVariableNamesRule

# Spec Section: "All Variable Used Defined"
from graphql.validation.rules.no_undefined_variables import NoUndefinedVariablesRule

# Spec Section: "All Variables Used"
from graphql.validation.rules.no_unused_variables import NoUnusedVariablesRule

# Spec Section: "Directives Are Defined"
from graphql.validation.rules.known_directives import KnownDirectivesRule

# Spec Section: "Directives Are Unique Per Location"
from graphql.validation.rules.unique_directives_per_location import (
    UniqueDirectivesPerLocationRule,
)

# Spec Section: "Argument Names"
from graphql.validation.rules.known_argument_names import KnownArgumentNamesRule
from graphql.validation.rules.known_argument_names import (
    KnownArgumentNamesOnDirectivesRule,
)

# Spec Section: "Argument Uniqueness"
from graphql.validation.rules.unique_argument_names import UniqueArgumentNamesRule

# Spec Section: "Value Type Correctness"
from graphql.validation.rules.values_of_correct_type import ValuesOfCorrectTypeRule

# Spec Section: "Argument Optionality"
from graphql.validation.rules.provided_required_arguments import (
    ProvidedRequiredArgumentsRule,
)
from graphql.validation.rules.provided_required_arguments import (
    ProvidedRequiredArgumentsOnDirectivesRule,
)

# Spec Section: "All Variable Usages Are Allowed"
from graphql.validation.rules.variables_in_allowed_position import (
    VariablesInAllowedPositionRule,
)

# Spec Section: "Field Selection Merging"
from graphql.validation.rules.overlapping_fields_can_be_merged import (
    OverlappingFieldsCanBeMergedRule,
)

# Spec Section: "Input Object Field Uniqueness"
from graphql.validation.rules.unique_input_field_names import UniqueInputFieldNamesRule


# This dictionary includes all validation rules defined by the GraphQL spec.
#
# The order of the rules in this dictionary has been adjusted to lead to the
# most clear output when encountering multiple validation errors.

specified_rules_map: Dict[str, Type[ASTValidationRule]] = {
    "executable_definitions": ExecutableDefinitionsRule,
    "unique_operation_names": UniqueOperationNamesRule,
    "lone_anonymous_operation": LoneAnonymousOperationRule,
    "single_field_subscriptions": SingleFieldSubscriptionsRule,
    "known_type_names": KnownTypeNamesRule,
    "fragments_on_composite_types": FragmentsOnCompositeTypesRule,
    "variables_are_input_types": VariablesAreInputTypesRule,
    "scalar_leafs": ScalarLeafsRule,
    "fields_on_correct_type": FieldsOnCorrectTypeRule,
    "unique_fragment_names": UniqueFragmentNamesRule,
    "known_fragment_names": KnownFragmentNamesRule,
    "possible_fragment_spreads": PossibleFragmentSpreadsRule,
    "no_fragment_cycles": NoFragmentCyclesRule,
    "no_unused_fragments": NoUnusedFragmentsRule,
    "unique_variable_names": UniqueVariableNamesRule,
    "no_undefined_variables": NoUndefinedVariablesRule,
    "no_unused_variables": NoUnusedVariablesRule,
    "known_directives": KnownDirectivesRule,
    "unique_directives_per_location": UniqueDirectivesPerLocationRule,
    "known_argument_names": KnownArgumentNamesRule,
    "unique_argument_names": UniqueArgumentNamesRule,
    "values_of_correct_type": ValuesOfCorrectTypeRule,
    "provided_required_arguments": ProvidedRequiredArgumentsRule,
    "variables_in_allowed_position": VariablesInAllowedPositionRule,
    "overlapping_fields_can_be_merged": OverlappingFieldsCanBeMergedRule,
    "unique_input_field_names": UniqueInputFieldNamesRule,
}
"""A dictionary with all validation rules defined by the GraphQL specification.

The keys are readable names for the rules, and the values are the rule classes.
The order of the rules in this dictionary has been adjusted to lead to the
most clear output when encountering multiple validation errors.
"""

__all__ = ["specified_rules_map", "ASTValidationRule"]
