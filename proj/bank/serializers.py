from datetime import timedelta
from decimal import Decimal
import logging
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import *


logger = logging.getLogger('gen.srl')

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ('id', 'abbrev', 'name', 'is_active', 'created', 'modified')


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ('id', 'abbrev', 'name', 'created', 'modified')


class AccountSerializer(serializers.ModelSerializer):
    inst = serializers.PrimaryKeyRelatedField(queryset=Institution.objects.all())
    class Meta:
        model = Account
        fields = ('id', 'inst', 'acct_name', 'acct_number', 'is_active', 'memo', 'created', 'modified')


class PaytypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paytype
        fields = ('id', 'paytype', 'created', 'modified')


class IncomeSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.exclude(username=ADMIN_USER))
    source = serializers.PrimaryKeyRelatedField(queryset=Source.objects.all())

    class Meta:
        model = Income
        fields = ('id', 'user', 'source', 'date_paid', 'amount', 'is_pre_tax', 'memo', 'created', 'modified')

    def create(self, validated_data):
        """This expects the following keys in validated_data:
            created_by:str
        """
        created_by = validated_data.pop('created_by')
        instance = Income.objects.create(created_by=created_by, **validated_data)
        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'catg', 'description', 'created', 'modified')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'tag', 'created', 'modified')


class InlineLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'loc_name', 'loc_address')


#
# Seller
#
# Used by ReadSellerSerializer
class ReadPrefAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferredAccount
        fields = ('id', 'account', 'paytype', 'user')
        read_only_fields = fields

class ReadSellerSerializer(serializers.ModelSerializer):
    pref_accounts = serializers.SerializerMethodField()

    def get_pref_accounts(self, obj):
        qset = PreferredAccount.objects.filter(seller=obj).order_by('id')
        return [ReadPrefAccountSerializer(m).data for m in qset]

    class Meta:
        model = Seller
        fields = ('id','seller_name','website','is_active','memo','auto_catg','auto_tags','pref_accounts','created','modified')
        read_only_fields = fields

# Used by CreateSellerSerializer
class InlinePrefAccountSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.exclude(username=ADMIN_USER))

    class Meta:
        model = PreferredAccount
        fields = ('id', 'account', 'paytype', 'user')

class CreateSellerSerializer(serializers.ModelSerializer):
    auto_catg = serializers.PrimaryKeyRelatedField(
            queryset=Category.objects.all(),
            required=False)
    auto_tags = serializers.PrimaryKeyRelatedField(
            queryset=Tag.objects.all(),
            required=False,
            many=True)
    location = InlineLocationSerializer()
    pref_accounts = InlinePrefAccountSerializer(many=True, required=False)

    class Meta:
        model = Seller
        fields = ('id', 'seller_name', 'website', 'is_active', 'auto_catg', 'auto_tags', 'location', 'pref_accounts', 'created', 'modified')

    def create(self, validated_data):
        """Create Seller and its first Location together
        """
        with transaction.atomic():
            seller = Seller.objects.create(
                seller_name=validated_data['seller_name'],
                website=validated_data['website'],
                is_active=validated_data['is_active'],
                auto_catg=validated_data.get('auto_catg', None)
            )
            print(seller)
            # tags (required=False, so use get)
            tags = validated_data.get('auto_tags', [])
            if tags:
                seller.auto_tags.set(tags)
                print(seller.formatTags())
            # preferred accounts (required=False)
            pref_accts = validated_data.get('pref_accounts', [])
            for d in pref_accts:
                pa = PreferredAccount.objects.create(
                    seller=seller,
                    account=d['account'],
                    paytype=d['paytype'],
                    user=d['user'])
                print(pa)
            # create first location
            loc_data = validated_data.pop('location')
            loc_name = loc_data['loc_name']
            loc_address = loc_data['loc_address']
            location = Location.objects.create(
                seller=seller,
                loc_name=loc_name,
                loc_address=loc_address,
                rank=100)
            print(location)
            return seller


# This does not allow updating child locations or pref_accounts (Use their own UpdateSerializers for that).
# If tags are given, they should be all the tags, as this will do a wholesale update.
class UpdateSellerSerializer(serializers.ModelSerializer):
    auto_catg = serializers.PrimaryKeyRelatedField(
            queryset=Category.objects.all(),
            required=False)
    auto_tags = serializers.PrimaryKeyRelatedField(
            queryset=Tag.objects.all(),
            required=False,
            many=True)
    class Meta:
        model = Seller
        fields = ('id', 'seller_name', 'website', 'is_active', 'auto_catg', 'auto_tags', 'created', 'modified')


# Add new or update existing Location (seller is read_only)
class LocationSerializer(serializers.ModelSerializer):
    seller = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Location
        fields = ('id', 'seller', 'loc_name', 'loc_address', 'rank', 'created', 'modified')


# Add new or update existing pref_account (seller is read_only)
class PrefAccountSerializer(serializers.ModelSerializer):
    seller = serializers.PrimaryKeyRelatedField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.exclude(username=ADMIN_USER))
    class Meta:
        model = PreferredAccount
        fields = ('id', 'seller', 'account', 'paytype', 'user')


