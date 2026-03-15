from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
# from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from .models import Category, Product, Rating, Cart, CartItem, Order, OrderItem
from .forms import RatingForm, CheckoutForm
from .utils import generate_sslcommerz_payment, send_order_confirmation_email
from django.db.models import Q, Min, Max, Avg
from django.core.paginator import Paginator

# Create your views here.
def home(request):
    feature_products = Product.objects.filter(available = True).order_by('created_at')[:8]
    categories = Category.objects.all()
    
    return render(request, 'products/home.html', {
        'feature_products': feature_products,
        'categories': categories,
    })
    
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available = True).order_by('id')
    
    if category_slug:
        category = get_object_or_404(Category, slug= category_slug)
        products = products.filter(category= category)
    
    min_price = products.aggregate(Min('price'))['price__min'] or 0
    max_price = products.aggregate(Max('price'))['price__max'] or 0
    
    if request.GET.get('min_price'):
        products = products.filter(price__gte = request.GET.get('min_price'))
    
    if request.GET.get('max_price'):
        products = products.filter(price__lte = request.GET.get('max_price'))
        
    if request.GET.get('rating'):
        min_rating = request.GET.get('rating')
        products = products.annotate(avg_rating = Avg('ratings__rating')).filter(avg_rating__gte = min_rating)# 4 ba 4 er besi rating er product show koranor jonno
    if request.GET.get('search'):
        query = request.GET.get('search')
        products = products.filter(
            Q(name__icontains = query)|
            Q(descriptions__icontains = query)|
            Q(category__name__icontains = query)
        )
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'products/product_list.html',{
        'category': category,
        'products': products,
        'categories': categories,
        'min_price': min_price,
        'max_price': max_price,
        'page_obj': page_obj,
    })
    

def product_detail(request, slug):
    product = get_object_or_404(Product, slug= slug, available = True)
    related_product = Product.objects.filter(category = product.category).exclude(id = product.id).order_by('-id')
    user_rating = None
    
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(product= product, user = request.user)
        except Rating.DoesNotExist:
            pass
    rating_form = RatingForm(instance= user_rating)
    
    paginator = Paginator(related_product, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'products/product_detail.html',{
        'product': product,
        'related_product': related_product,
        'user_rating': user_rating,
        'rating_form': rating_form,
        'page_obj': page_obj,
        
    })

@login_required(login_url='/account/login/')
def cart_details(request):
    try:
        cart = Cart.objects.get(user= request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user = request.user)
    return render(request, 'products/cart.html', {'cart':cart})    


@login_required(login_url='/account/login/')
def cart_add(request, product_id):
    product = get_object_or_404(Product, id= product_id)
    try:
        cart = Cart.objects.get(user= request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user = request.user)

    try:
        cart_item = CartItem.objects.get(cart = cart, product = product)
        cart_item.quantity +=1
        cart_item.save()
    except CartItem.DoesNotExist:
        CartItem.objects.create(cart = cart, product = product, quantity= 1)
        messages.success(request, f"{product.name} has been added to your cart")
    return redirect('product_detail', slug = product.slug)

@login_required(login_url='/account/login/')
def cart_remove(request, product_id):
    cart = get_object_or_404(Cart, user = request.user)
    product = get_object_or_404(Product, id= product_id)
    cart_item = get_object_or_404(CartItem , cart = cart, product= product)
    cart_item.delete()
    messages.success(request, f"{product.name} has been Removed from your cart")
    return redirect('cart_details')

@login_required(login_url='/account/login/')
def cart_update(request, product_id):
    cart = get_object_or_404(Cart, user = request.user)
    product = get_object_or_404(Product, id= product_id)
    cart_item = get_object_or_404(CartItem , cart = cart, product= product)
    
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        cart_item.delete()
        messages.success(request, f"{product.name} has been Removed from your cart")
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f"Cart Updated Successfully!")
    return redirect('cart_details')

