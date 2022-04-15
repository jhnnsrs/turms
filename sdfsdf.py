from typing import Literal, Optional, Union, Dict, List
from pydantic import Field, BaseModel
from tests.mocks import query
from enum import Enum

class EdgeInput(BaseModel):
    id: str
    type: str
    source: str
    target: str
    source_handle: Optional[str] = Field(alias='sourceHandle')
    target_handle: Optional[str] = Field(alias='targetHandle')
    label: Optional[str]

class FlowArgInput(BaseModel):
    key: str
    label: Optional[str]
    name: Optional[str]
    type: Optional[str]
    description: Optional[str]

class FlowKwargInput(BaseModel):
    key: str
    label: Optional[str]
    name: Optional[str]
    type: Optional[str]
    description: Optional[str]

class FlowReturnInput(BaseModel):
    key: str
    label: Optional[str]
    name: Optional[str]
    type: Optional[str]
    description: Optional[str]

class NodeInput(BaseModel):
    id: str
    type: str
    args: Optional[List[Optional[FlowArgInput]]]
    kwargs: Optional[List[Optional[FlowKwargInput]]]
    returns: Optional[List[Optional[FlowReturnInput]]]
    package: Optional[str]
    name: Optional[str]
    description: Optional[str]
    interface: Optional[str]
    kind: Optional[str]
    implementation: Optional[str]
    position: 'PositionInput'
    extra: Optional[Dict]

class PositionInput(BaseModel):
    x: float
    y: float

class Graph(BaseModel):
    typename: Optional[Literal['Graph']] = Field(alias='__typename')
    diagram: Optional[Dict]
    id: str
    template: Optional[str]
    name: Optional[str]

class ListGraph(BaseModel):
    typename: Optional[Literal['Graph']] = Field(alias='__typename')
    id: str
    name: Optional[str]
    template: Optional[str]

class FlowArg(BaseModel):
    typename: Optional[Literal['FlowArg']] = Field(alias='__typename')
    key: str
    type: Optional[str]
    name: Optional[str]
    label: Optional[str]
    type: Optional[str]
    description: Optional[str]

class FlowKwarg(BaseModel):
    typename: Optional[Literal['FlowKwarg']] = Field(alias='__typename')
    key: str
    type: Optional[str]
    label: Optional[str]
    name: Optional[str]
    type: Optional[str]
    description: Optional[str]

class FlowReturn(BaseModel):
    typename: Optional[Literal['FlowReturn']] = Field(alias='__typename')
    key: str
    type: Optional[str]
    name: Optional[str]
    label: Optional[str]
    type: Optional[str]
    description: Optional[str]

class FlowNodeCommonsBaseArgs(FlowArg, BaseModel):
    typename: Optional[Literal['FlowArg']] = Field(alias='__typename')

class FlowNodeCommonsBaseKwargs(FlowKwarg, BaseModel):
    typename: Optional[Literal['FlowKwarg']] = Field(alias='__typename')

class FlowNodeCommonsBaseReturns(FlowReturn, BaseModel):
    typename: Optional[Literal['FlowReturn']] = Field(alias='__typename')

class FlowNodeCommonsBase(BaseModel):
    """Amazing other interface"""
    args: Optional[List[Optional[FlowNodeCommonsBaseArgs]]]
    kwargs: Optional[List[Optional[FlowNodeCommonsBaseKwargs]]]
    returns: Optional[List[Optional[FlowNodeCommonsBaseReturns]]]

class ArkitektNode(FlowNodeCommonsBase, BaseModel):
    typename: Optional[Literal['ArkitektNode']] = Field(alias='__typename')
    name: Optional[str]
    description: Optional[str]
    package: Optional[str]
    interface: Optional[str]
    kind: str

class ReactiveNode(FlowNodeCommonsBase, BaseModel):
    typename: Optional[Literal['ReactiveNode']] = Field(alias='__typename')
    implementation: Optional[str]

class ArgNode(FlowNodeCommonsBase, BaseModel):
    typename: Optional[Literal['ArgNode']] = Field(alias='__typename')
    extra: Optional[str]

class KwargNode(FlowNodeCommonsBase, BaseModel):
    typename: Optional[Literal['KwargNode']] = Field(alias='__typename')
    extra: Optional[str]

class ReturnNode(FlowNodeCommonsBase, BaseModel):
    typename: Optional[Literal['ReturnNode']] = Field(alias='__typename')
    extra: Optional[str]

class FlowNodeBasePosition(BaseModel):
    typename: Optional[Literal['Position']] = Field(alias='__typename')
    x: int
    y: int

class FlowNodeBase(BaseModel):
    id: str
    position: FlowNodeBasePosition

class FlowNodeBaseArkitektNode(ArkitektNode, FlowNodeBase):
    pass

