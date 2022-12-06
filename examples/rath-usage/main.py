from rath import Rath
from rath.links.aiohttp import AIOHttpLink
from your_library.schema import get_capsules


rath = Rath(link=AIOHttpLink(endpoint_url="https://countries.trevorblades.com/"))

with rath:
    # This here is the actual query execution with turms of the schema
    t = get_capsules()
    for i in t:
        print(i.name) # Typesafe access to the data

