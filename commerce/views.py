import os
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Review
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from .form import SignUpForm, ContactForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required


def home(request, category_slug=None):

    category = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.all().filter(category=category, available=True)
    else:
        products = Product.objects.all().filter(available=True)

    return render(request, 'home.html', {'category': category, 'products': products})


def search(request):
    query = request.GET['query']
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(discription__icontains=query))
    return render(request, 'home.html', {'products': products, 'search': True})

# render html template to pdf


def _render_html_pdf(html_source, pdf_output):
    with open(pdf_output, "w+b") as result_file:
        # create a pdf
        pisa_status = pisa.CreatePDF(html_source, dest=result_file)
        result_file.close()
    if pisa_status.err:
        return False
    else:
        return True

# sendgrid helper function


def _send_email(subject, text_html, to_email=None, pdf_output=None):
    content = Content("text/html", text_html)
    from_email = settings.EMAIL_HOST_USER
    to_email = (to_email if to_email else settings.EMAIL_TO)
    message = Mail(
        from_email=From(from_email),
        to_emails=To(to_email),
        subject=Subject(subject),
        html_content=content,
    )
    if pdf_output:
        # encode pdf file to base64
        with open(pdf_output, "rb") as pdf_file:
            data = pdf_file.read()
            pdf_file.close()
            encoded_file = base64.b64encode(data).decode()

        # prepare attachment
        attachedFile = Attachment(
            FileContent(encoded_file),
            FileName(pdf_output),
            FileType('application/pdf'),
            Disposition('attachment')
        )

        message.attachment = attachedFile

    try:
        sg = SendGridAPIClient(
            settings.SENDGRID_API_KEY)
        response = sg.send(message)
        if pdf_output:
            os.remove(pdf_output)
        print(response.status_code, response.body, response.headers)

    except Exception as e:
        if pdf_output:
            os.remove(pdf_output)
        print(e)


def about(request):
    return render(request, 'about.html')

def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid:
            name = request.POST.get('name')
            your_email = request.POST.get('your_email')
            subject = request.POST.get('subject')
            message = request.POST.get('message')

            message_format = f'<strong>{name} with email: {your_email} has sent you a message: \n \n{message}<strong>'

            _send_email(subject=subject, text_html=message_format)
            return render(request, 'contact_success.html')

    return render(request, 'contact.html', {'form':form})


def product(request, product_id):
    product = Product.objects.get(pk=product_id)
    content = request.POST.get('content', None)
    reviews = Review.objects.filter(user=request.user, product=product)
    if request.method == 'POST' and request.user.is_authenticated and content:
        review = Review.objects.create(
            user=request.user, product=product, content=content)

    return render(request, 'product.html', {'product': product, 'reviews': reviews})


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
        # # line_items is related to new stripe api
        # line_items = []
        for item in cart_items:
            total += item.quantity*item.product.price
            counter += item.quantity
            # line_items.append(
            #     {'price_data': {
            #         'currency': 'eur',
            #         'product_data': {
            #             'name': item.product.name,
            #         },
            #         'unit_amount': int(item.product.price)*100,
            #     },
            #         'quantity': item.quantity,
            #     }
            # )
        registered_email = request.user.email
        context = {'cart': cart, 'cart_items': cart_items,
                   'total': total, 'counter': counter, 'email': registered_email}
    except ObjectDoesNotExist:
        pass

    stripe.api_key = settings.STRIPE_SECRET
    data_key = settings.STRIPE_PUBLISHABLE
    stripe_total = int(total*100)
    description = settings.STORE_NAME + ' - new order'

    # old stripe payment

    if request.method == 'POST':
        try:
            token = request.POST['stripeToken'] or registered_email
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

                # preparing purchase email
                order_items = OrderItem.objects.filter(order=order)
                email_context = {'order': order, 'order_items': order_items}
                html_source = get_template('email/email.html')
                html_source = html_source.render(email_context)
                pdf_output = 'purchase.pdf'
                is_pdf_rendered = _render_html_pdf(html_source, pdf_output)
                to_email = email
                subject = 'Thanks For Your Purchase'
                if is_pdf_rendered:
                    _send_email(
                        subject, html_source, to_email, pdf_output=pdf_output)
                else:
                    _send_email(
                        subject, html_source, to_email, pdf_output=None)

                return redirect('success', order.id)
            except ObjectDoesNotExist:
                pass
        except stripe.error.CardError as e:
            return False, e

    # new stripe api to be implemented

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

    # except stripe.error.CardError as e:
    #     return False, e

    payment_context = dict(data_key=data_key, stripe_total=stripe_total,
                           description=description)
    # # CHECKOUT_SESSION is related to new stripe api
    # payment_context.update({'CHECKOUT_SESSION':session})
    context.update(payment_context)
    return render(request, 'cart.html', context)

# authentication views


def signupView(request):
    form = SignUpForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            new_user = User.objects.get(username=username)
            customer_grup = Group.objects.get(name='Customer')
            customer_grup.user_set.add(new_user)
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

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


# payment success and cancel views

def success(request, order_id=None):
    order = Order.objects.get(id=order_id)
    return render(request, 'success.html', {'order': order})


def cancel(request):
    return render(request, 'cancel.html')


# orders_history and detail views

@login_required(redirect_field_name="next", login_url="signin")
def orders_history(request):
    if request.user.is_authenticated:
        email = request.user.email
        orders = Order.objects.filter(emailAddress=email)
    return render(request, 'orders_history.html', {'orders': orders})


@login_required(redirect_field_name="next", login_url="signin")
def order_detail(request, order_id):
    if request.user.is_authenticated:
        email = request.user.email
        order = Order.objects.get(id=order_id, emailAddress=email)
        order_items = OrderItem.objects.filter(order=order)
    return render(request, 'order_detail.html', {'order': order, 'order_items': order_items})
