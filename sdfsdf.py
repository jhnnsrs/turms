<<<<<<< HEAD
from typing import Any, Union, List, Dict, Literal, Optional
from pydantic import Field, BaseModel
=======
from typing import Any, Union, Literal, List, Optional, Dict
from pydantic import BaseModel, Field
>>>>>>> e307536ce6e5f0cbb9c0c10159b6664f94e0776e
from enum import Enum

class AgentStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    DISCONNECTED = 'DISCONNECTED'
    VANILLA = 'VANILLA'

class AgentStatusInput(str, Enum):
    ACTIVE = 'ACTIVE'
    DISCONNECTED = 'DISCONNECTED'
    VANILLA = 'VANILLA'

class AssignationLogLevel(str, Enum):
    CRITICAL = 'CRITICAL'
    INFO = 'INFO'
    DEBUG = 'DEBUG'
    ERROR = 'ERROR'
    WARN = 'WARN'
    YIELD = 'YIELD'
    CANCEL = 'CANCEL'
    RETURN = 'RETURN'
    DONE = 'DONE'
    EVENT = 'EVENT'

class AssignationStatus(str, Enum):
    PENDING = 'PENDING'
    ACKNOWLEDGED = 'ACKNOWLEDGED'
    RETURNED = 'RETURNED'
    DENIED = 'DENIED'
    ASSIGNED = 'ASSIGNED'
    PROGRESS = 'PROGRESS'
    RECEIVED = 'RECEIVED'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'
    CANCEL = 'CANCEL'
    CANCELING = 'CANCELING'
    CANCELLED = 'CANCELLED'
    YIELD = 'YIELD'
    DONE = 'DONE'

class AssignationStatusInput(str, Enum):
    PENDING = 'PENDING'
    ACKNOWLEDGED = 'ACKNOWLEDGED'
    RETURNED = 'RETURNED'
    DENIED = 'DENIED'
    ASSIGNED = 'ASSIGNED'
    PROGRESS = 'PROGRESS'
    RECEIVED = 'RECEIVED'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'
    CANCEL = 'CANCEL'
    CANCELING = 'CANCELING'
    CANCELLED = 'CANCELLED'
    YIELD = 'YIELD'
    DONE = 'DONE'

class BoundTypeInput(str, Enum):
    AGENT = 'AGENT'
    REGISTRY = 'REGISTRY'
    APP = 'APP'
    GLOBAL = 'GLOBAL'

class LogLevelInput(str, Enum):
    CRITICAL = 'CRITICAL'
    INFO = 'INFO'
    DEBUG = 'DEBUG'
    ERROR = 'ERROR'
    WARN = 'WARN'
    YIELD = 'YIELD'
    CANCEL = 'CANCEL'
    RETURN = 'RETURN'
    DONE = 'DONE'
    EVENT = 'EVENT'

class LokAppGrantType(str, Enum):
    CLIENT_CREDENTIALS = 'CLIENT_CREDENTIALS'
    IMPLICIT = 'IMPLICIT'
    AUTHORIZATION_CODE = 'AUTHORIZATION_CODE'
    PASSWORD = 'PASSWORD'
    SESSION = 'SESSION'

class NodeType(str, Enum):
    GENERATOR = 'GENERATOR'
    FUNCTION = 'FUNCTION'

class NodeTypeInput(str, Enum):
    GENERATOR = 'GENERATOR'
    FUNCTION = 'FUNCTION'

class PostmanProtocol(str, Enum):
    WEBSOCKET = 'WEBSOCKET'
    KAFKA = 'KAFKA'
    RABBITMQ = 'RABBITMQ'

class ProvisionAccess(str, Enum):
    EXCLUSIVE = 'EXCLUSIVE'
    EVERYONE = 'EVERYONE'

class ProvisionLogLevel(str, Enum):
    CRITICAL = 'CRITICAL'
    INFO = 'INFO'
    DEBUG = 'DEBUG'
    ERROR = 'ERROR'
    WARN = 'WARN'
    YIELD = 'YIELD'
    CANCEL = 'CANCEL'
    RETURN = 'RETURN'
    DONE = 'DONE'
    EVENT = 'EVENT'

class ProvisionMode(str, Enum):
    DEBUG = 'DEBUG'
    PRODUCTION = 'PRODUCTION'

class ProvisionStatus(str, Enum):
    PENDING = 'PENDING'
    BOUND = 'BOUND'
    PROVIDING = 'PROVIDING'
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    CANCELING = 'CANCELING'
    LOST = 'LOST'
    RECONNECTING = 'RECONNECTING'
    DENIED = 'DENIED'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'
    ENDED = 'ENDED'
    CANCELLED = 'CANCELLED'

class ProvisionStatusInput(str, Enum):
    PENDING = 'PENDING'
    BOUND = 'BOUND'
    PROVIDING = 'PROVIDING'
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    CANCELING = 'CANCELING'
    DISCONNECTED = 'DISCONNECTED'
    RECONNECTING = 'RECONNECTING'
    DENIED = 'DENIED'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'
    ENDED = 'ENDED'
    CANCELLED = 'CANCELLED'

class RepositoryType(str, Enum):
    APP = 'APP'
    MIRROR = 'MIRROR'

class ReservationLogLevel(str, Enum):
    CRITICAL = 'CRITICAL'
    INFO = 'INFO'
    DEBUG = 'DEBUG'
    ERROR = 'ERROR'
    WARN = 'WARN'
    YIELD = 'YIELD'
    CANCEL = 'CANCEL'
    RETURN = 'RETURN'
    DONE = 'DONE'
    EVENT = 'EVENT'

class ReservationStatus(str, Enum):
    ROUTING = 'ROUTING'
    PROVIDING = 'PROVIDING'
    WAITING = 'WAITING'
    REROUTING = 'REROUTING'
    DISCONNECTED = 'DISCONNECTED'
    DISCONNECT = 'DISCONNECT'
    CANCELING = 'CANCELING'
    ACTIVE = 'ACTIVE'
    ERROR = 'ERROR'
    ENDED = 'ENDED'
    CANCELLED = 'CANCELLED'
    CRITICAL = 'CRITICAL'

class ReservationStatusInput(str, Enum):
    ROUTING = 'ROUTING'
    PROVIDING = 'PROVIDING'
    WAITING = 'WAITING'
    REROUTING = 'REROUTING'
    DISCONNECTED = 'DISCONNECTED'
    DISCONNECT = 'DISCONNECT'
    CANCELING = 'CANCELING'
    ACTIVE = 'ACTIVE'
    ERROR = 'ERROR'
    ENDED = 'ENDED'
    CANCELLED = 'CANCELLED'
    CRITICAL = 'CRITICAL'

class StructureBound(str, Enum):
    AGENT = 'AGENT'
    REGISTRY = 'REGISTRY'
    APP = 'APP'
    GLOBAL = 'GLOBAL'

class WaiterStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    DISCONNECTED = 'DISCONNECTED'
    VANILLA = 'VANILLA'

class WardTypes(str, Enum):
    GRAPHQL = 'GRAPHQL'
    REST = 'REST'

class ArgPortInput(BaseModel):
    key: Optional[str]
    type: Optional[str]
    typename: Optional[str]
    description: Optional[str]
    label: Optional[str]
    identifier: Optional[str]
    widget: Optional['WidgetInput']
    bound: Optional[BoundTypeInput]
    child: Optional['ArgPortInput']
    transpile: Optional[str]
    options: Optional[Dict]

class DefinitionInput(BaseModel):
    description: Optional[str]
    name: str
    args: Optional[List[Optional[ArgPortInput]]]
    kwargs: Optional[List[Optional['KwargPortInput']]]
    returns: Optional[List[Optional['ReturnPortInput']]]
    interfaces: Optional[List[Optional[str]]]
    type: Optional[NodeTypeInput]
    interface: str
    package: Optional[str]

