"""moneysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from bank import views

api_patterns = [
    # ping test
    url(r'^ping/?$', views.PingTest.as_view(), name='ping-pong'),
    url(r'^source/?$', views.SourceList.as_view()),
    url(r'^source/(?P<pk>[0-9]+)/?$', views.SourceDetail.as_view()),
    url(r'^income/?$', views.IncomeList.as_view()),
    url(r'^income/(?P<pk>[0-9]+)/?$', views.IncomeDetail.as_view()),
    url(r'^institution/?$', views.InstitutionList.as_view()),
    url(r'^institution/(?P<pk>[0-9]+)/?$', views.InstitutionDetail.as_view()),
    url(r'^account/?$', views.AccountList.as_view()),
    url(r'^account/(?P<pk>[0-9]+)/?$', views.AccountDetail.as_view()),
    url(r'^paytype/?$', views.PaytypeList.as_view()),
    url(r'^paytype/(?P<pk>[0-9]+)/?$', views.PaytypeDetail.as_view()),
    url(r'^category/?$', views.CategoryList.as_view()),
    url(r'^category/(?P<pk>[0-9]+)/?$', views.CategoryDetail.as_view()),
    url(r'^tag/?$', views.TagList.as_view()),
    url(r'^tag/(?P<pk>[0-9]+)/?$', views.TagDetail.as_view()),
    url(r'^seller/?$', views.SellerList.as_view()),
    url(r'^seller/(?P<pk>[0-9]+)/?$', views.SellerDetail.as_view()),
    url(r'^pref-account/?$', views.PrefAccountList.as_view()),
    url(r'^pref-account/(?P<pk>[0-9]+)/?$', views.PrefAccountDetail.as_view()),
    url(r'^location/?$', views.LocationList.as_view()),
    url(r'^location/(?P<pk>[0-9]+)/?$', views.LocationDetail.as_view()),
    url(r'^order/?$', views.OrderList.as_view()),
    url(r'^order/(?P<pk>[0-9]+)/?$', views.OrderDetail.as_view()),
    url(r'^expense/?$', views.ExpenseList.as_view()),
    url(r'^expense/(?P<pk>[0-9]+)/?$', views.ExpenseDetail.as_view()),
    url(r'^expense-from-order/?$', views.CreateExpenseFromOrder.as_view()),
    url(r'^expense-from-order/(?P<pk>[0-9]+)/?$', views.UpdateOrderExpense.as_view()),
    url(r'^expense-from-order-shipment/?$', views.CreateExpenseFromOrderShipment.as_view()),
    url(r'^expense-catg/?$', views.ExpenseCatgList.as_view()),
    url(r'^expense-catg/(?P<pk>[0-9]+)/?$', views.ExpenseCatgDetail.as_view()),
]

api_patterns = format_suffix_patterns(api_patterns)

urlpatterns = [
    url(r'^api/v1/', include(api_patterns)),
    # Django admin interface
    url(r'^admin/', admin.site.urls),
    # DRF browsable api
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # oauth2_provider
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