@csrf_exempt
@login_required(login_url='/account/login/')
def checkout(request):
    try:
        cart = Cart.objects.get(user = request.user)
        if not cart.items.exists():
            messages.warning(request, f"Your Cart is Empty!")
            return redirect('product_list')
    except Cart.DoesNotExist:
        messages.warning(request, f"Your Cart is Empty!")
        return redirect('product_list')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            
            for item in cart.items.all():
                OrderItem.objects.create(
                    order = order,
                    product = item.product,
                    price = item.product.price,
                    quantity = item.quantity,
                )
            cart.items.all().delete()
            request.session['order_id']= order.id
            return redirect('payment_process')
    else:
        initial_data = {}
        if request.user.first_name:
            initial_data['first_name']= request.user.first_name
        if request.user.last_name:
            initial_data['last_name']= request.user.last_name
        if request.user.email:
            initial_data['email']= request.user.email
        
        form = CheckoutForm(initial= initial_data)
    return render(request, 'products/checkout.html', {
        'cart': cart,
        'form': form,
    })


@csrf_exempt
@login_required(login_url='/account/login/')
def payment_process(request):
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('home')
    
    order = get_object_or_404(Order, id= order_id)
    payment_data = generate_sslcommerz_payment(order, request)
    
    if payment_data['status'] == 'SUCCESS':
        return redirect(payment_data['GatewayPageURL'])
    else:
        messages.error(request, 'payment gateway error. Please try again.')
        return redirect('checkout')
    
@csrf_exempt
def payment_success(request, order_id):
    order = get_object_or_404(Order, id= order_id, user = request.user)
    order.paid = True
    order.status = 'processing'
    order.transaction_id = order.id
    order.save()
    
    order_items = order.items.all()
    for item in order_items:
        product = item.product
        product.stock -= item.quantity
        
        if product.stock < 0:
            product.stock = 0
        product.save()
    
    send_order_confirmation_email(order) # <----------------- email
    messages.success(request, 'Payment Successful.')
    return render(request, 'products/payment_success.html', {'order': order,}) 


@csrf_exempt
def payment_fail(request, order_id):
    order = get_object_or_404(Order, id= order_id, user = request.user)
    order.status = 'canceled'
    order.save()
    # return redirect('checkout') 
    return render(request, 'products/payment_fail.html', {'order':order})

@csrf_exempt
def payment_cancel(request, order_id):
    order = get_object_or_404(Order, id= order_id, user = request.user)
    order.status = 'canceled'
    order.save()
    # return redirect('cart_detail') 
    return render(request, 'products/payment_cancel.html', {'order':order})

@login_required(login_url='/account/login/')
def profile(request):
    tab = request.GET.get('tab')
    orders = Order.objects.filter(user = request.user).order_by('-created')
    completed_orders = orders.filter(status = 'delivered').count()
    total_spent = sum(order.get_total_cost() for order in orders if order.paid)
    order_history_active = (tab == 'orders')
    
    return render(request, 'products/profile.html', {
        'user': request.user,
        'orders': orders,
        'order_history_active': order_history_active,
        'completed_orders': completed_orders,
        'total_spent': total_spent,
    }) 

@login_required(login_url='/account/login/')
def rate_product(request, product_id):
    product = get_object_or_404(Product, id= product_id)
    order_items = OrderItem.objects.filter(
        order__user = request.user,
        order__paid = True,
        product = product
    )
    
    if not order_items.exists():
        messages.warning(request, "You can only rate products you have purchased")
        return redirect('shop:product_detail', slug = product.slug)
    try:
        rating = Rating.objects.get(product = product, user = request.user)
    except Rating.DoesNotExist:
        rating = None
    
    if request.method == 'POST':
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
            rating = form.save(commit= False)
            rating.product = product
            rating.user = request.user
            rating.save()
            return redirect('product_detail', slug = product.slug)
    else:
        form = RatingForm(instance=rating)
    return render(request, 'products/rate_product.html', {
        'form': form,
        'product': product,
        
    })
    