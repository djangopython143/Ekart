from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django_countries.fields import CountryField
import decimal
CATAGORY_CHOICES=(
    ('cl','Clothes'),
    ('fw','Footwear'),
    ('w','Watches'),
    )

ADRESSES=(
    ('b','Billing'),
    ('s','Shipping'),
    )

class Item(models.Model):
    title=models.CharField(max_length=30)
    price=models.DecimalField(decimal_places=2,max_digits=8)
    discount_percent=models.IntegerField(null=True,blank=True)
    catagory=models.CharField(max_length=2,choices=CATAGORY_CHOICES)
    brand=models.CharField(max_length=30)
    highlights=models.TextField()
    sales_package=models.CharField(max_length=30)
    model_num=models.CharField(max_length=30)
    image=models.ImageField(upload_to='media')
    description=models.TextField()
    slug=models.SlugField(blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:product',kwargs={'slug':self.slug})
    def add_to_cart_url(self):
        return reverse('core:add-to-cart',kwargs={'slug':self.slug})
    def remove_from_cart_url(self):
        return reverse('core:remove-from-cart',kwargs={'slug':self.slug})
    def offer_url(self):
        if self.discount_percent:
            discount=self.price*decimal.Decimal(self.discount_percent/100)
            discount=self.price-discount
            return round(discount,2)
        return self.price

class OrderItem(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    ordered=models.BooleanField(default=False)
    item=models.ForeignKey(Item,on_delete=models.CASCADE)
    quantity=models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_price(self):
        return self.quantity*self.item.offer_url()

    def total_saving(self):
        return self.quantity * (self.item.price - self.item.offer_url())
class Order(models.Model):
    ref_code=models.CharField(max_length=20)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    items=models.ManyToManyField(OrderItem)
    start_date=models.DateTimeField(auto_now_add=True)
    ordered_date=models.DateTimeField()
    ordered=models.BooleanField(default=False)
    billing_address=models.ForeignKey('Address',related_name='billing_address',
                                      on_delete=models.SET_NULL,blank=True,null=True)
    shipping_address=models.ForeignKey('Address',related_name='shipping_address',
                                      on_delete=models.SET_NULL,blank=True,null=True)

    payment=models.ForeignKey('Payment',on_delete=models.SET_NULL,blank=True,null=True)
    coupon=models.ForeignKey('Coupon',on_delete=models.SET_NULL,blank=True,null=True)
    being_delivered=models.BooleanField(default=False)
    recieved=models.BooleanField(default=False)
    refund_requested=models.BooleanField(default=False)
    refund_granted=models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    def grand_total_price(self):
        total=0
        for order_item in self.items.all():
            total += order_item.get_total_price()
        return total
    def coupon_disc_total(self):
        total=self.grand_total_price()
        if self.coupon is not None:
            return total - decimal.Decimal(self.coupon.coupon_amount)
        return total

class Address(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    name=models.CharField(max_length=30)
    mobile=models.CharField(max_length=12)
    address=models.TextField(max_length=100)
    landmark=models.CharField(max_length=50)
    country=CountryField(multiple=False)
    zip=models.CharField(max_length=6)
    Address_type=models.CharField(max_length=1,choices=ADRESSES)
    default=models.BooleanField(default=False)


    def __str__(self):
        return self.address
class Payment(models.Model):
    stripe_charge_id=models.CharField(max_length=30)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)
    amount=models.FloatField()
    timestamp=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class Coupon(models.Model):
    code=models.CharField(max_length=15)
    coupon_amount=models.FloatField()

    def __str__(self):
        return self.code


class Rfund(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE)
    reason=models.TextField()
    accepted=models.BooleanField(default=False)
    email=models.EmailField()

    def __str__(self):
        return f"{self.pk}"