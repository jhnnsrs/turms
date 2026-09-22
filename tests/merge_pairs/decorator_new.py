class Mutation:
    @strawberry.mutation()
    def createProject(self, info):
        pass

    @strawberry.mutation(description="New description")
    def createPdcVersion(self, info):
        pass

    @strawberry.field()
    def unrelatedField(self, info):
        pass
