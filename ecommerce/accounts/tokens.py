from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    pass

generate_token = EmailVerificationTokenGenerator()