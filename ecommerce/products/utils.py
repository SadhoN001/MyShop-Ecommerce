import json
import requests
from django.conf import settings
from django.template.loader import render_to_string
# from django.core.mail import EmailMultiAlternatives

def generate_sslcommerz_payment(order, request):
    """Generate SSLCommerz payment URL"""
    post_data = {
        'store_id': settings.SSLCOMMERZ_STORE_ID,
        'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
        'total_amount': float(order.get_total_cost()),
        'currency': 'BDT',
        'tran_id': str(order.id),
        'success_url': request.build_absolute_uri(f'/payment/success/{order.id}/'),
        'fail_url': request.build_absolute_uri(f'/payment/fail/{order.id}/'),
        'cancel_url': request.build_absolute_uri(f'/payment/cancel/{order.id}/'),
        'cus_name': f"{order.first_name} {order.last_name}",
        'cus_email': order.email,
        'cus_add1': order.address,
        'cus_city': order.city,
        'cus_postcode': order.postal_code,
        'cus_country': 'Bangladesh',
        'shipping_method': 'NO',
        'product_name': 'Products from our store',
        'product_category': 'General',
        'product_profile': 'general',
    }

    try:
        response = requests.post(settings.SSLCOMMERZ_PAYMENT_URL, data=post_data, timeout=30)
        print("SSLCommerz Response Status:", response.status_code)
        print("SSLCommerz Response Text:", response.text)
        
        if not response.text:
            return {'status': 'FAILED', 'failedreason': 'Empty response from SSLCommerz'}
        
        return json.loads(response.text)
    except Exception as e:
        print("SSLCommerz Error:", str(e))
        return {'status': 'FAILED', 'failedreason': str(e)}
    
def send_brevo_email(to_email, subject, text_content, html_content=None):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json"
    }
    data = {
        "sender": {"name": "MyShop", "email": "skdsadhon@gmail.com"},
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": text_content,
    }
    if html_content:
        data["htmlContent"] = html_content

    try:
        response = requests.post(url, json=data, headers=headers)
        return response.status_code == 201
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_verification_email(user, verify_url):
    """Registration verification email"""
    send_brevo_email(
        to_email=user.email,
        subject="Verify your Email",
        text_content=f"Click the link to verify your account: {verify_url}"
    )


# def send_order_confirmation_email(order):
#     subject = f"Order Confirmation - Order #{order.id}"
#     message = render_to_string('products/email/order_confirmation.html', {'order': order})
#     to = order.email 
#     send_email = EmailMultiAlternatives(subject, '', to=[to])
#     send_email.attach_alternative(message, 'text/html')
#     send_email.send()
def send_order_confirmation_email(order):
    """Order confirmation email"""
    html_content = render_to_string('products/email/order_confirmation.html', {'order': order})
    send_brevo_email(
        to_email=order.email,
        subject=f"Order Confirmation - Order #{order.id}",
        text_content=f"Your order #{order.id} has been confirmed!",
        html_content=html_content
    )