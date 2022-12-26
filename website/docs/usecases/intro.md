---
sidebar_position: 1
sidebar_label: "Introduction"
title: "Use Cases"
---

Generally you can devide use cases for graphql code generation
into to two broad catagories

- Schema (server) generation
- Documents (client) generation

A schema generation approach takes a GraphQL schema defined in its
SDL and generates code that mimics the properties of this schema
and then allows you to define resolvers for the fields of every type
in the schema, generating the *server*-side GraphQL api.

A document generation approach takes a set of GraphQL documents (queries,
mutations, subscriptions and fragments) and generateds python code that
running on the *client* helps serializing the input for and the output of that specific query,(mutation and serialization) as received from the server.




# General Remarks

### Why and when you should NOT consider turms?

Code generation is a powerful tool in a developers toolbox, but often gets a bad reputation when applied to a non suitable situation. Situations where you should alternatives to code geneneratio include:

- When you need to generate code that is highly customized or specific to your project: Turms is designed to automate the creation of repetitive or boilerplate code, and may not be suitable for generating code that is highly customized or specific to your project. In these cases, it may be more efficient to write the code yourself.

- When you need to generate code that requires a high level of control or fine-tuning: Albeit turms provide a extensive set of options for customizing the generated code it may not offer the level of control or fine-tuning that is needed for some projects.

Overall, it is important to carefully consider your specific needs and determine whether code generation is the best solution for your project. While code generation can be a useful tool in many situations, it may not always be the most efficient or appropriate choice.


### Regard your generated as a black box

It is generally best to see generated code as a black box because it can help to reduce the coupling between your code and the generated code, making your code more modular and flexible.

By treating the generated code as a black box, you can focus on the interfaces that your code uses to interact with the generated code, rather than the specific implementation details of the generated code. This can help to decouple your code from the generated code, making it easier to change or update the generated code without affecting your code.

Additionally, seeing the generated code as a black box can help to simplify the process of understanding and maintaining your code. By not relying on the specific implementation details of the generated code, you can focus on the overall functionality of your code and how it interacts with the rest of your application.




