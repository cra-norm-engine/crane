from uuid import uuid4

import pytest

from app.api.deps import get_current_user
from app.core.exceptions import ConflictException, ForbiddenException
from app.main import app
from app.models.manual_task import TaskNotification
from app.models.user import User
from app.schemas.comment import CommentCreate
from app.schemas.my_tasks import ManualTaskCreate, ManualTaskUpdate
from app.services.comment_service import CommentService
from app.services.manual_task_service import ManualTaskService


def test_manual_task_post_and_patch_routes(client, db_session) -> None:
    suffix = uuid4().hex
    creator = User(email=f"route-{suffix}@example.com", full_name="Route User", hashed_password="unused")
    db_session.add(creator)
    db_session.flush()
    app.dependency_overrides[get_current_user] = lambda: creator

    created = client.post("/api/v1/my-tasks/", json={"title": "Draft task"})
    assert created.status_code == 201

    updated = client.patch(
        f"/api/v1/my-tasks/{created.json()['entity_id']}",
        json={"title": "Edited task", "priority": "low"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Edited task"


def test_delegated_task_lifecycle_is_visible_and_auditable(db_session) -> None:
    suffix = uuid4().hex
    creator = User(email=f"creator-{suffix}@example.com", full_name="Creator", hashed_password="unused")
    assignee = User(email=f"assignee-{suffix}@example.com", full_name="Assignee", hashed_password="unused")
    db_session.add_all([creator, assignee])
    db_session.flush()

    service = ManualTaskService(db_session)
    task = service.create(ManualTaskCreate(title="Review release", priority="high", assigned_to_user_id=assignee.id), creator)

    assert task in service.list(creator, scope="assigned_by_me", state="open")
    task = service.update(task.id, ManualTaskUpdate(title="Review release evidence"), creator)
    assert task.title == "Review release evidence"
    assert task.assigned_to_user_id == assignee.id
    with pytest.raises(ForbiddenException):
        service.set_status(task.id, "in_progress", creator)

    completed = service.complete(task.id, "Review evidence accepted", assignee)
    assert completed.completed_at is not None
    assert completed.completed_by_user_id == assignee.id
    assert db_session.query(TaskNotification).filter_by(manual_task_id=task.id, recipient_user_id=creator.id, event_type="completed").one()

    CommentService(db_session).create_comment(CommentCreate(entity_type="manual_task", entity_id=task.id, body="Thanks"), creator)
    assert db_session.query(TaskNotification).filter_by(manual_task_id=task.id, recipient_user_id=assignee.id, event_type="commented").one()

    service.archive(task.id, "Superseded", creator)
    with pytest.raises(ConflictException):
        CommentService(db_session).create_comment(CommentCreate(entity_type="manual_task", entity_id=task.id, body="Too late"), assignee)
