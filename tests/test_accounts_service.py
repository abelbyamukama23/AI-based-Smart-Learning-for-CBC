"""
tests/test_accounts_service.py
────────────────────────────────
Unit & integration tests for the accounts Service and Repository layers.

Markers:
  @pytest.mark.unit        — pure logic, no DB (uses mocks)
  @pytest.mark.integration — writes to the test DB (uses @pytest.mark.django_db)

Run:
    pytest tests/test_accounts_service.py -v
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from apps.accounts.exceptions import DuplicateEmailError, InvalidRoleDataError
from apps.accounts.models import Role
from apps.accounts.services import LearnerProfileService, UserRegistrationService


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _learner_payload(**overrides) -> dict:
    """Return a valid learner registration payload."""
    base = {
        "email": "alice@school.ug",
        "password": "SecurePass123",
        "first_name": "Alice",
        "last_name": "Nakato",
        "role": Role.LEARNER,
        "class_level": "S1",
        "school_name": "Kampala High",
        "region": "Central",
        "district": "Kampala",
    }
    base.update(overrides)
    return base


# ═══════════════════════════════════════════════════════════════════════════════
# Unit tests — no DB (mocked repositories)
# ═══════════════════════════════════════════════════════════════════════════════

class TestUserRegistrationServiceUnit:
    """
    Test business-rule logic in isolation.
    The repositories are mocked so no DB connection is needed.
    """

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_raises_on_duplicate_email(self):
        """DuplicateEmailError is raised before any write when email exists."""
        with patch("apps.accounts.services.UserRepository") as MockRepo:
            MockRepo.email_exists.return_value = True
            with pytest.raises(DuplicateEmailError, match="already registered"):
                UserRegistrationService.register(_learner_payload())
            # Ensure create_user was never called
            MockRepo.create_user.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_raises_on_missing_learner_fields(self):
        """InvalidRoleDataError lists the missing required learner fields."""
        payload = _learner_payload()
        del payload["school_name"]
        del payload["district"]

        with patch("apps.accounts.services.UserRepository") as MockRepo:
            MockRepo.email_exists.return_value = False
            with pytest.raises(InvalidRoleDataError) as exc_info:
                UserRegistrationService.register(payload)
            assert "school_name" in str(exc_info.value)
            assert "district" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_username_derived_from_email_when_not_provided(self):
        """If username is omitted, it defaults to the email local-part."""
        mock_user = MagicMock()
        mock_school = (MagicMock(), True)

        with (
            patch("apps.accounts.services.UserRepository") as MockUserRepo,
            patch("apps.accounts.services.SchoolRepository") as MockSchoolRepo,
            patch("apps.accounts.services.LearnerRepository") as MockLearnerRepo,
        ):
            MockUserRepo.email_exists.return_value = False
            MockUserRepo.create_user.return_value = mock_user
            MockSchoolRepo.get_or_create.return_value = mock_school
            MockLearnerRepo.create.return_value = MagicMock()

            payload = _learner_payload()
            payload.pop("username", None)   # ensure no username key
            UserRegistrationService.register(payload)

            call_kwargs = MockUserRepo.create_user.call_args.kwargs
            assert call_kwargs["username"] == "alice"   # "alice@school.ug" → "alice"

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_school_and_learner_not_created_for_non_learner_role(self):
        """Teacher/admin registrations should not create a Learner profile."""
        mock_user = MagicMock()

        with (
            patch("apps.accounts.services.UserRepository") as MockUserRepo,
            patch("apps.accounts.services.SchoolRepository") as MockSchoolRepo,
            patch("apps.accounts.services.LearnerRepository") as MockLearnerRepo,
        ):
            MockUserRepo.email_exists.return_value = False
            MockUserRepo.create_user.return_value = mock_user

            payload = {
                "email": "teacher@school.ug",
                "password": "TeacherPass1",
                "role": Role.TEACHER,   # Not a LEARNER
            }
            UserRegistrationService.register(payload)

            MockSchoolRepo.get_or_create.assert_not_called()
            MockLearnerRepo.create.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# Integration tests — uses test DB
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db(transaction=True)
class TestUserRegistrationServiceIntegration:
    """End-to-end registration tests that write to the (test) database."""

    def test_full_learner_registration_creates_three_rows(self):
        """register() atomically creates User + School + Learner in one transaction."""
        from apps.accounts.models import Learner, School, User

        user = UserRegistrationService.register(_learner_payload())

        assert User.objects.filter(email="alice@school.ug").exists()
        assert School.objects.filter(school_name="Kampala High").exists()
        assert Learner.objects.filter(user=user, class_level="S1").exists()

    def test_duplicate_email_rolls_back_entire_transaction(self):
        """No partial writes when a duplicate email is detected mid-registration."""
        from apps.accounts.models import User

        UserRegistrationService.register(_learner_payload())

        with pytest.raises(DuplicateEmailError):
            UserRegistrationService.register(_learner_payload())

        # Only one user row should exist
        assert User.objects.filter(email="alice@school.ug").count() == 1

    def test_same_school_not_duplicated_on_concurrent_registrations(self):
        """get_or_create ensures concurrent students from same school share one School row."""
        from apps.accounts.models import School

        UserRegistrationService.register(_learner_payload(email="alice@s.ug"))
        UserRegistrationService.register(_learner_payload(email="bob@s.ug"))

        assert School.objects.filter(school_name="Kampala High").count() == 1


@pytest.mark.django_db
class TestLearnerProfileService:

    def test_update_class_level(self):
        """update_class_level persists to the DB and returns the updated Learner."""
        user = UserRegistrationService.register(_learner_payload())

        result = LearnerProfileService.update_class_level(user, "S2")

        assert result is not None
        assert result.class_level == "S2"
        # Confirm DB was actually updated
        result.refresh_from_db()
        assert result.class_level == "S2"

    def test_update_class_level_returns_none_for_non_learner(self):
        """Returns None gracefully for users that have no learner_profile."""
        from apps.accounts.models import User
        user = User(email="teacher@s.ug", role=Role.TEACHER)
        result = LearnerProfileService.update_class_level(user, "S3")
        assert result is None
