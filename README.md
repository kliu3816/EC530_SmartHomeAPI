# EC530_SmartHomeAPI
This is a FastAPI-based application designed to manage users, houses, rooms, and devices in a home management system. The application uses SQLAlchemy for database interactions and SQLite as the database engine. The API provides CRUD (Create, Read, Update, Delete) operations for users, houses, rooms, and devices.

Install dependencies:
pip install fastapi sqlalchemy pydantic uvicorn

Start the FastAPI application using Uvicorn:
uvicorn main:app --reload

Open your browser and navigate to http://127.0.0.1:8000/docs to access the Swagger UI documentation for the API.

# API Endpoints
## User Endpoints
Create a new user: POST /users/

Get all users: GET /users/

Get a specific user by email: GET /users/{user_email}

Update a user: PUT /users/{user_email}

Delete a user: DELETE /users/{user_email}

## House Endpoints
Create a new house: POST /houses/

Get all houses: GET /houses/

Get a specific house by address: GET /houses/{house_address}

Update a house: PUT /houses/{house_address}

Delete a house: DELETE /houses/{house_address}

## Room Endpoints
Create a new room: POST /rooms/

Get all rooms: GET /rooms/

Get a specific room by name: GET /rooms/{room_name}

Update a room: PUT /rooms/{room_name}

Delete a room: DELETE /rooms/{room_name}

## Device Endpoints
Create a new device: POST /devices/

Get all devices: GET /devices/

Get a specific device by name: GET /devices/{device_name}

Update a device: PUT /devices/{device_name}

Delete a device: DELETE /devices/{device_name}

# Database Schema
The database schema consists of four main tables:

**Users:** Stores user information.

name: User's name.

email: User's email (primary key).

**Houses:** Stores house information.

address: House address (primary key).

user_email: Foreign key referencing the user who owns the house.

**Rooms:** Stores room information.

name: Room name (primary key).

house_adrs: Foreign key referencing the house the room belongs to.

**Devices:** Stores device information.

name: Device name (primary key).

room_name: Foreign key referencing the room the device is in.
