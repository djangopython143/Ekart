from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from allauth.account.forms import SignupForm

class CustomSignupForm(SignupForm):
	first_name = forms.CharField(max_length=30, label='First Name',
                                 widget=forms.TextInput(attrs={
                                     'placeholder':'First Name'
                                 }))
	last_name = forms.CharField(max_length=30, label='Last Name',
                                widget=forms.TextInput(attrs={
                                    'placeholder': 'Last Name'
                                }))

PAYMENT_CHOICES=(
    ('S','Stripe'),
    ('P','PayPal'),
)
class CheckoutForm(forms.Form):
    shipping_name=forms.CharField(required=False)
    shipping_mobile=forms.CharField(required=False)
    shipping_address=forms.CharField(required=False)
    shipping_landmark=forms.CharField(required=False)
    shipping_country=CountryField(blank_label='Select Country').formfield(required=False,
        widget=CountrySelectWidget(attrs={'class':'custom-select d-block w-100'}))
    shipping_zip=forms.CharField(required=False)
    same_billing_address=forms.BooleanField(required=False)
    set_default_shipping=forms.BooleanField(required=False)
    use_default_shipping=forms.BooleanField(required=False)

    Billing_name = forms.CharField(required=False)
    Billing_mobile = forms.CharField(required=False)
    Billing_address = forms.CharField(required=False)
    Billing_landmark = forms.CharField(required=False)
    Billing_country = CountryField(blank_label='Select Country').formfield(required=False,
        widget=CountrySelectWidget(attrs={'class': 'custom-select d-block w-100'})
    )
    Billing_zip = forms.CharField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)

    save_info=forms.BooleanField(required=False)
    payment_option=forms.ChoiceField(choices=PAYMENT_CHOICES,widget=forms.RadioSelect())

class CouponForm(forms.Form):
    code=forms.CharField(widget=forms.TextInput(
        attrs={'class':'form-control','placeholder':'Promo Code Eg:FIRST10',
               'aria-label':"Recipient's username", 'aria-describedby':"basic-addon2"}
    ))


class RefundForm(forms.Form):
    ref_code=forms.CharField()
    message=forms.CharField(widget=forms.Textarea(attrs={'rows':4}))
    email=forms.EmailField()