class OrderSerializer(serializers.ModelSerializer):
    location = serializers.PrimaryKeyRelatedField(
            queryset=Location.objects.all())
    account = serializers.PrimaryKeyRelatedField(
            queryset=Account.objects.all())
    paytype= serializers.PrimaryKeyRelatedField(
            queryset=Paytype.objects.all())
    amount = serializers.DecimalField(max_digits=7, decimal_places=2, coerce_to_string=False)
    class Meta:
        model = Order
        fields = '__all__'

#
# Expense
#

class ReadExpenseCatgSerializer(serializers.ModelSerializer):
    weight = serializers.DecimalField(max_digits=3, decimal_places=2, coerce_to_string=False)
    class Meta:
        model = ExpenseCategory
        fields = ('id', 'category', 'weight')
        read_only_fields = fields

class ReadExpenseSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=7, decimal_places=2, coerce_to_string=False)

    def get_categories(self, obj):
        qset = ExpenseCategory.objects.filter(expense=obj).order_by('id')
        return [ReadExpenseCatgSerializer(m).data for m in qset]

    class Meta:
        model = Expense
        fields = ('id',
            'location',
            'account',
            'paytype',
            'order',
            'date_paid',
            'amount',
            'memo',
            'categories',
            'tags',
            'check_no',
            'shipment_no',
            'invoiceid',
            'created_by',
            'created',
            'modified'
        )
        read_only_fields = fields

class InlineExpenseCatgSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
            queryset=Category.objects.all())
    weight = serializers.DecimalField(max_digits=3, decimal_places=2, coerce_to_string=False)
    class Meta:
        model = ExpenseCategory
        fields = ('id', 'category', 'weight')

# Complete an order and enter an expense
class ExpenseCompleteOrderSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.filter(is_complete=False, is_cancelled=False))
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    categories = InlineExpenseCatgSerializer(many=True, required=False)
    class Meta:
        model = Expense
        fields = ('id', 'order', 'date_paid', 'amount', 'memo', 'tags', 'categories')

    def create(self, validated_data):
        """This expects the following keys in validated_data:
            created_by:str
        1. Call Expense Manager method to complete the order and create the expense.
        2. Assign tags to expense if given.
        3. Call ExpenseCategory Manager method to populate the categories and weights if given.
        """
        tags = None
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
        ec = []
        if 'categories' in validated_data:
            ec = validated_data.pop('categories')
        instance = Expense.objects.completeOrder(**validated_data)
        if tags:
            instance.tags.set(tags)
        if ec:
            ExpenseCategory.objects.enterForExpense(instance, ec)
        return instance

# Complete an order shipment and enter an expense
class ExpenseCompleteShipmentSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.filter(is_complete=False, is_cancelled=False))
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    categories = InlineExpenseCatgSerializer(many=True, required=False)
    class Meta:
        model = Expense
        fields = ('id', 'order', 'date_paid', 'amount', 'memo', 'shipment_no', 'tags', 'categories')

    def create(self, validated_data):
        """This expects the following keys in validated_data:
            created_by:str
        1. Call Expense Manager method to update the order, and create
            the expense. If shipment_no == order.num_shipments, then
            the order is also marked as complete.
        2. Assign tags to expense if given.
        3. Call ExpenseCategory Manager method to populate the categories and weights if given.
        """
        tags = None
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
        ec = []
        if 'categories' in validated_data:
            ec = validated_data.pop('categories')
        instance = Expense.objects.completeShipment(**validated_data)
        if tags:
            instance.tags.set(tags)
        if ec:
            ExpenseCategory.objects.enterForExpense(instance, ec)
        return instance

# For all non-Order expenses
class CreateRegularExpenseSerializer(serializers.ModelSerializer):
    location = serializers.PrimaryKeyRelatedField(
            queryset=Location.objects.all())
    account = serializers.PrimaryKeyRelatedField(
            queryset=Account.objects.all())
    paytype= serializers.PrimaryKeyRelatedField(
            queryset=Paytype.objects.all())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    categories = InlineExpenseCatgSerializer(many=True, required=False)

    class Meta:
        model = Expense
        exclude = ('order', 'created_by')

    def create(self, validated_data):
        """This expects the following keys in validated_data:
            created_by:str
        """
        tags = None
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
        ec = []
        if 'categories' in validated_data:
            ec = validated_data.pop('categories')
        instance = Expense.objects.create(**validated_data)
        if tags:
            instance.tags.set(tags)
        if ec:
            ExpenseCategory.objects.enterForExpense(instance, ec)
        print(instance)
        return instance

# If given, tags are replaced wholesale
# Categories must be inserted/updated/deleted separately
class UpdateRegularExpenseSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    class Meta:
        model = Expense
        exclude = ('order', 'categories', 'shipment_no')

# If given, tags are replaced wholesale
# Categories must be inserted/updated/deleted separately
class UpdateOrderExpenseSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    class Meta:
        model = Expense
        fields = ('id', 'order', 'date_paid', 'amount', 'memo', 'shipment_no', 'check_no', 'tags')


# Add new or update existing EC (expense is read_only)
class ExpenseCatgSerializer(serializers.ModelSerializer):
    expense = serializers.PrimaryKeyRelatedField(read_only=True)
    weight = serializers.DecimalField(max_digits=3, decimal_places=2, coerce_to_string=False)
    class Meta:
        model = ExpenseCategory
        fields = ('id','expense', 'category', 'weight')