class FlowNodeBaseReactiveNode(ReactiveNode, FlowNodeBase):
    pass

class FlowNodeBaseArgNode(ArgNode, FlowNodeBase):
    pass

class FlowNodeBaseKwargNode(KwargNode, FlowNodeBase):
    pass

class FlowNodeBaseReturnNode(ReturnNode, FlowNodeBase):
    pass
FlowNode = Union[FlowNodeBaseArkitektNode, FlowNodeBaseReactiveNode, FlowNodeBaseArgNode, FlowNodeBaseKwargNode, FlowNodeBaseReturnNode, FlowNodeBase]

class FlowEdgeCommonsBase(BaseModel):
    """Amazing Interface"""
    label: Optional[str]
    'SUper intersting Interface field'

class LabeledEdge(FlowEdgeCommonsBase, BaseModel):
    typename: Optional[Literal['LabeledEdge']] = Field(alias='__typename')

class FancyEdge(FlowEdgeCommonsBase, BaseModel):
    typename: Optional[Literal['FancyEdge']] = Field(alias='__typename')

class FlowEdgeBase(BaseModel):
    id: str
    source: str
    source_handle: str = Field(alias='sourceHandle')
    target: str
    target_handle: str = Field(alias='targetHandle')

class FlowEdgeBaseLabeledEdge(LabeledEdge, FlowEdgeBase):
    pass

class FlowEdgeBaseFancyEdge(FancyEdge, FlowEdgeBase):
    pass
FlowEdge = Union[FlowEdgeBaseLabeledEdge, FlowEdgeBaseFancyEdge, FlowEdgeBase]

class Flow(BaseModel):
    typename: Optional[Literal['Flow']] = Field(alias='__typename')
    name: Optional[str]
    id: str
    nodes: Optional[List[Optional[FlowNode]]]
    edges: Optional[List[Optional[FlowEdge]]]

class ListFlow(BaseModel):
    typename: Optional[Literal['Flow']] = Field(alias='__typename')
    id: str
    name: Optional[str]

class Get_graph(BaseModel):
    graph: Optional[Graph]

    class Arguments(BaseModel):
        id: Optional[str] = None
        template: Optional[str] = None

    class Meta:
        document = 'fragment Graph on Graph {\n  diagram\n  id\n  template\n  name\n}\n\nquery get_graph($id: ID, $template: ID) {\n  graph(id: $id, template: $template) {\n    ...Graph\n  }\n}'

class My_graphs(BaseModel):
    mygraphs: Optional[List[Optional[ListGraph]]]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = 'fragment ListGraph on Graph {\n  id\n  name\n  template\n}\n\nquery my_graphs {\n  mygraphs {\n    ...ListGraph\n  }\n}'

class Get_flow(BaseModel):
    flow: Optional[Flow]

    class Arguments(BaseModel):
        id: Optional[str] = None

    class Meta:
        document = 'fragment FlowKwarg on FlowKwarg {\n  key\n  type\n  label\n  name\n  type\n  description\n}\n\nfragment FlowArg on FlowArg {\n  key\n  type\n  name\n  label\n  type\n  description\n}\n\nfragment FlowReturn on FlowReturn {\n  key\n  type\n  name\n  label\n  type\n  description\n}\n\nfragment FlowNodeCommons on FlowNodeCommons {\n  args {\n    __typename\n    ...FlowArg\n  }\n  kwargs {\n    __typename\n    ...FlowKwarg\n  }\n  returns {\n    __typename\n    ...FlowReturn\n  }\n}\n\nfragment FlowEdgeCommons on FlowEdgeCommons {\n  label\n}\n\nfragment ReturnNode on ReturnNode {\n  ...FlowNodeCommons\n  __typename\n  extra\n}\n\nfragment ReactiveNode on ReactiveNode {\n  ...FlowNodeCommons\n  __typename\n  implementation\n}\n\nfragment FancyEdge on FancyEdge {\n  ...FlowEdgeCommons\n  __typename\n}\n\nfragment ArgNode on ArgNode {\n  ...FlowNodeCommons\n  __typename\n  extra\n}\n\nfragment ArkitektNode on ArkitektNode {\n  ...FlowNodeCommons\n  __typename\n  name\n  description\n  package\n  interface\n  kind\n}\n\nfragment LabeledEdge on LabeledEdge {\n  ...FlowEdgeCommons\n  __typename\n}\n\nfragment KwargNode on KwargNode {\n  ...FlowNodeCommons\n  __typename\n  extra\n}\n\nfragment FlowNode on FlowNode {\n  id\n  position {\n    x\n    y\n  }\n  type: __typename\n  ...ArkitektNode\n  ...ReactiveNode\n  ...ArgNode\n  ...KwargNode\n  ...ReturnNode\n}\n\nfragment FlowEdge on FlowEdge {\n  id\n  source\n  sourceHandle\n  target\n  targetHandle\n  type: __typename\n  ...LabeledEdge\n  ...FancyEdge\n}\n\nfragment Flow on Flow {\n  __typename\n  name\n  id\n  nodes {\n    ...FlowNode\n  }\n  edges {\n    ...FlowEdge\n  }\n}\n\nquery get_flow($id: ID) {\n  flow(id: $id) {\n    ...Flow\n  }\n}'

