from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from .models import Brand, Profile

User = get_user_model()


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug"]


class MeSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(source="profile.brand", read_only=True)
    role = serializers.CharField(source="profile.role", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "brand", "role"]


class RegisterSerializer(serializers.Serializer):
    """Creates a user together with a brand they own (one request, one transaction)."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    brand_name = serializers.CharField(max_length=120)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is taken.")
        return value

    def validate_brand_name(self, value):
        if Brand.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A brand with this name already exists.")
        if not slugify(value):
            raise serializers.ValidationError("Brand name must contain letters or numbers.")
        return value

    def validate(self, attrs):
        validate_password(attrs["password"], User(username=attrs["username"]))
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        brand = Brand.objects.create(name=validated_data["brand_name"], slug=slugify(validated_data["brand_name"]))
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        Profile.objects.create(user=user, brand=brand, role=Profile.Role.OWNER)
        return user
