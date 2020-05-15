from django.shortcuts import render,get_object_or_404,redirect
from .models import Item,OrderItem,Order,Address,Payment,Coupon,Rfund
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView,DetailView,View
from django.contrib import messages
from django.urls import resolve
from .forms import CheckoutForm,CouponForm,RefundForm
from django.core.exceptions import ObjectDoesNotExist
import stripe
from django.conf import settings
stripe.api_key=settings.STRIPE_SECRET_KEY
import random
import string

def Create_Ref_code():
    code=''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    return code

class HomeView(ListView):
    model = Item
    paginate_by = 8
    template_name = 'home.html'
    def post(self,*args,**kwargs):
        stext=self.request.POST.get('search_text')
        if stext is '':
            return redirect('core:home')
        qs=Item.objects.filter(title__icontains=stext)|Item.objects.filter(brand__icontains=stext)
        if qs.exists():
            messages.success(self.request,'Search results:')
            return render(self.request,'home.html',{'object_list':qs})
        messages.warning(self.request,'No search items found')
        return redirect('core:home')


def cat_filter(request,slug):
    object_list=Item.objects.filter(catagory=slug)
    return render(request,'home.html',{'object_list':object_list})

class ItemDetailView(DetailView):
    model = Item
    object=Item.objects.all()
    template_name = 'product.html'

@login_required
def add_to_cart(request,slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]

        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            # order_item.quantity += 1
            # order_item.save()
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            current_url = resolve(request.path_info).url_name
            if current_url=='buy-now':
                return redirect('core:order-summary')
            else:
                messages.info(request, "This item was added to your cart.")
                return redirect("core:product",slug=slug)
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("core:product",slug=slug)
        # kwargs={'slug':slug}) # if reverse( )
@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
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
            order.save()
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:product",slug=slug)
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


class order_summary(LoginRequiredMixin,View):
    def get(self,*args,**kwargs):
        try:
            order=Order.objects.get(user=self.request.user,ordered=False)
            context={'object':order}
            return render(self.request,'order_summary.html',context)
        except ObjectDoesNotExist:
            messages.info(self.request,'You dont have an active order')
            return redirect('core:home')
@login_required
def increase_quantity(request,slug):
    q=OrderItem.objects.get(user=request.user,item__slug=slug,ordered=False)
    if q.quantity<5:
        q.quantity += 1
        q.save()
        messages.info(request,'Item Quantity was updated')
        return redirect('core:order-summary')
    messages.warning(request, 'No stock')
    return redirect('core:order-summary')
@login_required
def decrease_quantity(request,slug):
    q=OrderItem.objects.get(item__slug=slug,user=request.user,ordered=False)
    if q.quantity > 1:
        q.quantity -= 1
        q.save()
        messages.info(request, 'Item Quantity was updated')
        return redirect('core:order-summary')
    return redirect('core:order-summary')
@login_required
def remove_from_order_summary(request,id):
    try:
        ps=OrderItem.objects.get(id=id,user_id=request.user.id)
        ps.delete()
        return redirect('core:order-summary')
    except ObjectDoesNotExist:
        messages.info(request, 'Item does not exist')
        return redirect('core:order-summary')

def form_is_valid(values):
    valid=True
    for fields in values:
        if fields=='':
            valid=False
    return valid

