import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

class Query(CRMQuery, graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    hi = graphene.String(default_value="hi, GraphQL!")
    pass

schema = graphene.Schema(query=Query, mutation=CRMMutation)