class KwargPortInput(BaseModel):
    key: Optional[str]
    type: Optional[str]
    typename: Optional[str]
    description: Optional[str]
    label: Optional[str]
    default_dict: Optional[Dict] = Field(alias='defaultDict')
    default_option: Optional[Dict] = Field(alias='defaultOption')
    default_int: Optional[int] = Field(alias='defaultInt')
    default_bool: Optional[bool] = Field(alias='defaultBool')
    default_float: Optional[float] = Field(alias='defaultFloat')
    default_id: Optional[str] = Field(alias='defaultID')
    default_string: Optional[str] = Field(alias='defaultString')
    default_list: Optional[List[Optional[Dict]]] = Field(alias='defaultList')
    identifier: Optional[str]
    widget: Optional['WidgetInput']
    bound: Optional[BoundTypeInput]
    child: Optional['KwargPortInput']
    transpile: Optional[str]
    options: Optional[Dict]

class ReserveParamsInput(BaseModel):
    auto_provide: Optional[bool] = Field(alias='autoProvide')
    auto_unprovide: Optional[bool] = Field(alias='autoUnprovide')
    registries: Optional[List[Optional[str]]]
    agents: Optional[List[Optional[str]]]
    templates: Optional[List[Optional[str]]]
    desired_instances: Optional[int] = Field(alias='desiredInstances')
    minimal_instances: Optional[int] = Field(alias='minimalInstances')

class ReturnPortInput(BaseModel):
    key: Optional[str]
    type: Optional[str]
    typename: Optional[str]
    description: Optional[str]
    bound: Optional[BoundTypeInput]
    label: Optional[str]
    identifier: Optional[str]
    child: Optional['ReturnPortInput']
    transpile: Optional[str]

class WidgetInput(BaseModel):
    typename: str
    query: Optional[str]
    dependencies: Optional[List[Optional[str]]]
    max: Optional[int]
    min: Optional[int]
    placeholder: Optional[str]

class AssignationParent(BaseModel):
    typename: Optional[Literal['Assignation']] = Field(alias='__typename')
    id: str

class Assignation(BaseModel):
    typename: Optional[Literal['Assignation']] = Field(alias='__typename')
    args: Optional[List[Optional[Any]]]
    kwargs: Optional[Dict]
    id: str
    parent: Optional[AssignationParent]
    id: str
    status: AssignationStatus
    statusmessage: str

class TranscriptPostman(BaseModel):
    typename: Optional[Literal['PostmanSettings']] = Field(alias='__typename')
    type: Optional[PostmanProtocol]
    kwargs: Optional[Dict]

class Transcript(BaseModel):
    typename: Optional[Literal['Transcript']] = Field(alias='__typename')
    postman: Optional[TranscriptPostman]

class Node(BaseModel):
    typename: Optional[Literal['Node']] = Field(alias='__typename')
    name: str
    interface: str
    package: str
    description: str
    type: NodeType
    id: str
    args: Optional[List[Optional['ArgPort']]]
    kwargs: Optional[List[Optional['KwargPort']]]
    returns: Optional[List[Optional['ReturnPort']]]

class StringArgPort(BaseModel):
    typename: Optional[Literal['StringArgPort']] = Field(alias='__typename')
    key: Optional[str]

class IntArgPort(BaseModel):
    typename: Optional[Literal['IntArgPort']] = Field(alias='__typename')
    key: Optional[str]

class StructureArgPort(BaseModel):
    typename: Optional[Literal['StructureArgPort']] = Field(alias='__typename')
    key: Optional[str]
    identifier: Optional[str]

class ListArgPortChildBase(BaseModel):
    pass

class ListArgPortChildStructureArgPortInlineFragment(ListArgPortChildBase):
    typename: Optional[Literal['StructureArgPort']] = Field(alias='__typename')
    identifier: Optional[str]

class ListArgPortChildIntArgPortInlineFragment(ListArgPortChildBase):
    typename: Optional[Literal['IntArgPort']] = Field(alias='__typename')

class ListArgPortChildBoolArgPortInlineFragment(ListArgPortChildBase):
    typename: Optional[Literal['BoolArgPort']] = Field(alias='__typename')

class ListArgPortChildStringArgPortInlineFragment(ListArgPortChildBase):
    typename: Optional[Literal['StringArgPort']] = Field(alias='__typename')

class ListArgPort(BaseModel):
    typename: Optional[Literal['ListArgPort']] = Field(alias='__typename')
    key: Optional[str]
    child: Optional[Union[ListArgPortChildStructureArgPortInlineFragment, ListArgPortChildIntArgPortInlineFragment, ListArgPortChildBoolArgPortInlineFragment, ListArgPortChildStringArgPortInlineFragment]]

class DictArgPortChildBase(BaseModel):
    pass

class DictArgPortChildStructureArgPortInlineFragment(DictArgPortChildBase):
    typename: Optional[Literal['StructureArgPort']] = Field(alias='__typename')
    identifier: Optional[str]

class DictArgPortChildIntArgPortInlineFragment(DictArgPortChildBase):
    typename: Optional[Literal['IntArgPort']] = Field(alias='__typename')

class DictArgPortChildBoolArgPortInlineFragment(DictArgPortChildBase):
    typename: Optional[Literal['BoolArgPort']] = Field(alias='__typename')

class DictArgPortChildStringArgPortInlineFragment(DictArgPortChildBase):
    typename: Optional[Literal['StringArgPort']] = Field(alias='__typename')

class DictArgPort(BaseModel):
    typename: Optional[Literal['DictArgPort']] = Field(alias='__typename')
    key: Optional[str]
    child: Optional[Union[DictArgPortChildStructureArgPortInlineFragment, DictArgPortChildIntArgPortInlineFragment, DictArgPortChildBoolArgPortInlineFragment, DictArgPortChildStringArgPortInlineFragment]]

class DictKwargPortChildBase(BaseModel):
    pass

class DictKwargPortChildStructureKwargPortInlineFragment(DictKwargPortChildBase):
    typename: Optional[Literal['StructureKwargPort']] = Field(alias='__typename')
    identifier: Optional[str]

class DictKwargPortChildIntKwargPortInlineFragment(DictKwargPortChildBase):
    typename: Optional[Literal['IntKwargPort']] = Field(alias='__typename')

class DictKwargPortChildBoolKwargPortInlineFragment(DictKwargPortChildBase):
    typename: Optional[Literal['BoolKwargPort']] = Field(alias='__typename')

class DictKwargPortChildStringKwargPortInlineFragment(DictKwargPortChildBase):
    typename: Optional[Literal['StringKwargPort']] = Field(alias='__typename')

class DictKwargPort(BaseModel):
    typename: Optional[Literal['DictKwargPort']] = Field(alias='__typename')
    key: Optional[str]
    default_dict: Optional[Dict] = Field(alias='defaultDict')
    child: Optional[Union[DictKwargPortChildStructureKwargPortInlineFragment, DictKwargPortChildIntKwargPortInlineFragment, DictKwargPortChildBoolKwargPortInlineFragment, DictKwargPortChildStringKwargPortInlineFragment]]

class BoolKwargPort(BaseModel):
    typename: Optional[Literal['BoolKwargPort']] = Field(alias='__typename')
    key: Optional[str]
    default_bool: Optional[bool] = Field(alias='defaultBool')

class IntKwargPort(BaseModel):
    typename: Optional[Literal['IntKwargPort']] = Field(alias='__typename')
    key: Optional[str]
    default_int: Optional[int] = Field(alias='defaultInt')

class StringKwargPort(BaseModel):
    typename: Optional[Literal['StringKwargPort']] = Field(alias='__typename')
    key: Optional[str]
    default_string: Optional[str] = Field(alias='defaultString')

class ListKwargPortChildBase(BaseModel):
    pass

class ListKwargPortChildStructureKwargPortInlineFragment(ListKwargPortChildBase):
    typename: Optional[Literal['StructureKwargPort']] = Field(alias='__typename')
    identifier: Optional[str]

class ListKwargPortChildIntKwargPortInlineFragment(ListKwargPortChildBase):
    typename: Optional[Literal['IntKwargPort']] = Field(alias='__typename')

class ListKwargPortChildBoolKwargPortInlineFragment(ListKwargPortChildBase):
    typename: Optional[Literal['BoolKwargPort']] = Field(alias='__typename')

class ListKwargPortChildStringKwargPortInlineFragment(ListKwargPortChildBase):
    typename: Optional[Literal['StringKwargPort']] = Field(alias='__typename')

