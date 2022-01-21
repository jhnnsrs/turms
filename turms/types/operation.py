from pydantic.main import BaseModel, ModelMetaclass


class OperationMeta(ModelMetaclass):
    """
    The Model Meta class extends the Pydantic Metaclass and adds in
    syncrhonous and asynchronous Managers. These Managers allow direct
    interaction with serverside Objects mimicking the Django ORM Scheme
    (https://docs.djangoproject.com/en/3.2/topics/db/queries/) it
    also registeres the Model as a potential serializer.

    Every Class using this metaclass has to subclass pydantic.BaseModel and
    implement a Meta class with the identifier attribute set to a cleartext
    identifier on the arkitekt platform.

    If this identifier does not exist, the serializer can potentially be auto
    registered with the platform according to the apps name

    Args:
        ModelMetaclass ([type]): [description]
    """

    def __new__(mcls, name, bases, attrs):
        slots = set(
            attrs.pop("__slots__", tuple())
        )  # The slots from: https://github.com/samuelcolvin/pydantic/issues/655#issuecomment-610900376
        for base in bases:
            if hasattr(base, "__slots__"):
                slots.update(base.__slots__)

        if "__dict__" in slots:
            slots.remove("__dict__")
        attrs["__slots__"] = tuple(slots)

        return super(OperationMeta, mcls).__new__(mcls, name, bases, attrs)

    @property
    def get_meta(cls):
        return cls.__meta

    def __init__(self, name, bases, attrs):
        super(OperationMeta, self).__init__(name, bases, attrs)
        if attrs["__qualname__"] not in "Operation":
            # This gets allso called for our Baseclass which is abstract
            self.__meta = attrs["Meta"] if "Meta" in attrs else None
            assert (
                self.__meta is not None
            ), f"Please provide a Meta class in your Query Model {name}"

            try:
                if self.__meta.abstract:
                    return
            except:
                pass

            assert hasattr(
                self.__meta, "domain"
            ), f"Please specifiy which Ward this Model should use in Meta of  {attrs['__qualname__']}"

            assert hasattr(
                self.__meta, "document"
            ), f"Please specifiy the document to use for this Operation in Meta document"


class GraphQLOperation(BaseModel, metaclass=OperationMeta):
    @classmethod
    def execute(cls, variables):
        raise NotImplementedError()

    @classmethod
    async def aexecute(cls, variables):
        raise NotImplementedError()

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
