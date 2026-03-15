from django.urls import path
from .views import (home, product_list, product_detail, cart_details, cart_add, cart_remove, cart_update,
    checkout, payment_process, payment_success, payment_fail, payment_cancel, profile, rate_product)

urlpatterns =[
    path('', home, name='home'),
    path('products/', product_list, name='product_list'),
    path('products/<slug:category_slug>/', product_list, name= 'product_list_by_category'),
    path('product/<slug:slug>/', product_detail, name= 'product_detail'),
    
    path('cart/', cart_details, name='cart_details'),
    path('cart/add/<int:product_id>/', cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', cart_remove, name='cart_remove'),
    path('cart/update/<int:product_id>/', cart_update, name='cart_update'),
    
    path('checkout/', checkout, name='checkout'),
    path('payment/process/', payment_process, name='payment_process'),
    path('payment/success/<int:order_id>/', payment_success, name='payment_success'),
    path('payment/fail/<int:order_id>/', payment_fail, name='payment_fail'),
    path('payment/cancel/<int:order_id>/', payment_cancel, name='payment_cancel'),
    
    path('profile/', profile, name='profile'),
    path('rate/<int:product_id>/', rate_product, name='rate_product')
    
]