from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import User
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework.views import APIView

from rest_framework.parsers import MultiPartParser, FormParser


from .serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    # def post(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     user = serializer.save()
    #     refresh = RefreshToken.for_user(user)
    #     return Response(
    #         {
    #             "user": UserSerializer(user).data,
    #             "refresh": str(refresh),
    #             "access": str(refresh.access_token),
    #         },
    #         status=status.HTTP_201_CREATED,
    #     )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.is_email_verified = False
        user.email_verification_token = get_random_string(64)
        user.save()

        # Send verification email
        send_mail(
            "Verify Your Email",
            f"Click to verify: http://localhost:3000/verify-email?token={user.email_verification_token}&email={user.email}",
            "noreply@jobboard.com",
            [user.email],
            fail_silently=False,
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "message": "Please verify your email",
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
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
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

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
                {"error": "No user found with this email"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Generate reset token
        token = get_random_string(64)
        user.email_verification_token = token
        user.save()

        # Send email
        send_mail(
            "Password Reset Request",
            f"Your password reset token: {token}\n\nUse this token to reset your password.",
            "noreply@jobboard.com",
            [user.email],
            fail_silently=False,
        )

        return Response(
            {"message": "Password reset link sent to your email"},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        for user in User.objects.all():
            if request.session.get(f"reset_token_{user.id}") == token:
                user.set_password(new_password)
                user.save()
                del request.session[f"reset_token_{user.id}"]
                return Response({"message": "Password reset successful"}, status=200)

        return Response({"error": "Invalid token"}, status=400)


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")
        email = request.data.get("email")

        try:
            user = User.objects.get(email=email)
            if user.email_verification_token == token:
                user.is_email_verified = True
                user.email_verification_token = None
                user.save()
                return Response({"message": "Email verified successfully"}, status=200)
        except User.DoesNotExist:
            pass

        return Response({"error": "Invalid verification token"}, status=400)


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


class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # ← For file upload

    def get_object(self):
        return self.request.user
