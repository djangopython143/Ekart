from django.template import Library
from core.models import Order,OrderItem,Item


register=Library()

@register.filter
def cart_item_count(user):
    if user.is_authenticated:
        qs=Order.objects.filter(user=user,ordered=False)
        if qs.exists():
            return qs[0].items.count()
    return 0

@register.filter
def perticular_item(userid,id):
    qs=len(OrderItem.objects.filter(user_id=userid,item_id=id,ordered=False))
    # qs = len(Order.objects.get(user=userid, ordered=False))
    if qs!=0:
        return 1
    return 0
@register.filter
def highlight(id):
    qs=Item.objects.get(id=id)
    li=qs.highlights.split('\n')
    return li





