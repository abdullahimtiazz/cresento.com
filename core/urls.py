from django.urls import path
from .views import (
    ItemDetailView,
    CheckoutView,
    HomeView,
    OrderSummaryView,
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart,
    PaymentView,
    AddCouponView,
    RequestRefundView,
    AllProductsView,
    viewToS,
    viewPrivacyPolicy,
    whyUs,
    aboutUs,
    contactUs,
    checkStats
)

app_name = 'core'

urlpatterns = [
    path('', HomeView, name='home'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('all-products/', AllProductsView.as_view(), name= 'all-products'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-item-from-cart/<slug>/', remove_single_item_from_cart,
         name='remove-single-item-from-cart'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('request-refund/', RequestRefundView.as_view(), name='request-refund'),
    path('policies/terms-of-service/', viewToS, name='terms-of-service'),
    path('policies/privacy-policy/', viewPrivacyPolicy, name='privacy-policy'),
    path('why-us/', whyUs, name='why-us'),
    path('about-us/', aboutUs, name='about-us'),
    path('contact/', contactUs, name='contact-us'),
    path('check-your-stats/', checkStats, name="check-your-stats")
]
