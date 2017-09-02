from datetime import datetime
import logging
import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework import generics, exceptions, permissions, status, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters import rest_framework as filters
import django_filters
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, TokenHasScope
# app
from .models import *
from .serializers import *

logger = logging.getLogger('api.views')

class PingTest(APIView):
    """ping test response"""
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        context = {'success': True}
        return Response(context, status=status.HTTP_200_OK)

# Source
class SourceList(generics.ListCreateAPIView):
    queryset = Source.objects.all().order_by('id')
    serializer_class = SourceSerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

class SourceDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

# Institution
class InstitutionList(generics.ListCreateAPIView):
    queryset = Institution.objects.all().order_by('id')
    serializer_class = InstitutionSerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

class InstitutionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

# Paytype
class PaytypeList(generics.ListCreateAPIView):
    queryset = Paytype.objects.all().order_by('id')
    serializer_class = PaytypeSerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

class PaytypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Paytype.objects.all()
    serializer_class = PaytypeSerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

# Category
class CategoryList(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

# Tag
class TagList(generics.ListCreateAPIView):
    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

class TagDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

# Account
class AccountList(generics.ListCreateAPIView):
    queryset = Account.objects.all().order_by('id')
    serializer_class = AccountSerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

class AccountDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

# Income
class IncomeFilter(filters.FilterSet):
    date_paid_from = django_filters.IsoDateTimeFilter(name='date_paid', lookup_expr='gte')
    date_paid_to = django_filters.IsoDateTimeFilter(name='date_paid', lookup_expr='lte')
    class Meta:
        model = Income
        fields = ('user','source', 'date_paid_from', 'date_paid_to',)
        strict = django_filters.STRICTNESS.RETURN_NO_RESULTS

class IncomeList(generics.ListCreateAPIView):
    queryset = Income.objects.all().order_by('-date_paid')
    serializer_class = IncomeSerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)
    filter_class = IncomeFilter

    def perform_create(self, serializer, format=None):
        user = self.request.user
        instance = serializer.save(created_by=user.username)
        return instance

class IncomeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer
    #permission_classes = (permissions.IsAuthenticated, TokenHasReadWriteScope)

class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass

# Seller
class SellerFilter(filters.FilterSet):
    name__iexact = django_filters.CharFilter(name='seller_name', label='Name iexact', lookup_expr='iexact')
    name__icontains = django_filters.CharFilter(name='seller_name', label='Name icontains', lookup_expr='icontains')
    uncategorized = django_filters.BooleanFilter(name='auto_catg', lookup_expr='isnull')
    auto_tags = NumberInFilter(name='auto_tags', lookup_expr='in')

    class Meta:
        model = Seller
        fields = ('seller_name','is_active', 'auto_catg', 'name__iexact', 'name__icontains', 'uncategorized', 'auto_tags')
        strict = django_filters.STRICTNESS.RETURN_NO_RESULTS

class SellerList(generics.ListCreateAPIView):
    queryset = Seller.objects.all().order_by('id')
    filter_class = SellerFilter

    def get_serializer_class(self):
        if hasattr(self, 'request') and self.request.method not in permissions.SAFE_METHODS:
            return CreateSellerSerializer
        return ReadSellerSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        out_serializer = ReadSellerSerializer(instance)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

class SellerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Seller.objects.all()

    def get_serializer_class(self):
        if hasattr(self, 'request') and request.method not in permissions.SAFE_METHODS:
            return UpdateSellerSerializer
        return ReadSellerSerializer


class PrefAccountFilter(filters.FilterSet):
    class Meta:
        model = PreferredAccount
        fields = ('account','seller','user')
        strict = django_filters.STRICTNESS.RETURN_NO_RESULTS

class PrefAccountList(generics.ListCreateAPIView):
    queryset = PreferredAccount.objects.all().order_by('seller','id')
    serializer_class = PrefAccountSerializer
    filter_class = PrefAccountFilter

class PrefAccountDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PreferredAccount.objects.all()
    serializer_class = PrefAccountSerializer


class LocationFilter(filters.FilterSet):
    class Meta:
        model = Location
        fields = ('seller','loc_name','rank')
        strict = django_filters.STRICTNESS.RETURN_NO_RESULTS

class LocationList(generics.ListCreateAPIView):
    queryset = Location.objects.all().order_by('id')
    serializer_class = LocationSerializer
    filter_class = LocationFilter

class LocationDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class OrderFilter(filters.FilterSet):
    order_date_from = django_filters.IsoDateTimeFilter(name='order_date', lookup_expr='gte')
    order_date_to = django_filters.IsoDateTimeFilter(name='order_date', lookup_expr='lte')
    class Meta:
        model = Order
        fields = (
            'account',
            'location',
            'order_number',
            'is_complete',
            'order_date_from',
            'order_date_to'
        )
        strict = django_filters.STRICTNESS.RETURN_NO_RESULTS

class OrderList(generics.ListCreateAPIView):
    queryset = Order.objects.all().order_by('-modified')
    serializer_class = OrderSerializer
    filter_class = OrderFilter

class OrderDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

#
# Expense views
#

class ExpenseFilter(filters.FilterSet):
    date_paid_from = django_filters.IsoDateTimeFilter(name='date_paid', lookup_expr='gte')
    date_paid_to = django_filters.IsoDateTimeFilter(name='date_paid', lookup_expr='lte')
    memo__icontains = django_filters.CharFilter(name='memo', label='Memo icontains', lookup_expr='icontains')
    categories = NumberInFilter(name='categories', lookup_expr='in')
    tags = NumberInFilter(name='tags', lookup_expr='in')
    class Meta:
        model = Expense
        fields = (
            'account',
            'location',
            'paytype',
            'order',
            'date_paid_from',
            'date_paid_to',
            'check_no',
            'shipment_no',
            'invoiceid',
            'memo__icontains',
            'categories',
            'tags'
        )
        strict = django_filters.STRICTNESS.RETURN_NO_RESULTS

