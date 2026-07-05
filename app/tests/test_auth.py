import pytest
import uuid
from httpx import AsyncClient
from fastapi import status
from app.main import app
from app.dependencies.auth import get_current_user
from app.schemas.users import SUserOut
import datetime
import jwt
from app.config import settings 


@pytest.fixture
def unique_email():
    return f"user_{uuid.uuid4().hex[:8]}@example.com"


@pytest.mark.anyio
async def test_registration_fails_on_invalid_pydantic_form_fields(async_http_test_client: AsyncClient):
    invalid_form_payload = {
        "email": "not_an_email_address",
        "password": "123",
        "confirmPassword": "321"
    }
    response = await async_http_test_client.post("/api/auth/user", data=invalid_form_payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_json = response.json()
    assert "message" in response_json
    assert isinstance(response_json["message"], str)


@pytest.mark.anyio
async def test_registration_fails_on_password_mismatch(async_http_test_client: AsyncClient, unique_email: str):
    mismatch_payload = {
        "email": unique_email,
        "password": "correct_password_123",
        "confirmPassword": "different_password_456"
    }
    response = await async_http_test_client.post("/api/auth/user", data=mismatch_payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_json = response.json()
    assert "message" in response_json
    assert "Passwords do not match" in response_json["message"]


@pytest.mark.anyio
async def test_registration_succeeds_and_sets_secure_auth_cookies(async_http_test_client: AsyncClient, unique_email: str):
    valid_payload = {
        "email": unique_email,
        "password": "strong_password_123",
        "confirmPassword": "strong_password_123"
    }
    response = await async_http_test_client.post("/api/auth/user", data=valid_payload)
    
    assert response.status_code == status.HTTP_200_OK
    
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.anyio
async def test_registration_fails_on_duplicate_email(async_http_test_client: AsyncClient, unique_email: str):
    payload = {
        "email": unique_email,
        "password": "strong_password_123",
        "confirmPassword": "strong_password_123"
    }
    first_resp = await async_http_test_client.post("/api/auth/user", data=payload)
    assert first_resp.status_code == status.HTTP_200_OK
    
    second_resp = await async_http_test_client.post("/api/auth/user", data=payload)
    
    assert second_resp.status_code == status.HTTP_409_CONFLICT
    assert second_resp.json() == {"message": "This email is already taken"}


@pytest.mark.anyio
async def test_login_fails_with_invalid_credentials(async_http_test_client: AsyncClient, unique_email: str):
    reg_payload = {
        "email": unique_email,
        "password": "correct_password_123",
        "confirmPassword": "correct_password_123"
    }
    await async_http_test_client.post("/api/auth/user", data=reg_payload)
    
    wrong_login_payload = {
        "email": unique_email,
        "password": "wrong_password_999"
    }
    response = await async_http_test_client.post("/api/auth/session", data=wrong_login_payload)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"message": "Invalid credentials"}


@pytest.mark.anyio
async def test_get_user_profile_returns_valid_json_for_authenticated_session(async_http_test_client: AsyncClient):
    local_email = "profile_tester@example.com"
    
    async def mock_get_current_user():
        return SUserOut(id=1, email=local_email)
        
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    try:
        response = await async_http_test_client.get("/api/auth/user")
        
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        
        assert "id" in response_json
        assert response_json["email"] == local_email
        
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_profile_fails_without_authentication(async_http_test_client: AsyncClient):
    response = await async_http_test_client.get("/api/auth/user")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response_json = response.json()
    assert "message" in response_json


@pytest.mark.anyio
async def test_logout_invalidates_session_and_wipes_client_cookies(async_http_test_client: AsyncClient, unique_email: str):
    payload = {
        "email": unique_email,
        "password": "strong_password_123",
        "confirmPassword": "strong_password_123"
    }
    await async_http_test_client.post("/api/auth/user", data=payload)
    
    logout_response = await async_http_test_client.delete("/api/auth/session")
    assert logout_response.status_code == status.HTTP_204_NO_CONTENT
    
    profile_response = await async_http_test_client.get("/api/auth/user")
    assert profile_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_registration_fails_on_missing_required_fields(async_http_test_client: AsyncClient):
    empty_payload = {} 
    response = await async_http_test_client.post("/api/auth/user", data=empty_payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_json = response.json()
    assert "message" in response_json
    assert isinstance(response_json["message"], str)


@pytest.mark.anyio
async def test_login_fails_on_non_existent_user(async_http_test_client: AsyncClient):
    ghost_payload = {
        "email": "ghost_user_999@example.com",
        "password": "some_password_123"
    }
    response = await async_http_test_client.post("/api/auth/session", data=ghost_payload)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"message": "Invalid credentials"}


@pytest.mark.anyio
async def test_protected_route_fails_with_malformed_token(async_http_test_client: AsyncClient):
    async_http_test_client.cookies.set("access_token", "invalid_broken_token_string_xyz")
    
    response = await async_http_test_client.get("/api/auth/user")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response_json = response.json()
    assert "message" in response_json
    assert "Session expired" in response_json["message"] or "User not found" in response_json["message"]


@pytest.mark.anyio
async def test_protected_route_fails_with_expired_token(async_http_test_client: AsyncClient):  
    expire = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=10)
    to_encode = {
        "sub": "1", 
        "type": "access", 
        "exp": expire
    }
    
    expired_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    async_http_test_client.cookies.set("access_token", expired_jwt)
    
    response = await async_http_test_client.get("/api/auth/user")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "message" in response.json()

