class Mutation:
    @strawberry.mutation(extensions=[PermissionExtension([IsAdmin()])])
    def createProject(self, info):
        return do_create(info)

    @strawberry.mutation(
        description="Old description",
        extensions=[PermissionExtension([CanMutateProject(get_project_id=_direct_project_id)])],
    )
    def createPdcVersion(self, info):
        return do_create_pdc_version(info)

    @strawberry.field()
    def unrelatedField(self, info):
        return None
