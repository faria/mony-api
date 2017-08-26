from django.db import models
import logging
from datetime import datetime
from decimal import Decimal
import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Prefetch, Count, Sum
from django.utils import timezone

logger = logging.getLogger('gen.models')

TAX_ADJUSTED_PCT = 0.7
ADMIN_USER= 'admin'


class Source(models.Model):
    name = models.CharField(max_length=100, unique=True)
    abbrev = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.abbrev

class Income(models.Model):
    user = models.ForeignKey(
        User,
        db_index=True,
        related_name='incomes',
        on_delete=models.CASCADE
    )
    source = models.ForeignKey(
        Source,
        db_index=True,
        related_name='incomes',
        on_delete=models.CASCADE
    )
    date_paid = models.DateTimeField()
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    is_pre_tax = models.BooleanField(default=False)
    memo = models.TextField(blank=True, default='')
    created_by = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{0.user}|{0.source}|{1}'.format(self, timezone.localtime(self.date_paid))

    def adjustedAmount(self):
        if self.is_pre_tax:
            return self.amount * Decimal(str(TAX_ADJUSTED_PCT))
        return self.amount
    adjustedAmount.short_description='AdjustedAmount'

    class Meta:
        unique_together = ('user', 'source', 'date_paid')
        ordering = ['-date_paid',]

