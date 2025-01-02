from django.shortcuts import render
import base64
import json

from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import actions, api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import F, Q, Prefetch
from rest_framework.views import APIView
from user.models import User
from .models import Book, Image, Category, CartItem
from .serializers import CategorySerializer, ImageSerializer, BookSerializer, \
    CartItemSerializer, BookSerializer1, CategorySerializer1, CustomBookSerializer
# Create your views here.


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Book.objects.prefetch_related(
            Prefetch('categories', queryset=Category.objects.only('id_category', 'name_category'))
        ).all()
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many = True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many = True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def hot_books(self, request):
        hot_books = Book.objects.all().order_by(F('avg_rating').desc(nulls_last=True))[:4]
        serializer = self.get_serializer(hot_books, many = True)
        return Response(serializer.data)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "book detected successfully"}, status=status.HTTP_200_OK)
    @action(detail=False, methods=['get'])
    def all_books(self, request):
        books = self.queryset.all()
        serializer = self.get_serializer(books, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "category detected successfully"}, status=status.HTTP_200_OK)

class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.select_related('id_book').all()
    serializer_class = ImageSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many = True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, match = True)
        return Response(serializer.data)
    
    def get_queryset(self):
        return Image.objects.select_related('id_book').all()
    
    @action(detail = False, methods = ['get'], url_path = 'book.(?P<book_id>\d+)')
    def images_by_books(self, request, book_id = None):
        cache_key = f'images_book_{book_id}'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return Response(cached_data)
        images = self.get_queryset().filter(id_book = book_id)
        serializer = self.get_serializer(images, many = True)
        cache.set(cache_key, serializer.data, timeout=3600)
        return Response(serializer.data)
    
