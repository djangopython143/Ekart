from django.contrib import admin
from . models import Item,OrderItem,Order,Payment,Coupon,Rfund,Address

def Orders_to_update_refund_status(modeladmin,request,quaryset):
    quaryset.update(refund_granted=True)
Orders_to_update_refund_status.short_description='update refund status'

def set_discount(modeladmin,request,quaryset):
    quaryset.update(discount_percent=20)
set_discount.short_description='set discount 20'
class ItemAdmin(admin.ModelAdmin):
    list_display=['title',
                  'price',
                  'discount_percent',
                  'catagory',
                  'image',
                  'description',
                  'slug']
    actions = [set_discount]

class OdrderAdmin(admin.ModelAdmin):
    list_display = ['user','ref_code','ordered','being_delivered','recieved',
                    'refund_requested','refund_granted',
                    'billing_address','shipping_address','payment','coupon']
    list_filter = ['user','ordered','being_delivered','recieved',
                    'refund_requested','refund_granted']
    list_display_links = ['user','billing_address','payment','coupon']
    search_fields = ['user__username','ref_code']
    actions = [Orders_to_update_refund_status]

class AddressAdmin(admin.ModelAdmin):
    list_display = ['user','name','mobile','address','landmark','country','zip',
                    'Address_type','default']

admin.site.register(Item,ItemAdmin)
admin.site.register(OrderItem)
admin.site.register(Order,OdrderAdmin)
admin.site.register(Payment)
admin.site.register(Rfund)
admin.site.register(Coupon)
admin.site.register(Address,AddressAdmin)