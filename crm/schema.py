import graphene
from graphene_django import DjangoObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount")

class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_orders(self, info):
        return Order.objects.all()

# Mutations

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        try:
            customer = Customer(name=name, email=email, phone=phone)
            customer.full_clean()  # Validate
            customer.save()
            return CreateCustomer(customer=customer, message="Customer created successfully")
        except ValidationError as e:
            raise graphene.GraphQLError(str(e))
        except Exception as e:
            raise graphene.GraphQLError(f"Error creating customer: {str(e)}")

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        created = []
        errors = []
        for i, cust_data in enumerate(input):
            try:
                customer = Customer(
                    name=cust_data.name,
                    email=cust_data.email,
                    phone=getattr(cust_data, 'phone', None)
                )
                customer.full_clean()
                customer.save()
                created.append(customer)
            except Exception as e:
                errors.append(f"Customer {i+1}: {str(e)}")
        return BulkCreateCustomers(customers=created, errors=errors)

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock = graphene.Int()

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock=0):
        try:
            product = Product(name=name, price=price, stock=stock)
            product.full_clean()
            product.save()
            return CreateProduct(product=product)
        except ValidationError as e:
            raise graphene.GraphQLError(str(e))

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime()

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(pk=customer_id)
            products = Product.objects.filter(pk__in=product_ids)
            if not products.exists():
                raise graphene.GraphQLError("No valid products found")
            if len(products) != len(product_ids):
                raise graphene.GraphQLError("Some product IDs are invalid")
            order = Order(customer=customer, order_date=order_date)
            order.save()
            order.products.set(products)
            order.total_amount = sum(p.price for p in products)
            order.save()
            return CreateOrder(order=order)
        except Customer.DoesNotExist:
            raise graphene.GraphQLError("Customer not found")
        except Exception as e:
            raise graphene.GraphQLError(str(e))

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()