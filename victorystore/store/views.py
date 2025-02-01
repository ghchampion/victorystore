from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Profile, Wallet, WalletTransaction
from decimal import Decimal
from .forms import CustomUserCreationForm
from django.db.models import Q

def home(request):
    products = Product.objects.filter(available=True)[:6]
    return render(request, 'store/home.html', {'products': products})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(
                user=user,
                phone=form.cleaned_data['phone'],
                country=form.cleaned_data['country']
            )
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'store/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else 'dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'store/login.html')

@login_required
def dashboard(request):
    profile = Profile.objects.get_or_create(user=request.user)[0]
    wallet = Wallet.objects.get_or_create(user=request.user)[0]
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    cart = Cart.objects.filter(user=request.user).first()
    cart_items_count = CartItem.objects.filter(cart=cart).count() if cart else 0
    orders_count = orders.count()
    recent_orders = orders[:5]
    
    context = {
        'profile': profile,
        'wallet': wallet,
        'orders_count': orders_count,
        'cart_items_count': cart_items_count,
        'recent_orders': recent_orders
    }
    return render(request, 'store/dashboard.html', context)

def logout_view(request):
    logout(request)
    return redirect('home')

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request, 'store/product_list.html',
                 {'category': category,
                  'categories': categories,
                  'products': products})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    return render(request, 'store/product_detail.html',
                 {'product': product})

@login_required
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return redirect('cart_detail')

@login_required
def cart_detail(request):
    cart = Cart.objects.filter(user=request.user).first()
    return render(request, 'store/cart_detail.html', {'cart': cart})

@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    
    if not cart or not cart.items.exists():
        messages.error(request, 'Your cart is empty')
        return redirect('cart_detail')

    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            address=request.POST.get('address'),
            phone=request.POST.get('phone'),
            payment_method='pending'  # Add default payment method
        )
        
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )
        
        cart.delete()
        return render(request, 'store/payment_options.html', {'order': order})
    
    return render(request, 'store/checkout.html', {'cart': cart})

@login_required
def payment_options(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    return render(request, 'store/payment_options.html', {
        'order': order,
        'wallet': wallet
    })

@login_required
def cart_update(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart_item.quantity = quantity
        cart_item.save()
    return redirect('cart_detail')

@login_required
def cart_remove(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        cart_item.delete()
    return redirect('cart_detail')

@login_required
def order_complete(request):
    return render(request, 'store/order_complete.html')

@login_required
def wallet_detail(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-timestamp')
    return render(request, 'store/wallet.html', {
        'wallet': wallet,
        'transactions': transactions
    })

@login_required
def add_funds(request):
    wallet = Wallet.objects.get(user=request.user)
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        wallet.balance += amount
        wallet.save()
        
        WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='deposit',
            description='User deposit'
        )
        
        messages.success(request, f'${amount} added to your wallet')
        return redirect('dashboard')
        
    return render(request, 'store/add_funds.html', {'wallet': wallet})

@login_required
def pay_with_wallet(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    wallet = get_object_or_404(Wallet, user=request.user)
    
    if wallet.balance >= order.get_total_cost():
        wallet.balance -= order.get_total_cost()
        wallet.save()
        
        WalletTransaction.objects.create(
            wallet=wallet,
            amount=-order.get_total_cost(),
            transaction_type='purchase',
            description=f'Payment for Order #{order.id}',
            order=order
        )
        
        order.paid = True
        order.payment_method = 'wallet'
        order.save()
        return redirect('order_complete')
    else:
        messages.error(request, 'Insufficient wallet balance')
        return redirect('checkout')

def search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query)
    ).filter(available=True)
    
    return render(request, 'store/search_results.html', {
        'products': products,
        'query': query
    })
