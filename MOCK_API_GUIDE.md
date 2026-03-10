# MockApi CRUD API Documentation

## Overview
Complete CRUD API for managing MockApi entries in DynamoDB using FastAPI and boto3.

## Table Structure
- **Table Name**: MockApi
- **Partition Key**: project_id (String)
- **Sort Key**: api_id (String - UUID auto-generated)

## API Endpoints

### 1. Get All Mock APIs
```http
GET /mock-apis
```
**Response:**
```json
{
  "success": true,
  "data": [
    {
      "project_id": "c04ce07e-2513-46f5-a17d-c798bbae8599",
      "api_id": "550e8400-e29b-41d4-a716-446655440000",
      "method": "POST",
      "request_condition": {...},
      "expression": {...},
      "state_condition": {...},
      "query_header": {...},
      "response": {...},
      "description": "Create new user",
      "is_active": true,
      "created_at": "2026-03-10T10:42:43.783Z",
      "updated_at": "2026-03-10T10:42:43.783Z",
      "created_by": "admin",
      "updated_by": "admin"
    }
  ]
}
```

### 2. Get Active Mock APIs
```http
GET /mock-apis/active
```
Returns only mock APIs where `is_active = true`.

### 3. Get Mock API by ID
```http
GET /mock-apis/{project_id}/{api_id}
```
**Example:**
```http
GET /mock-apis/c04ce07e-2513-46f5-a17d-c798bbae8599/550e8400-e29b-41d4-a716-446655440000
```

### 4. Create Mock API
```http
POST /mock-apis
Content-Type: application/json

{
  "project_id": "c04ce07e-2513-46f5-a17d-c798bbae8599",
  "method": "POST",
  "request_condition": {
    "condition_1": "request path exactly matches",
    "condition_2": "request path starts with",
    "condition_3": "request path contains"
  },
  "expression": {
    "expression_1": "/test",
    "expression_2": "/users",
    "expression_3": "/tables"
  },
  "state_condition": {
    "variable": "visit count",
    "condition": "create",
    "value": 3,
    "response_body": {
      "description": "Create new user",
      "new": "Create new user"
    }
  },
  "query_header": {
    "Content-Type": "application/json"
  },
  "response": {
    "Response_1": {
      "IsDynamic": "True",
      "Response_delay": 3,
      "HTTP_status": "200 OK",
      "Response_Header": {
        "Content-Type": "application/json"
      },
      "Response_Body": {
        "UUID": "FGH45NJ67980SDC2"
      }
    },
    "Response_2": {
      "IsDynamic": "True",
      "Response_delay": 3,
      "HTTP_status": "200 OK",
      "Response_Header": {
        "Content-Type": "application/json"
      },
      "Response_Body": {
        "UUID": "FGH45NJ67980SDC2"
      }
    }
  },
  "description": "Create new user",
  "is_active": true,
  "created_by": "admin",
  "updated_by": "admin"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Mock API created successfully",
    "api_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 5. Update Mock API
```http
PUT /mock-apis/{project_id}/{api_id}
Content-Type: application/json

{
  "description": "Updated description",
  "method": "GET",
  "response": {
    "Response_1": {
      "HTTP_status": "201 Created"
    }
  },
  "updated_by": "admin"
}
```

**Note:** All fields except `updated_by` are optional. Only provided fields will be updated.

### 6. Deactivate Mock API
```http
PATCH /mock-apis/{project_id}/{api_id}/deactivate
```
Sets `is_active = false` and updates `updated_at` timestamp.

### 7. Activate Mock API
```http
PATCH /mock-apis/{project_id}/{api_id}/activate
```
Sets `is_active = true` and updates `updated_at` timestamp.

## Features
- ✅ UUID auto-generation for `api_id`
- ✅ Automatic `created_at`/`updated_at` timestamps (ISO 8601 format)
- ✅ Input validation with Pydantic models
- ✅ Proper error handling with HTTP status codes
- ✅ Structured JSON responses
- ✅ Active/inactive filtering
- ✅ Partial updates (PUT only updates provided fields)
- ✅ Follows existing project patterns

## Error Responses
```json
{
  "detail": "Mock API not found with project_id=xxx and api_id=yyy"
}
```

## Running the API
```bash
cd app
uvicorn main:app --reload
```

**API Documentation:** http://127.0.0.1:8000/docs

## Testing
Run the comprehensive test script:
```bash
./test_mock_api.sh
```

This will create a mock API, test all CRUD operations, and clean up automatically.
