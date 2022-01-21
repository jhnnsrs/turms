from herre import Herre
from koil import Koil
from fakts import Fakts


class WardMeta(type):
    """ """

    def __init__(self, name, bases, attrs):
        super(WardMeta, self).__init__(name, bases, attrs)
        if attrs["__qualname__"] != "BaseWard":
            # This gets allso called for our Baseclass which is abstract
            meta = attrs["Meta"] if "Meta" in attrs else None
            assert (
                meta is not None
            ), f"Please provide a Meta class in your Arnheim Model {name}"

            try:
                if meta.abstract:
                    return
            except:
                pass

            register = getattr(meta, "register", True)

            if register:
                from herre.wards.registry import get_ward_registry

                key = getattr(meta, "domain", None)
                assert (
                    key is not None
                ), f"Please provide domain in your Meta class to register the Ward {attrs['__qualname__']}, or specifiy register=False"
                get_ward_registry().register_ward(key, self)


class BaseWard(metaclass=WardMeta):
    """Ward

    Wards are connectors between Models and there Corresponding Endpoints (Servers). They are automatically registered in a common ward registry
    so models can just specify the ward they want to use by referencing it in their Meta

    Args:
        BaseModel ([type]): [description]
        metaclass ([type], optional): [description]. Defaults to ModelMeta.

    Raises:
        NotImplementedError: [description]
        NotImplementedError: [description]

    Returns:
        [type]: [description]
    """

    id: str
    configClass = Config

    def __init__(
        self,
        *args,
        herre: Herre = None,
        koil: Koil = None,
        fakts: Fakts = None,
        max_retries=4,
        **kwargs,
    ) -> None:
        self.herre = herre or get_current_herre()
        self.koil = koil or get_current_koil()
        self.fakts = fakts or get_current_fakts()
        self.connected = False
        self.transcript = None
        self.config = None
        self.max_retries = max_retries
        super().__init__()

    @abstractmethod
    async def handle_run(self, query: BaseQuery, parsed_variables: dict, files: dict):
        raise NotImplementedError("Your Ward must overwrite run")

    @abstractmethod
    async def handle_connect(self):
        raise NotImplementedError("Your Ward must overwrite run")

    @abstractmethod
    async def handle_disconnect(self):
        raise NotImplementedError("Your Ward must overwrite run")

    async def negotiate(self):
        """Negotiation is a step before launching the first query to your backend service,
        it allows for initial configurations to be transfer
        """
        return None

    async def arun(self, query: BaseQuery, variables: dict = {}):
        assert isinstance(query, BaseQuery), "Query must be of type BaseQuery"
        if not self.connected:
            await self.aconnect()

        variables, files = await parse_variables(variables)

        return await self.handle_run(query, variables, files)

    def run(self, query: BaseQuery, variables: dict = {}):
        return koil(self.arun(query, variables))

    async def adisconnect(self):
        await self.handle_disconnect()
        self.transcript = None
        self.connected = False

    async def aconnect(self):
        if not self.fakts.loaded:
            await self.fakts.aload()

        if not self.herre.logged_in:
            await self.herre.login()

        self.config = await self.configClass.from_fakts(fakts=self.fakts)
        await self.handle_connect()
        self.connected = True
        self.transcript = await self.negotiate()

    class Meta:
        abstract = True
