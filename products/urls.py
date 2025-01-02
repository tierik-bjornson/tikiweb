from django.conf import settings
from django.urls import path, include
from .views import BookViewSet, CategoryViewSet, ImageViewSet, CartItemViewSet, BookImagesView, \
    BookSearchView, BookSaveView, BookUpdateView, category_view, get_total_books
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('books', BookViewSet)
router.register('categories', CategoryViewSet)
router.register('images', ImageViewSet)
router.register(r'cart-item', CartItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('images/book/<int:id_book>/', BookImagesView.as_view(), name='book-images'),
    path('cart-item/add_to_cart/<int:id_user>/', CartItemViewSet.as_view({'post': 'add_to_cart'}), name='cart-item-add'),
    path('cart-item/add_to_cart1/<int:id_user>/', CartItemViewSet.as_view({'post': 'add_to_cart1'}), name='cart-item-add1'),
    path('cart-items/update_cart_item/<int:id_cart>/<int:id_user>/', CartItemViewSet.as_view({'put': 'update_cart_item'}), name='cart-item-update'),
    path('cart-item/user/<int:id_user>/', CartItemViewSet.as_view({'get': 'get_cart_by_user'}), name='cart-item-get-by-user'),
    path('books/search', BookSearchView.as_view(), name='book-search'),
    path('book/save/', BookSaveView.as_view(), name='book-save'),
    path('book/update/<int:pk>/', BookUpdateView.as_view(), name='book-update'),
    path('categorie/', category_view, name='create_category'),
    path('categorie/<int:category_id>/', category_view, name='update_category'),
    path('book/get-total', get_total_books, name='get_total_books'),


]
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]