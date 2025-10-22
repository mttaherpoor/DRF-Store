from django.urls import path, include
from rest_framework_nested import routers
from . import views

router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='product')
router.register('categoies', views.CategoryViewSet, basename='category')
router.register('carts', views.CartViewSet, basename='cart')
router.register('customers', views.CustomerViewSet, basename='customer')
router.register('orders', views.OrderViewSet, basename='order')


product_routers = routers.NestedDefaultRouter(router, 'products', lookup='product')
product_routers.register('comments', views.CommentViewSet, basename='product-comments')

cart_routers = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
cart_routers.register('items', views.CartItemViewSet, basename='cart-items')

urlpatterns = router.urls+ product_routers.urls + cart_routers.urls



# [
#     # path('products/', views.ProductList.as_view(), name='product-list'),
#     # path('products/<int:pk>/', views.ProductDetail.as_view(), name='product-detail'),
#     # path('categories/', views.CategotyList.as_view(), name='category-list'),
#     # path('categories/<int:pk>/', views.CategoryDetail.as_view(), name='category-detail'),
#     path('', include(router.urls)),
#     path('', include(product_routers.urls)),

#]
