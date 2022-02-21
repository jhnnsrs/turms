---
sidebar_position: 1
sidebar_label: "Operations"
---

# Design

Rath is structured around links and their orchestration

```mermaid
flowchart LR;
    id0(Query)-->|Request|id1(Rath Client)
    id1(Rath Client)-->|Operation|id2(Continuation Link)
    id2(Continuation Link)-->|Operation|id3(Terminating Link)
```

### Terminating Links

Terminating Links make network requests to the underlying graphql
endpoint.

### Continuation Links

Continuation Links take requests in form of operations and
alter the request or introduce logic before a underlying request to
the endpoint.

As an example an Auth link

```mermaid
sequenceDiagram
    autonumber
    participant Rath
    participant AuthLink
    participant TerminationLink
    Rath->>AuthLink: Operation
    AuthLink->>AuthLink: Get Token
    AuthLink-->>TerminationLink: Operation + Token
    TerminationLink -->> AuthLink: Result
    AuthLink -->> Rath: Result
```

The authlink can then on further store the auth token and append it to
the operation.
They can also handle complex failures

```mermaid
sequenceDiagram
    autonumber
    participant Rath
    participant AuthLink
    participant TerminationLink
    Rath->>AuthLink: Operation
    AuthLink-->>TerminationLink: Operation + Token
    TerminationLink--XAuthLink: Error
    AuthLink->>AuthLink: Refech Token
    AuthLink-->>TerminationLink: Operation + Refreshed Token
    TerminationLink -->> AuthLink: Result
    AuthLink -->> Rath: Result
```
