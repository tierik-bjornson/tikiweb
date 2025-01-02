from django.urls import path
from .views import add_order, create_payment, get_all_orders, get_all_orders_by_user, get_single_order, get_order_user, \
    get_order_payment, get_order_detail_list, get_order_detail_book, update_order

urlpatterns = [
    path('order/add-order', add_order, name='add_order'),
    path('vnpay/create-payment', create_payment, name='create_payment'),
    path('orders/', get_all_orders, name='get_all_orders'),
    path('users/<int:user_id>/orderList/', get_all_orders_by_user, name='get_all_orders_by_user'),
    path('orders/<int:order_id>/', get_single_order, name='get_single_order'),
    path('orders/<int:order_id>/user/',get_order_user, name='get_order_user'),
    path('orders/<int:order_id>/payment/',get_order_payment, name='get_order_payment'),
    path('orders/<int:order_id>/orderDetailList/', get_order_detail_list, name='get_order_detail_list'),
    path('order-details/<int:order_detail_id>/book/', get_order_detail_book, name='get_order_detail_book'),
    path('order/update-order/', update_order, name='update_order'),
]