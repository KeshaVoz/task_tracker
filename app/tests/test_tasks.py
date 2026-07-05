from datetime import date, datetime, timedelta, timezone

import pytest
import uuid
from httpx import AsyncClient
from fastapi import status
from app.auth.token_service import TokenService
from app.dao.tasks import TaskDAO
from app.dao.users import UserDAO
from app.services.tasks import TaskService

@pytest.fixture
async def authenticated_client(async_http_test_client: AsyncClient, monkeypatch):
    unique_email = f"task_user_{uuid.uuid4().hex[:8]}@example.com"

    user = await UserDAO.add(
        email=unique_email,
        hashed_password="fake_hashed_password" 
    )
    
    user_id = user.id if hasattr(user, 'id') else 1

    token = TokenService.create_access_token(user_id=user_id)

    async_http_test_client.cookies.set("access_token", token)
    
    async_http_test_client.cookies.set("access_token", token, domain="test", path="/")

    class MockUser:
        id = user_id
        email = unique_email

    monkeypatch.setattr(
        "app.dependencies.auth.get_current_user", 
        lambda: MockUser()
    )
    
    return async_http_test_client


@pytest.mark.anyio
async def test_create_task_success(authenticated_client: AsyncClient):
    form_data = {
        "title": "Do smth",
        "text": "Somewhere",
        "isCompleted": "false"
    }
    
    response = await authenticated_client.post("/api/task", data=form_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    json_data = response.json()
    
    assert json_data["id"] is not None
    assert json_data["title"] == "Do smth"
    assert json_data["text"] == "Somewhere"
    assert json_data["isCompleted"] is False
    assert json_data["completedAt"] is None


@pytest.mark.anyio
async def test_create_task_validation_error(authenticated_client: AsyncClient):
    form_data = {
        "text": "Title forgotten"
    }
    
    response = await authenticated_client.post("/api/task", data=form_data)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    json_data = response.json()
    
    assert "message" in json_data
    assert "Field required" in json_data["message"]


@pytest.mark.anyio
async def test_patch_task_text_debounce(authenticated_client: AsyncClient):
    task = await TaskDAO.add(title="Old title", text="Old text", owner_id=1, is_completed=False)
    
    patch_data = {
        "id": task.id,
        "text": "New text"
    }
    response = await authenticated_client.patch("/api/task", data=patch_data)
    
    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["text"] == "New text"
    assert json_data["title"] == "Old title"
    assert json_data["isCompleted"] is False
    assert json_data["completedAt"] is None


@pytest.mark.anyio
async def test_patch_task_checkbox_toggle(authenticated_client: AsyncClient):
    task = await TaskDAO.add(title="Задача", owner_id=1, is_completed=False)
    
    response = await authenticated_client.patch("/api/task", data={"id": task.id, "isCompleted": "true"})
    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["isCompleted"] is True
    assert json_data["completedAt"] is not None

    response = await authenticated_client.patch("/api/task", data={"id": task.id, "isCompleted": "false"})
    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["isCompleted"] is False
    assert json_data["completedAt"] is None


@pytest.mark.anyio
async def test_patch_or_delete_foreign_task(authenticated_client: AsyncClient):
    foreign_task = await TaskDAO.add(title="Not your task", owner_id=999, is_completed=False)
    
    patch_response = await authenticated_client.patch("/api/task", data={"id": foreign_task.id, "title": "Взлом"})
    assert patch_response.status_code == status.HTTP_404_NOT_FOUND
    assert patch_response.json()["message"] == "Task not found or you don't have permission to modify it."

    delete_response = await authenticated_client.request("DELETE", "/api/task", data={"id": foreign_task.id})
    assert delete_response.status_code == status.HTTP_404_NOT_FOUND
    assert delete_response.json()["message"] == "Task not found or you don't have permission to delete it."


@pytest.mark.anyio
async def test_delete_task_success(authenticated_client: AsyncClient):
    task = await TaskDAO.add(title="To del", owner_id=1, is_completed=False)
    
    response = await authenticated_client.request("DELETE", "/api/task", data={"id": task.id})
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.text == ""
    
    db_task = await TaskDAO.find_one_or_none(id=task.id)
    assert db_task is None


@pytest.mark.anyio
async def test_patch_non_existent_task(authenticated_client: AsyncClient):
    patch_data = {
        "id": 99999,
        "text": "Patch try"
    }
    response = await authenticated_client.patch("/api/task", data=patch_data)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Task not found" in response.json()["message"]


@pytest.mark.anyio
async def test_daily_analytics_edge_cases(authenticated_client: AsyncClient):
    user_id = 1
    yesterday_date = date.today() - timedelta(days=1)
    
    yesterday_datetime = datetime.combine(yesterday_date, datetime.min.time(), tzinfo=timezone.utc)
    await TaskDAO.add(title="Completed yesterday", owner_id=user_id, is_completed=True, completed_at=yesterday_datetime)
    
    await TaskDAO.add(title="Completed today", owner_id=user_id, is_completed=True, completed_at=datetime.now(timezone.utc))
    
    for i in range(6):
        await TaskDAO.add(title=f"Active task {i}", owner_id=user_id, is_completed=False)

    analytics_data = TaskService.get_user_daily_analytics(user_id=user_id, yesterday=yesterday_date)
    
    assert analytics_data.total_pending == 6
    
    assert len(analytics_data.pending_titles) == 5
    
    assert analytics_data.pending_titles[0] == "Active task 0"
    
    assert analytics_data.completed_count == 1
    assert analytics_data.completed_titles == ["Completed yesterday"]