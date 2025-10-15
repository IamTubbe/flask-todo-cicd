from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, Todo

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """API Root Endpoint"""
    return jsonify({
        'message': 'Welcome to the Flask Todo API!',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'todos': '/api/todos'
        }
    })


@bp.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
        status_code = 200
        overall_status = 'healthy'
    except Exception as e:
        db_status = 'disconnected'
        status_code = 503
        overall_status = 'unhealthy'
        return jsonify({
            'status': overall_status,
            'database': db_status,
            'error': str(e)
        }), status_code

    return jsonify({
        'status': overall_status,
        'database': db_status
    }), status_code


@bp.route('/api/todos', methods=['GET'])
def get_todos():
    """Get all todo items"""
    try:
        todos = Todo.query.order_by(Todo.created_at.desc()).all()
        return jsonify({
            'success': True,
            'count': len(todos),
            'data': [todo.to_dict() for todo in todos]
        })
    except SQLAlchemyError as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500


@bp.route('/api/todos', methods=['POST'])
def create_todo():
    """Create a new todo"""
    data = request.get_json()

    if not data or 'title' not in data or not data['title'].strip():
        return jsonify({'success': False, 'error': 'Title is required'}), 400

    try:
        new_todo = Todo(
            title=data['title'],
            description=data.get('description', '')
        )
        db.session.add(new_todo)
        db.session.commit()
        return jsonify({
            'success': True,
            'data': new_todo.to_dict(),
            'message': 'Todo created successfully'
        }), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500


@bp.route('/api/todos/<int:id>', methods=['GET'])
def get_todo(id):
    """Get a single todo by its ID"""
    todo = Todo.query.get_or_404(id)
    return jsonify({
        'success': True,
        'data': todo.to_dict()
    })


@bp.route('/api/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    """Update an existing todo"""
    todo = Todo.query.get_or_404(id)
    data = request.get_json()

    try:
        todo.title = data.get('title', todo.title)
        todo.description = data.get('description', todo.description)
        todo.completed = data.get('completed', todo.completed)
        db.session.commit()
        return jsonify({
            'success': True,
            'data': todo.to_dict(),
            'message': 'Todo updated successfully'
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500


@bp.route('/api/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    """Delete a todo"""
    todo = Todo.query.get_or_404(id)
    try:
        db.session.delete(todo)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Todo deleted successfully'
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
