from flask import Flask, jsonify, request
from datetime import datetime
import os

app = Flask(__name__)

# In-memory data store
items = [
    {"id": 1, "name": "Item 1", "description": "First item"},
    {"id": 2, "name": "Item 2", "description": "Second item"}
]


@app.route('/')
def index():
    return jsonify({
        "message": "Welcome to Demo Service v2.0",
        "status": "running",
        "endpoints": ["GET /", "GET /health", "GET /api/items", "GET /api/items/<id>", "POST /api/items"],
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route('/health')
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route('/api/items', methods=['GET'])
def get_items():
    return jsonify({"count": len(items), "items": items})


@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = next((i for i in items if i['id'] == item_id), None)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item)


@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Name is required"}), 400
    
    new_item = {
        "id": len(items) + 1,
        "name": data['name'],
        "description": data.get('description', '')
    }
    items.append(new_item)
    return jsonify(new_item), 201


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
