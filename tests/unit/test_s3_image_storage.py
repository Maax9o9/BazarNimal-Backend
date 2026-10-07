"""S3ImageStorage con el cliente de boto3 simulado (Stubber): no necesita una cuenta de R2."""

import re

import pytest
from botocore.stub import ANY, Stubber

from src.core.config.settings import Settings
from src.core.storage.s3_image_storage import S3ImageStorage
from src.shared.contracts.image_storage import InvalidImageError
from tests.helpers import make_png, settings_kwargs

S3_SETTINGS = {
    "storage_driver": "s3",
    "s3_endpoint_url": "https://account123.r2.cloudflarestorage.com",
    "s3_bucket": "bazarnimal-images",
    "s3_access_key_id": "test-access-key",
    "s3_secret_access_key": "test-secret-key",
    "s3_public_base_url": "https://pub-123.r2.dev/",
}


@pytest.fixture
def storage() -> S3ImageStorage:
    return S3ImageStorage(Settings(_env_file=None, **settings_kwargs(**S3_SETTINGS)))


async def test_save_uploads_reencoded_webp(storage):
    with Stubber(storage._client) as stub:
        stub.add_response(
            "put_object",
            {},
            {
                "Bucket": "bazarnimal-images",
                "Key": ANY,
                "Body": ANY,
                "ContentType": "image/webp",
                "CacheControl": ANY,
            },
        )
        relative_url = await storage.save(make_png(), "pets")
        stub.assert_no_pending_responses()

    assert re.fullmatch(r"/uploads/images/pets/[0-9a-f]{32}\.webp", relative_url)
    assert storage.public_url(relative_url) == f"https://pub-123.r2.dev{relative_url}"


async def test_invalid_image_is_rejected_before_upload(storage):
    with Stubber(storage._client) as stub, pytest.raises(InvalidImageError):
        await storage.save(b"not an image", "pets")
        stub.assert_no_pending_responses()


async def test_delete_only_touches_server_generated_keys(storage):
    url = "/uploads/images/pets/" + "a" * 32 + ".webp"
    with Stubber(storage._client) as stub:
        stub.add_response("delete_object", {}, {"Bucket": "bazarnimal-images", "Key": url.lstrip("/")})
        await storage.delete(url)
        await storage.delete("/uploads/images/../../secret.txt")  # ignorado: no es una ruta generada
        await storage.delete(None)
        stub.assert_no_pending_responses()


def test_s3_driver_requires_all_settings():
    with pytest.raises(ValueError, match="S3_BUCKET"):
        Settings(_env_file=None, **settings_kwargs(**{**S3_SETTINGS, "s3_bucket": None}))
