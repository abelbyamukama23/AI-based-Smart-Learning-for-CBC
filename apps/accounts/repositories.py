"""
apps/accounts/repositories.py
──────────────────────────────
Repository Pattern — isolates all ORM query logic for the accounts domain.

Design Principles applied:
  • SRP  — queries live here, not in views or serializers
  • OCP  — add new query methods without touching callers
  • DIP  — views/services depend on the repository abstraction, not raw ORM
"""

from __future__ import annotations

from django.db.models import QuerySet

from .models import User, Learner, School


class UserRepository:
    """All database access operations for the User model."""

    @staticmethod
    def get_by_id(user_id) -> User:
        """Fetch a user by primary key; raises User.DoesNotExist on miss."""
        return User.objects.select_related("learner_profile__school").get(pk=user_id)

    @staticmethod
    def get_by_email(email: str) -> User:
        """Fetch a user by email address; raises User.DoesNotExist on miss."""
        return User.objects.select_related("learner_profile__school").get(email=email)

    @staticmethod
    def email_exists(email: str) -> bool:
        return User.objects.filter(email=email).exists()

    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        role: str = "",
    ) -> User:
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
        )


class SchoolRepository:
    """All database access operations for the School model."""

    @staticmethod
    def get_or_create(school_name: str, region: str, district: str) -> tuple[School, bool]:
        """
        Return (school, created).  Uses get_or_create so concurrent registrations
        from the same school don't race and produce duplicates.
        """
        return School.objects.get_or_create(
            school_name=school_name,
            defaults={"region": region, "district": district},
        )


class LearnerRepository:
    """All database access operations for the Learner model."""

    @staticmethod
    def create(user: User, school: School, class_level: str) -> Learner:
        return Learner.objects.create(user=user, school=school, class_level=class_level)

    @staticmethod
    def update_class_level(learner: Learner, class_level: str) -> Learner:
        learner.class_level = class_level
        learner.save(update_fields=["class_level"])
        return learner
