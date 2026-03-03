# API Documentation - DynamoDB FastAPI v2.0

## Setup & Run
```bash
cd app
pip install -r requirements.txt
uvicorn main:app --reload
```

API: `http://127.0.0.1:8000`
Docs: `http://127.0.0.1:8000/docs`

---

## Response Format

### Success
```json
{
  "success": true,
  "data": { ... }
}
```

### Error
```json
{
  "success": false,
  "message": "Error description"
}
```

---

## Users API

### GET /users
Get all users
```bash
curl http://127.0.0.1:8000/users
```

### GET /users/{user_id}
Get single user
```bash
curl http://127.0.0.1:8000/users/550e8400-e29b-41d4-a716-446655440000
```

### POST /users
Create user (userId auto-generated)
```bash
curl -X POST http://127.0.0.1:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "John Doe",
    "role": "admin",
    "email": "john@example.com",
    "login_type": "email",
    "subscription": "premium",
    "is_active": true,
    "created_by": "system",
    "updated_by": "system"
  }'
```

**Note:** Do NOT send `userId` - it will return 400 error.

### PUT /users/{user_id}
Update user
```bash
curl -X PUT http://127.0.0.1:8000/users/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "Jane Doe",
    "email": "jane@example.com",
    "updated_by": "admin"
  }'
```

### DELETE /users/{user_id}
Delete user
```bash
curl -X DELETE http://127.0.0.1:8000/users/550e8400-e29b-41d4-a716-446655440000
```

---

## Projects API

### GET /projects
Get all projects
```bash
curl http://127.0.0.1:8000/projects
```

### GET /projects/{user_id}/{project_id}
Get single project
```bash
curl http://127.0.0.1:8000/projects/user123/proj456
```

### POST /projects
Create project
```bash
curl -X POST http://127.0.0.1:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "project_id": "proj456",
    "project_name": "My Project",
    "visibility": "private",
    "environment_type": "production",
    "created_by": "user123",
    "updated_by": "user123"
  }'
```

### PUT /projects/{user_id}/{project_id}
Update project
```bash
curl -X PUT http://127.0.0.1:8000/projects/user123/proj456 \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Updated Project",
    "visibility": "public",
    "updated_by": "user123"
  }'
```

### DELETE /projects/{user_id}/{project_id}
Delete project
```bash
curl -X DELETE http://127.0.0.1:8000/projects/user123/proj456
```

---

## Global Variables API

### GET /global-variables
Get all global variables
```bash
curl http://127.0.0.1:8000/global-variables
```

### GET /global-variables/{project_id}/{variable_id}
Get single global variable
```bash
curl http://127.0.0.1:8000/global-variables/proj123/var456
```

### POST /global-variables
Create global variable
```bash
curl -X POST http://127.0.0.1:8000/global-variables \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj123",
    "variable_id": "var456",
    "variable_name": "API_KEY",
    "environment_names": {
      "dev": "dev_key_123",
      "prod": "prod_key_456"
    },
    "created_by": "user123",
    "updated_by": "user123"
  }'
```

### PUT /global-variables/{project_id}/{variable_id}
Update global variable
```bash
curl -X PUT http://127.0.0.1:8000/global-variables/proj123/var456 \
  -H "Content-Type: application/json" \
  -d '{
    "variable_name": "API_SECRET",
    "environment_names": {
      "dev": "new_dev_key",
      "prod": "new_prod_key"
    },
    "updated_by": "user123"
  }'
```

### DELETE /global-variables/{project_id}/{variable_id}
Delete global variable
```bash
curl -X DELETE http://127.0.0.1:8000/global-variables/proj123/var456
```

---

## Responses API

### GET /responses
Get all responses
```bash
curl http://127.0.0.1:8000/responses
```

### GET /responses/{api_id}/{response_id}
Get single response
```bash
curl http://127.0.0.1:8000/responses/api123/resp456
```

### POST /responses
Create response
```bash
curl -X POST http://127.0.0.1:8000/responses \
  -H "Content-Type: application/json" \
  -d '{
    "api_id": "api123",
    "response_id": "resp456",
    "response_type": "json",
    "response_delay": 0,
    "status": "200",
    "response_header": {
      "Content-Type": "application/json"
    },
    "response_body": {
      "message": "Success"
    }
  }'
```

### PUT /responses/{api_id}/{response_id}
Update response
```bash
curl -X PUT http://127.0.0.1:8000/responses/api123/resp456 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "201",
    "response_delay": 100,
    "response_body": {
      "message": "Created"
    }
  }'
```

### DELETE /responses/{api_id}/{response_id}
Delete response
```bash
curl -X DELETE http://127.0.0.1:8000/responses/api123/resp456
```

---

## Key Features

✅ **Auto-generated UUID** for Users (userId)  
✅ **Email validation** using Pydantic EmailStr  
✅ **Clean response format** - `{success, data}` or `{success, message}`  
✅ **Separate endpoints** for each resource  
✅ **Full CRUD** operations (GET, POST, PUT, DELETE)  
✅ **Automatic timestamps** (created_at, updated_at)  
✅ **404 handling** for missing records  
✅ **Primary key protection** - cannot update partition/sort keys
