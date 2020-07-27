from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect, HttpResponseRedirect
from .models import Category, Product, Cart, CartItem, Order, OrderItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from .form import SignUpForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
import stripe
from django.conf import settings


def home(request, category_slug=None):

    category = None
    if category_slug != None:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.all().filter(category=category, available=True)
    else:
        products = Product.objects.all().filter(available=True)

    return render(request, 'home.html', {'category': category, 'products': products})


def about(request):
    return render(request, 'about.html')


def product(request, product_id):
    product = Product.objects.get(pk=product_id)

    return render(request, 'product.html', {'product': product})


def _get_cart_session(request):
    cart_session = request.session.session_key or request.session.create()
    return cart_session


def _get_cart(request):
    try:
        cart = Cart.objects.get(cart_session=_get_cart_session(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_session=_get_cart_session(request))
        cart.save()
    return cart


def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart = _get_cart(request)
    try:
        cart_item = CartItem.objects.get(
            product=product, cart=cart)
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1

        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(product=product, cart=cart)
        cart_item.save()
    return redirect('cart_detail')


def remove_from_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart = _get_cart(request)
    try:
        cart_item = CartItem.objects.get(
            product=product, cart=cart)
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect('cart_detail')


def subtract_from_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart = _get_cart(request)
    try:
        cart_item = CartItem.objects.get(
            product=product, cart=cart)
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            cart_item.delete()
        else:
            cart_item.save()
    except CartItem.DoesNotExist:
        pass
    return redirect('cart_detail')


def cart_detail(request, total=0, counter=0, cart_items=None, context=None):
    try:
        cart = _get_cart(request)
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        line_items = []
        for item in cart_items:
            total += item.quantity*item.product.price
            counter += item.quantity
            line_items.append(
                {'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': item.product.name,
                    },
                    'unit_amount': int(item.product.price)*100,
                },
                    'quantity': item.quantity,
                }
            )

        context = {'cart': cart, 'cart_items': cart_items,
                   'total': total, 'counter': counter}
    except ObjectDoesNotExist:
        pass

    stripe.api_key = settings.STRIPE_SECRET
    data_key = settings.STRIPE_PUBLISHABLE
    stripe_total = int(total*100)
    description = settings.STORE_NAME + ' - new order'

    # old stripe payment

    if request.method == 'POST':
        try:
            token = request.POST['stripeToken']
            email = request.POST['stripeEmail']
            billingName = request.POST['stripeBillingName']
            billingAddress1 = request.POST['stripeBillingAddressLine1']
            billingCity = request.POST['stripeBillingAddressCity']
            billingPostcode = request.POST['stripeBillingAddressZip']
            billingCountry = request.POST['stripeBillingAddressCountryCode']
            shippingName = request.POST['stripeShippingName']
            shippingAddress1 = request.POST['stripeShippingAddressLine1']
            shippingCity = request.POST['stripeShippingAddressCity']
            shippingPostcode = request.POST['stripeShippingAddressZip']
            shippingCountry = request.POST['stripeShippingAddressCountryCode']
            customer = stripe.Customer.create(
                source=token,
                email=email
            )
            charge = stripe.Charge.create(
                amount=stripe_total,
                currency='eur',
                description=description,
                customer=customer.id
            )

            try:
                order = Order.objects.create(token=token,
                                                     total=total,
                                                     emailAddress=email,
                                                     billingName=billingName,
                                                     billingAddress1=billingAddress1,
                                                     billingCity=billingCity,
                                                     billingPostcode=billingPostcode,
                                                     billingCountry=billingCountry,
                                                     shippingName=shippingName,
                                                     shippingAddress1=shippingAddress1,
                                                     shippingCity=shippingCity,
                                                     shippingPostcode=shippingPostcode,
                                                     shippingCountry=shippingCountry)
                order.save()

                for cart_item in cart_items:
                    order_item = OrderItem.objects.create(product=cart_item.product.name,
                                                          quantity=cart_item.quantity,
                                                          price=cart_item.product.price,
                                                          order=order)
                    order_item.save()
                    # reduce stock
                    product = Product.objects.get(id=cart_item.product.id)
                    product.stock -= cart_item.quantity
                    product.save()
                    cart_item.delete()
                return redirect('success', order.id)
            except ObjectDoesNotExist:
                pass
        except stripe.error.CardError as e:
            return False, e

    # new stripe to be implemented

    # domain_url = 'http://localhost:8000/home/account/'
    # try:
    #     if not stripe.Customer.retrieve(str(request.user.id)):
    #         stripe.Customer.create(
    #             id=str(request.user.id),
    #             email=request.user.email,
    #         )
    #     session = stripe.checkout.Session.create(
    #         customer=str(request.user.id),
    #         payment_method_types=['card', 'giropay'],
    #         line_items=line_items,
    #         mode='payment',
    #         success_url=domain_url+f'success?session_id={request.user.id}',
    #         cancel_url=domain_url+'cancel/',
    #     )

        # delete this
        # print(request.user.first_name)
        # print(session)
        # print(stripe.Customer.retrieve("8"))
    # except stripe.error.CardError as e:
    #     return False, e

    payment_context = dict(data_key=data_key, stripe_total=stripe_total,
                           description=description)
    # CHECKOUT_SESSION=session)
    context.update(payment_context)
    return render(request, 'cart.html', context)

# authentication views


def signupView(request):
    form = SignUpForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            new_user = User.objects.get(username=username)
            customer_grup = Group.objects.get(name='Customer')
            customer_grup.user_set.add(new_user)

    return render(request, 'signup.html', {'form': form})


def signinView(request):
    form = AuthenticationForm(data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                return redirect('signup')

    return render(request, 'signin.html', {'form': form})


def signoutView(request):
    logout(request)
    return redirect('signin')


def success(request, order_id=None):

    order = Order.objects.get(id=order_id)

    return render(request, 'success.html', {'order':order})


def cancel(request):
    return render(request, 'cancel.html')
