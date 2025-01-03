import random

from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order, OrderDetail, Payment, Delivery
from products.models import Book
from users.models import User
import json
from decimal import Decimal
from django.conf import settings
import urllib.parse
import hashlib
import hmac
import datetime

@api_view(['POST'])
def add_order(request):
    try:
        data = request.data
        user_id = data.get('idUser')
        payment_id = data.get('idPayment')
        delivery_id = data.get('idDelivery')
        print(f"user_id: {user_id}, payment_id: {payment_id}, delivery_id: {delivery_id}")
        user = get_object_or_404(User, id=user_id)
        payment = get_object_or_404(Payment, id=payment_id)
        delivery = get_object_or_404(Delivery, id=delivery_id)
        order = Order.objects.create(
            user=user,
            purchase_address=data.get('purchaseAddress', ''),
            delivery_address=data.get('deliveryAddress', ''),
            total_price_product=data.get('totalPriceProduct', 0),
            fee_payment=data.get('feePayment', 0),
            status=data.get('status', 'Đang xử lí'),
            note=data.get('note', ''),
            phone_number=data.get('phoneNumber', ''),
            full_name=data.get('fullName', ''),
            fee_delivery=data.get('feeDelivery', 0),
            total_price=data.get('totalPrice', 0),
            status_payment=data.get('statusPayment', 'Pending'),
            status_delivery=data.get('statusDelivery', 'Pending'),
            payment=payment,
            delivery=delivery
        )
        print(f"Order created: {order}")
        book_data = data.get('book', [])
        for book_entry in book_data:
            quantity = int(book_entry['quantity'])
            book_id = book_entry['book']['idBook']
            book = Book.objects.get(id_book=book_id)

            book.quantity -= quantity
            book.sold_quantity += quantity
            book.save()
            order_detail = OrderDetail(
                quantity=quantity,
                book=book,
                order=order,
                price=quantity * book.sell_price,
            )
            order_detail.save()
        return Response({'message': 'Order created successfully'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        print(e)
        return Response({'error': 'Failed to create order'}, status=status.HTTP_400_BAD_REQUEST)

class VnpayConfig:
    vnp_TmnCode = 'LXKRH0ZN'
    vnp_Version = '2.1.0'
    vnp_Command = 'pay'
    vnp_PayUrl = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'
    vnp_ReturnUrl = 'http://localhost:3000/check-out/status'
    secretKey = 'JJHU2TIN2ANY6GMPJTWUWAVBGNVWZHPW'

    @staticmethod
    def get_random_number(length):
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])

    @staticmethod
    def hmac_sha512(key, message):
        return hmac.new(key.encode('utf-8'), message.encode('utf-8'), hashlib.sha512).hexdigest().upper()

@api_view(['POST'])
def create_payment(request):
    amount = request.data.get('amount', 0)
    amount = int(amount * 100)
    vnp_TxnRef = VnpayConfig.get_random_number(8)
    vnp_IpAddr = request.META.get('REMOTE_ADDR', '')

    vnp_Params = {
        "vnp_Version": VnpayConfig.vnp_Version,
        "vnp_Command": VnpayConfig.vnp_Command,
        "vnp_TmnCode": VnpayConfig.vnp_TmnCode,
        "vnp_Amount": str(amount),
        "vnp_CurrCode": "VND",
        "vnp_BankCode": "NCB",
        "vnp_TxnRef": vnp_TxnRef,
        "vnp_OrderInfo": "Thanh toan don hang:" + vnp_TxnRef,
        "vnp_OrderType": "other",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": VnpayConfig.vnp_ReturnUrl,
        "vnp_IpAddr": vnp_IpAddr,
    }

    now = datetime.datetime.now()
    vnp_CreateDate = now.strftime('%Y%m%d%H%M%S')
    vnp_Params["vnp_CreateDate"] = vnp_CreateDate

    expire_time = now + datetime.timedelta(minutes=15)
    vnp_ExpireDate = expire_time.strftime('%Y%m%d%H%M%S')
    vnp_Params["vnp_ExpireDate"] = vnp_ExpireDate

    sorted_params = sorted(vnp_Params.items())
    hash_data = '&'.join([f"{k}={urllib.parse.quote_plus(v)}" for k, v in sorted_params])
    vnp_SecureHash = VnpayConfig.hmac_sha512(VnpayConfig.secretKey, hash_data)
    query_url = f"{VnpayConfig.vnp_PayUrl}?{hash_data}&vnp_SecureHash={vnp_SecureHash}"

    return JsonResponse({'payment_url': query_url}, status=200)
