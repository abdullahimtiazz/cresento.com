import random
import string

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, View

from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm, ContactForm
from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund, UserProfile, CarouselImage

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


class AllProductsView(ListView):
    model = Item    
    paginate_by = 10 
    template_name = "all_products.html"


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


def transfer_session_cart_to_user(request, user):

# if the user has an empty cart
#     transfer the items Over
# otherwise
#     let the existing cart override it and warn the user

    cart = request.session.get('cart', {})
    order = Order.objects.filter(user=user, ordered=False).first()
    if order:
        request.session['cart'] = {}
        messages.warning(request, "You already have an active order. Your cart has been restored.")
    else:
        if cart:
            order, created = Order.objects.get_or_create(user=user, ordered=False, ordered_date= timezone.now()) 
            for slug, item_data in cart.items():
                item = get_object_or_404(Item, slug=slug)
                order_item, created = OrderItem.objects.get_or_create(
                    item=item,
                    user=user,
                    ordered=False
                )
                order_item.quantity = item_data['quantity']
                order_item.save()
                order.items.add(order_item)
            request.session['cart'] = {}
            messages.success(request, "Your cart has been transferred to your account.")


class CheckoutView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            orders = Order.objects.filter(user=self.request.user, ordered=False)
            order = orders.first()
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")
# work on post function please
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            orders = Order.objects.filter(user=self.request.user, ordered=False)
            order = orders.first()
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                return redirect('core:payment', payment_option='stripe')

                # if payment_option == 'S':
                #     return redirect('core:payment', payment_option='stripe')
                # elif payment_option == 'P':
                #     return redirect('core:payment', payment_option='paypal')
                # else:
                #     messages.warning(
                #         self.request, "Invalid payment option selected")
                #     return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")        


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,
                'STRIPE_PUBLIC_KEY' : settings.STRIPE_PUBLIC_KEY
            }
            userprofile = self.request.user.userprofile
            if userprofile.one_click_purchasing:
                # fetch the users card list
                cards = stripe.Customer.list_sources(
                    userprofile.stripe_customer_id,
                    limit=3,
                    object='card'
                )
                card_list = cards['data']
                if len(card_list) > 0:
                    # update the context with the default card
                    context.update({
                        'card': card_list[0]
                    })
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
                    customer = stripe.Customer.retrieve(
                        userprofile.stripe_customer_id)
                    customer.sources.create(source=token)

                else:
                    customer = stripe.Customer.create(
                        email=self.request.user.email,
                    )
                    customer.sources.create(source=token)
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_total() * 100)

            try:

                if use_default or save:
                    # charge the customer because we cannot charge the token more than once
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="hkd",
                        customer=userprofile.stripe_customer_id
                    )
                else:
                    # charge once off on the token
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="hkd",
                        source=token
                    )

                # create the payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # assign the payment to the order

                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request, "Your order was successful!")
                return redirect("/")

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect("/")

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, "Rate limit error")
                return redirect("/")

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                print(e)
                messages.warning(self.request, "Invalid parameters")
                return redirect("/")

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.warning(self.request, "Not authenticated")
                return redirect("/")

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.warning(self.request, "Network error")
                return redirect("/")

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.warning(
                    self.request, "Something went wrong. You were not charged. Please try again.")
                return redirect("/")

            except Exception as e:
                # send an email to ourselves
                messages.warning(
                    self.request, "A serious error occurred. We have been notifed.")
                return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")


def HomeView(request):
    carousel_images = CarouselImage.objects.all()
    return render(request, 'home.html', {'carousel_images': carousel_images})


class OrderSummaryView(View):
    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            try:
                order = Order.objects.get(user=self.request.user, ordered=False)
                context = {
                    'object': order
                }
                return render(self.request, 'order_summary.html', context)
            except ObjectDoesNotExist:
                messages.warning(self.request, "You do not have an active order")
                order, created = Order.objects.get_or_create(user=self.request.user, ordered= False, ordered_date=timezone.now())
                return redirect("core:order-summary")
        else:
            try:
                cart = self.request.session.get('cart', {})
                cart_items = []
                total = 0
                print(cart)
                for slug, item_data in cart.items():
                    item = get_object_or_404(Item, slug=slug)
                    item_total = float(item.price) * item_data['quantity']
                    cart_items.append({
                        'title': item.title,  
                        'price': item.price,  
                        'quantity': item_data['quantity'],
                        'total_item_price': item_total,
                        'slug': slug
                    })
                    total += item_total
                print(cart_items)
                context = {
                    'cart_items': cart_items,
                    'total': total
                }
                return render(self.request, 'order_summary.html', context)
            except KeyError:
                messages.error(self.request, "There was an error with your cart")
                return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"



