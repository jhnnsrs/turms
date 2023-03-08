from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from your_library.schema import get_capsules

# Select your transport with a defined url endpoint
transport = AIOHTTPTransport(url="https://countries.trevorblades.com/")

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)


# This here is the actual query execution with turms of the schema
t = get_capsules(client)
for i in t:
    print(i.name) # Typesafe access to the data

