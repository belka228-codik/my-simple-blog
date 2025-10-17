import json
import os
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request

app = Flask(__name__)

# In-memory storage
users = {}
posts = {}
next_user_id = 1
next_post_id = 1


# Load data from file
def load_data():
    global users, posts, next_user_id, next_post_id
    try:
        if os.path.exists("data.json"):
            with open("data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                users = {int(k): v for k, v in data.get("users", {}).items()}
                posts = {int(k): v for k, v in data.get("posts", {}).items()}
                next_user_id = max(users.keys(), default=0) + 1
                next_post_id = max(posts.keys(), default=0) + 1
    except Exception as e:
        print(f"Error loading data: {e}")
        users = {}
        posts = {}


def save_data():
    try:
        data = {"users": users, "posts": posts}
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving data: {e}")


# Load data on startup
load_data()


# Web routes
@app.route("/")
def index():
    posts_list = list(posts.values())
    # Sort by creation date, newest first
    posts_list.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
    return render_template("index.html", posts=posts_list)


@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    post = posts.get(post_id)
    if not post:
        return "Post not found", 404
    return render_template("post.html", post=post)


@app.route("/create", methods=["GET", "POST"])
def create_post_page():
    if request.method == "POST":
        global next_post_id

        author_id = int(request.form.get("authorId", 1))
        if author_id not in users:
            # Create default user if not exists
            users[author_id] = {
                "id": author_id,
                "email": f"user{author_id}@example.com",
                "login": f"user{author_id}",
                "password": "password",
                "createdAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat(),
            }

        post = {
            "id": next_post_id,
            "authorId": author_id,
            "title": request.form["title"],
            "content": request.form["content"],
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }

        posts[next_post_id] = post
        next_post_id += 1
        save_data()

        return redirect("/")

    return render_template("create_post.html")


# API Routes - Users
@app.route("/api/users", methods=["POST"])
def create_user():
    global next_user_id
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    user = {
        "id": next_user_id,
        "email": data.get("email"),
        "login": data.get("login"),
        "password": data.get("password"),
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
    }

    users[next_user_id] = user
    next_user_id += 1
    save_data()

    return jsonify(user), 201


@app.route("/api/users", methods=["GET"])
def get_all_users():
    return jsonify(list(users.values()))


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = users.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@app.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = users.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    user.update(data)
    user["updatedAt"] = datetime.now().isoformat()
    save_data()

    return jsonify(user)


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404

    del users[user_id]
    # Delete user's posts
    global posts
    posts = {pid: post for pid, post in posts.items() if post["authorId"] != user_id}
    save_data()

    return jsonify({"message": "User deleted"})


# API Routes - Posts
@app.route("/api/posts", methods=["POST"])
def create_post():
    global next_post_id
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    author_id = data.get("authorId")
    if author_id not in users:
        return jsonify({"error": "Author not found"}), 404

    post = {
        "id": next_post_id,
        "authorId": author_id,
        "title": data.get("title"),
        "content": data.get("content"),
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
    }

    posts[next_post_id] = post
    next_post_id += 1
    save_data()

    return jsonify(post), 201


@app.route("/api/posts", methods=["GET"])
def get_all_posts():
    return jsonify(list(posts.values()))


@app.route("/api/posts/<int:post_id>", methods=["GET"])
def get_post_api(post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    return jsonify(post)


@app.route("/api/posts/<int:post_id>", methods=["PUT"])
def update_post_api(post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    post.update(data)
    post["updatedAt"] = datetime.now().isoformat()
    save_data()

    return jsonify(post)


@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post_api(post_id):
    if post_id not in posts:
        return jsonify({"error": "Post not found"}), 404

    del posts[post_id]
    save_data()

    return jsonify({"message": "Post deleted"})


# Health check
@app.route("/health")
def health_check():
    return jsonify({"status": "healthy", "users": len(users), "posts": len(posts)})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
