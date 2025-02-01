from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('checkout/', views.checkout, name='checkout'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('order/complete/', views.order_complete, name='order_complete'),
    path('wallet/pay/<int:order_id>/', views.pay_with_wallet, name='pay_with_wallet'),
    path('search/', views.search, name='search'),  # Change name to 'search'
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('wallet/', views.wallet_detail, name='wallet_detail'),
    path('wallet/add/', views.add_funds, name='add_funds'),
    path('payment-options/<int:order_id>/', views.payment_options, name='payment_options'),
]