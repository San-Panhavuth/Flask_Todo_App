from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# MongoDB Connection
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
db = client['todoapp']
todos_collection = db['todos']

# Helper function to convert MongoDB document to JSON serializable format
def todo_to_dict(todo):
    return {
        'id': str(todo['_id']),
        'title': todo['title'],
        'description': todo.get('description', ''),
        'completed': todo.get('completed', False)
    }

# REST API Endpoints
@app.route('/todos', methods=['GET'])
def get_todos():
    todos = list(todos_collection.find())
    return jsonify([todo_to_dict(todo) for todo in todos])

@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.json
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    todo = {
        'title': data['title'],
        'description': data.get('description', ''),
        'completed': data.get('completed', False)
    }
    
    result = todos_collection.insert_one(todo)
    todo['id'] = str(result.inserted_id)
    return jsonify(todo), 201

@app.route('/todos/<todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = request.json
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(todo_id)
    except:
        return jsonify({'error': 'Invalid todo ID'}), 400
    
    # Prepare update fields
    update_fields = {}
    if 'title' in data:
        update_fields['title'] = data['title']
    if 'description' in data:
        update_fields['description'] = data['description']
    if 'completed' in data:
        update_fields['completed'] = data['completed']
    
    # Perform update
    result = todos_collection.update_one(
        {'_id': object_id}, 
        {'$set': update_fields}
    )
    
    if result.modified_count:
        updated_todo = todos_collection.find_one({'_id': object_id})
        return jsonify(todo_to_dict(updated_todo))
    else:
        return jsonify({'error': 'Todo not found'}), 404

@app.route('/todos/<todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(todo_id)
    except:
        return jsonify({'error': 'Invalid todo ID'}), 400
    
    # Delete todo
    result = todos_collection.delete_one({'_id': object_id})
    
    if result.deleted_count:
        return '', 204
    else:
        return jsonify({'error': 'Todo not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)