from django.contrib import admin
from django.db.models import Count
from .models import *

class SourceAdmin(admin.ModelAdmin):
    list_display = ('id','abbrev','is_active', 'name')

class IncomeAdmin(admin.ModelAdmin):
    list_display = ('id','user','source','date_paid','amount','is_pre_tax', 'adjustedAmount')
    list_filter = ('user','source')
    list_select_related = True
    date_hierarchy = 'date_paid'


class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('id','abbrev', 'name')

class AccountAdmin(admin.ModelAdmin):
    list_display = ('id','inst', 'acct_name', 'acct_number', 'is_active','memo')
    list_filter = ('inst','is_active')
    list_select_related = True


class PaytypeAdmin(admin.ModelAdmin):
    list_display =  ('id','paytype')

class LocationInline(admin.TabularInline):
    model = Location
    fields = ('loc_name','loc_address')
    extra = 1

class PrefAccountInline(admin.TabularInline):
    model = PreferredAccount
    extra = 1

class SellerAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller_name', 'auto_catg', 'formatTags')
    list_filter = ('is_active',)
    filter_horizontal = ('auto_tags',)
    list_select_related = True
    inlines = [
        LocationInline,
        PrefAccountInline,
    ]

    def get_queryset(self, request):
        qs = super(SellerAdmin, self).get_queryset(request)
        return qs.prefetch_related('auto_tags')

class LocationAdmin(admin.ModelAdmin):
    list_display = ('id','seller', 'loc_name', 'rank', 'loc_address')
    list_select_related = True

class CategoryAdmin(admin.ModelAdmin):
    list_display =  ('id','catg','description')

class TagAdmin(admin.ModelAdmin):
    list_display =  ('id','tag')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','location','order_date', 'order_number', 'account','paytype', 'amount', 'is_complete', 'num_shipments', 'memo')
    list_filter = ('is_complete', 'account')
    list_select_related = True
    search_fields = ('=order_number', 'memo')
    radio_fields = {'paytype': admin.VERTICAL}
    date_hierarchy = 'order_date'

class ExpenseCatgInline(admin.TabularInline):
    model = ExpenseCategory

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id','location','date_paid','account','paytype','amount','isOrder','memo')
    list_filter = ('account','paytype')
    filter_horizontal = ('tags',)
    search_fields = ('memo',)
    radio_fields = {'paytype': admin.VERTICAL}
    ordering = ('-created',)
    inlines = [
        ExpenseCatgInline,
    ]
    list_select_related = True
    date_hierarchy = 'date_paid'


# register models
admin.site.register(Source, SourceAdmin)
admin.site.register(Income, IncomeAdmin)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Paytype, PaytypeAdmin)
admin.site.register(Seller, SellerAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Expense, ExpenseAdmin)