class Institution(models.Model):
    name = models.CharField(max_length=100, unique=True)
    abbrev = models.CharField(max_length=20, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.abbrev

class Account(models.Model):
    inst = models.ForeignKey(
        Institution,
        db_index=True,
        related_name='accounts',
        on_delete=models.CASCADE,
        help_text='Institution'
    )
    acct_name = models.CharField(max_length=80)
    acct_number = models.CharField(max_length=60)
    is_active = models.BooleanField(default=True)
    memo = models.TextField(blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def last4(self):
        return self.acct_number[-4:]

    def __str__(self):
        return '{0.acct_name}/{0.inst}/{1}'.format(self, self.last4())

    class Meta:
        unique_together = ('inst','acct_number')


class Paytype(models.Model):
    paytype = models.CharField(max_length=20, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.paytype


class Category(models.Model):
    catg = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.catg

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['catg',]


class Tag(models.Model):
    tag = models.CharField(max_length=20, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tag

    class Meta:
        ordering = ['tag',]


class Seller(models.Model):
    seller_name = models.CharField(max_length=60, unique=True)
    website = models.URLField(max_length=1000, blank=True, help_text='Link to website of seller')
    is_active = models.BooleanField(default=True)
    memo = models.TextField(blank=True, default='')
    auto_catg = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        db_index=True,
        related_name='sellers',
        on_delete=models.CASCADE,
        help_text='Automatic category to apply to an expense.'
    )
    auto_tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='sellers',
        help_text='Automatic tags to apply to an expense'
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.seller_name

    def formatTags(self):
        return ", ".join([t.tag for t in self.auto_tags.all()])
    formatTags.short_description = "autoTags"

    class Meta:
        ordering = ['seller_name',]

# This is used to pre-populate the account/paytype fields in an expense form for a given seller and logged-in user.
class PreferredAccount(models.Model):
    seller = models.ForeignKey(Seller, db_index=True, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, db_index=True, on_delete=models.CASCADE)
    paytype = models.ForeignKey(Paytype, db_index=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)

    def __str__(self):
        return '{0.user}|{0.account.acct_name}|{0.paytype}|{0.seller}'.format(self)

    class Meta:
        unique_together = ('account', 'seller', 'user')

class Location(models.Model):
    seller = models.ForeignKey(
        Seller,
        db_index=True,
        related_name='locations',
        on_delete=models.CASCADE
    )
    loc_name = models.CharField(max_length=60)
    lat = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    loc_address = models.CharField(max_length=100, blank=True)
    rank = models.PositiveIntegerField(default=100)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{0.seller} @{0.loc_name}'.format(self)

    class Meta:
        unique_together = ('seller','loc_name')
        ordering = ['rank','seller','loc_name']

class Order(models.Model):
    location = models.ForeignKey(
        Location,
        db_index=True,
        related_name='orders',
        on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        Account,
        db_index=True,
        related_name='orders',
        on_delete=models.CASCADE
    )
    paytype = models.ForeignKey(
        Paytype,
        db_index=True,
        related_name='orders',
        on_delete=models.CASCADE
    )
    order_number = models.CharField(max_length=64)
    order_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    is_complete = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    num_shipments = models.PositiveSmallIntegerField(default=1, blank=True)
    memo = models.TextField(blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_number

    class Meta:
        unique_together = ('location', 'order_number')
        ordering = ['-modified',]


class ExpenseManager(models.Manager):

    def completeOrder(self, order, date_paid, created_by, amount=None, memo=None):
        """Create an expense from an order and complete the order in a transaction
        Args:
            order: incomplete Order instance (single shipment)
            date_paid: Datetime
            created_by: str
            amount: Decimal/None. If None, use order.amount
            memo: str/None. If None use order.memo
        Returns: Expense instance
        """
        if not order.is_complete:
            if not amount:
                amount = order.amount
            if not memo:
                memo = order.memo
            with transaction.atomic():
                expense = self.model.objects.create(
                    location=order.location,
                    account=order.account,
                    paytype=order.paytype,
                    order=order,
                    date_paid=date_paid,
                    amount=amount,
                    memo=memo,
                    created_by=created_by
                )
                order.is_complete = True
                order.save()
            return expense
        else:
            raise ValueError('Order is already complete')


    def completeShipment(self, order, date_paid, created_by, amount, memo, shipment_no):
        """Create an expense with a shipment_no for an order with multiple shipments
        Args:
            order: incomplete Order instance (multiple shipments)
            date_paid: Datetime
            created_by: str
            amount: Decimal - amount for this shipment
            memo: str
        """
        if order.is_complete:
            raise ValueError('Order is already complete')
            return
        if order.num_shipments < 2:
            raise ValueError('Order does not have multiple shipments.')
            return
        if shipment_no > order.num_shipments:
            raise ValueError('Shipment_no must be less than or equal to order.num_shipments.')
            return
        if amount > order.amount:
            raise ValueError('Expense amount for shipment cannot be greater than order.amount.')
            return
        with transaction.atomic():
            expense = self.model.objects.create(
                location=order.location,
                account=order.account,
                paytype=order.paytype,
                order=order,
                date_paid=date_paid,
                amount=amount,
                shipment_no=shipment_no,
                memo=memo,
                created_by=created_by
            )
            if order.expenses.all().count() == order.num_shipments:
                print('completeShipment: order is complete')
                order.is_complete = True
                order.save()
        return expense


class Expense(models.Model):
    location = models.ForeignKey(
        Location,
        db_index=True,
        related_name='expenses',
        on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        Account,
        db_index=True,
        related_name='expenses',
        on_delete=models.CASCADE
    )
    paytype = models.ForeignKey(
        Paytype,
        db_index=True,
        related_name='expenses',
        on_delete=models.CASCADE
    )
    order = models.ForeignKey(
        Order,
        blank=True,
        null=True,
        db_index=True,
        related_name='expenses',
        on_delete=models.CASCADE
    )
    date_paid = models.DateTimeField()
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    memo = models.TextField(blank=True, default='')
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='expenses',
        through='ExpenseCategory'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='expenses')
    check_no = models.PositiveSmallIntegerField(null=True, blank=True, default=None,
            help_text='Check number if paid via personal check.')
    shipment_no = models.PositiveSmallIntegerField(null=True, blank=True, default=None,
            help_text='Shipment number if order has multiple shipments.')
    invoiceid = models.CharField(max_length=32, blank=True, default='',
            help_text='Used to track OrderId for expenses without creating an order')
    created_by = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    objects = ExpenseManager()

    def __str__(self):
        #return '{0.location}/{0.date_paid:%Y-%m-%d}'.format(self)
        return "{0.location}|{0.account}|{0.paytype}|{0.date_paid:%Y-%m-%d}|${0.amount}|{0.memo}".format(self)

    def isOrder(self):
        return self.order is not None
    isOrder.short_description = 'Is Order'

    def formatTags(self):
        return ", ".join([t.tag for t in self.tags.all()])
    formatTags.short_description = "tags"

    class Meta:
        ordering = ['-created',]


# Expense-Category association
class ExpenseCategoryManager(models.Manager):
    def enterForExpense(self, expense, data):
        """Enter the full set of weights (whose sum must be <= 1) for a given expense.
        Note: sum < 1 is permitted to allow for partial entry.
        Args:
            expense: Expense object
            data: list of dicts [{category:Category, weight:Decimal}]
        """
        wt = sum([d['weight'] for d in data])
        if wt > 1:
            raise ValueError('enterForExpense: sum of category weights cannot exceed 1.0')
            return
        for d in data:
            catg = d['category']
            weight = d['weight']
            ec = self.model.objects.create(expense=expense, category=catg, weight=weight)


class ExpenseCategory(models.Model):
    expense = models.ForeignKey(Expense, db_index=True, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, db_index=True, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=3, decimal_places=2)
    objects = ExpenseCategoryManager()

    def __str__(self):
        return str(self.weight)

    class Meta:
        verbose_name_plural = 'ExpenseCategories'
        unique_together = ('expense', 'category')
        ordering = ['expense','weight']
