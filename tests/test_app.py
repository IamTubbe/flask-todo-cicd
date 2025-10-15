import pytest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from app.models import db, Todo

# This fixture is run once per test module.
@pytest.fixture(scope='module')
def app():
    """Create and configure a new app instance for each test module."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

# This fixture is run for each test function.
@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    return app.test_client()

# This fixture is run for each test function, ensuring a clean database.
@pytest.fixture(scope='function')
def init_database(app):
    """Clear all data from tables."""
    with app.app_context():
        db.session.query(Todo).delete()
        db.session.commit()


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_endpoint_success(self, client):
        """Test health check returns 200 when database is healthy"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'

    @patch('app.routes.db.session.execute')
    def test_health_endpoint_database_error(self, mock_execute, client):
        """Test health check returns 503 when database is down"""
        mock_execute.side_effect = Exception('Database connection failed')
        
        response = client.get('/api/health')
        assert response.status_code == 503
        data = response.get_json()
        assert data['status'] == 'unhealthy'
        assert data['database'] == 'disconnected'
        assert 'error' in data


class TestTodoAPI:
    """Test Todo CRUD operations"""
    
    def test_get_empty_todos(self, client, init_database):
        """Test getting todos when database is empty"""
        response = client.get('/api/todos')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 0
        assert data['data'] == []
    
    def test_create_todo(self, client, init_database):
        """Test creating a new todo"""
        todo_data = {'title': 'New Todo', 'description': 'A test todo'}
        response = client.post('/api/todos', json=todo_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'New Todo'

    def test_create_todo_without_title_fails(self, client, init_database):
        """Test creating todo without title fails"""
        response = client.post('/api/todos', json={'description': 'No title'})
        assert response.status_code == 400
        assert b'Title is required' in response.data

    @patch('app.routes.db.session.commit')
    def test_create_todo_db_error(self, mock_commit, client, init_database):
        """Test a database error during todo creation"""
        mock_commit.side_effect = SQLAlchemyError("DB connection error")
        response = client.post('/api/todos', json={'title': 'Will Fail'})
        assert response.status_code == 500
        assert b'Database error' in response.data
    
    def test_get_specific_todo(self, client, app, init_database):
        """Test getting a specific todo by ID"""
        with app.app_context():
            todo = Todo(title='Specific Todo')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id
        
        response = client.get(f'/api/todos/{todo_id}')
        assert response.status_code == 200
        assert b'Specific Todo' in response.data

    def test_get_nonexistent_todo(self, client):
        """Test getting a todo that doesn't exist returns 404"""
        response = client.get('/api/todos/99999')
        assert response.status_code == 404

    def test_update_todo(self, client, app, init_database):
        """Test updating an existing todo"""
        with app.app_context():
            todo = Todo(title='Original Title')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        update_data = {'title': 'Updated Title', 'completed': True}
        response = client.put(f'/api/todos/{todo_id}', json=update_data)
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['title'] == 'Updated Title'
        assert data['data']['completed'] is True

    def test_update_nonexistent_todo(self, client):
        """Test updating a non-existent todo returns 404"""
        response = client.put('/api/todos/99999', json={'title': 'No one here'})
        assert response.status_code == 404

    @patch('app.routes.db.session.commit')
    def test_update_todo_db_error(self, mock_commit, client, app, init_database):
        """Test a database error during todo update"""
        with app.app_context():
            todo = Todo(title='To be updated')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        mock_commit.side_effect = SQLAlchemyError("DB connection error")
        response = client.put(f'/api/todos/{todo_id}', json={'title': 'Will Fail'})
        assert response.status_code == 500
        assert b'Database error' in response.data

    def test_delete_todo(self, client, app, init_database):
        """Test deleting a todo"""
        with app.app_context():
            todo = Todo(title='To be deleted')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = client.delete(f'/api/todos/{todo_id}')
        assert response.status_code == 200
        assert b'Todo deleted successfully' in response.data

        # Verify it's actually deleted
        response = client.get(f'/api/todos/{todo_id}')
        assert response.status_code == 404

    def test_delete_nonexistent_todo(self, client):
        """Test deleting a non-existent todo returns 404"""
        response = client.delete('/api/todos/99999')
        assert response.status_code == 404

    @patch('app.routes.db.session.commit')
    def test_delete_todo_db_error(self, mock_commit, client, app, init_database):
        """Test a database error during todo deletion"""
        with app.app_context():
            todo = Todo(title='To be deleted')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        mock_commit.side_effect = SQLAlchemyError("DB connection error")
        response = client.delete(f'/api/todos/{todo_id}')
        assert response.status_code == 500
        assert b'Database error' in response.data
