from django.dispatch import receiver
from allauth.account.signals import user_logged_in, user_signed_up
from .views import transfer_session_cart_to_user

@receiver(user_logged_in)
def user_logged_in_handler(request, user, **kwargs):
    transfer_session_cart_to_user(request, user)

@receiver(user_signed_up)
def user_signed_up_handler(request, user, **kwargs):
    transfer_session_cart_to_user(request, user)