class ExpenseList(generics.ListCreateAPIView):
    queryset = Expense.objects.all().order_by('-created')
    filter_class = ExpenseFilter

    def get_serializer_class(self):
        if hasattr(self, 'request') and self.request.method not in permissions.SAFE_METHODS:
            return CreateRegularExpenseSerializer
        return ReadExpenseSerializer

    def perform_create(self, serializer, format=None):
        """Check that this is a regular (non-order) expense
        """
        data = self.request.data
        if 'order' in data and data['order'] is not None:
            error_msg = 'Use different endpoint to create expense from order'
            raise serializers.ValidationError(error_msg, code='order')
        else:
            user = self.request.user
            instance = serializer.save(created_by=user.username)
            return instance

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        out_serializer = ReadExpenseSerializer(instance)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

class ExpenseDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Expense.objects.all()

    def get_serializer_class(self):
        if hasattr(self, 'request') and self.request.method not in permissions.SAFE_METHODS:
            return UpdateRegularExpenseSerializer
        return ReadExpenseSerializer

    def perform_update(self, serializer, format=None):
        data = self.request.data
        if 'order' in data and data['order'] is not None:
            error_msg = 'This endpoint only allows update of a regular expense with no order ID.'
            raise serializers.ValidationError(error_msg, code='order')
        else:
            instance = serializer.save()
            return instance

    def update(self, request, *args, **kwargs):
        """After update, return updated object using ReadExpenseSerializer
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        expense = Expense.objects.get(pk=instance.pk)
        out_serializer = ReadExpenseSerializer(instance)
        return Response(out_serializer.data)


class CreateExpenseFromOrder(generics.CreateAPIView):
    """This action will complete the order and create an expense.
    """
    queryset = Expense.objects.all()
    serializer_class = ExpenseCompleteOrderSerializer

    def perform_create(self, serializer, format=None):
        data = self.request.data
        if 'order' not in data or data['order'] is None:
            error_msg = 'This endpoint expects an order to create expense from order.'
            raise serializers.ValidationError(error_msg, code='order')
        else:
            try:
                order = Order.objects.get(pk=data['order'])
                shipment_no = data.get('shipment_no', 1)
                if shipment_no > order.num_shipments:
                    error_msg = "The shipment_no cannot exceed order.num_shipments."
                    raise serializers.ValidationError(error_msg, code='shipment_no')
            except Order.DoesNotExist:
                error_msg = 'Invalid order id. Does not exist.'
                raise serializers.ValidationError(error_msg, code='order')
            else:
                user = self.request.user
                instance = serializer.save(created_by=user.username)
                return instance

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        out_serializer = ReadExpenseSerializer(instance)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

class UpdateOrderExpense(generics.UpdateAPIView):
    """This action allows updating the appropriate fields of an
    expense that was created from an order (or partial order shipment).
    """
    queryset = Expense.objects.all()
    serializer_class = UpdateOrderExpenseSerializer

    def perform_update(self, serializer, format=None):
        data = self.request.data
        if 'order' not in data or data['order'] is None:
            error_msg = 'This endpoint expects a valid order id for the expense to update.'
            raise serializers.ValidationError(error_msg, code='order')
        else:
            try:
                order = Order.objects.get(pk=data['order'])
                shipment_no = data.get('shipment_no', 1)
                if shipment_no > order.num_shipments:
                    error_msg = "The shipment_no cannot exceed order.num_shipments."
                    raise serializers.ValidationError(error_msg, code='shipment_no')
            except Order.DoesNotExist:
                error_msg = 'Invalid order id. Does not exist.'
                raise serializers.ValidationError(error_msg, code='order')
            else:
                user = self.request.user
                instance = serializer.save()
                return instance

    def update(self, request, *args, **kwargs):
        """After update, return updated object using ReadExpenseSerializer
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        expense = Expense.objects.get(pk=instance.pk)
        out_serializer = ReadExpenseSerializer(instance)
        return Response(out_serializer.data)

class CreateExpenseFromOrderShipment(generics.CreateAPIView):
    """This action will create an expense and only complete the
    order if expense.shipment_no == order.num_shipments.
    """
    queryset = Expense.objects.all()
    serializer_class = ExpenseCompleteShipmentSerializer

    def perform_create(self, serializer, format=None):
        data = self.request.data
        if 'order' not in data or data['order'] is None:
            error_msg = 'This endpoint expects an order to create expense from order shipment.'
            raise serializers.ValidationError(error_msg, code='order')
        elif 'shipment_no' not in data or data['shipment_no'] is None:
            error_msg = 'This endpoint expects a shipment_no to create expense from order shipment.'
            raise serializers.ValidationError(error_msg, code='order')
        else:
            user = self.request.user
            instance = serializer.save(created_by=user.username)
            return instance

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        out_serializer = ReadExpenseSerializer(instance)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


class ExpenseCatgFilter(filters.FilterSet):
    class Meta:
        model = ExpenseCategory
        fields = (
            'expense',
            'category',
        )
        strict = django_filters.STRICTNESS.RETURN_NO_RESULTS

class ExpenseCatgList(generics.ListCreateAPIView):
    queryset = ExpenseCategory.objects.all().order_by('id')
    serializer_class = ExpenseCatgSerializer
    filter_class = ExpenseCatgFilter

class ExpenseCatgDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCatgSerializer
