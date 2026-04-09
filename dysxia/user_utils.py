import json
from werkzeug.security import generate_password_hash, check_password_hash
import os

USER_FILE = 'account.json'


def load_users():
    if not os.path.exists(USER_FILE):
        return []
    with open(USER_FILE, 'r') as f:
        return json.load(f)


def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)


def find_user(email):
    users = load_users()
    for user in users:
        if user['email'] == email:
            return user
    return None


def register_user(name, email, password):
    users = load_users()
    if find_user(email):
        return False  # email already registered
    hashed = generate_password_hash(password)
    users.append({'name': name, 'email': email, 'password': hashed})
    save_users(users)
    return True


def verify_user(email, password):
    user = find_user(email)
    if user and check_password_hash(user['password'], password):
        return True
    return False


USER_FILE = 'account.json'


def load_users():
    if not os.path.exists(USER_FILE):
        return []
    with open(USER_FILE, 'r') as f:
        return json.load(f)


def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)


def find_user(email):
    users = load_users()
    for user in users:
        if user['email'] == email:
            return user
    return None


def register_user(name, email, password):
    users = load_users()
    if find_user(email):
        return False  # Email already registered
    hashed_password = generate_password_hash(password)
    users.append({
        'name': name,
        'email': email,
        'password': hashed_password
    })
    save_users(users)
    return True


def valid_credentials(email, password):
    user = find_user(email)
    if user and check_password_hash(user['password'], password):
        return True
    return False
