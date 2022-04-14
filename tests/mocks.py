

def query(model, variables):
    return model(variables)


async def aquery(model, variables):
    return model(variables)


def subscribe(model, variables):
    yield model(variables)
    yield model(variables)


async def asubscribe(model, variables):
    yield model(variables)
    yield model(variables)