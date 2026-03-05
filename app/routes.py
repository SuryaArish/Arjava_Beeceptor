from fastapi import APIRouter, HTTPException
from datetime import datetime
from decimal import Decimal
import uuid
from database import db_client
from boto3.dynamodb.conditions import Attr
from models import (
    UserCreate, UserUpdate,
    ProjectCreate, ProjectUpdate,
    GlobalVariableCreate, GlobalVariableUpdate,
    ResponseCreate, ResponseUpdate,
    MockApiCreate, MockApiUpdate
)

router = APIRouter()

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    return obj

# ==================== USERS ====================

@router.get("/users")
async def get_all_users():
    try:
        table = db_client.get_table("Users")
        response = table.scan(Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/active")
async def get_active_users():
    try:
        table = db_client.get_table("Users")
        response = table.scan(FilterExpression=Attr("is_active").eq(True), Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        table = db_client.get_table("Users")
        response = table.get_item(Key={"userId": user_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "data": decimal_to_float(response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users")
async def create_user(user: UserCreate):
    try:
        table = db_client.get_table("Users")
        timestamp = datetime.utcnow().isoformat()
        
        item = user.model_dump(exclude={"userId"})
        item["userId"] = str(uuid.uuid4())
        item["created_at"] = timestamp
        item["updated_at"] = timestamp
        
        table.put_item(Item=item)
        return {"success": True, "data": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}")
async def update_user(user_id: str, user: UserUpdate):
    try:
        table = db_client.get_table("Users")
        
        response = table.get_item(Key={"userId": user_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="User not found")
        
        update_data = user.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
        expr_attr_names = {f"#{k}": k for k in update_data.keys()}
        expr_attr_values = {f":{k}": v for k, v in update_data.items()}
        
        table.update_item(
            Key={"userId": user_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        
        updated_response = table.get_item(Key={"userId": user_id})
        return {"success": True, "data": decimal_to_float(updated_response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/users/{user_id}")
async def deactivate_user(user_id: str):
    try:
        table = db_client.get_table("Users")
        
        response = table.get_item(Key={"userId": user_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="User not found")
        
        table.update_item(
            Key={"userId": user_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": False, ":time": datetime.utcnow().isoformat()}
        )
        
        return {"success": True, "data": {"message": "Record deactivated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/users/{user_id}/activate")
async def activate_user(user_id: str):
    try:
        table = db_client.get_table("Users")
        
        response = table.get_item(Key={"userId": user_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="User not found")
        
        table.update_item(
            Key={"userId": user_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": True, ":time": datetime.utcnow().isoformat()}
        )
        
        return {"success": True, "data": {"message": "Record activated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PROJECTS ====================

@router.get("/projects")
async def get_all_projects():
    try:
        table = db_client.get_table("Projects")
        response = table.scan(Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/active")
async def get_active_projects():
    try:
        table = db_client.get_table("Projects")
        response = table.scan(FilterExpression=Attr("is_active").eq(True), Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{user_id}/{project_id}")
async def get_project(user_id: str, project_id: str):
    try:
        table = db_client.get_table("Projects")
        response = table.get_item(Key={"user_id": user_id, "project_id": project_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True, "data": decimal_to_float(response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects")
async def create_project(project: ProjectCreate):
    try:
        table = db_client.get_table("Projects")
        timestamp = datetime.utcnow().isoformat()
        
        item = project.model_dump(exclude={"project_id"})
        item["project_id"] = str(uuid.uuid4())
        item["created_at"] = timestamp
        item["updated_at"] = timestamp
        item["is_active"] = True
        
        table.put_item(Item=item)
        return {"success": True, "data": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/projects/{user_id}/{project_id}")
async def update_project(user_id: str, project_id: str, project: ProjectUpdate):
    try:
        table = db_client.get_table("Projects")
        
        response = table.get_item(Key={"user_id": user_id, "project_id": project_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="Project not found")
        
        update_data = project.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
        expr_attr_names = {f"#{k}": k for k in update_data.keys()}
        expr_attr_values = {f":{k}": v for k, v in update_data.items()}
        
        table.update_item(
            Key={"user_id": user_id, "project_id": project_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        
        updated_response = table.get_item(Key={"user_id": user_id, "project_id": project_id})
        return {"success": True, "data": decimal_to_float(updated_response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/projects/{user_id}/{project_id}")
async def deactivate_project(user_id: str, project_id: str):
    try:
        table = db_client.get_table("Projects")
        
        response = table.get_item(Key={"user_id": user_id, "project_id": project_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="Project not found")
        
        table.update_item(
            Key={"user_id": user_id, "project_id": project_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": False, ":time": datetime.utcnow().isoformat()}
        )
        
        return {"success": True, "data": {"message": "Record deactivated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/projects/{user_id}/{project_id}/activate")
async def activate_project(user_id: str, project_id: str):
    try:
        table = db_client.get_table("Projects")
        
        response = table.get_item(Key={"user_id": user_id, "project_id": project_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Project not found")
        
        table.update_item(
            Key={"user_id": user_id, "project_id": project_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": True, ":time": datetime.utcnow().isoformat()}
        )
        
        return {"success": True, "data": {"message": "Record activated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== GLOBAL VARIABLES ====================

@router.get("/global-variables")
async def get_all_global_variables():
    try:
        table = db_client.get_table("GlobalVariable")
        response = table.scan(Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/global-variables/active")
async def get_active_global_variables():
    try:
        table = db_client.get_table("GlobalVariable")
        response = table.scan(FilterExpression=Attr("is_active").eq(True), Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/global-variables/{project_id}/{variable_id}")
async def get_global_variable(project_id: str, variable_id: str):
    try:
        table = db_client.get_table("GlobalVariable")
        response = table.get_item(Key={"project_id": project_id, "variable_id": variable_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Global variable not found")
        return {"success": True, "data": decimal_to_float(response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/global-variables")
async def create_global_variable(variable: GlobalVariableCreate):
    try:
        table = db_client.get_table("GlobalVariable")
        timestamp = datetime.utcnow().isoformat()
        
        item = variable.model_dump(exclude={"variable_id"})
        item["variable_id"] = str(uuid.uuid4())
        item["created_at"] = timestamp
        item["updated_at"] = timestamp
        item["is_active"] = True
        
        table.put_item(Item=item)
        return {"success": True, "data": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/global-variables/{project_id}/{variable_id}")
async def update_global_variable(project_id: str, variable_id: str, variable: GlobalVariableUpdate):
    try:
        table = db_client.get_table("GlobalVariable")
        
        response = table.get_item(Key={"project_id": project_id, "variable_id": variable_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Global variable not found")
        
        update_data = variable.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
        expr_attr_names = {f"#{k}": k for k in update_data.keys()}
        expr_attr_values = {f":{k}": v for k, v in update_data.items()}
        
        table.update_item(
            Key={"project_id": project_id, "variable_id": variable_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        
        updated_response = table.get_item(Key={"project_id": project_id, "variable_id": variable_id})
        return {"success": True, "data": decimal_to_float(updated_response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/global-variables/{project_id}/{variable_id}")
async def deactivate_global_variable(project_id: str, variable_id: str):
    try:
        table = db_client.get_table("GlobalVariable")
        
        response = table.get_item(Key={"project_id": project_id, "variable_id": variable_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail=f"Global variable not found with project_id={project_id} and variable_id={variable_id}")
        
        table.update_item(
            Key={"project_id": project_id, "variable_id": variable_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": False, ":time": datetime.utcnow().isoformat()}
        )
        
        return {"success": True, "data": {"message": "Record deactivated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/global-variables/{project_id}/{variable_id}/activate")
async def activate_global_variable(project_id: str, variable_id: str):
    try:
        table = db_client.get_table("GlobalVariable")
        
        response = table.get_item(Key={"project_id": project_id, "variable_id": variable_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Global variable not found")
        
        table.update_item(
            Key={"project_id": project_id, "variable_id": variable_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": True, ":time": datetime.utcnow().isoformat()}
        )
        
        return {"success": True, "data": {"message": "Record activated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== RESPONSES ====================

@router.get("/responses")
async def get_all_responses():
    try:
        table = db_client.get_table("Response")
        response = table.scan(Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/responses/active")
async def get_active_responses():
    try:
        table = db_client.get_table("Response")
        response = table.scan(FilterExpression=Attr("is_active").eq(True), Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/responses/{api_id}/{response_id}")
async def get_response(api_id: str, response_id: str):
    try:
        table = db_client.get_table("Response")
        response = table.get_item(Key={"api_id": api_id, "response_id": response_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="Response not found")
        return {"success": True, "data": decimal_to_float(response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/responses")
async def create_response(response_data: ResponseCreate):
    try:
        table = db_client.get_table("Response")
        timestamp = datetime.utcnow().isoformat()
        
        item = response_data.model_dump(exclude={"response_id"})
        item["response_id"] = str(uuid.uuid4())
        item["created_at"] = timestamp
        item["updated_at"] = timestamp
        
        table.put_item(Item=item)
        return {"success": True, "data": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/responses/{api_id}/{response_id}")
async def update_response(api_id: str, response_id: str, response_data: ResponseUpdate):
    try:
        table = db_client.get_table("Response")
        
        response = table.get_item(Key={"api_id": api_id, "response_id": response_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="Response not found")
        
        update_data = response_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
        expr_attr_names = {f"#{k}": k for k in update_data.keys()}
        expr_attr_values = {f":{k}": v for k, v in update_data.items()}
        
        table.update_item(
            Key={"api_id": api_id, "response_id": response_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        
        updated_response = table.get_item(Key={"api_id": api_id, "response_id": response_id})
        return {"success": True, "data": decimal_to_float(updated_response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/responses/{api_id}/{response_id}")
async def deactivate_response(api_id: str, response_id: str):
    try:
        table = db_client.get_table("Response")
        
        response = table.get_item(Key={"api_id": api_id, "response_id": response_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="Response not found")
        
        table.update_item(
            Key={"api_id": api_id, "response_id": response_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": False, ":time": datetime.utcnow().isoformat()}
        )
        
        return {"success": True, "data": {"message": "Record deactivated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/responses/{api_id}/{response_id}/activate")
async def activate_response(api_id: str, response_id: str):
    try:
        table = db_client.get_table("Response")
        
        response = table.get_item(Key={"api_id": api_id, "response_id": response_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Response not found")
        
        table.update_item(
            Key={"api_id": api_id, "response_id": response_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": True, ":time": datetime.utcnow().isoformat()}
        )
        
        return {"success": True, "data": {"message": "Record activated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MOCK APIS ====================

@router.get("/mock_api")
async def get_all_mock_apis():
    try:
        table = db_client.get_table("MockApi")
        response = table.scan(Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mock_api/active")
async def get_active_mock_apis():
    try:
        table = db_client.get_table("MockApi")
        response = table.scan(FilterExpression=Attr("is_active").eq(True), Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mock_api/{project_id}/{api_id}")
async def get_mock_api(project_id: str, api_id: str):
    try:
        table = db_client.get_table("MockApi")
        response = table.get_item(Key={"project_id": project_id, "api_id": api_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="Mock API not found")
        return {"success": True, "data": decimal_to_float(response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mock_api")
async def create_mock_api(mock_api: MockApiCreate):
    try:
        table = db_client.get_table("MockApi")
        timestamp = datetime.utcnow().isoformat()
        
        item = mock_api.model_dump(exclude={"api_id"})
        item["api_id"] = str(uuid.uuid4())
        item["created_at"] = timestamp
        item["updated_at"] = timestamp
        
        table.put_item(Item=item)
        return {"success": True, "data": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/mock_api/{project_id}/{api_id}")
async def update_mock_api(project_id: str, api_id: str, mock_api: MockApiUpdate):
    try:
        table = db_client.get_table("MockApi")
        
        response = table.get_item(Key={"project_id": project_id, "api_id": api_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="Mock API not found")
        
        update_data = mock_api.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
        expr_attr_names = {f"#{k}": k for k in update_data.keys()}
        expr_attr_values = {f":{k}": v for k, v in update_data.items()}
        
        table.update_item(
            Key={"project_id": project_id, "api_id": api_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        
        updated_response = table.get_item(Key={"project_id": project_id, "api_id": api_id})
        return {"success": True, "data": decimal_to_float(updated_response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/mock_api/{project_id}/{api_id}")
async def deactivate_mock_api(project_id: str, api_id: str):
    try:
        table = db_client.get_table("MockApi")
        
        response = table.get_item(Key={"project_id": project_id, "api_id": api_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="Mock API not found")
        
        table.update_item(
            Key={"project_id": project_id, "api_id": api_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": False, ":time": datetime.utcnow().isoformat()}
        )
        
        return {"success": True, "data": {"message": "Record deactivated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/mock_api/{project_id}/{api_id}/activate")
async def activate_mock_api(project_id: str, api_id: str):
    try:
        table = db_client.get_table("MockApi")
        
        response = table.get_item(Key={"project_id": project_id, "api_id": api_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Mock API not found")
        
        table.update_item(
            Key={"project_id": project_id, "api_id": api_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": True, ":time": datetime.utcnow().isoformat()}
        )
        
        return {"success": True, "data": {"message": "Record activated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.patch("/mock_apies/{project_id}/{api_id}/activate")
async def activate_mock_api(project_id: str, api_id: str):
    try:
        table = db_client.get_table("MockApi")
        
        response = table.get_item(Key={"project_id": project_id, "api_id": api_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Mock API not found")
        
        table.update_item(
            Key={"project_id": project_id, "api_id": api_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": True, ":time": datetime.utcnow().isoformat()}
        )
        
        return {"success": True, "data": {"message": "Record activated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
