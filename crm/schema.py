import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")
        interfaces = (graphene.relay.Node,)

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        interfaces = (graphene.relay.Node,)

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount")
        interfaces = (graphene.relay.Node,)

class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter, order_by=graphene.List(graphene.String))
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter, order_by=graphene.List(graphene.String))
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter, order_by=graphene.List(graphene.String))

    # Keep the old ones for backward compatibility or remove if not needed
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

class UpdateLowStockProducts(graphene.Mutation):
    """
    Mutation to update low-stock products (stock < 10).
    Increments stock by 10 for each product and returns updated products.
    """
    class Arguments:
        pass

    updated_products = graphene.List(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info):
        try:
            # Query products with stock < 10
            low_stock_products = Product.objects.filter(stock__lt=10)
            
            if not low_stock_products.exists():
                return UpdateLowStockProducts(
                    updated_products=[],
                    success=True,
                    message="No products with low stock found"
                )
            
            # Increment stock by 10 for each product
            updated_products = []
            for product in low_stock_products:
                product.stock += 10
                product.full_clean()
                product.save()
                updated_products.append(product)
            
            return UpdateLowStockProducts(
                updated_products=updated_products,
                success=True,
                message=f"Successfully updated {len(updated_products)} products"
            )
        except Exception as e:
            raise graphene.GraphQLError(f"Error updating low stock products: {str(e)}")

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()