class ListKwargPort(BaseModel):
    typename: Optional[Literal['ListKwargPort']] = Field(alias='__typename')
    key: Optional[str]
    child: Optional[Union[ListKwargPortChildStructureKwargPortInlineFragment, ListKwargPortChildIntKwargPortInlineFragment, ListKwargPortChildBoolKwargPortInlineFragment, ListKwargPortChildStringKwargPortInlineFragment]]
    default_list: Optional[List[Optional[Dict]]] = Field(alias='defaultList')

class ListReturnPortChildBase(BaseModel):
    pass

class ListReturnPortChildStructureReturnPortInlineFragment(ListReturnPortChildBase):
    typename: Optional[Literal['StructureReturnPort']] = Field(alias='__typename')
    identifier: Optional[str]

class ListReturnPortChildStringReturnPortInlineFragment(ListReturnPortChildBase):
    typename: Optional[Literal['StringReturnPort']] = Field(alias='__typename')

class ListReturnPortChildIntReturnPortInlineFragment(ListReturnPortChildBase):
    typename: Optional[Literal['IntReturnPort']] = Field(alias='__typename')

class ListReturnPortChildBoolReturnPortInlineFragment(ListReturnPortChildBase):
    typename: Optional[Literal['BoolReturnPort']] = Field(alias='__typename')

class ListReturnPort(BaseModel):
    typename: Optional[Literal['ListReturnPort']] = Field(alias='__typename')
    key: Optional[str]
    child: Optional[Union[ListReturnPortChildStructureReturnPortInlineFragment, ListReturnPortChildStringReturnPortInlineFragment, ListReturnPortChildIntReturnPortInlineFragment, ListReturnPortChildBoolReturnPortInlineFragment]]

class DictReturnPortChildBase(BaseModel):
    pass

class DictReturnPortChildStructureReturnPortInlineFragment(DictReturnPortChildBase):
    typename: Optional[Literal['StructureReturnPort']] = Field(alias='__typename')
    identifier: Optional[str]

class DictReturnPortChildStringReturnPortInlineFragment(DictReturnPortChildBase):
    typename: Optional[Literal['StringReturnPort']] = Field(alias='__typename')

class DictReturnPortChildIntReturnPortInlineFragment(DictReturnPortChildBase):
    typename: Optional[Literal['IntReturnPort']] = Field(alias='__typename')

class DictReturnPortChildBoolReturnPortInlineFragment(DictReturnPortChildBase):
    typename: Optional[Literal['BoolReturnPort']] = Field(alias='__typename')

class DictReturnPort(BaseModel):
    typename: Optional[Literal['DictReturnPort']] = Field(alias='__typename')
    key: Optional[str]
    child: Optional[Union[DictReturnPortChildStructureReturnPortInlineFragment, DictReturnPortChildStringReturnPortInlineFragment, DictReturnPortChildIntReturnPortInlineFragment, DictReturnPortChildBoolReturnPortInlineFragment]]

class StructureReturnPort(BaseModel):
    typename: Optional[Literal['StructureReturnPort']] = Field(alias='__typename')
    key: Optional[str]
    identifier: Optional[str]

class StringReturnPort(BaseModel):
    typename: Optional[Literal['StringReturnPort']] = Field(alias='__typename')
    key: Optional[str]

class IntReturnPort(BaseModel):
    typename: Optional[Literal['IntReturnPort']] = Field(alias='__typename')
    key: Optional[str]

class ReturnPortBase(BaseModel):
    key: Optional[str]
    description: Optional[str]

class ReturnPortBaseListReturnPort(ListReturnPort, ReturnPortBase):
    pass

class ReturnPortBaseStructureReturnPort(StructureReturnPort, ReturnPortBase):
    pass

class ReturnPortBaseStringReturnPort(StringReturnPort, ReturnPortBase):
    pass

class ReturnPortBaseIntReturnPort(IntReturnPort, ReturnPortBase):
    pass

class ReturnPortBaseDictReturnPort(DictReturnPort, ReturnPortBase):
    pass
ReturnPort = Union[ReturnPortBaseListReturnPort, ReturnPortBaseStructureReturnPort, ReturnPortBaseStringReturnPort, ReturnPortBaseIntReturnPort, ReturnPortBaseDictReturnPort, ReturnPortBase]

class KwargPortBase(BaseModel):
    key: Optional[str]
    description: Optional[str]

class KwargPortBaseDictKwargPort(DictKwargPort, KwargPortBase):
    pass

class KwargPortBaseBoolKwargPort(BoolKwargPort, KwargPortBase):
    pass

class KwargPortBaseIntKwargPort(IntKwargPort, KwargPortBase):
    pass

class KwargPortBaseListKwargPort(ListKwargPort, KwargPortBase):
    pass

class KwargPortBaseStringKwargPort(StringKwargPort, KwargPortBase):
    pass
KwargPort = Union[KwargPortBaseDictKwargPort, KwargPortBaseBoolKwargPort, KwargPortBaseIntKwargPort, KwargPortBaseListKwargPort, KwargPortBaseStringKwargPort, KwargPortBase]

class ArgPortBase(BaseModel):
    key: Optional[str]
    description: Optional[str]

class ArgPortBaseStringArgPort(StringArgPort, ArgPortBase):
    pass

class ArgPortBaseStructureArgPort(StructureArgPort, ArgPortBase):
    pass

class ArgPortBaseListArgPort(ListArgPort, ArgPortBase):
    pass

class ArgPortBaseIntArgPort(IntArgPort, ArgPortBase):
    pass

class ArgPortBaseDictArgPort(DictArgPort, ArgPortBase):
    pass
ArgPort = Union[ArgPortBaseStringArgPort, ArgPortBaseStructureArgPort, ArgPortBaseListArgPort, ArgPortBaseIntArgPort, ArgPortBaseDictArgPort, ArgPortBase]

class ReserveParams(BaseModel):
    typename: Optional[Literal['ReserveParams']] = Field(alias='__typename')
    registries: Optional[List[Optional[str]]]
    minimal_instances: Optional[int] = Field(alias='minimalInstances')
    desired_instances: Optional[int] = Field(alias='desiredInstances')

class ReservationNode(BaseModel):
    typename: Optional[Literal['Node']] = Field(alias='__typename')
    id: str
    pure: bool

class Reservation(BaseModel):
    typename: Optional[Literal['Reservation']] = Field(alias='__typename')
    id: str
    statusmessage: str
    status: ReservationStatus
    node: Optional[ReservationNode]
    params: Optional[ReserveParams]

class TemplateRegistryApp(BaseModel):
    typename: Optional[Literal['LokApp']] = Field(alias='__typename')
    name: str

class TemplateRegistryUser(BaseModel):
    typename: Optional[Literal['LokUser']] = Field(alias='__typename')
    username: str

class TemplateRegistry(BaseModel):
    typename: Optional[Literal['Registry']] = Field(alias='__typename')
    name: Optional[str]
    'DEPRECATED Will be replaced in the future: : None '
    app: Optional[TemplateRegistryApp]
    user: Optional[TemplateRegistryUser]

class Template(BaseModel):
    typename: Optional[Literal['Template']] = Field(alias='__typename')
    id: str
    registry: TemplateRegistry
    node: Node

class Assign(BaseModel):
    assign: Optional[Assignation]

    class Arguments(BaseModel):
        reservation: str
        args: List[Optional[Dict]]
        kwargs: Optional[Dict] = None

    class Meta:
        document = 'fragment Assignation on Assignation {\n  args\n  kwargs\n  id\n  parent {\n    id\n  }\n  id\n  status\n  statusmessage\n}\n\nmutation assign($reservation: ID!, $args: [GenericScalar]!, $kwargs: GenericScalar) {\n  assign(reservation: $reservation, args: $args, kwargs: $kwargs) {\n    ...Assignation\n  }\n}'

class Unassign(BaseModel):
    unassign: Optional[Assignation]

    class Arguments(BaseModel):
        assignation: str

    class Meta:
        document = 'fragment Assignation on Assignation {\n  args\n  kwargs\n  id\n  parent {\n    id\n  }\n  id\n  status\n  statusmessage\n}\n\nmutation unassign($assignation: ID!) {\n  unassign(assignation: $assignation) {\n    ...Assignation\n  }\n}'

class Negotiate(BaseModel):
    negotiate: Optional[Transcript]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = 'fragment Transcript on Transcript {\n  postman {\n    type\n    kwargs\n  }\n}\n\nmutation negotiate {\n  negotiate {\n    ...Transcript\n  }\n}'

