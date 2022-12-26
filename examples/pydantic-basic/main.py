from rath import Rath
from rath.links.aiohttp import AIOHttpLink
from your_library.schema import Get_countries, CountryFilterInput, StringQueryOperatorInput


rath = Rath(link=AIOHttpLink(endpoint_url="https://countries.trevorblades.com/"))

with rath:
    # This here is the actual query execution with turms of the schema
    t = rath.query(Get_countries.Meta.document, Get_countries.Arguments(filter=CountryFilterInput(code=StringQueryOperatorInput(eq="DE")))))
    countries = Get_countries(**t.data)

    for i in countries.countries:
        print(i.name)
