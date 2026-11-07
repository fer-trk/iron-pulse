import pytest
from pydantic import ValidationError

from app.core.config import DEVELOPMENT_SECRET, Settings


@pytest.mark.parametrize("secret", ["", "short", " " * 40, DEVELOPMENT_SECRET,
                                      "your-secret-key-min-32-chars-here"])
def test_production_rejects_missing_weak_or_example_secret(secret):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, DEBUG=False, SECRET_KEY=secret)


def test_production_accepts_explicit_private_key():
    config = Settings(_env_file=None, DEBUG=False, SECRET_KEY="test-only-private-key-with-more-than-32-characters")
    assert not config.DEBUG


def test_development_can_use_documented_development_key():
    config = Settings(_env_file=None, DEBUG=True, SECRET_KEY=DEVELOPMENT_SECRET)
    assert config.SECRET_KEY == DEVELOPMENT_SECRET


@pytest.mark.parametrize("field", ["ACCESS_TOKEN_EXPIRE_MINUTES", "REFRESH_TOKEN_EXPIRE_DAYS"])
def test_token_lifetime_must_be_positive(field):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, DEBUG=True, **{field: 0})
