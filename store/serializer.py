from django.utils.text import slugify
from django.db import transaction
from rest_framework import serializers
from decimal import Decimal

from .models import Cart, CartItem, Category, Comment, Customer, Order, OrderItem, Product


class CategorySerializer(serializers.ModelSerializer):
    num_products = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'title', 'description', 'num_products']
        read_only_fields = ['id', 'num_products']

    def get_num_products(self, category):
        return category.product_count if hasattr(category, 'product_count') else 0

class ProductSerializer(serializers.ModelSerializer):
    # id = serializers.IntegerField()
    title = serializers.CharField(max_length=255, source='name')
    price = serializers.DecimalField(max_digits=6 ,decimal_places=2, source='unit_price')
    unit_price_after_tax = serializers.SerializerMethodField(method_name='calculate_tax')
    # inventory = serializers.IntegerField()

    # category = serializers.PrimaryKeyRelatedField(
    #     queryset = Category.objects.all()
    # )
    # category = serializers.StringRelatedField() #or :
    # # category = CategorySerializer() or
    # category = serializers.HyperlinkedRelatedField(
    #     queryset = Category.objects.all(),
    #     view_name='category-detail',
    # )
    
    class Meta:
        model = Product
        fields = ['id','title','price','unit_price_after_tax', 'category','inventory','description']
        read_only_fields = ['id',]

    def calculate_tax(self, product):
        return round(product.unit_price * Decimal(1.10), 2)

    def validate(self, data):
        if len(data['name']) < 6:
            raise serializers.ValidationError('Product title length should be at least 6.')
        return data
    
    def create(self, validated_data):
        product = Product(**validated_data)
        product.slug = slugify(product.name)
        product.save()
        return product
    
    # def update(self, instance:Product, validated_data:dict):
    #     instance.inventory = validated_data.get('inventory')
    #     instance.save()
    #     return instance
    

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'name', 'body', ]

    def create(self, validated_data):
        product_id = self.context['product_pk']
        return Comment.objects.create(product_id=product_id, **validated_data)


class CartProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id','name','unit_price', ]


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']


class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id','product', 'quantity', ]

    def create(self, validated_data):
        cart_id = self.context['cart_pk']

        product = validated_data.get('product')
        quantity = validated_data.get('quantity')

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product.id) 
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(cart_id=cart_id, **validated_data)
        
        self.instance = cart_item
        return cart_item


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer()
    item_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product','quantity', 'item_total', ]

    def get_item_total(self, cart_item:CartItem):
        return cart_item.quantity * cart_item.product.unit_price


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price',]
        read_only_fields = ['id', ]
    
    def get_total_price(self, cart:Cart):
        return sum(item.quantity * item.product.unit_price for item in cart.items.all())
    

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'user', 'birth_date',]
        read_only_fields = ['user', ]


class OrderCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'full_name', 'first_name', 'last_name', 'email', 'birth_date',]
        read_only_fields = ['user', ]


class OrderItemProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id','name','unit_price', ]


class OrderItemSerializer(serializers.ModelSerializer):
    product = OrderItemProductSerializer()
    # item_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product','quantity',]# 'item_total', ]

    # def get_item_total(self, order_item:OrderItem):
    #     return order_item.quantity * order_item.product.unit_price


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    # total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'status', 'datetime_created', 'items', ]
        read_only_fields = ['id', ]
    
    # def get_total_price(self, cart:Cart):
    #     return sum(item.quantity * item.product.unit_price for item in cart.items.all())


class OrderForAdminSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer = OrderCustomerSerializer()
    # total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'status', 'datetime_created', 'items', ]
        read_only_fields = ['id', ]
    
    # def get_total_price(self, cart:Cart):
    #     return sum(item.quantity * item.product.unit_price for item in cart.items.all())


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']


class OrderCreateSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        # both method have 2 query 

        # try:
        #     if Cart.objects.prefetch_related('items').get(id=cart_id).items.count() == 0:
        #         raise serializers.ValidationError('Your cart is empty. Please add some products to it first')
        # except Cart.DoesNotExist:
        #         raise serializers.ValidationError('There is no cart with this card id!')
        
        if not Cart.objects.filter(id=cart_id):
            raise serializers.ValidationError('There is no cart with this card id!')
        
        if CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError('Your cart is empty. Please add some products to it first')

        return cart_id
    
    @transaction.atomic
    def save(self, **kwargs):
        cart_id = self.validated_data['cart_id']
        user_id = self.context['user_id']
        customer = Customer.objects.filter(user_id=user_id)

        order = Order()
        order.customer = customer
        order.save()

        cart_items = CartItem.objects.select_related('product').filter(cart_id=cart_id)


        order_items = [
            OrderItem(
                order=order,
                product=cart_item.product,
                unit_price =cart_item.product.unit_price,
                quantity=cart_item.quantity,
            ) for cart_item in cart_items
        ]    
        # order_items = list()
        # for cart_item in cart_items:
        #     order_item = OrderItem()
        #     order_item.order = order
        #     order_item.product_id = cart_item.product_id
        #     order_item.unit_price = cart_item.product.unit_price
        #     order_item.quantity = cart_item.quantity

        #     order_items.append(order_item)
        
        OrderItem.objects.bulk_create(order_items)

        Cart.objects.filter(pk=cart_id).delete()

        return order