class Graph(BaseModel):
    graph: Optional[Graph]

    class Arguments(BaseModel):
        id: Optional[str] = None
        template: Optional[str] = None

    class Meta:
        document = 'fragment Graph on Graph {\n  diagram\n  id\n  template\n  name\n}\n\nquery Graph($id: ID, $template: ID) {\n  graph(id: $id, template: $template) {\n    ...Graph\n  }\n}'

class Flow(BaseModel):
    flow: Optional[Flow]

    class Arguments(BaseModel):
        id: Optional[str] = None

    class Meta:
        document = 'fragment FlowKwarg on FlowKwarg {\n  key\n  type\n  label\n  name\n  type\n  description\n}\n\nfragment FlowArg on FlowArg {\n  key\n  type\n  name\n  label\n  type\n  description\n}\n\nfragment FlowReturn on FlowReturn {\n  key\n  type\n  name\n  label\n  type\n  description\n}\n\nfragment FlowNodeCommons on FlowNodeCommons {\n  args {\n    __typename\n    ...FlowArg\n  }\n  kwargs {\n    __typename\n    ...FlowKwarg\n  }\n  returns {\n    __typename\n    ...FlowReturn\n  }\n}\n\nfragment FlowEdgeCommons on FlowEdgeCommons {\n  label\n}\n\nfragment ReturnNode on ReturnNode {\n  ...FlowNodeCommons\n  __typename\n  extra\n}\n\nfragment ReactiveNode on ReactiveNode {\n  ...FlowNodeCommons\n  __typename\n  implementation\n}\n\nfragment FancyEdge on FancyEdge {\n  ...FlowEdgeCommons\n  __typename\n}\n\nfragment ArgNode on ArgNode {\n  ...FlowNodeCommons\n  __typename\n  extra\n}\n\nfragment ArkitektNode on ArkitektNode {\n  ...FlowNodeCommons\n  __typename\n  name\n  description\n  package\n  interface\n  kind\n}\n\nfragment LabeledEdge on LabeledEdge {\n  ...FlowEdgeCommons\n  __typename\n}\n\nfragment KwargNode on KwargNode {\n  ...FlowNodeCommons\n  __typename\n  extra\n}\n\nfragment FlowNode on FlowNode {\n  id\n  position {\n    x\n    y\n  }\n  type: __typename\n  ...ArkitektNode\n  ...ReactiveNode\n  ...ArgNode\n  ...KwargNode\n  ...ReturnNode\n}\n\nfragment FlowEdge on FlowEdge {\n  id\n  source\n  sourceHandle\n  target\n  targetHandle\n  type: __typename\n  ...LabeledEdge\n  ...FancyEdge\n}\n\nfragment Flow on Flow {\n  __typename\n  name\n  id\n  nodes {\n    ...FlowNode\n  }\n  edges {\n    ...FlowEdge\n  }\n}\n\nquery Flow($id: ID) {\n  flow(id: $id) {\n    ...Flow\n  }\n}'

class MyGraphs(BaseModel):
    mygraphs: Optional[List[Optional[ListGraph]]]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = 'fragment ListGraph on Graph {\n  id\n  name\n  template\n}\n\nquery MyGraphs {\n  mygraphs {\n    ...ListGraph\n  }\n}'

class MyFlows(BaseModel):
    myflows: Optional[List[Optional[ListFlow]]]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = 'fragment ListFlow on Flow {\n  id\n  name\n}\n\nquery MyFlows {\n  myflows {\n    ...ListFlow\n  }\n}'

