---
sidebar_position: 1
sidebar_label: "Introduction"
---

# Why and when would you like to use Code generation?

Code generation is a powerful tool in a developers toolbox, but often
gets a bad reputation when applied to a non suitable situation. 


# Why does GraphQL lend it so perfectly to code generation?

GraphQL is a schema-ful API language, that provides a
single source of truth for all things API. Importantly this schema
provides type information.

# What are the main use cases for graphql code generation?

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

