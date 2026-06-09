from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta

from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)
from .utils import generate_verification_token
from .tasks import (
    send_verification_email,
    send_password_reset_email,
    send_welcome_email,
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate verification token
        user.email_verification_token = generate_verification_token()
        user.email_verification_sent_at = timezone.now()
        user.is_email_verified = False
        user.save()

        send_verification_email.delay(
            user.id, user.email, user.email_verification_token
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "message": "Verification email sent. Please verify your email to login.",
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")
        email = request.data.get("email")

        try:
            user = User.objects.get(email=email, email_verification_token=token)

            if user.email_verification_sent_at:
                expiry_time = user.email_verification_sent_at + timedelta(hours=24)
                if timezone.now() > expiry_time:
                    return Response(
                        {"error": "Verification link has expired. Request a new one."},
                        status=400,
                    )

            user.is_email_verified = True
            user.email_verification_token = None
            user.save()

            send_welcome_email.delay(user.id, user.email, user.username)

            return Response(
                {"message": "Email verified successfully. You can now login."},
                status=200,
            )

        except User.DoesNotExist:
            return Response({"error": "Invalid verification token"}, status=400)


class ResendVerificationEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")

        try:
            user = User.objects.get(email=email)

            if user.is_email_verified:
                return Response({"error": "Email already verified"}, status=400)

            user.email_verification_token = generate_verification_token()
            user.email_verification_sent_at = timezone.now()
            user.save()

            send_verification_email.delay(
                user.id, user.email, user.email_verification_token
            )

            return Response({"message": "Verification email resent"}, status=200)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)


class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        # Check if email is verified
        if not user.is_email_verified:
            return Response(
                {"error": "Please verify your email before logging in."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    Supports both JSON and multipart/form-data so tests that send JSON
    (the default in APIClient) don't get 415 Unsupported Media Type.
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"message": "Password changed successfully"}, status=200)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"message": "If an account exists, a reset link has been sent."},
                status=200,
            )

        token = get_random_string(64)
        user.reset_password_token = token
        user.reset_password_sent_at = timezone.now()
        user.save()

        send_password_reset_email.delay(user.id, user.email, token)

        return Response(
            {"message": "Password reset link sent to your email"},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")
        email = request.data.get("email")
        new_password = request.data.get("new_password")

        try:
            user = User.objects.get(email=email, reset_password_token=token)

            if user.reset_password_sent_at:
                expiry_time = user.reset_password_sent_at + timedelta(hours=1)
                if timezone.now() > expiry_time:
                    return Response({"error": "Reset link has expired"}, status=400)

            user.set_password(new_password)
            user.reset_password_token = None
            user.reset_password_sent_at = None
            user.save()

            return Response({"message": "Password reset successful"}, status=200)

        except User.DoesNotExist:
            return Response({"error": "Invalid reset token"}, status=400)


class AdminBlockUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.is_active = False
            user.save()
            return Response({"message": f"User {user.username} blocked"}, status=200)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()
            return Response({"message": f"User {user.username} unblocked"}, status=200)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
