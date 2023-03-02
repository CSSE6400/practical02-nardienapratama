from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timedelta
from sqlalchemy import exc

api = Blueprint('api', __name__, url_prefix='/api/v1') 

class UnknownFieldException(Exception):
    "Raised when there are unknown fields."

class IDMismatchException(Exception):
    "Todo ID does not match ID in JSON object"

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})


@api.route('/todos', methods=['GET'])
def get_todos():
    """Return the list of todo items"""
    completed = request.args.get('completed')
    window = request.args.get('window', 100)
    todos = Todo.query.all()
    result = []
    for todo in todos:
        if completed == 'true':
            if todo.completed is True:
                if todo.deadline_at < (datetime.now() + timedelta(days=int(window))):
                    result.append(todo.to_dict())
        else:
            if todo.deadline_at < (datetime.now() + timedelta(days=int(window))):
                result.append(todo.to_dict())

    return jsonify(result)

@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """Return the details of a todo item"""
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST'])
def create_todo():
    """Create a new todo item and return the created item"""
    try:
        todo = Todo(
            title=request.json.get('title'),
            description=request.json.get('description'),
            completed=request.json.get('completed', False),
        )
        if 'deadline_at' in request.json:
            todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at'))

        if todo.title == '':
            raise exc.IntegrityError

        if len(set(request.json.keys()) - {'title', 'description', 'completed', 'deadline_at', 'created_at', 'updated_at'}) > 0:
            raise UnknownFieldException

        # Adds a new record to the database or will update an existing record
        db.session.add(todo)

        # Commits the changes to the daatabase, this must be called for the changes to be saved
        db.session.commit()
        return jsonify(todo.to_dict()), 201
    
    except exc.IntegrityError as e:
        print(str(e))
        db.session.rollback()
        return jsonify({'error': 'Failed to create Todo'}), 400

    except UnknownFieldException:
        return jsonify({'error': 'There are missing or extra fields'}), 400


@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """Update a todo item and return the updated item"""
    try:
        todo = Todo.query.get(todo_id)
        if todo is None:
            return jsonify({'error': 'Todo not found'}), 404

        if len(set(request.json.keys()) - {'title', 'description', 'completed', 'deadline_at', 'created_at', 'updated_at'}) > 0:
                raise UnknownFieldException

        if request.json.get('id'):
            if todo.id != request.json.get('id'):
                raise IDMismatchException

        todo.title = request.json.get('title', todo.title)
        todo.description = request.json.get('description', todo.description)
        todo.completed = request.json.get('completed', todo.completed)
        todo.deadline_at = request.json.get('deadline_at', todo.deadline_at)
        db.session.commit()

        return jsonify(todo.to_dict())
    except UnknownFieldException:
        return jsonify({'error': 'There are missing or extra fields'}), 400
    
    except IDMismatchException:
        return jsonify({'Todo ID does not match ID in JSON object'}), 400

@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """Delete a todo item and return the deleted item"""
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({}), 200

    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200
 
