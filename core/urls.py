from django.urls import path
from core.views import HomeView,ItemDetailView,CheckOutView,add_to_cart,\
    remove_from_cart,order_summary,increase_quantity,decrease_quantity,\
    remove_from_order_summary,cat_filter,PaymentView,add_coupon_view,\
    Request_RefundView,MyOrders
app_name='core'

urlpatterns=[
    path('',HomeView.as_view(), name='home'),
    path('catogory/<slug>/',cat_filter, name='catagory-filter'),
    path('product/<slug>/',ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/',add_to_cart,name='add-to-cart'),
    path('buy_now/<slug>/',add_to_cart,name='buy-now'),
    path('remove-from-cart/<slug>/',remove_from_cart,name='remove-from-cart'),
    path('order_summary/',order_summary.as_view(),name='order-summary'),
    path('increase-quantity/<slug>/',increase_quantity,name='increase-quantity'),
    path('decrease-quantity/<slug>/',decrease_quantity,name='decrease-quantity'),
    path('remove_from_order_summary/<id>/',remove_from_order_summary,name='remove-item-from-summary'),
    path('checkout/',CheckOutView.as_view(), name='checkout'),
    path('coupon/',add_coupon_view, name='coupon'),
    path('payment/<payment_option>/',PaymentView.as_view(), name='payment'),
    path('refund-request',Request_RefundView.as_view(),name='refund-request'),
    path('myorders',MyOrders,name='myorders')
]