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
        table = db_client.get_table("users")
        response = table.scan(Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/active")
async def get_active_users():
    try:
        table = db_client.get_table("users")
        response = table.scan(FilterExpression=Attr("is_active").eq(True), Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        table = db_client.get_table("users")
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
        table = db_client.get_table("users")
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
        table = db_client.get_table("users")
        
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
        table = db_client.get_table("users")
        
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
        table = db_client.get_table("users")
        
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

@router.get("/projects/active")
async def get_active_projects():
    try:
        table = db_client.get_table("projects")
        response = table.scan(FilterExpression=Attr("is_active").eq(True), Limit=100)
        items = decimal_to_float(response.get("Items", []))
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENVIRONMENT VARIABLES ====================

@router.get("/environment-variables")
async def get_all_environment_variables():
    try:
        table = db_client.get_table("environment_variable")
        response = table.scan(Limit=100)
        return {"success": True, "data": decimal_to_float(response.get("Items", []))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/environment-variables/{project_id}/{env_id}")
async def get_environment_variable(project_id: str, env_id: str):
    try:
        table = db_client.get_table("environment_variable")
        response = table.get_item(Key={"project_id": project_id, "env_id": env_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Environment variable not found")
        return {"success": True, "data": decimal_to_float(response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/environment-variables")
async def create_environment_variable(variable: EnvironmentVariableCreate):
    try:
        table = db_client.get_table("environment_variable")
        timestamp = datetime.now(timezone.utc).isoformat()

        item = {
            "project_id": variable.project_id,
            "env_id": str(uuid.uuid4()),
            "environment_name": variable.environment_name,
            "environment_values": variable.environment_values,
            "created_at": timestamp,
            "updated_at": timestamp,
            "created_by": variable.created_by,
            "updated_by": variable.updated_by
        }

        table.put_item(Item=item)
        return {"success": True, "data": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/environment-variables/{project_id}/{env_id}")
async def update_environment_variable(project_id: str, env_id: str, variable: EnvironmentVariableUpdate):
    try:
        table = db_client.get_table("environment_variable")

        response = table.get_item(Key={"project_id": project_id, "env_id": env_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Environment variable not found")

        update_data = variable.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
        expr_attr_names = {f"#{k}": k for k in update_data.keys()}
        expr_attr_values = {f":{k}": v for k, v in update_data.items()}

        table.update_item(
            Key={"project_id": project_id, "env_id": env_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )

        updated = table.get_item(Key={"project_id": project_id, "env_id": env_id})
        return {"success": True, "data": decimal_to_float(updated["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/environment-variables/{project_id}/{env_id}")
async def delete_environment_variable(project_id: str, env_id: str):
    try:
        table = db_client.get_table("environment_variable")

        response = table.get_item(Key={"project_id": project_id, "env_id": env_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Environment variable not found")

        table.delete_item(Key={"project_id": project_id, "env_id": env_id})
        return {"success": True, "data": {"message": "Environment variable deleted successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
