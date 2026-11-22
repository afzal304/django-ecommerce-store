from django.urls import path
from . import views

urlpatterns = [
	#Leave as empty string for base url
	path('', views.store, name="store"),
	path('cart/', views.cart, name="cart"),
	path('checkout/', views.checkout, name="checkout"),
	path('update_item/', views.updateItem, name="update_item"),
	path('process_order/', views.processOrder, name="process_order"),
	path('product/<int:pk>/', views.product_detail, name="product_detail"),
	path('profile/',views.user_profile ,name="user_profile"),
	path('order/<int:order_id>/detail/', views.order_detail, name='order_detail'),

	#auth path
	path('login/', views.login_view , name='login'),
	path('signup/', views.signup_view , name='signup'),
	path('logout/', views.logout_view , name='logout'),
]