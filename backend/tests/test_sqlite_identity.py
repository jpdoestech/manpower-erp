"""Run the existing identity acceptance cases unchanged on disposable SQLite."""

from collections.abc import Iterator
from tempfile import TemporaryDirectory

import pytest
from test_account_controls import (
    admins,
    test_admin_access_denies_anonymous_ordinary_forged_headers_and_csrf,
    test_admin_throttle_and_pair_preservation,
    test_bootstrap_cli_is_atomic_one_time_and_hidden,
    test_bootstrap_duplicate_rolls_back_and_concurrency,
    test_bootstrap_rolls_back_first_account_when_second_conflicts,
    test_concurrent_approval_issues_only_one_token,
    test_concurrent_token_redemption_is_single_use,
    test_deactivate_and_unlock_are_independently_approved,
    test_invalidated_recovery_fails_generically,
    test_recovery_rate_limit_origin_validation_and_no_auto_login,
    test_registration_requires_admin_and_distinct_approval,
    test_requester_revoked_or_request_expired,
    test_reset_hash_single_use_and_session_revocation,
    test_target_cannot_approve_own_reset_and_actors_rechecked,
)
from test_identity import (
    api,
    client,
    log_output,
    migrated,
    test_cli_confirmation_mismatch_creates_no_user,
    test_credentials_fail_generically_and_are_audited,
    test_current_head_and_safe_empty_downgrade,
    test_expired_and_deactivated_sessions_fail_immediately,
    test_global_limit_and_concurrent_name_limit,
    test_login_cookie_self_identity_and_no_company_grants,
    test_origin_and_payload_privilege_injection_are_rejected,
    test_password_change_and_operator_reset_revoke_sessions,
    test_password_change_revokes_other_sessions,
    test_password_token_and_username_are_absent_from_logs,
    test_per_name_attempt_limits_and_window_reset,
    test_populated_downgrade_refuses_to_destroy_identity,
    test_rotation_logout_csrf_and_replay,
    test_secure_cookie_and_cross_user_csrf,
    test_user_uniqueness_and_cli_prompts,
)

from app.database import LOCAL_DIRECTORY

__all__ = [
    "admins",
    "test_admin_access_denies_anonymous_ordinary_forged_headers_and_csrf",
    "test_admin_throttle_and_pair_preservation",
    "test_bootstrap_cli_is_atomic_one_time_and_hidden",
    "test_bootstrap_duplicate_rolls_back_and_concurrency",
    "test_bootstrap_rolls_back_first_account_when_second_conflicts",
    "test_concurrent_approval_issues_only_one_token",
    "test_concurrent_token_redemption_is_single_use",
    "test_deactivate_and_unlock_are_independently_approved",
    "test_invalidated_recovery_fails_generically",
    "test_recovery_rate_limit_origin_validation_and_no_auto_login",
    "test_registration_requires_admin_and_distinct_approval",
    "test_requester_revoked_or_request_expired",
    "test_reset_hash_single_use_and_session_revocation",
    "test_target_cannot_approve_own_reset_and_actors_rechecked",
    "api",
    "client",
    "log_output",
    "migrated",
    "test_cli_confirmation_mismatch_creates_no_user",
    "test_credentials_fail_generically_and_are_audited",
    "test_current_head_and_safe_empty_downgrade",
    "test_expired_and_deactivated_sessions_fail_immediately",
    "test_global_limit_and_concurrent_name_limit",
    "test_login_cookie_self_identity_and_no_company_grants",
    "test_origin_and_payload_privilege_injection_are_rejected",
    "test_password_change_and_operator_reset_revoke_sessions",
    "test_password_change_revokes_other_sessions",
    "test_password_token_and_username_are_absent_from_logs",
    "test_per_name_attempt_limits_and_window_reset",
    "test_populated_downgrade_refuses_to_destroy_identity",
    "test_rotation_logout_csrf_and_replay",
    "test_secure_cookie_and_cross_user_csrf",
    "test_user_uniqueness_and_cli_prompts",
]


@pytest.fixture
def disposable_database(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    LOCAL_DIRECTORY.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="sqlite-test-", dir=LOCAL_DIRECTORY) as directory:
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("DATABASE_MODE", "sqlite")
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{directory}/test.db")
        monkeypatch.setenv("AUTH_PROVIDER", "local")
        yield
