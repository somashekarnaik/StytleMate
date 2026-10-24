import unittest

from app.core.auth import (
    create_session_token,
    get_session_user_id,
    hash_password,
    verify_password,
)


class AuthenticationTests(unittest.TestCase):
    def test_password_hash_verifies_only_the_original_password(self) -> None:
        encoded = hash_password("correct horse battery staple")

        self.assertTrue(verify_password("correct horse battery staple", encoded))
        self.assertFalse(verify_password("incorrect password", encoded))

    def test_session_token_contains_signed_user_identity(self) -> None:
        token = create_session_token(42)

        self.assertEqual(get_session_user_id(token), 42)
        payload, signature = token.split(".")
        tampered = f"{payload[:-1]}x.{signature}"
        self.assertIsNone(get_session_user_id(tampered))


if __name__ == "__main__":
    unittest.main()
