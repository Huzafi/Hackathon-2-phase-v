"""
Automated API tests for advanced task management features.

Run with: pytest tests/test_advanced_features.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.main import app
from src.core.database import get_session
from src.models.user import User
from src.models.todo import Todo, PriorityEnum
from src.models.tag import Tag
from src.models.recurrence import RecurrenceRule, RecurrencePattern
from src.models.reminder import Reminder
from datetime import datetime, timedelta


# Test fixtures
@pytest.fixture(name="session")
def session_fixture():
    """Create a new database session for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with database session."""
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def user_fixture(session: Session):
    """Create test user."""
    from src.core.security import create_password_hash
    
    user = User(
        email="test@example.com",
        hashed_password=create_password_hash("Test1234!"),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="auth_token")
def token_fixture(client: TestClient, test_user: User):
    """Get authentication token for test user."""
    response = client.post(
        "/api/auth/signin",
        json={"email": test_user.email, "password": "Test1234!"}
    )
    return response.json()["access_token"]


@pytest.fixture(name="test_task")
def task_fixture(session: Session, test_user: User):
    """Create test task."""
    task = Todo(
        title="Test Task",
        description="Test Description",
        user_id=test_user.id,
        due_date=datetime.utcnow() + timedelta(days=7),
        priority=PriorityEnum.medium,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture(name="test_tag")
def tag_fixture(session: Session, test_user: User):
    """Create test tag."""
    tag = Tag(
        user_id=test_user.id,
        name="test",
        color="#3B82F6",
    )
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


# Test: Due Dates and Priorities
class TestDueDatesAndPriorities:
    """Test due dates and priorities functionality."""
    
    def test_create_task_with_due_date_and_priority(
        self, client: TestClient, auth_token: str
    ):
        """Test creating task with due date and priority."""
        response = client.post(
            "/api/todos",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": "High Priority Task",
                "description": "Due tomorrow",
                "priority": "high",
                "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "High Priority Task"
        assert data["priority"] == "high"
        assert "due_date" in data
    
    def test_create_task_with_invalid_priority(
        self, client: TestClient, auth_token: str
    ):
        """Test creating task with invalid priority."""
        response = client.post(
            "/api/todos",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": "Invalid Task",
                "priority": "invalid_priority"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_filter_tasks_by_priority(
        self, client: TestClient, auth_token: str, test_user: User, session: Session
    ):
        """Test filtering tasks by priority."""
        # Create tasks with different priorities
        for priority in [PriorityEnum.high, PriorityEnum.medium, PriorityEnum.low]:
            task = Todo(
                title=f"{priority.value} Priority Task",
                user_id=test_user.id,
                priority=priority,
            )
            session.add(task)
        session.commit()
        
        # Filter by high priority
        response = client.get(
            "/api/todos?priority=high",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["priority"] == "high"


# Test: Tags
class TestTags:
    """Test tags functionality."""
    
    def test_create_tag(self, client: TestClient, auth_token: str):
        """Test creating a tag."""
        response = client.post(
            "/api/tags",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "urgent",
                "color": "#EF4444"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "urgent"
        assert data["color"] == "#EF4444"
    
    def test_create_duplicate_tag(
        self, client: TestClient, auth_token: str, test_tag: Tag
    ):
        """Test creating duplicate tag (should fail)."""
        response = client.post(
            "/api/tags",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": test_tag.name.upper(),  # Case-insensitive duplicate
                "color": "#EF4444"
            }
        )
        
        assert response.status_code == 400
    
    def test_assign_tag_to_task(
        self, client: TestClient, auth_token: str,
        test_task: Todo, test_tag: Tag
    ):
        """Test assigning tag to task."""
        response = client.put(
            f"/api/todos/{test_task.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": test_task.title,
                "tag_ids": [test_tag.id]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["id"] == test_tag.id


# Test: Recurring Tasks
class TestRecurringTasks:
    """Test recurring tasks functionality."""
    
    def test_set_recurrence_rule(
        self, client: TestClient, auth_token: str, test_task: Todo
    ):
        """Test setting recurrence rule for task."""
        response = client.post(
            f"/api/tasks/{test_task.id}/recurrence",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "pattern": "weekly",
                "interval": 1,
                "start_date": datetime.utcnow().date().isoformat(),
                "by_weekday": "MO"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["pattern"] == "weekly"
        assert data["interval"] == 1
    
    def test_get_recurrence_rule(
        self, client: TestClient, auth_token: str,
        test_task: Todo, session: Session
    ):
        """Test getting recurrence rule."""
        # Create recurrence rule
        rule = RecurrenceRule(
            task_id=test_task.id,
            pattern=RecurrencePattern.weekly,
            interval=1,
            start_date=datetime.utcnow().date(),
            by_weekday="MO",
        )
        session.add(rule)
        session.commit()
        
        # Get recurrence rule
        response = client.get(
            f"/api/tasks/{test_task.id}/recurrence",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["pattern"] == "weekly"
    
    def test_remove_recurrence_rule(
        self, client: TestClient, auth_token: str,
        test_task: Todo, session: Session
    ):
        """Test removing recurrence rule."""
        # Create recurrence rule
        rule = RecurrenceRule(
            task_id=test_task.id,
            pattern=RecurrencePattern.weekly,
            interval=1,
            start_date=datetime.utcnow().date(),
        )
        session.add(rule)
        session.commit()
        
        # Remove recurrence rule
        response = client.delete(
            f"/api/tasks/{test_task.id}/recurrence",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 204


# Test: Reminders
class TestReminders:
    """Test reminders functionality."""
    
    def test_create_reminder(
        self, client: TestClient, auth_token: str, test_task: Todo
    ):
        """Test creating reminder."""
        trigger_time = datetime.utcnow() + timedelta(hours=1)
        
        response = client.post(
            "/api/reminders",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "task_id": test_task.id,
                "trigger_time": trigger_time.isoformat()
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == test_task.id
    
    def test_create_reminder_in_past(
        self, client: TestClient, auth_token: str, test_task: Todo
    ):
        """Test creating reminder in past (should fail)."""
        trigger_time = datetime.utcnow() - timedelta(hours=1)
        
        response = client.post(
            "/api/reminders",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "task_id": test_task.id,
                "trigger_time": trigger_time.isoformat()
            }
        )
        
        assert response.status_code == 400
    
    def test_get_reminders_for_task(
        self, client: TestClient, auth_token: str,
        test_task: Todo, session: Session
    ):
        """Test getting reminders for task."""
        # Create reminder
        reminder = Reminder(
            task_id=test_task.id,
            trigger_time=datetime.utcnow() + timedelta(hours=1),
        )
        session.add(reminder)
        session.commit()
        
        # Get reminders
        response = client.get(
            f"/api/reminders?task_id={test_task.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["reminders"]) == 1
    
    def test_delete_reminder(
        self, client: TestClient, auth_token: str,
        test_task: Todo, session: Session
    ):
        """Test deleting reminder."""
        # Create reminder
        reminder = Reminder(
            task_id=test_task.id,
            trigger_time=datetime.utcnow() + timedelta(hours=1),
        )
        session.add(reminder)
        session.commit()
        reminder_id = reminder.id
        
        # Delete reminder
        response = client.delete(
            f"/api/reminders/{reminder_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 204


# Test: Integration
class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_recurring_task_generates_next_instance(
        self, client: TestClient, auth_token: str,
        test_task: Todo, session: Session
    ):
        """Test completing recurring task generates next instance."""
        # Set recurrence rule
        rule = RecurrenceRule(
            task_id=test_task.id,
            pattern=RecurrencePattern.daily,
            interval=1,
            start_date=datetime.utcnow().date(),
        )
        session.add(rule)
        session.commit()
        
        # Complete task
        response = client.patch(
            f"/api/todos/{test_task.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"completed": True}
        )
        
        assert response.status_code == 200
        
        # Verify next instance created
        tasks = session.query(Todo).filter(
            Todo.id != test_task.id,
            Todo.user_id == test_task.user_id
        ).all()
        
        assert len(tasks) == 1
        assert not tasks[0].is_completed


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