def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if request.user.is_authenticated:   
        order_item, created = OrderItem.objects.get_or_create(
            item=item,
            user=request.user,
            ordered=False
        )       
        order_qs = Order.objects.filter(user=request.user, ordered=False)       
        if order_qs.exists():
            order = order_qs[0]         
            if order.items.filter(item__slug=item.slug).exists():
                order_item.quantity += 1
                order_item.save()
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order-summary")
            else:
                order.items.add(order_item)
                messages.info(request, "This item was added to your cart.")
                return redirect("core:order-summary")
        else:
            ordered_date = timezone.now()
            order = Order.objects.create(user=request.user, ordered_date=ordered_date)
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order-summary")
    else:
        cart = request.session.get('cart', {})
        if slug in cart:
            cart[slug]['quantity'] += 1
        else:
            cart[slug] = {
                'quantity': 1,
                'title': str(item.title),
                'price': float(item.price),
                'slug': str(slug)
            }
        request.session['cart'] = cart
        messages.info(request, "Item was added to your cart.")
        return redirect("core:order-summary")


def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if request.user.is_authenticated:
        order_qs = Order.objects.filter(
            user=request.user,
            ordered=False
        )
        if order_qs.exists():
            order = order_qs[0]
            # check if the order item is in the order
            if order.items.filter(item__slug=item.slug).exists():
                order_item = OrderItem.objects.filter(
                    item=item,
                    user=request.user,
                    ordered=False
                )[0]
                order.items.remove(order_item)
                order_item.delete()
                messages.info(request, "This item was removed from your cart.")
                return redirect("core:order-summary")
            else:
                messages.info(request, "This item was not in your cart")
                return redirect("core:product", slug=slug)
        else:
            messages.info(request, "You do not have an active order")
            return redirect("core:product", slug=slug)
    else:
        cart = request.session.get('cart', {})
        if slug in cart:
            del cart[slug]
            messages.info(request, "This item was removed from your cart.")
            request.session['cart'] = cart
            return redirect('core:order-summary')
        else:
            messages.info(request, "Item was not in your cart")
            request.session['cart'] = cart
            return redirect("core:product", slug= slug)



def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if request.user.is_authenticated:
        order_qs = Order.objects.filter(
            user=request.user,
            ordered=False
        )
        if order_qs.exists():
            order = order_qs[0]
            # check if the order item is in the order
            if order.items.filter(item__slug=item.slug).exists():
                order_item = OrderItem.objects.filter(
                    item=item,
                    user=request.user,
                    ordered=False
                )[0]
                if order_item.quantity > 1:
                    order_item.quantity -= 1
                    order_item.save()
                else:
                    order.items.remove(order_item)
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order-summary")
            else:
                messages.info(request, "This item was not in your cart")
                return redirect("core:product", slug=slug)
        else:
            messages.info(request, "You do not have an active order")
            return redirect("core:product", slug=slug)
    else:
        cart = request.session.get('cart', {})
        if slug in cart:
            if cart[slug]['quantity'] > 1:
                cart[slug]['quantity'] -= 1
            else:
                del cart[slug]
            messages.info(request, "This item was removed from your cart.")
        else:
            messages.info(request, "Item was not in your cart")
        request.session['cart'] = cart
        return redirect("core:order-summary")



def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received.")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("core:request-refund")

def viewToS(request):
    return render(request, 'terms_of_service.html')

def viewPrivacyPolicy(request):
    return render(request, 'privacy_policy.html')

def whyUs(request):
    return render(request, 'why_us.html')

def aboutUs(request):
    return render(request, 'about.html')

def contactUs(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        print("Form is submitted", request.POST)
        print(form.fields)
        print(form.errors)
        print(form.is_bound)
        print(form.data)
        if form.is_valid():            
            form.save()
            print("Form is saved.")
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('core:contact-us')
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})

def checkStats(request):
    return render(request, "empty_statistics.html")