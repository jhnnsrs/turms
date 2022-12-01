"use strict";(self.webpackChunkwebsite=self.webpackChunkwebsite||[]).push([[677],{3905:function(e,n,t){t.d(n,{Zo:function(){return u},kt:function(){return d}});var r=t(67294);function i(e,n,t){return n in e?Object.defineProperty(e,n,{value:t,enumerable:!0,configurable:!0,writable:!0}):e[n]=t,e}function a(e,n){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);n&&(r=r.filter((function(n){return Object.getOwnPropertyDescriptor(e,n).enumerable}))),t.push.apply(t,r)}return t}function o(e){for(var n=1;n<arguments.length;n++){var t=null!=arguments[n]?arguments[n]:{};n%2?a(Object(t),!0).forEach((function(n){i(e,n,t[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):a(Object(t)).forEach((function(n){Object.defineProperty(e,n,Object.getOwnPropertyDescriptor(t,n))}))}return e}function l(e,n){if(null==e)return{};var t,r,i=function(e,n){if(null==e)return{};var t,r,i={},a=Object.keys(e);for(r=0;r<a.length;r++)t=a[r],n.indexOf(t)>=0||(i[t]=e[t]);return i}(e,n);if(Object.getOwnPropertySymbols){var a=Object.getOwnPropertySymbols(e);for(r=0;r<a.length;r++)t=a[r],n.indexOf(t)>=0||Object.prototype.propertyIsEnumerable.call(e,t)&&(i[t]=e[t])}return i}var s=r.createContext({}),p=function(e){var n=r.useContext(s),t=n;return e&&(t="function"==typeof e?e(n):o(o({},n),e)),t},u=function(e){var n=p(e.components);return r.createElement(s.Provider,{value:n},e.children)},c={inlineCode:"code",wrapper:function(e){var n=e.children;return r.createElement(r.Fragment,{},n)}},f=r.forwardRef((function(e,n){var t=e.components,i=e.mdxType,a=e.originalType,s=e.parentName,u=l(e,["components","mdxType","originalType","parentName"]),f=p(t),d=i,g=f["".concat(s,".").concat(d)]||f[d]||c[d]||a;return t?r.createElement(g,o(o({ref:n},u),{},{components:t})):r.createElement(g,o({ref:n},u))}));function d(e,n){var t=arguments,i=n&&n.mdxType;if("string"==typeof e||i){var a=t.length,o=new Array(a);o[0]=f;var l={};for(var s in n)hasOwnProperty.call(n,s)&&(l[s]=n[s]);l.originalType=e,l.mdxType="string"==typeof e?e:i,o[1]=l;for(var p=2;p<a;p++)o[p]=t[p];return r.createElement.apply(null,o)}return r.createElement.apply(null,t)}f.displayName="MDXCreateElement"},2175:function(e,n,t){t.r(n),t.d(n,{frontMatter:function(){return l},contentTitle:function(){return s},metadata:function(){return p},toc:function(){return u},default:function(){return f}});var r=t(87462),i=t(63366),a=(t(67294),t(3905)),o=["components"],l={sidebar_label:"funcs",title:"plugins.funcs"},s=void 0,p={unversionedId:"reference/plugins/funcs",id:"reference/plugins/funcs",title:"plugins.funcs",description:"get\\definitions\\for\\_onode",source:"@site/docs/reference/plugins/funcs.md",sourceDirName:"reference/plugins",slug:"/reference/plugins/funcs",permalink:"/turms/docs/reference/plugins/funcs",editUrl:"https://github.com/jhnnsrs/turms/edit/master/website/docs/reference/plugins/funcs.md",tags:[],version:"current",frontMatter:{sidebar_label:"funcs",title:"plugins.funcs"},sidebar:"tutorialSidebar",previous:{title:"fragments",permalink:"/turms/docs/reference/plugins/fragments"},next:{title:"inputs",permalink:"/turms/docs/reference/plugins/inputs"}},u=[{value:"get_definitions_for_onode",id:"get_definitions_for_onode",children:[],level:4},{value:"get_operation_class_name",id:"get_operation_class_name",children:[],level:4},{value:"get_return_type_annotation",id:"get_return_type_annotation",children:[],level:4},{value:"FuncsPlugin Objects",id:"funcsplugin-objects",children:[],level:2}],c={toc:u};function f(e){var n=e.components,t=(0,i.Z)(e,o);return(0,a.kt)("wrapper",(0,r.Z)({},c,t,{components:n,mdxType:"MDXLayout"}),(0,a.kt)("h4",{id:"get_definitions_for_onode"},"get","_","definitions","_","for","_","onode"),(0,a.kt)("pre",null,(0,a.kt)("code",{parentName:"pre",className:"language-python"},"def get_definitions_for_onode(operation_definition: OperationDefinitionNode,\n                              plugin_config: FuncsPluginConfig) -> List[Arg]\n")),(0,a.kt)("p",null,"Checks the Plugin Config if the operation definition should be included\nin the generated functions"),(0,a.kt)("p",null,(0,a.kt)("strong",{parentName:"p"},"Arguments"),":"),(0,a.kt)("ul",null,(0,a.kt)("li",{parentName:"ul"},(0,a.kt)("inlineCode",{parentName:"li"},"operation_definition")," ",(0,a.kt)("em",{parentName:"li"},"OperationDefinitionNode")," - ",(0,a.kt)("em",{parentName:"li"},"description")),(0,a.kt)("li",{parentName:"ul"},(0,a.kt)("inlineCode",{parentName:"li"},"plugin_config")," ",(0,a.kt)("em",{parentName:"li"},"FuncsPluginConfig")," - ",(0,a.kt)("em",{parentName:"li"},"description"))),(0,a.kt)("p",null,(0,a.kt)("strong",{parentName:"p"},"Returns"),":"),(0,a.kt)("ul",null,(0,a.kt)("li",{parentName:"ul"},(0,a.kt)("inlineCode",{parentName:"li"},"List[Arg]")," - ",(0,a.kt)("em",{parentName:"li"},"description"))),(0,a.kt)("h4",{id:"get_operation_class_name"},"get","_","operation","_","class","_","name"),(0,a.kt)("pre",null,(0,a.kt)("code",{parentName:"pre",className:"language-python"},"def get_operation_class_name(o: OperationDefinitionNode,\n                             registry: ClassRegistry) -> str\n")),(0,a.kt)("p",null,"Generates the name of the Operation Class for the given OperationDefinitionNode"),(0,a.kt)("p",null,(0,a.kt)("strong",{parentName:"p"},"Arguments"),":"),(0,a.kt)("ul",null,(0,a.kt)("li",{parentName:"ul"},(0,a.kt)("inlineCode",{parentName:"li"},"o")," ",(0,a.kt)("em",{parentName:"li"},"OperationDefinitionNode")," - The graphql o node"),(0,a.kt)("li",{parentName:"ul"},(0,a.kt)("inlineCode",{parentName:"li"},"registry")," ",(0,a.kt)("em",{parentName:"li"},"ClassRegistry")," - The registry (used to get the operation class name)")),(0,a.kt)("p",null,(0,a.kt)("strong",{parentName:"p"},"Raises"),":"),(0,a.kt)("ul",null,(0,a.kt)("li",{parentName:"ul"},(0,a.kt)("inlineCode",{parentName:"li"},"Exception")," - If the operation type is not supported")),(0,a.kt)("p",null,(0,a.kt)("strong",{parentName:"p"},"Returns"),":"),(0,a.kt)("ul",null,(0,a.kt)("li",{parentName:"ul"},(0,a.kt)("inlineCode",{parentName:"li"},"str")," - ",(0,a.kt)("em",{parentName:"li"},"description"))),(0,a.kt)("h4",{id:"get_return_type_annotation"},"get","_","return","_","type","_","annotation"),(0,a.kt)("pre",null,(0,a.kt)("code",{parentName:"pre",className:"language-python"},"def get_return_type_annotation(o: OperationDefinitionNode,\n                               client_schema: GraphQLSchema,\n                               registry: ClassRegistry,\n                               collapse: bool = True) -> ast.AST\n")),(0,a.kt)("p",null,"Gets the return type annotation for the given operation definition node"),(0,a.kt)("p",null,"Ulized an autocollapse feature to collapse the return type annotation if it is a single fragment,\nto not generate unnecessary classes"),(0,a.kt)("h2",{id:"funcsplugin-objects"},"FuncsPlugin Objects"),(0,a.kt)("pre",null,(0,a.kt)("code",{parentName:"pre",className:"language-python"},"class FuncsPlugin(Plugin)\n")),(0,a.kt)("p",null,"This plugin generates functions for each operation in the schema."),(0,a.kt)("p",null,"Contratry to the ",(0,a.kt)("inlineCode",{parentName:"p"},"operations")," plugin, this plugin generates real python function\nwith type annotations and docstrings according to the operation definition."),(0,a.kt)("p",null,"These functions the can be used to call a proxy function (specified through the config)\nto execute the operation."),(0,a.kt)("p",null,"You can also specify a list of extra arguments and keyword arguments that will be passed to the proxy function."),(0,a.kt)("p",null,"Please consult the examples for more information."),(0,a.kt)("p",null,(0,a.kt)("strong",{parentName:"p"},"Example"),":"),(0,a.kt)("pre",null,(0,a.kt)("code",{parentName:"pre",className:"language-python"},"\nasync def aexecute(operation: Model, variables: Dict[str, Any], client = None):\n    client = client # is the grahql client that can be passed as an extra argument (or retrieved from a contextvar)\n    x = await client.aquery(\n        operation.Meta.document, operation.Arguments(**variables).dict(by_alias=True)\n    )# is the proxy function that will be called (u can validate the variables here)\n    return operation(**x.data) # Serialize the result\n\n")),(0,a.kt)("p",null,"  Subscriptions are supported and will map to an async iterator."))}f.isMDXComponent=!0}}]);