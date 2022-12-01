"use strict";(self.webpackChunkwebsite=self.webpackChunkwebsite||[]).push([[6410],{3905:function(e,t,n){n.d(t,{Zo:function(){return m},kt:function(){return d}});var r=n(67294);function a(e,t,n){return t in e?Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[t]=n,e}function i(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),n.push.apply(n,r)}return n}function l(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{};t%2?i(Object(n),!0).forEach((function(t){a(e,t,n[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):i(Object(n)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))}))}return e}function o(e,t){if(null==e)return{};var n,r,a=function(e,t){if(null==e)return{};var n,r,a={},i=Object.keys(e);for(r=0;r<i.length;r++)n=i[r],t.indexOf(n)>=0||(a[n]=e[n]);return a}(e,t);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);for(r=0;r<i.length;r++)n=i[r],t.indexOf(n)>=0||Object.prototype.propertyIsEnumerable.call(e,n)&&(a[n]=e[n])}return a}var p=r.createContext({}),s=function(e){var t=r.useContext(p),n=t;return e&&(n="function"==typeof e?e(t):l(l({},t),e)),n},m=function(e){var t=s(e.components);return r.createElement(p.Provider,{value:t},e.children)},u={inlineCode:"code",wrapper:function(e){var t=e.children;return r.createElement(r.Fragment,{},t)}},c=r.forwardRef((function(e,t){var n=e.components,a=e.mdxType,i=e.originalType,p=e.parentName,m=o(e,["components","mdxType","originalType","parentName"]),c=s(n),d=a,k=c["".concat(p,".").concat(d)]||c[d]||u[d]||i;return n?r.createElement(k,l(l({ref:t},m),{},{components:n})):r.createElement(k,l({ref:t},m))}));function d(e,t){var n=arguments,a=t&&t.mdxType;if("string"==typeof e||a){var i=n.length,l=new Array(i);l[0]=c;var o={};for(var p in t)hasOwnProperty.call(t,p)&&(o[p]=t[p]);o.originalType=e,o.mdxType="string"==typeof e?e:a,l[1]=o;for(var s=2;s<i;s++)l[s]=n[s];return r.createElement.apply(null,l)}return r.createElement.apply(null,n)}c.displayName="MDXCreateElement"},84065:function(e,t,n){n.r(t),n.d(t,{frontMatter:function(){return o},contentTitle:function(){return p},metadata:function(){return s},toc:function(){return m},default:function(){return c}});var r=n(87462),a=n(63366),i=(n(67294),n(3905)),l=["components"],o={sidebar_label:"recurse",title:"recurse"},p=void 0,s={unversionedId:"reference/recurse",id:"reference/recurse",title:"recurse",description:"recurse\\_annotation",source:"@site/docs/reference/recurse.md",sourceDirName:"reference",slug:"/reference/recurse",permalink:"/turms/docs/reference/recurse",editUrl:"https://github.com/jhnnsrs/turms/edit/master/website/docs/reference/recurse.md",tags:[],version:"current",frontMatter:{sidebar_label:"recurse",title:"recurse"},sidebar:"tutorialSidebar",previous:{title:"mocks",permalink:"/turms/docs/reference/mocks"},next:{title:"registry",permalink:"/turms/docs/reference/registry"}},m=[{value:"recurse_annotation",id:"recurse_annotation",children:[],level:4},{value:"type_field_node",id:"type_field_node",children:[],level:4}],u={toc:m};function c(e){var t=e.components,n=(0,a.Z)(e,l);return(0,i.kt)("wrapper",(0,r.Z)({},u,n,{components:t,mdxType:"MDXLayout"}),(0,i.kt)("h4",{id:"recurse_annotation"},"recurse","_","annotation"),(0,i.kt)("pre",null,(0,i.kt)("code",{parentName:"pre",className:"language-python"},"def recurse_annotation(node: FieldNode,\n                       parent: str,\n                       type: GraphQLType,\n                       client_schema: GraphQLSchema,\n                       config: GeneratorConfig,\n                       subtree: ast.AST,\n                       registry: ClassRegistry,\n                       is_optional=True) -> ast.AST\n")),(0,i.kt)("p",null,"Recurse Annotations"),(0,i.kt)("p",null,"Resolves the type of a field and returns the appropriate annotation.\nIf we deal with nested object types it recurses further and generated the objects\ntogether with the type_field_node method:"),(0,i.kt)("p",null,"class X(BaseModel):\na: int"),(0,i.kt)("p",null,"in this case ",'"',"a",'"'," is generated by type_field_node and ",'"',"X",'"'," is generated by recurse_annotation"),(0,i.kt)("p",null,(0,i.kt)("strong",{parentName:"p"},"Arguments"),":"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"node")," ",(0,i.kt)("em",{parentName:"li"},"FieldNode")," - The node"),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"type")," ",(0,i.kt)("em",{parentName:"li"},"GraphQLType")," - The type of the field as specified in the schema"),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"client_schema")," ",(0,i.kt)("em",{parentName:"li"},"GraphQLSchema")," - The schema itself"),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"config")," ",(0,i.kt)("em",{parentName:"li"},"GeneratorConfig")," - The generator config (with the defaults)"),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"subtree")," ",(0,i.kt)("em",{parentName:"li"},"ast.AST")," - The passed subtree"),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"registry")," ",(0,i.kt)("em",{parentName:"li"},"ClassRegistry")," - A class registry where classes and their imports are registered"),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"parent_name")," ",(0,i.kt)("em",{parentName:"li"},"str, optional")," - If resolving nested types the name of parent. Defaults to ",'"','"',"."),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"is_optional")," ",(0,i.kt)("em",{parentName:"li"},"bool, optional")," - A recurse modifier for optional types. Defaults to True.")),(0,i.kt)("p",null,(0,i.kt)("strong",{parentName:"p"},"Raises"),":"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"NotImplementedError")," - Not implemneted errors"),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"NotImplementedError")," - ",(0,i.kt)("em",{parentName:"li"},"description"))),(0,i.kt)("p",null,(0,i.kt)("strong",{parentName:"p"},"Returns"),":"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"ast.AST")," - The returned tree")),(0,i.kt)("h4",{id:"type_field_node"},"type","_","field","_","node"),(0,i.kt)("pre",null,(0,i.kt)("code",{parentName:"pre",className:"language-python"},"def type_field_node(node: FieldNode,\n                    parent: str,\n                    field: GraphQLField,\n                    client_schema: GraphQLSchema,\n                    config: GeneratorConfig,\n                    subtree: ast.AST,\n                    registry: ClassRegistry,\n                    is_optional=True)\n")),(0,i.kt)("p",null,"Types a field node"),(0,i.kt)("p",null,"This"),(0,i.kt)("p",null,(0,i.kt)("strong",{parentName:"p"},"Arguments"),":"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"node")," ",(0,i.kt)("em",{parentName:"li"},"FieldNode")," - ",(0,i.kt)("em",{parentName:"li"},"description")),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"field")," ",(0,i.kt)("em",{parentName:"li"},"GraphQLField")," - ",(0,i.kt)("em",{parentName:"li"},"description")),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"client_schema")," ",(0,i.kt)("em",{parentName:"li"},"GraphQLSchema")," - ",(0,i.kt)("em",{parentName:"li"},"description")),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"config")," ",(0,i.kt)("em",{parentName:"li"},"GeneratorConfig")," - ",(0,i.kt)("em",{parentName:"li"},"description")),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"subtree")," ",(0,i.kt)("em",{parentName:"li"},"ast.AST")," - ",(0,i.kt)("em",{parentName:"li"},"description")),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"registry")," ",(0,i.kt)("em",{parentName:"li"},"ClassRegistry")," - ",(0,i.kt)("em",{parentName:"li"},"description")),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"parent_name")," ",(0,i.kt)("em",{parentName:"li"},"str, optional")," - ",(0,i.kt)("em",{parentName:"li"},"description"),". Defaults to ",'"','"',"."),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"is_optional")," ",(0,i.kt)("em",{parentName:"li"},"bool, optional")," - ",(0,i.kt)("em",{parentName:"li"},"description"),". Defaults to True.")),(0,i.kt)("p",null,(0,i.kt)("strong",{parentName:"p"},"Returns"),":"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("inlineCode",{parentName:"li"},"_type_")," - ",(0,i.kt)("em",{parentName:"li"},"description"))))}c.isMDXComponent=!0}}]);