class Create_node(BaseModel):
    create_node: Optional[Node] = Field(alias='createNode')

    class Arguments(BaseModel):
        name: str
        interface: str
        args: Optional[List[Optional[ArgPortInput]]] = None

    class Meta:
        document = 'fragment BoolKwargPort on BoolKwargPort {\n  key\n  defaultBool\n}\n\nfragment DictReturnPort on DictReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StringArgPort on StringArgPort {\n  key\n}\n\nfragment StructureReturnPort on StructureReturnPort {\n  __typename\n  key\n  identifier\n}\n\nfragment IntReturnPort on IntReturnPort {\n  __typename\n  key\n}\n\nfragment StringReturnPort on StringReturnPort {\n  __typename\n  key\n}\n\nfragment DictArgPort on DictArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment ListReturnPort on ListReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StructureArgPort on StructureArgPort {\n  key\n  identifier\n}\n\nfragment IntArgPort on IntArgPort {\n  key\n}\n\nfragment ListArgPort on ListArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment IntKwargPort on IntKwargPort {\n  key\n  defaultInt\n}\n\nfragment StringKwargPort on StringKwargPort {\n  key\n  defaultString\n}\n\nfragment ListKwargPort on ListKwargPort {\n  key\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n  defaultList\n}\n\nfragment DictKwargPort on DictKwargPort {\n  key\n  defaultDict\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n}\n\nfragment ReturnPort on ReturnPort {\n  __typename\n  key\n  description\n  ...ListReturnPort\n  ...StructureReturnPort\n  ...StringReturnPort\n  ...IntReturnPort\n  ...DictReturnPort\n}\n\nfragment KwargPort on KwargPort {\n  __typename\n  key\n  description\n  ...DictKwargPort\n  ...BoolKwargPort\n  ...IntKwargPort\n  ...ListKwargPort\n  ...StringKwargPort\n}\n\nfragment ArgPort on ArgPort {\n  __typename\n  key\n  description\n  ...StringArgPort\n  ...StructureArgPort\n  ...ListArgPort\n  ...IntArgPort\n  ...DictArgPort\n}\n\nfragment Node on Node {\n  name\n  interface\n  package\n  description\n  type\n  id\n  args {\n    ...ArgPort\n  }\n  kwargs {\n    ...KwargPort\n  }\n  returns {\n    ...ReturnPort\n  }\n}\n\nmutation create_node($name: String!, $interface: String!, $args: [ArgPortInput]) {\n  createNode(name: $name, interface: $interface, args: $args) {\n    ...Node\n  }\n}'

class Define(BaseModel):
    define: Optional[Node]

    class Arguments(BaseModel):
        definition: DefinitionInput

    class Meta:
        document = 'fragment BoolKwargPort on BoolKwargPort {\n  key\n  defaultBool\n}\n\nfragment DictReturnPort on DictReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StringArgPort on StringArgPort {\n  key\n}\n\nfragment StructureReturnPort on StructureReturnPort {\n  __typename\n  key\n  identifier\n}\n\nfragment IntReturnPort on IntReturnPort {\n  __typename\n  key\n}\n\nfragment StringReturnPort on StringReturnPort {\n  __typename\n  key\n}\n\nfragment DictArgPort on DictArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment ListReturnPort on ListReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StructureArgPort on StructureArgPort {\n  key\n  identifier\n}\n\nfragment IntArgPort on IntArgPort {\n  key\n}\n\nfragment ListArgPort on ListArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment IntKwargPort on IntKwargPort {\n  key\n  defaultInt\n}\n\nfragment StringKwargPort on StringKwargPort {\n  key\n  defaultString\n}\n\nfragment ListKwargPort on ListKwargPort {\n  key\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n  defaultList\n}\n\nfragment DictKwargPort on DictKwargPort {\n  key\n  defaultDict\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n}\n\nfragment ReturnPort on ReturnPort {\n  __typename\n  key\n  description\n  ...ListReturnPort\n  ...StructureReturnPort\n  ...StringReturnPort\n  ...IntReturnPort\n  ...DictReturnPort\n}\n\nfragment KwargPort on KwargPort {\n  __typename\n  key\n  description\n  ...DictKwargPort\n  ...BoolKwargPort\n  ...IntKwargPort\n  ...ListKwargPort\n  ...StringKwargPort\n}\n\nfragment ArgPort on ArgPort {\n  __typename\n  key\n  description\n  ...StringArgPort\n  ...StructureArgPort\n  ...ListArgPort\n  ...IntArgPort\n  ...DictArgPort\n}\n\nfragment Node on Node {\n  name\n  interface\n  package\n  description\n  type\n  id\n  args {\n    ...ArgPort\n  }\n  kwargs {\n    ...KwargPort\n  }\n  returns {\n    ...ReturnPort\n  }\n}\n\nmutation define($definition: DefinitionInput!) {\n  define(definition: $definition) {\n    ...Node\n  }\n}'

class Reset_repositoryResetrepository(BaseModel):
    typename: Optional[Literal['ResetRepositoryReturn']] = Field(alias='__typename')
    ok: Optional[bool]

class Reset_repository(BaseModel):
    reset_repository: Optional[Reset_repositoryResetrepository] = Field(alias='resetRepository')

    class Arguments(BaseModel):
        pass

    class Meta:
        document = 'mutation reset_repository {\n  resetRepository {\n    ok\n  }\n}'

class Reserve(BaseModel):
    reserve: Optional[Reservation]

    class Arguments(BaseModel):
        node: Optional[str] = None
        template: Optional[str] = None
        params: Optional[ReserveParamsInput] = None
        title: Optional[str] = None
        callbacks: Optional[List[Optional[str]]] = None
        creator: Optional[str] = None
        app_group: Optional[str] = None

    class Meta:
        document = 'fragment ReserveParams on ReserveParams {\n  registries\n  minimalInstances\n  desiredInstances\n}\n\nfragment Reservation on Reservation {\n  id\n  statusmessage\n  status\n  node {\n    id\n    pure\n  }\n  params {\n    ...ReserveParams\n  }\n}\n\nmutation reserve($node: ID, $template: ID, $params: ReserveParamsInput, $title: String, $callbacks: [Callback], $creator: ID, $appGroup: ID) {\n  reserve(\n    node: $node\n    template: $template\n    params: $params\n    title: $title\n    callbacks: $callbacks\n    creator: $creator\n    appGroup: $appGroup\n  ) {\n    ...Reservation\n  }\n}'

class Unreserve(BaseModel):
    unreserve: Optional[Reservation]

    class Arguments(BaseModel):
        id: str

    class Meta:
        document = 'fragment ReserveParams on ReserveParams {\n  registries\n  minimalInstances\n  desiredInstances\n}\n\nfragment Reservation on Reservation {\n  id\n  statusmessage\n  status\n  node {\n    id\n    pure\n  }\n  params {\n    ...ReserveParams\n  }\n}\n\nmutation unreserve($id: ID!) {\n  unreserve(id: $id) {\n    ...Reservation\n  }\n}'