class Draw(BaseModel):
    makeflow: Optional[Flow]

    class Arguments(BaseModel):
        name: str
        nodes: Optional[List[Optional[NodeInput]]] = None
        edges: Optional[List[Optional[EdgeInput]]] = None

    class Meta:
        document = 'fragment FlowKwarg on FlowKwarg {\n  key\n  type\n  label\n  name\n  type\n  description\n}\n\nfragment FlowArg on FlowArg {\n  key\n  type\n  name\n  label\n  type\n  description\n}\n\nfragment FlowReturn on FlowReturn {\n  key\n  type\n  name\n  label\n  type\n  description\n}\n\nfragment FlowNodeCommons on FlowNodeCommons {\n  args {\n    __typename\n    ...FlowArg\n  }\n  kwargs {\n    __typename\n    ...FlowKwarg\n  }\n  returns {\n    __typename\n    ...FlowReturn\n  }\n}\n\nfragment FlowEdgeCommons on FlowEdgeCommons {\n  label\n}\n\nfragment ReturnNode on ReturnNode {\n  ...FlowNodeCommons\n  __typename\n  extra\n}\n\nfragment ReactiveNode on ReactiveNode {\n  ...FlowNodeCommons\n  __typename\n  implementation\n}\n\nfragment FancyEdge on FancyEdge {\n  ...FlowEdgeCommons\n  __typename\n}\n\nfragment ArgNode on ArgNode {\n  ...FlowNodeCommons\n  __typename\n  extra\n}\n\nfragment ArkitektNode on ArkitektNode {\n  ...FlowNodeCommons\n  __typename\n  name\n  description\n  package\n  interface\n  kind\n}\n\nfragment LabeledEdge on LabeledEdge {\n  ...FlowEdgeCommons\n  __typename\n}\n\nfragment KwargNode on KwargNode {\n  ...FlowNodeCommons\n  __typename\n  extra\n}\n\nfragment FlowNode on FlowNode {\n  id\n  position {\n    x\n    y\n  }\n  type: __typename\n  ...ArkitektNode\n  ...ReactiveNode\n  ...ArgNode\n  ...KwargNode\n  ...ReturnNode\n}\n\nfragment FlowEdge on FlowEdge {\n  id\n  source\n  sourceHandle\n  target\n  targetHandle\n  type: __typename\n  ...LabeledEdge\n  ...FancyEdge\n}\n\nfragment Flow on Flow {\n  __typename\n  name\n  id\n  nodes {\n    ...FlowNode\n  }\n  edges {\n    ...FlowEdge\n  }\n}\n\nmutation draw($name: String!, $nodes: [NodeInput], $edges: [EdgeInput]) {\n  makeflow(name: $name, nodes: $nodes, edges: $edges) {\n    ...Flow\n  }\n}'

class ResetFlussReset(BaseModel):
    typename: Optional[Literal['ResetReturn']] = Field(alias='__typename')
    ok: Optional[bool]

class ResetFluss(BaseModel):
    reset: Optional[ResetFlussReset]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = 'mutation ResetFluss {\n  reset {\n    ok\n  }\n}'

def get_graph(id: Optional[str]=None, template: Optional[str]=None) -> Optional[Graph]:
    """get_graph 



Arguments:
    id (Optional[str], optional): id. 
    template (Optional[str], optional): template. 

Returns:
    Optional[Graph]"""
    return query(Get_graph, {'id': id, 'template': template}).graph

def my_graphs() -> Optional[List[Optional[ListGraph]]]:
    """my_graphs 



Arguments:

Returns:
    Optional[List[Optional[ListGraph]]]"""
    return query(My_graphs, {}).mygraphs

def get_flow(id: Optional[str]=None) -> Optional[Flow]:
    """get_flow 



Arguments:
    id (Optional[str], optional): id. 

Returns:
    Optional[Flow]"""
    return query(Get_flow, {'id': id}).flow

def graph(id: Optional[str]=None, template: Optional[str]=None) -> Optional[Graph]:
    """Graph 



Arguments:
    id (Optional[str], optional): id. 
    template (Optional[str], optional): template. 

Returns:
    Optional[Graph]"""
    return query(Graph, {'id': id, 'template': template}).graph

def flow(id: Optional[str]=None) -> Optional[Flow]:
    """Flow 



Arguments:
    id (Optional[str], optional): id. 

Returns:
    Optional[Flow]"""
    return query(Flow, {'id': id}).flow

def my_graphs() -> Optional[List[Optional[ListGraph]]]:
    """MyGraphs 



Arguments:

Returns:
    Optional[List[Optional[ListGraph]]]"""
    return query(MyGraphs, {}).mygraphs

def my_flows() -> Optional[List[Optional[ListFlow]]]:
    """MyFlows 



Arguments:

Returns:
    Optional[List[Optional[ListFlow]]]"""
    return query(MyFlows, {}).myflows

async def adraw(name: str, nodes: Optional[List[Optional[NodeInput]]]=None, edges: Optional[List[Optional[EdgeInput]]]=None) -> Optional[Flow]:
    """draw 



Arguments:
    name (str): name
    nodes (Optional[List[Optional[NodeInput]]], optional): nodes. 
    edges (Optional[List[Optional[EdgeInput]]], optional): edges. 

Returns:
    Optional[Flow]"""
    return (await query(Draw, {'name': name, 'nodes': nodes, 'edges': edges})).makeflow

async def areset_fluss() -> Optional[ResetFlussReset]:
    """ResetFluss 



Arguments:

Returns:
    Optional[ResetFlussReset]"""
    return (await query(ResetFluss, {})).reset
NodeInput.update_forward_refs()