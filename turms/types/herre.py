from pydantic import BaseModel, ValidationError
from herre.wards.graphql import GraphQLWard
from koil import koil, get_current_koil
from turms.types.operation import OperationMeta
from herre.wards.registry import get_ward_registry


class OperationExpansionError(Exception):
    pass


class GraphQLOperation(BaseModel, metaclass=OperationMeta):
    @classmethod
    def execute(cls, variables):
        return koil(cls.aexecute(variables))

    @classmethod
    async def aexecute(cls, variables):
        x = get_ward_registry().get_ward_instance(cls.get_meta().domain)
        data = await x.arun(cls.get_meta().document, variables)
        try:
            return cls(**data)
        except ValidationError as e:
            raise OperationExpansionError(
                f"Could not expand {data} to {cls.__name__}"
            ) from e

    class Meta:
        abstract = True


class GraphQLQuery(GraphQLOperation):
    class Meta:
        abstract = True


class GraphQLMutation(GraphQLOperation):
    class Meta:
        abstract = True


class GraphQLSubscription(GraphQLOperation):
    class Meta:
        abstract = True