class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    @action(detail = False, methods = ['post'], url_path = 'add-to-cart/(?P<id_user>\d+)')
    def add_to_cart(self, request, id_user):
        print(f"Authenticated User ID: {request.user.id}")
        print(f"Requested User IDL {id_user}")
        try:
            data = json.loads(request.body)
            user = get_object_or_404(User, id = id_user)
            
            added_items = []
            with transaction.atomic():
                for item_data in data:
                    book = get_object_or_404(Book, id_book = item_data['book']['idBook'])
                    quantity = item_data['quantity']
                    
                    cart_item, created = CartItem.objects.get_or_create(
                        id_book = book,
                        id_user = user,
                        defaults = {
                            'quantity': quantity}
                    )
                    
                    if not created:
                        cart_item.quantity += quantity
                        cart_item.save()
                    
                    added_items.append({
                        'idCart': cart_item.id_cart,
                        'quantity': cart_item.quantity,
                        'book': {
                            'idBook': book.id_book,
                            'nameBook': book.name_book,
                        }
                    })
            if len(data) ==1:
                return Response({'idCart': added_items[0]['idCart']}, status= status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    @action(detail = False, methods=['put'], url_path = 'update-cart-item', permission_classes = [IsAuthenticated]) 
    def update_cart_item(self, request, id_cart, id_user):
        try:
            data = request.data
            quantity = data.get('quantity')
            
            cart_item = get_object_or_404(CartItem, id_cart = id_cart)
            
            if request.user.id != cart_item.user.id:
                return Response({"detail": "Don't have permission to modify this"}, status=status.HTTP_403_FORBIDDEN) 
            
            cart_item.quantity = quantity
            cart_item.save()
            return Response({"detail": "Cart item updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    @actions(detail = False, methods = ['get'], url_path = 'user/(?P<id_user>\d+)')
    def get_cart_by_user(self, request, id_user = None):
        if str(request.user.id) != id_user:
            return Response({"detail": "Don't have permission to view this"}, status=status.HTTP_403_FORBIDDEN)
        
        user = get_object_or_404(User, id = id_user)
        cart_items = CartItem.objects.filter(id_user = user)
        
        formatted_items = []
        for item in cart_items:
            formatted_items.append({
                'idCart': item.id_cart,
                'quantity': item.quantity,
                'book': {
                    'idBook': item.id_book.id_book,
                    'nameBook': item.id_book.name_book,
                }   
            })
            
        return Response(formatted_items, status=status.HTTP_200_OK)
    
    @action(detail = True, methods = ['get'], url_path = 'book')
    def get_book_info(self, request, pk = None):
        cart_item = get_object_or_404(CartItem, id_cart=pk)
        
        book = cart_item.id_book
        serializer = BookSerializer(bool)
        return Response(serializer.data)

class BookImagesView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        keyword = request.query_params.get('keyword', '')
        id_genre = request.query_params.get('idCategory')
        filter_option = request.query_params.get('sort', '')
        page_size = int(request.query_params.get('pageSize', 12))
        page_no = int(request.query_params.get('pageNo', 1))
        
        queryset = Book.objects.all()
        
        if keyword:
            queryset = queryset.filter(Q(name_book__icontains=keyword) | Q(author__icontains=keyword))
        
        if id_genre and id_genre != '0':
            queryset = queryset.filter(categories__id_category=id_genre)
            
        if filter_option:
            if filter_option == 'nameBook':
                queryset = queryset.order_by('name_book')
            elif filter_option == 'nameBook,desc':
                queryset = queryset.order_by('-name_book')
            elif filter_option == 'sellPrice':
                queryset = queryset.order_by('sell_price')
            elif filter_option =='sellPrice,desc':
                queryset = queryset.order_by('-sell_price')
            elif filter_option == 'soldQuantity,desc':
                queryset = queryset.order_by('-sold_quantity')
                
        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_no)
        
        serializer = BookSerializer(page, many=True)
        
        return Response({
            'books': serializer.data,
            'currentPage': page.number,
            'totalPages': paginator.num_pages,
            'totalItems': paginator.count,
        })

class BookSearchView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        keyword = request.query_params.get('keyword', '')
        id_genre = request.query_params.get('idCategory')
        filter_option = request.query_params.get('sort', '')
        page_size = int(request.query_params.get('pageSize', 12))
        page_no = int(request.query_params.get('pageNo', 1))

        queryset = Book.objects.all()

        if keyword:
            queryset = queryset.filter(
                Q(name_book__icontains=keyword)
            )

        if id_genre and id_genre != '0':
            queryset = queryset.filter(categories__id_category=id_genre)

        if filter_option:
            if filter_option == 'nameBook':
                queryset = queryset.order_by('name_book')
            elif filter_option == 'nameBook,desc':
                queryset = queryset.order_by('-name_book')
            elif filter_option == 'sellPrice':
                queryset = queryset.order_by('sell_price')
            elif filter_option == 'sellPrice,desc':
                queryset = queryset.order_by('-sell_price')
            elif filter_option == 'soldQuantity,desc':
                queryset = queryset.order_by('-sold_quantity')

        # Pagination
        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_no)

        serializer = BookSerializer(page, many=True)

        return Response({
            'books': serializer.data,
            'currentPage': page.number,
            'totalPages': paginator.num_pages,
            'totalItems': paginator.count,
        })

class BookSaveView(APIView):
    def post(self, request):
        serializer = CustomBookSerializer(data=request.data)
        if serializer.is_valid():
            try:
                book = serializer.save()
                return Response(CustomBookSerializer(book).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookUpdateView(APIView):

    def put(self, request, pk):
        try:
            book = Book.objects.get(id_book=pk)
        except Book.DoesNotExist:
            return Response("Book not found", status=status.HTTP_404_NOT_FOUND)

        serializer = CustomBookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid():
            book = serializer.save()
            return Response(CustomBookSerializer(book).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST', 'PUT'])
@csrf_exempt
@permission_classes([IsAuthenticated])

def category_view(request, category_id=None):
    if request.method == 'POST':
        serializer = CategorySerializer1(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            return Response({
                'idCategory': category.id_category,
                'nameCategory': category.name_category
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'PUT':
        try:
            category = Category.objects.get(id_category=category_id)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CategorySerializer1(category, data=request.data)
        if serializer.is_valid():
            updated_category = serializer.save()
            print(updated_category)
            return Response({
                'idCategory': updated_category.id_category,
                'nameCategory': updated_category.name_category
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@require_http_methods(["GET"])
def get_total_books(request):
    try:
        total_books = Book.objects.count()
        return JsonResponse({'total': total_books})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)