class Create_template(BaseModel):
    create_template: Optional[Template] = Field(alias='createTemplate')

    class Arguments(BaseModel):
        node: str
        params: Optional[Dict] = None
        extensions: Optional[List[Optional[str]]] = None
        version: Optional[str] = None

    class Meta:
        document = 'fragment BoolKwargPort on BoolKwargPort {\n  key\n  defaultBool\n}\n\nfragment DictReturnPort on DictReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StringArgPort on StringArgPort {\n  key\n}\n\nfragment StructureReturnPort on StructureReturnPort {\n  __typename\n  key\n  identifier\n}\n\nfragment IntReturnPort on IntReturnPort {\n  __typename\n  key\n}\n\nfragment StringReturnPort on StringReturnPort {\n  __typename\n  key\n}\n\nfragment DictArgPort on DictArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment ListReturnPort on ListReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StructureArgPort on StructureArgPort {\n  key\n  identifier\n}\n\nfragment IntArgPort on IntArgPort {\n  key\n}\n\nfragment ListArgPort on ListArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment IntKwargPort on IntKwargPort {\n  key\n  defaultInt\n}\n\nfragment StringKwargPort on StringKwargPort {\n  key\n  defaultString\n}\n\nfragment ListKwargPort on ListKwargPort {\n  key\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n  defaultList\n}\n\nfragment DictKwargPort on DictKwargPort {\n  key\n  defaultDict\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n}\n\nfragment ReturnPort on ReturnPort {\n  __typename\n  key\n  description\n  ...ListReturnPort\n  ...StructureReturnPort\n  ...StringReturnPort\n  ...IntReturnPort\n  ...DictReturnPort\n}\n\nfragment ArgPort on ArgPort {\n  __typename\n  key\n  description\n  ...StringArgPort\n  ...StructureArgPort\n  ...ListArgPort\n  ...IntArgPort\n  ...DictArgPort\n}\n\nfragment KwargPort on KwargPort {\n  __typename\n  key\n  description\n  ...DictKwargPort\n  ...BoolKwargPort\n  ...IntKwargPort\n  ...ListKwargPort\n  ...StringKwargPort\n}\n\nfragment Node on Node {\n  name\n  interface\n  package\n  description\n  type\n  id\n  args {\n    ...ArgPort\n  }\n  kwargs {\n    ...KwargPort\n  }\n  returns {\n    ...ReturnPort\n  }\n}\n\nfragment Template on Template {\n  id\n  registry {\n    name\n    app {\n      name\n    }\n    user {\n      username\n    }\n  }\n  node {\n    ...Node\n  }\n}\n\nmutation create_template($node: ID!, $params: GenericScalar, $extensions: [String], $version: String) {\n  createTemplate(\n    node: $node\n    params: $params\n    extensions: $extensions\n    version: $version\n  ) {\n    ...Template\n  }\n}'

class Get_agentAgentRegistry(BaseModel):
    typename: Optional[Literal['Registry']] = Field(alias='__typename')
    id: str
    name: Optional[str]
    'DEPRECATED Will be replaced in the future: : None '

class Get_agentAgent(BaseModel):
    typename: Optional[Literal['Agent']] = Field(alias='__typename')
    registry: Optional[Get_agentAgentRegistry]
    name: str
    identifier: str

class Get_agent(BaseModel):
    agent: Optional[Get_agentAgent]

    class Arguments(BaseModel):
        id: str

    class Meta:
        document = 'query get_agent($id: ID!) {\n  agent(id: $id) {\n    registry {\n      id\n      name\n    }\n    name\n    identifier\n  }\n}'

class Todolist(BaseModel):
    todolist: Optional[List[Optional[Assignation]]]

    class Arguments(BaseModel):
        app_group: Optional[str] = None

    class Meta:
        document = 'fragment Assignation on Assignation {\n  args\n  kwargs\n  id\n  parent {\n    id\n  }\n  id\n  status\n  statusmessage\n}\n\nquery todolist($appGroup: ID) {\n  todolist(appGroup: $appGroup) {\n    ...Assignation\n  }\n}'

class Find(BaseModel):
    node: Optional[Node]

    class Arguments(BaseModel):
        id: Optional[str] = None
        package: Optional[str] = None
        interface: Optional[str] = None
        template: Optional[str] = None
        q: Optional[str] = None

    class Meta:
        document = 'fragment BoolKwargPort on BoolKwargPort {\n  key\n  defaultBool\n}\n\nfragment DictReturnPort on DictReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StringArgPort on StringArgPort {\n  key\n}\n\nfragment StructureReturnPort on StructureReturnPort {\n  __typename\n  key\n  identifier\n}\n\nfragment IntReturnPort on IntReturnPort {\n  __typename\n  key\n}\n\nfragment StringReturnPort on StringReturnPort {\n  __typename\n  key\n}\n\nfragment DictArgPort on DictArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment ListReturnPort on ListReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StructureArgPort on StructureArgPort {\n  key\n  identifier\n}\n\nfragment IntArgPort on IntArgPort {\n  key\n}\n\nfragment ListArgPort on ListArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment IntKwargPort on IntKwargPort {\n  key\n  defaultInt\n}\n\nfragment StringKwargPort on StringKwargPort {\n  key\n  defaultString\n}\n\nfragment ListKwargPort on ListKwargPort {\n  key\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n  defaultList\n}\n\nfragment DictKwargPort on DictKwargPort {\n  key\n  defaultDict\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n}\n\nfragment ReturnPort on ReturnPort {\n  __typename\n  key\n  description\n  ...ListReturnPort\n  ...StructureReturnPort\n  ...StringReturnPort\n  ...IntReturnPort\n  ...DictReturnPort\n}\n\nfragment KwargPort on KwargPort {\n  __typename\n  key\n  description\n  ...DictKwargPort\n  ...BoolKwargPort\n  ...IntKwargPort\n  ...ListKwargPort\n  ...StringKwargPort\n}\n\nfragment ArgPort on ArgPort {\n  __typename\n  key\n  description\n  ...StringArgPort\n  ...StructureArgPort\n  ...ListArgPort\n  ...IntArgPort\n  ...DictArgPort\n}\n\nfragment Node on Node {\n  name\n  interface\n  package\n  description\n  type\n  id\n  args {\n    ...ArgPort\n  }\n  kwargs {\n    ...KwargPort\n  }\n  returns {\n    ...ReturnPort\n  }\n}\n\nquery find($id: ID, $package: String, $interface: String, $template: ID, $q: QString) {\n  node(\n    id: $id\n    package: $package\n    interface: $interface\n    template: $template\n    q: $q\n  ) {\n    ...Node\n  }\n}'

class Get_provisionProvisionTemplateNode(BaseModel):
    typename: Optional[Literal['Node']] = Field(alias='__typename')
    name: str

class Get_provisionProvisionTemplateRegistryApp(BaseModel):
    typename: Optional[Literal['LokApp']] = Field(alias='__typename')
    name: str

class Get_provisionProvisionTemplateRegistry(BaseModel):
    typename: Optional[Literal['Registry']] = Field(alias='__typename')
    app: Optional[Get_provisionProvisionTemplateRegistryApp]

class Get_provisionProvisionTemplate(BaseModel):
    typename: Optional[Literal['Template']] = Field(alias='__typename')
    id: str
    node: Get_provisionProvisionTemplateNode
    registry: Get_provisionProvisionTemplateRegistry
    extensions: Optional[List[Optional[str]]]

class Get_provisionProvisionBoundRegistry(BaseModel):
    typename: Optional[Literal['Registry']] = Field(alias='__typename')
    id: str
    name: Optional[str]
    'DEPRECATED Will be replaced in the future: : None '

class Get_provisionProvisionBound(BaseModel):
    typename: Optional[Literal['Agent']] = Field(alias='__typename')
    registry: Optional[Get_provisionProvisionBoundRegistry]
    name: str
    identifier: str

class Get_provisionProvisionReservationsCreator(BaseModel):
    typename: Optional[Literal['LokUser']] = Field(alias='__typename')
    username: str

class Get_provisionProvisionReservationsApp(BaseModel):
    typename: Optional[Literal['LokApp']] = Field(alias='__typename')
    name: str

class Get_provisionProvisionReservations(BaseModel):
    typename: Optional[Literal['Reservation']] = Field(alias='__typename')
    id: str
    reference: str
    creator: Optional[Get_provisionProvisionReservationsCreator]
    app: Optional[Get_provisionProvisionReservationsApp]

class Get_provisionProvision(BaseModel):
    typename: Optional[Literal['Provision']] = Field(alias='__typename')
    template: Optional[Get_provisionProvisionTemplate]
    bound: Optional[Get_provisionProvisionBound]
    reservations: List[Get_provisionProvisionReservations]

class Get_provision(BaseModel):
    provision: Optional[Get_provisionProvision]

    class Arguments(BaseModel):
        reference: str

    class Meta:
        document = 'query get_provision($reference: ID!) {\n  provision(reference: $reference) {\n    template {\n      id\n      node {\n        name\n      }\n      registry {\n        app {\n          name\n        }\n      }\n      extensions\n    }\n    bound {\n      registry {\n        id\n        name\n      }\n      name\n      identifier\n    }\n    reservations {\n      id\n      reference\n      creator {\n        username\n      }\n      app {\n        name\n      }\n    }\n  }\n}'

class Get_reservationReservationTemplateRegistryApp(BaseModel):
    typename: Optional[Literal['LokApp']] = Field(alias='__typename')
    id: str
    name: str

