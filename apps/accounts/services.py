"""
apps/accounts/services.py
──────────────────────────
Service Layer for the accounts domain.

Design Patterns applied:
  • Service Layer  — all business logic lives here, not in views/serializers
  • Unit of Work   — multi-step writes wrapped in @transaction.atomic
  • SRP            — each class has exactly one reason to change

Views and serializers are pure I/O adapters; they delegate all decisions here.
"""

from __future__ import annotations

from django.db import transaction

from .exceptions import DuplicateEmailError, InvalidRoleDataError
from .models import Role
from .repositories import LearnerRepository, SchoolRepository, UserRepository


class UserRegistrationService:
    """
    Orchestrates the full user registration flow.

    Responsibilities:
      1. Validate uniqueness (email).
      2. Create the User row.
      3. If role=LEARNER: resolve/create School, create Learner profile.

    All three steps execute inside a single database transaction (Unit of Work).
    If step 3 fails, steps 1-2 are rolled back — no orphaned User rows.
    """

    @staticmethod
    @transaction.atomic
    def register(data: dict):
        """
        Registers a new user.

        Args:
            data: Validated dict with keys: email, password, username, first_name,
                  last_name, role, and (for LEARNER) class_level, school_name,
                  region, district.

        Returns:
            The newly created User instance.

        Raises:
            DuplicateEmailError: If the email is already registered.
            InvalidRoleDataError: If required learner fields are missing.
        """
        email = data["email"]

        if UserRepository.email_exists(email):
            raise DuplicateEmailError(f"Email '{email}' is already registered.")

        role = data.get("role", Role.LEARNER)

        if role == Role.LEARNER:
            required_fields = ["class_level", "school_name", "region", "district"]
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                raise InvalidRoleDataError(
                    f"Learner registration requires: {', '.join(missing)}."
                )

        username = data.get("username") or email.split("@")[0]

        user = UserRepository.create_user(
            username=username,
            email=email,
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            role=role,
        )

        if role == Role.LEARNER:
            school, _ = SchoolRepository.get_or_create(
                school_name=data["school_name"],
                region=data["region"],
                district=data["district"],
            )
            LearnerRepository.create(
                user=user,
                school=school,
                class_level=data["class_level"],
            )

        return user


class LearnerProfileService:
    """
    Handles learner-specific profile mutations.
    """

    @staticmethod
    def update_class_level(user, class_level: str):
        """
        Updates a learner's class level.

        Args:
            user: The User instance (must have a learner_profile relation).
            class_level: New class level string (e.g. 'S4').

        Returns:
            Updated Learner instance, or None if user has no learner profile.
        """
        if not hasattr(user, "learner_profile"):
            return None
        return LearnerRepository.update_class_level(user.learner_profile, class_level)
