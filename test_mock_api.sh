#!/bin/bash

# MockApi CRUD API Test Script
BASE_URL="http://127.0.0.1:8000"

echo "=== MockApi CRUD API Test ==="
echo

# 1. Create Mock API
echo "1. Creating Mock API..."
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/mock-apis" \
  -H "Content-Type: application/json" \
  -d '{
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
  }')

echo "$CREATE_RESPONSE"

# Extract api_id from response (assuming it's in the response)
API_ID=$(echo "$CREATE_RESPONSE" | grep -o '"api_id":"[^"]*"' | cut -d'"' -f4)
PROJECT_ID="c04ce07e-2513-46f5-a17d-c798bbae8599"

echo -e "\n\n2. Get All Mock APIs..."
curl -s "$BASE_URL/mock-apis" | jq '.'

echo -e "\n\n3. Get Active Mock APIs..."
curl -s "$BASE_URL/mock-apis/active" | jq '.'

if [ ! -z "$API_ID" ]; then
    echo -e "\n\n4. Get Single Mock API (ID: $API_ID)..."
    curl -s "$BASE_URL/mock-apis/$PROJECT_ID/$API_ID" | jq '.'

    echo -e "\n\n5. Update Mock API..."
    curl -s -X PUT "$BASE_URL/mock-apis/$PROJECT_ID/$API_ID" \
      -H "Content-Type: application/json" \
      -d '{
        "description": "Updated description - Create new user endpoint",
        "method": "GET",
        "updated_by": "admin"
      }' | jq '.'

    echo -e "\n\n6. Deactivate Mock API..."
    curl -s -X PATCH "$BASE_URL/mock-apis/$PROJECT_ID/$API_ID/deactivate" | jq '.'

    echo -e "\n\n7. Activate Mock API..."
    curl -s -X PATCH "$BASE_URL/mock-apis/$PROJECT_ID/$API_ID/activate" | jq '.'
else
    echo -e "\n\nCould not extract API_ID from create response. Manual testing required."
    echo "Use these commands with the actual api_id:"
    echo "curl \"$BASE_URL/mock-apis/$PROJECT_ID/{api_id}\""
    echo "curl -X PUT \"$BASE_URL/mock-apis/$PROJECT_ID/{api_id}\" -H \"Content-Type: application/json\" -d '{\"description\": \"Updated\", \"updated_by\": \"admin\"}'"
    echo "curl -X PATCH \"$BASE_URL/mock-apis/$PROJECT_ID/{api_id}/deactivate\""
    echo "curl -X PATCH \"$BASE_URL/mock-apis/$PROJECT_ID/{api_id}/activate\""
fi

echo -e "\n\n=== Test Complete ==="