class Get_reservationReservationTemplateRegistryUser(BaseModel):
    typename: Optional[Literal['LokUser']] = Field(alias='__typename')
    id: str
    email: str

class Get_reservationReservationTemplateRegistry(BaseModel):
    typename: Optional[Literal['Registry']] = Field(alias='__typename')
    app: Optional[Get_reservationReservationTemplateRegistryApp]
    user: Optional[Get_reservationReservationTemplateRegistryUser]

class Get_reservationReservationTemplate(BaseModel):
    typename: Optional[Literal['Template']] = Field(alias='__typename')
    id: str
    registry: Get_reservationReservationTemplateRegistry

class Get_reservationReservationProvisions(BaseModel):
    typename: Optional[Literal['Provision']] = Field(alias='__typename')
    id: str
    status: ProvisionStatus

class Get_reservationReservationNode(BaseModel):
    typename: Optional[Literal['Node']] = Field(alias='__typename')
    id: str
    type: NodeType
    name: str

class Get_reservationReservation(BaseModel):
    typename: Optional[Literal['Reservation']] = Field(alias='__typename')
    id: str
    template: Optional[Get_reservationReservationTemplate]
    provisions: List[Get_reservationReservationProvisions]
    title: Optional[str]
    status: ReservationStatus
    id: str
    reference: str
    node: Optional[Get_reservationReservationNode]

class Get_reservation(BaseModel):
    reservation: Optional[Get_reservationReservation]

    class Arguments(BaseModel):
        reference: str

    class Meta:
        document = 'query get_reservation($reference: ID!) {\n  reservation(reference: $reference) {\n    id\n    template {\n      id\n      registry {\n        app {\n          id\n          name\n        }\n        user {\n          id\n          email\n        }\n      }\n    }\n    provisions {\n      id\n      status\n    }\n    title\n    status\n    id\n    reference\n    node {\n      id\n      type\n      name\n    }\n  }\n}'

class Waitlist(BaseModel):
    waitlist: Optional[List[Optional[Reservation]]]

    class Arguments(BaseModel):
        app_group: Optional[str] = None

    class Meta:
        document = 'fragment ReserveParams on ReserveParams {\n  registries\n  minimalInstances\n  desiredInstances\n}\n\nfragment Reservation on Reservation {\n  id\n  statusmessage\n  status\n  node {\n    id\n    pure\n  }\n  params {\n    ...ReserveParams\n  }\n}\n\nquery waitlist($appGroup: ID) {\n  waitlist(appGroup: $appGroup) {\n    ...Reservation\n  }\n}'

<<<<<<< HEAD
class Find(BaseModel):
    node: Optional[Node]

    class Arguments(BaseModel):
        id: Optional[str] = None
        package: Optional[str] = None
        interface: Optional[str] = None
        template: Optional[str] = None
        q: Optional[str] = None

    class Meta:
        document = 'fragment StringArgPort on StringArgPort {\n  key\n}\n\nfragment DictArgPort on DictArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment StructureReturnPort on StructureReturnPort {\n  __typename\n  key\n  identifier\n}\n\nfragment IntKwargPort on IntKwargPort {\n  key\n  defaultInt\n}\n\nfragment IntArgPort on IntArgPort {\n  key\n}\n\nfragment StructureArgPort on StructureArgPort {\n  key\n  identifier\n}\n\nfragment DictReturnPort on DictReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StringReturnPort on StringReturnPort {\n  __typename\n  key\n}\n\nfragment BoolKwargPort on BoolKwargPort {\n  key\n  defaultBool\n}\n\nfragment ListReturnPort on ListReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment ListArgPort on ListArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment DictKwargPort on DictKwargPort {\n  key\n  defaultDict\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n}\n\nfragment StringKwargPort on StringKwargPort {\n  key\n  defaultString\n}\n\nfragment IntReturnPort on IntReturnPort {\n  __typename\n  key\n}\n\nfragment ListKwargPort on ListKwargPort {\n  key\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n  defaultList\n}\n\nfragment ReturnPort on ReturnPort {\n  __typename\n  key\n  description\n  ...ListReturnPort\n  ...StructureReturnPort\n  ...StringReturnPort\n  ...IntReturnPort\n  ...DictReturnPort\n}\n\nfragment ArgPort on ArgPort {\n  __typename\n  key\n  description\n  ...StringArgPort\n  ...StructureArgPort\n  ...ListArgPort\n  ...IntArgPort\n  ...DictArgPort\n}\n\nfragment KwargPort on KwargPort {\n  __typename\n  key\n  description\n  ...DictKwargPort\n  ...BoolKwargPort\n  ...IntKwargPort\n  ...ListKwargPort\n  ...StringKwargPort\n}\n\nfragment Node on Node {\n  name\n  interface\n  package\n  description\n  type\n  id\n  args {\n    ...ArgPort\n  }\n  kwargs {\n    ...KwargPort\n  }\n  returns {\n    ...ReturnPort\n  }\n}\n\nquery find($id: ID, $package: String, $interface: String, $template: ID, $q: QString) {\n  node(\n    id: $id\n    package: $package\n    interface: $interface\n    template: $template\n    q: $q\n  ) {\n    ...Node\n  }\n}'

=======
>>>>>>> e307536ce6e5f0cbb9c0c10159b6664f94e0776e
class Get_template(BaseModel):
    template: Optional[Template]

    class Arguments(BaseModel):
        id: str

    class Meta:
<<<<<<< HEAD
        document = 'fragment StringArgPort on StringArgPort {\n  key\n}\n\nfragment DictArgPort on DictArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment StructureReturnPort on StructureReturnPort {\n  __typename\n  key\n  identifier\n}\n\nfragment IntKwargPort on IntKwargPort {\n  key\n  defaultInt\n}\n\nfragment IntArgPort on IntArgPort {\n  key\n}\n\nfragment StructureArgPort on StructureArgPort {\n  key\n  identifier\n}\n\nfragment DictReturnPort on DictReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StringReturnPort on StringReturnPort {\n  __typename\n  key\n}\n\nfragment BoolKwargPort on BoolKwargPort {\n  key\n  defaultBool\n}\n\nfragment ListReturnPort on ListReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment ListArgPort on ListArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment DictKwargPort on DictKwargPort {\n  key\n  defaultDict\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n}\n\nfragment StringKwargPort on StringKwargPort {\n  key\n  defaultString\n}\n\nfragment IntReturnPort on IntReturnPort {\n  __typename\n  key\n}\n\nfragment ListKwargPort on ListKwargPort {\n  key\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n  defaultList\n}\n\nfragment ArgPort on ArgPort {\n  __typename\n  key\n  description\n  ...StringArgPort\n  ...StructureArgPort\n  ...ListArgPort\n  ...IntArgPort\n  ...DictArgPort\n}\n\nfragment ReturnPort on ReturnPort {\n  __typename\n  key\n  description\n  ...ListReturnPort\n  ...StructureReturnPort\n  ...StringReturnPort\n  ...IntReturnPort\n  ...DictReturnPort\n}\n\nfragment KwargPort on KwargPort {\n  __typename\n  key\n  description\n  ...DictKwargPort\n  ...BoolKwargPort\n  ...IntKwargPort\n  ...ListKwargPort\n  ...StringKwargPort\n}\n\nfragment Node on Node {\n  name\n  interface\n  package\n  description\n  type\n  id\n  args {\n    ...ArgPort\n  }\n  kwargs {\n    ...KwargPort\n  }\n  returns {\n    ...ReturnPort\n  }\n}\n\nfragment Template on Template {\n  id\n  registry {\n    name\n    app {\n      name\n    }\n    user {\n      username\n    }\n  }\n  node {\n    ...Node\n  }\n}\n\nquery get_template($id: ID!) {\n  template(id: $id) {\n    ...Template\n  }\n}'

class Get_agentAgentRegistry(BaseModel):
    typename: Optional[Literal['Registry']] = Field(alias='__typename')
    id: str
    name: Optional[str]
    'DEPRECATED Will be replaced in the future: : None '

class Get_agentAgent(BaseModel):
    typename: Optional[Literal['Agent']] = Field(alias='__typename')
    registry: Optional[Get_agentAgentRegistry]
    name: str
    identifier: str

