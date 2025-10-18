import graphene

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    hi = graphene.String(default_value="hi, GraphQL!")

schema = graphene.Schema(query=Query)