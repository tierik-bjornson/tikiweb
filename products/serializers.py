import base64
import binascii
import logging
import re

import cloudinary 
from django.core.files.base import ContentFile
from rest_framework import serializers
from .models import Book, Category, Image, CartItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id_image', 'name_image', 'is_thumbnail', 'url_image', 'data_image', 'id_book']

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'
class BookSerializer1(serializers.ModelSerializer):
    categories = CategorySerializer(many = True, read_only = True)
    
    class Meta:
        model = Book
        fields = [
            'id_book', 'name_book', 'author', 'description', 'list_price', 'sell_price', 
            'quantity', 'sold_quantity', 'avg_rating', 'discount_percent', 'categories']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        field_mapping = {
            'id_book': 'idBook',
            'name_book': 'nameBook',
            'list_price': 'listPrice',
            'sell_price': 'sellPrice',
            'avg_rating': 'avgRating',
            'sold_quantity': 'soldQuantity',
            'discount_percent': 'discountPercent'
        }
        
        for old_key, new_key in field_mapping.items():
            if old_key in representation:
                representation[new_key] = representation.pop(old_key)
                
        numeric_fields = ['listPrice', 'sellPrice', 'avgRating', 'discountPercent']
        for field in numeric_fields:
            if field in representation and representation[field] is not None:
                representation[field] = float(representation[field])
        
        representation['ISBN'] = representation.pop('isbn', '') or ''
        
        if not representation['categories']:
            representation.pop('categories')
        
        return representation

class CustomBookSerializer(serializers.ModelSerializer):
    nameBook = serializers.CharField(source = 'name_book')
    listPrice = serializers.DecimalField(source = 'list_price', max_digits = 10, decimal_places = 2)
    sellPrice = serializers.DecimalField(source ='sell_price', max_digits = 10, decimal_places = 2)
    avgRating = serializers.FloatField(source = 'avg_rating', allow_null = True)
    soldQuantity = serializers.IntegerField(source = 'sold_quantity', allow_null = True)
    discountPercent = serializers.IntegerField(source = 'discount_percent')
    idGenres = serializers.ListField(source = serializers.IntegerField(), write_only = True)
    thumbnail = serializers.CharField(write_only = True)
    relatedImg = serializers.ListField(source = serializers.CharField(), write_only= True)
    
    class Meta:
        model = Book
        fields = [
            'nameBook', 'author', 'listPrice', 'sellPrice', 'quantity', 
            'description', 'avgRating', 'soldQuantity', 'discountPercent', 
            'idGenres', 'thumbnail', 'relatedImg', 'ISBN'
        ]
        
    def create(self, validated_data):
        logging.info("Starting to create method")
        genres_data = validated_data.pop('idGenres')
        thumbnail_data = validated_data.pop('thumbnail', None)
        related_img_data = validated_data.pop('relatedImg', [])
        
        logging.info(f"Creating book with data : {validated_data}")                                     
        book = Book.objects.create(**validated_data)
        logging.info(f"Book created with ID : {book.id_book}")
        
        logging.info(f"setting categories: {genres_data}")
        categories = Category.objects.filter(id_category__in=genres_data)
        book.categories.set(categories)
        
        if thumbnail_data:
            logging.info("Saveing thumbnail")
            self._save_image(book, thumbnail_data, is_thumbnail=True)
            
        logging.info(f"Saving {len(related_img_data)} related images")
        
        for idx, img_data in enumerate(related_img_data):
            self._save_image(book, img_data, is_thumbnail = False, idx=idx)
            
        logging.info("Book created successfully")
        return book

    def update(self, instance, validated_data):
        genres_data = validated_data.pop('idGenres', None)
        thumbnail_data = validated_data.pop('thumbnail', None)
        related_img_data = validated_data.pop('relatedImg', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if genres_data is not None:
            categories = Category.objects.filter(id_category__in =genres_data)
            instance.categories.set(categories)
        
        if thumbnail_data:
            self._save_image(instance, thumbnail_data, is_thumbnail=True)
            for idx, img_data in enumerate(related_img_data):
                self._save_image(instance, img_data, is_thumbnail=False, idx = idx)
        return instance

    def _save_image(self, book, img_data, is_thumbnail=False, idx=None):
        try:
            img_data = re.sub(r'^data:image/.+;base64,','',img_data)
            img_data = img_data.strip()
            
            image_data = base64.b64decode(img_data)
            temp_image = ContentFile(image_data)
            result = cloudinary.uploader.upload(temp_image)
            
            cloudinary_url = result['secure_url']
            
            image, created = Image.objects.get_or_create(
                id_book=book,
                is_thumbnail=is_thumbnail,
                defaults={
                    'name_image': f'Book_{book.id_book}_{"thumb" if is_thumbnail else idx}',
                    'url_image': cloudinary_url,
                    'data_image': img_data
                }
            )
            
            if not created:
                if image.url_image:
                    try:
                        old_public_id = image.url_image.split('/')[-1].split('.')[0]
                        cloudinary.uploader.destroy(old_public_id)
                    except Exception:
                        pass
                image.name_image = f'Book_{book.id_book}_{"thumb" if is_thumbnail else idx}'
                image.url_image = cloudinary_url
                image.data_image = img_data
                image.save()
        except binascii.Error as e:
            raise serializers.ValidationError(f"Invalid base64 string for image: {str(e)}")
        except Exception as e:
            raise serializers.ValidationError(f"Error processing image: {str(e)}")

class CategorySerializer1(serializers.ModelSerializer):
    idCategory = serializers.IntegerField(source='id_category', required=False)
    nameCategory = serializers.CharField(source='name_category')
    
    class Meta:
        model = Category
        fields = ['idCategory', 'nameCategory']
        
    def create(self, validated_data):
        return Category.objects.create(name_category=validated_data['name_category'])
    def update(self, instance, validated_data):
        instance.name_category = validated_data.get('name_category', instance.name_category)
        instance.save()
        return instance
