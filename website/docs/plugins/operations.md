---
sidebar_position: 4
sidebar_label: "Operations"
---

# Operations

Operations generates python wrappers for graphql operations (Subscription, Mutation, Query)

### Default Configuration

```yaml
project:
  default:
    schema: ...
    extensions:
      turms:
        plugins:
          - type: turms.plugins.operations.OperationsPlugin
            query_bases: # List[str]
            mutation_bases: # List[str]
            subscription_bases: #List[str]
            operations_glob: # Optional[str] A specific glob only for operations
```

If not specified query_bases, mutation_bases and subscription_bases will resort to the basic
configuration object_bases.