class Get_agent(BaseModel):
    agent: Optional[Get_agentAgent]

    class Arguments(BaseModel):
        id: str

    class Meta:
        document = 'query get_agent($id: ID!) {\n  agent(id: $id) {\n    registry {\n      id\n      name\n    }\n    name\n    identifier\n  }\n}'

class Assign(BaseModel):
    assign: Optional[Assignation]

    class Arguments(BaseModel):
        reservation: str
        args: List[Optional[Dict]]
        kwargs: Optional[Dict] = None

    class Meta:
        document = 'fragment Assignation on Assignation {\n  args\n  kwargs\n  id\n  parent {\n    id\n  }\n  id\n  status\n  statusmessage\n}\n\nmutation assign($reservation: ID!, $args: [GenericScalar]!, $kwargs: GenericScalar) {\n  assign(reservation: $reservation, args: $args, kwargs: $kwargs) {\n    ...Assignation\n  }\n}'

class Unassign(BaseModel):
    unassign: Optional[Assignation]

    class Arguments(BaseModel):
        assignation: str

    class Meta:
        document = 'fragment Assignation on Assignation {\n  args\n  kwargs\n  id\n  parent {\n    id\n  }\n  id\n  status\n  statusmessage\n}\n\nmutation unassign($assignation: ID!) {\n  unassign(assignation: $assignation) {\n    ...Assignation\n  }\n}'

class Negotiate(BaseModel):
    negotiate: Optional[Transcript]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = 'fragment Transcript on Transcript {\n  postman {\n    type\n    kwargs\n  }\n}\n\nmutation negotiate {\n  negotiate {\n    ...Transcript\n  }\n}'

class Reserve(BaseModel):
    reserve: Optional[Reservation]

    class Arguments(BaseModel):
        node: Optional[str] = None
        template: Optional[str] = None
        params: Optional[ReserveParamsInput] = None
        title: Optional[str] = None
        callbacks: Optional[List[Optional[str]]] = None
        creator: Optional[str] = None
        app_group: Optional[str] = None

    class Meta:
        document = 'fragment ReserveParams on ReserveParams {\n  registries\n  minimalInstances\n  desiredInstances\n}\n\nfragment Reservation on Reservation {\n  id\n  statusmessage\n  status\n  node {\n    id\n    pure\n  }\n  params {\n    ...ReserveParams\n  }\n}\n\nmutation reserve($node: ID, $template: ID, $params: ReserveParamsInput, $title: String, $callbacks: [Callback], $creator: ID, $appGroup: ID) {\n  reserve(\n    node: $node\n    template: $template\n    params: $params\n    title: $title\n    callbacks: $callbacks\n    creator: $creator\n    appGroup: $appGroup\n  ) {\n    ...Reservation\n  }\n}'

class Unreserve(BaseModel):
    unreserve: Optional[Reservation]

    class Arguments(BaseModel):
        id: str

    class Meta:
        document = 'fragment ReserveParams on ReserveParams {\n  registries\n  minimalInstances\n  desiredInstances\n}\n\nfragment Reservation on Reservation {\n  id\n  statusmessage\n  status\n  node {\n    id\n    pure\n  }\n  params {\n    ...ReserveParams\n  }\n}\n\nmutation unreserve($id: ID!) {\n  unreserve(id: $id) {\n    ...Reservation\n  }\n}'

class Create_node(BaseModel):
    create_node: Optional[Node] = Field(alias='createNode')

    class Arguments(BaseModel):
        name: str
        interface: str
        args: Optional[List[Optional[ArgPortInput]]] = None

    class Meta:
        document = 'fragment StringArgPort on StringArgPort {\n  key\n}\n\nfragment DictArgPort on DictArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment StructureReturnPort on StructureReturnPort {\n  __typename\n  key\n  identifier\n}\n\nfragment IntKwargPort on IntKwargPort {\n  key\n  defaultInt\n}\n\nfragment IntArgPort on IntArgPort {\n  key\n}\n\nfragment StructureArgPort on StructureArgPort {\n  key\n  identifier\n}\n\nfragment DictReturnPort on DictReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StringReturnPort on StringReturnPort {\n  __typename\n  key\n}\n\nfragment BoolKwargPort on BoolKwargPort {\n  key\n  defaultBool\n}\n\nfragment ListReturnPort on ListReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment ListArgPort on ListArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment DictKwargPort on DictKwargPort {\n  key\n  defaultDict\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n}\n\nfragment StringKwargPort on StringKwargPort {\n  key\n  defaultString\n}\n\nfragment IntReturnPort on IntReturnPort {\n  __typename\n  key\n}\n\nfragment ListKwargPort on ListKwargPort {\n  key\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n  defaultList\n}\n\nfragment ReturnPort on ReturnPort {\n  __typename\n  key\n  description\n  ...ListReturnPort\n  ...StructureReturnPort\n  ...StringReturnPort\n  ...IntReturnPort\n  ...DictReturnPort\n}\n\nfragment ArgPort on ArgPort {\n  __typename\n  key\n  description\n  ...StringArgPort\n  ...StructureArgPort\n  ...ListArgPort\n  ...IntArgPort\n  ...DictArgPort\n}\n\nfragment KwargPort on KwargPort {\n  __typename\n  key\n  description\n  ...DictKwargPort\n  ...BoolKwargPort\n  ...IntKwargPort\n  ...ListKwargPort\n  ...StringKwargPort\n}\n\nfragment Node on Node {\n  name\n  interface\n  package\n  description\n  type\n  id\n  args {\n    ...ArgPort\n  }\n  kwargs {\n    ...KwargPort\n  }\n  returns {\n    ...ReturnPort\n  }\n}\n\nmutation create_node($name: String!, $interface: String!, $args: [ArgPortInput]) {\n  createNode(name: $name, interface: $interface, args: $args) {\n    ...Node\n  }\n}'
=======
        document = 'fragment BoolKwargPort on BoolKwargPort {\n  key\n  defaultBool\n}\n\nfragment DictReturnPort on DictReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StringArgPort on StringArgPort {\n  key\n}\n\nfragment StructureReturnPort on StructureReturnPort {\n  __typename\n  key\n  identifier\n}\n\nfragment IntReturnPort on IntReturnPort {\n  __typename\n  key\n}\n\nfragment StringReturnPort on StringReturnPort {\n  __typename\n  key\n}\n\nfragment DictArgPort on DictArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment ListReturnPort on ListReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StructureArgPort on StructureArgPort {\n  key\n  identifier\n}\n\nfragment IntArgPort on IntArgPort {\n  key\n}\n\nfragment ListArgPort on ListArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment IntKwargPort on IntKwargPort {\n  key\n  defaultInt\n}\n\nfragment StringKwargPort on StringKwargPort {\n  key\n  defaultString\n}\n\nfragment ListKwargPort on ListKwargPort {\n  key\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n  defaultList\n}\n\nfragment DictKwargPort on DictKwargPort {\n  key\n  defaultDict\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n}\n\nfragment ReturnPort on ReturnPort {\n  __typename\n  key\n  description\n  ...ListReturnPort\n  ...StructureReturnPort\n  ...StringReturnPort\n  ...IntReturnPort\n  ...DictReturnPort\n}\n\nfragment ArgPort on ArgPort {\n  __typename\n  key\n  description\n  ...StringArgPort\n  ...StructureArgPort\n  ...ListArgPort\n  ...IntArgPort\n  ...DictArgPort\n}\n\nfragment KwargPort on KwargPort {\n  __typename\n  key\n  description\n  ...DictKwargPort\n  ...BoolKwargPort\n  ...IntKwargPort\n  ...ListKwargPort\n  ...StringKwargPort\n}\n\nfragment Node on Node {\n  name\n  interface\n  package\n  description\n  type\n  id\n  args {\n    ...ArgPort\n  }\n  kwargs {\n    ...KwargPort\n  }\n  returns {\n    ...ReturnPort\n  }\n}\n\nfragment Template on Template {\n  id\n  registry {\n    name\n    app {\n      name\n    }\n    user {\n      username\n    }\n  }\n  node {\n    ...Node\n  }\n}\n\nquery get_template($id: ID!) {\n  template(id: $id) {\n    ...Template\n  }\n}'

