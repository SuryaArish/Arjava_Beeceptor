# DynamoDB FastAPI - Setup & Run Guide

## 1. Install Dependencies
```bash
cd app
pip install -r requirements.txt
```

## 2. Configure AWS Credentials
Edit `.env` file with your actual AWS credentials:
```
AWS_ACCESS_KEY_ID=your_actual_access_key 
AWS_SECRET_ACCESS_KEY=your_actual_secret_key
AWS_REGION=eu-north-1
```

## 3. Run the Application
```bash
uvicorn main:app --reload
```

API will be available at: `http://127.0.0.1:8000`

## 4. API Documentation
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 5. Example API Calls

### Get All Users (with pagination)
```bash
curl http://127.0.0.1:8000/Users?limit=10
```

### Create User
```bash
curl -X POST http://127.0.0.1:8000/Users \
  -H "Content-Type: application/json" \
  -d '{
    "userId": 1,
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

### Get Single User
```bash
curl http://127.0.0.1:8000/Users/1
```

### Create Project (with sort key)
```bash
curl -X POST http://127.0.0.1:8000/Projects \
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

### Get Single Project (with sort key)
```bash
curl "http://127.0.0.1:8000/Projects/user123?sort_key=proj456"
```

## Notes
- `created_at` and `updated_at` are automatically added
- Email validation is enforced via Pydantic
- Pagination uses `last_evaluated_key` from response