@require_http_methods(["GET"])
def get_all_orders(request):
    orders = Order.objects.all().order_by('-id')[:100000]
    data = []
    for order in orders:
        order_data = {
            'idOrder': order.id,
            'deliveryAddress': order.delivery_address,
            'totalPrice': order.total_price,
            'totalPriceProduct': order.total_price_product,
            'feeDelivery': order.fee_delivery,
            'feePayment': order.fee_payment,
            'dateCreated': order.date_created,
            'status': order.status,
            'user': order.user.last_name,
            'fullName': order.full_name,
            'note': order.note,
            'payment': order.payment.name,
        }
        data.append(order_data)
    return JsonResponse({'orders': data})

@require_http_methods(["GET"])
def get_all_orders_by_user(request, user_id):
    orders = Order.objects.filter(user_id=user_id).order_by('-id')
    data = []
    for order in orders:
        order_data = {
            'idOrder': order.id,
            'deliveryAddress': order.delivery_address,
            'totalPrice': order.total_price,
            'totalPriceProduct': order.total_price_product,
            'feeDelivery': order.fee_delivery,
            'feePayment': order.fee_payment,
            'dateCreated': order.date_created,
            'status': order.status,
            'user': order.user.to_dict(),
            'fullName': order.full_name,
            'note': order.note,
            'payment': order.payment.name,
        }
        data.append(order_data)
    return JsonResponse({'orders': data})

@require_http_methods(["GET"])
def get_single_order(request, order_id):
    try:
        order = Order.objects.prefetch_related(
            Prefetch('order_details', queryset=OrderDetail.objects.select_related('book'))
        ).get(id=order_id)

        cart_items = []
        for order_detail in order.order_details.all():
            cart_items.append({
                'book': order_detail.book.to_dict(),
                'quantity': order_detail.quantity
            })

        order_data = {
            'idOrder': order.id,
            'deliveryAddress': order.delivery_address,
            'totalPrice': order.total_price,
            'totalPriceProduct': order.total_price_product,
            'feeDelivery': order.fee_delivery,
            'feePayment': order.fee_payment,
            'dateCreated': order.date_created,
            'status': order.status,
            'user': order.user.to_dict(),
            'fullName': order.full_name,
            'phoneNumber': order.phone_number,
            'note': order.note,
            'cartItems': cart_items,
            'payment': order.payment.name,
        }
        return JsonResponse(order_data)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

@require_http_methods(["POST"])
def update_order(request):
    data = json.loads(request.body)
    order_id = data.get('idOrder')
    try:
        order = Order.objects.get(id=order_id)
        order.status = data.get('status', order.status)
        order.save()
        return JsonResponse({'message': 'Order updated successfully'})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
@require_http_methods(["GET"])
def get_order_detail_book(request, order_detail_id):
    try:
        order_detail = OrderDetail.objects.select_related('book').get(id=order_detail_id)
        return JsonResponse(order_detail.book.to_dict())
    except OrderDetail.DoesNotExist:
        return JsonResponse({'error': 'Order detail not found'}, status=404)
@require_http_methods(["GET"])
def get_order_detail_list(request, order_id):
    try:
        order_details = OrderDetail.objects.filter(order_id=order_id).select_related('book')
        data = []
        for od in order_details:
            data.append({
                'idOrderDetail': od.id,
                'quantity': od.quantity,
                'book': od.book.to_dict()
            })
        return JsonResponse({'orderDetails': data})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
@require_http_methods(["GET"])
def get_order_payment(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return JsonResponse({'namePayment': order.payment.name})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
@require_http_methods(["GET"])
def get_order_user(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return JsonResponse(order.user.to_dict())
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
@csrf_exempt
@require_http_methods(["PUT"])
def update_order(request):
    try:
        data = json.loads(request.body)
        order_id = data.get('idOrder')
        order = Order.objects.get(id=order_id)
        order.status = data.get('status', order.status)
        order.delivery_address = data.get('deliveryAddress', order.delivery_address)
        order.total_price = data.get('totalPrice', order.total_price)
        order.total_price_product = data.get('totalPriceProduct', order.total_price_product)
        order.fee_delivery = data.get('feeDelivery', order.fee_delivery)
        order.fee_payment = data.get('feePayment', order.fee_payment)

        order.save()

        return JsonResponse({
            'message': 'Order updated successfully',
            'order': {
                'idOrder': order.id,
                'status': order.status,
                'deliveryAddress': order.delivery_address,
                'totalPrice': order.total_price,
                'totalPriceProduct': order.total_price_product,
                'feeDelivery': order.fee_delivery,
                'feePayment': order.fee_payment,
                'dateCreated': order.date_created,
            }
        })
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)