class TodosTodos(BaseModel):
    typename: Optional[Literal['TodoEvent']] = Field(alias='__typename')
    create: Optional[Assignation]
    update: Optional[Assignation]
    delete: Optional[str]
>>>>>>> e307536ce6e5f0cbb9c0c10159b6664f94e0776e

class Todos(BaseModel):
    todos: Optional[TodosTodos]

    class Arguments(BaseModel):
        identifier: str

    class Meta:
<<<<<<< HEAD
        document = 'fragment StringArgPort on StringArgPort {\n  key\n}\n\nfragment DictArgPort on DictArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment StructureReturnPort on StructureReturnPort {\n  __typename\n  key\n  identifier\n}\n\nfragment IntKwargPort on IntKwargPort {\n  key\n  defaultInt\n}\n\nfragment IntArgPort on IntArgPort {\n  key\n}\n\nfragment StructureArgPort on StructureArgPort {\n  key\n  identifier\n}\n\nfragment DictReturnPort on DictReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StringReturnPort on StringReturnPort {\n  __typename\n  key\n}\n\nfragment BoolKwargPort on BoolKwargPort {\n  key\n  defaultBool\n}\n\nfragment ListReturnPort on ListReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment ListArgPort on ListArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment DictKwargPort on DictKwargPort {\n  key\n  defaultDict\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n}\n\nfragment StringKwargPort on StringKwargPort {\n  key\n  defaultString\n}\n\nfragment IntReturnPort on IntReturnPort {\n  __typename\n  key\n}\n\nfragment ListKwargPort on ListKwargPort {\n  key\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n  defaultList\n}\n\nfragment ReturnPort on ReturnPort {\n  __typename\n  key\n  description\n  ...ListReturnPort\n  ...StructureReturnPort\n  ...StringReturnPort\n  ...IntReturnPort\n  ...DictReturnPort\n}\n\nfragment ArgPort on ArgPort {\n  __typename\n  key\n  description\n  ...StringArgPort\n  ...StructureArgPort\n  ...ListArgPort\n  ...IntArgPort\n  ...DictArgPort\n}\n\nfragment KwargPort on KwargPort {\n  __typename\n  key\n  description\n  ...DictKwargPort\n  ...BoolKwargPort\n  ...IntKwargPort\n  ...ListKwargPort\n  ...StringKwargPort\n}\n\nfragment Node on Node {\n  name\n  interface\n  package\n  description\n  type\n  id\n  args {\n    ...ArgPort\n  }\n  kwargs {\n    ...KwargPort\n  }\n  returns {\n    ...ReturnPort\n  }\n}\n\nmutation define($definition: DefinitionInput!) {\n  define(definition: $definition) {\n    ...Node\n  }\n}'

class Reset_repositoryResetrepository(BaseModel):
    typename: Optional[Literal['ResetRepositoryReturn']] = Field(alias='__typename')
    ok: Optional[bool]

class Reset_repository(BaseModel):
    reset_repository: Optional[Reset_repositoryResetrepository] = Field(alias='resetRepository')

    class Arguments(BaseModel):
        pass
=======
        document = 'fragment Assignation on Assignation {\n  args\n  kwargs\n  id\n  parent {\n    id\n  }\n  id\n  status\n  statusmessage\n}\n\nsubscription todos($identifier: ID!) {\n  todos(identifier: $identifier) {\n    create {\n      ...Assignation\n    }\n    update {\n      ...Assignation\n    }\n    delete\n  }\n}'
>>>>>>> e307536ce6e5f0cbb9c0c10159b6664f94e0776e

class WaiterReservations(BaseModel):
    typename: Optional[Literal['ReservationsEvent']] = Field(alias='__typename')
    create: Optional[Reservation]
    update: Optional[Reservation]
    delete: Optional[str]

class Waiter(BaseModel):
    reservations: Optional[WaiterReservations]

    class Arguments(BaseModel):
        identifier: str

    class Meta:
<<<<<<< HEAD
        document = 'fragment StringArgPort on StringArgPort {\n  key\n}\n\nfragment DictArgPort on DictArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment StructureReturnPort on StructureReturnPort {\n  __typename\n  key\n  identifier\n}\n\nfragment IntKwargPort on IntKwargPort {\n  key\n  defaultInt\n}\n\nfragment IntArgPort on IntArgPort {\n  key\n}\n\nfragment StructureArgPort on StructureArgPort {\n  key\n  identifier\n}\n\nfragment DictReturnPort on DictReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment StringReturnPort on StringReturnPort {\n  __typename\n  key\n}\n\nfragment BoolKwargPort on BoolKwargPort {\n  key\n  defaultBool\n}\n\nfragment ListReturnPort on ListReturnPort {\n  key\n  child {\n    __typename\n    ... on StructureReturnPort {\n      __typename\n      identifier\n    }\n    ... on StringReturnPort {\n      __typename\n    }\n    ... on IntReturnPort {\n      __typename\n    }\n    ... on BoolReturnPort {\n      __typename\n    }\n  }\n}\n\nfragment ListArgPort on ListArgPort {\n  key\n  child {\n    __typename\n    ... on StructureArgPort {\n      __typename\n      identifier\n    }\n    ... on IntArgPort {\n      __typename\n    }\n    ... on BoolArgPort {\n      __typename\n    }\n    ... on StringArgPort {\n      __typename\n    }\n  }\n}\n\nfragment DictKwargPort on DictKwargPort {\n  key\n  defaultDict\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n}\n\nfragment StringKwargPort on StringKwargPort {\n  key\n  defaultString\n}\n\nfragment IntReturnPort on IntReturnPort {\n  __typename\n  key\n}\n\nfragment ListKwargPort on ListKwargPort {\n  key\n  child {\n    __typename\n    ... on StructureKwargPort {\n      __typename\n      identifier\n    }\n    ... on IntKwargPort {\n      __typename\n    }\n    ... on BoolKwargPort {\n      __typename\n    }\n    ... on StringKwargPort {\n      __typename\n    }\n  }\n  defaultList\n}\n\nfragment ArgPort on ArgPort {\n  __typename\n  key\n  description\n  ...StringArgPort\n  ...StructureArgPort\n  ...ListArgPort\n  ...IntArgPort\n  ...DictArgPort\n}\n\nfragment ReturnPort on ReturnPort {\n  __typename\n  key\n  description\n  ...ListReturnPort\n  ...StructureReturnPort\n  ...StringReturnPort\n  ...IntReturnPort\n  ...DictReturnPort\n}\n\nfragment KwargPort on KwargPort {\n  __typename\n  key\n  description\n  ...DictKwargPort\n  ...BoolKwargPort\n  ...IntKwargPort\n  ...ListKwargPort\n  ...StringKwargPort\n}\n\nfragment Node on Node {\n  name\n  interface\n  package\n  description\n  type\n  id\n  args {\n    ...ArgPort\n  }\n  kwargs {\n    ...KwargPort\n  }\n  returns {\n    ...ReturnPort\n  }\n}\n\nfragment Template on Template {\n  id\n  registry {\n    name\n    app {\n      name\n    }\n    user {\n      username\n    }\n  }\n  node {\n    ...Node\n  }\n}\n\nmutation create_template($node: ID!, $params: GenericScalar, $extensions: [String], $version: String) {\n  createTemplate(\n    node: $node\n    params: $params\n    extensions: $extensions\n    version: $version\n  ) {\n    ...Template\n  }\n}'
KwargPortInput.update_forward_refs()
=======
        document = 'fragment ReserveParams on ReserveParams {\n  registries\n  minimalInstances\n  desiredInstances\n}\n\nfragment Reservation on Reservation {\n  id\n  statusmessage\n  status\n  node {\n    id\n    pure\n  }\n  params {\n    ...ReserveParams\n  }\n}\n\nsubscription waiter($identifier: ID!) {\n  reservations(identifier: $identifier) {\n    create {\n      ...Reservation\n    }\n    update {\n      ...Reservation\n    }\n    delete\n  }\n}'
>>>>>>> e307536ce6e5f0cbb9c0c10159b6664f94e0776e
DefinitionInput.update_forward_refs()
ArgPortInput.update_forward_refs()
ReturnPortInput.update_forward_refs()
KwargPortInput.update_forward_refs()
Node.update_forward_refs()