class CheckOutView(LoginRequiredMixin,View):
    def get(self,*args,**kwargs):
        order = Order.objects.get(user=self.request.user,ordered=False)
        coupon_form=CouponForm()
        # if order.billing_address:
        form=CheckoutForm()
        context={'form':form,'order':order,'coupon_form':coupon_form}
        l=shipping_address_qs=Address.objects.filter(
            user=self.request.user,
            Address_type='s',
            default=True
        )
        if shipping_address_qs.exists():
            context.update({'default_shipping_address':shipping_address_qs[len(l)-1]})
        l=billing_address_qs = Address.objects.filter(
            user=self.request.user,
            Address_type='b',
            default=True
        )
        if billing_address_qs.exists():
            context.update({'default_billing_address':billing_address_qs[len(l)-1]})
        return render(self.request,'checkout-page.html',context)

    def post(self,*args,**kwargs):
        form=CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get('use_default_shipping')
                if use_default_shipping:
                    l=address_qs = Address.objects.filter(
                        user=self.request.user,
                        Address_type='s',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[len(l)-1]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    shipping_name = form.cleaned_data.get('shipping_name')
                    shipping_mobile = form.cleaned_data.get('shipping_mobile')
                    shipping_address = form.cleaned_data.get('shipping_address')
                    shipping_landmark = form.cleaned_data.get('shipping_landmark')
                    shipping_country = form.cleaned_data.get('shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')
                    if form_is_valid([shipping_name,shipping_mobile,shipping_address,
                                      shipping_landmark,shipping_country,shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            name=shipping_name,
                            mobile=shipping_mobile,
                            address=shipping_address,
                            landmark=shipping_landmark,
                            country=shipping_country,
                            zip=shipping_zip,
                            Address_type='s'
                        )
                        shipping_address.save()
                        order.shipping_address = shipping_address
                        order.save()
                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                    else:
                        messages.warning(self.request,'Fill out required shipping address fields')
                        return redirect('core:checkout')

                same_billing_address = form.cleaned_data.get('same_billing_address')
                use_default_billing = form.cleaned_data.get('use_default_billing')
                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.Address_type = 'b'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()
                elif use_default_billing:
                    l=address_qs = Address.objects.filter(
                        user=self.request.user,
                        Address_type='b',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[len(l)-1]
                        order.billing_address = billing_address
                        order.save()
                else:
                    Billing_name = form.cleaned_data.get('Billing_name')
                    Billing_mobile = form.cleaned_data.get('Billing_mobile')
                    Billing_address = form.cleaned_data.get('Billing_address')
                    Billing_landmark = form.cleaned_data.get('Billing_landmark')
                    Billing_country = form.cleaned_data.get('Billing_country')
                    Billing_zip = form.cleaned_data.get('Billing_zip')
                    if form_is_valid([Billing_name, Billing_mobile, Billing_address,
                                      Billing_landmark,Billing_country,Billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            name=Billing_name,
                            mobile=Billing_mobile,
                            address=Billing_address,
                            landmark=Billing_landmark,
                            country=Billing_country,
                            zip=Billing_zip,
                            Address_type='b'
                        )
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()
                        set_default_billing = form.cleaned_data.get('set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                    else:
                        messages.warning(self.request,'Fill out required billing address fields')
                        return redirect('core:checkout')
                # TODO:add redirect to selected payment option view
                payment_option = form.cleaned_data.get('payment_option')
                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(self.request, 'Invalid payment option')
                    return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.info(self.request,'Your cart is empty')
            return redirect('core:order-summary')

class PaymentView(LoginRequiredMixin,View):
    def get(self,*args,**kwargs):

        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address and order.shipping_address:
            coupon_form = CouponForm()
            address=order.shipping_address.address.split('\n')
            context = {'order': order, 'coupon_form': coupon_form,'address':address}
            return render(self.request,'payment.html',context)
        else:
            messages.warning(self.request,'Your are not added billing address')
            return redirect('core:checkout')

    def post(self, *args, **kwargs):
        try:
            order=Order.objects.get(user=self.request.user,ordered=False)
            token=self.request.POST.get('stripeToken')
            charge=stripe.Charge.create(
                amount=int(order.coupon_disc_total()*100),
                currency="inr",
                source=token,
            )

            #create the payment
            payment=Payment()
            payment.stripe_charge_id=charge['id']
            payment.user=self.request.user
            payment.amount=order.coupon_disc_total()
            amount=order.coupon_disc_total()
            payment.save()
            #assign the payment to the order

            order_items=order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()
            order.ordered = True
            order.payment=payment
            order.ref_code=Create_Ref_code()
            order.save()

            # messages.success(self.request,'Your order placed successfully')
            messages.success(self.request,f"Amount paid: Rs. {amount}/-, Your order was successful")
            return redirect('core:home')
        except stripe.error.CardError as e:
            body=e.json_body
            err=body.get('error',{})
            messages.warning(self.request,f"{err.get('message')}")
            return redirect('/')
        except stripe.error.RateLimitError as e:
            messages.warning(self.request, 'RateLimitError')
            return redirect('/')
        except stripe.error.InvalidRequestError as e:
            messages.warning(self.request, 'InvalidRequestError Invalid parameters')
            return redirect('/')
        except stripe.error.AuthenticationError as e:
            messages.warning(self.request, 'AuthenticationError Not Authenticated')
            return redirect('/')
        except stripe.error.APIConnectionError as e:
            messages.warning(self.request, 'APIConnectionError Network Error')
            return redirect('/')
        except stripe.error.StripeError as e:
            messages.warning(self.request, 'StripeError something wrong you were not'
                                         'charged. please try again.')
            return redirect('/')
        except Exception as e:
            messages.warning(self.request, 'A serious error occured')
            return redirect('/')

def get_coupon(request,code):
    try:
        coupon=Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        pass

@login_required
def add_coupon_view(request):
    if request.method=='POST':
        form=CouponForm(request.POST)
        if form.is_valid():
            code=form.cleaned_data.get('code')
            coupon_code=get_coupon(request,code)
            if coupon_code:
                order=Order.objects.get(user=request.user,ordered=False)
                order.coupon=coupon_code
                order.save()
                messages.success(request,'coupon applied successfully')
                return redirect(request.META.get('HTTP_REFERER'))
            messages.warning(request,'Invalid promo code')
            return redirect(request.META.get('HTTP_REFERER'))
    return redirect('core:home')
class Request_RefundView(LoginRequiredMixin,View):
    def get(self,*args,**kwargs):
        order=Order.objects.filter(user=self.request.user,ordered=True,recieved=True)
        if order.exists():
            rform=RefundForm()
            return render(self.request,'request-refund.html',{'rform':rform})
        messages.warning(self.request,'Your item not delivered yet')
        return redirect('core:home')
    def post(self,*args,**kwargs):
        rform=RefundForm(self.request.POST)
        if rform.is_valid():
            ref_code=rform.cleaned_data.get('ref_code')
            message=rform.cleaned_data.get('message')
            email=rform.cleaned_data.get('email')
            # edit the order
            try:
                order=Order.objects.get(ref_code=ref_code)
                order.refund_requested=True
                order.save()
            #store the refund model
                refund=Rfund()
                refund.order=order
                refund.reason=message
                refund.email=email
                refund.save()
                messages.success(self.request,'Your request was received')
            except ObjectDoesNotExist:
                messages.info(self.request,'Order does not exist.')
                return redirect('/')

def signup(self, request, user):
	user.first_name = self.cleaned_data['first_name']
	user.last_name = self.cleaned_data['last_name']
	user.save()
	return user
@login_required
def MyOrders(request):
    try:
        myorders=Order.objects.filter(user=request.user,ordered=True)
        return render(request,'myorders.html',{'myorders':myorders})
    except ObjectDoesNotExist:
        messages.info(request,'No orders')
        return redirect('/')

