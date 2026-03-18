from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from decimal import Decimal
import uuid
from app.database import db_client
from boto3.dynamodb.conditions import Attr
from app.auth import verify_token
from app.models import (
    UserCreate, UserUpdate,
    ProjectCreate, ProjectUpdate,
    EnvironmentVariableCreate, EnvironmentVariableUpdate,
    ResponseCreate, ResponseUpdate,
    MockApiCreate, MockApiUpdate
)

router = APIRouter(dependencies=[Depends(verify_token)])


# ==================== PROJECTS ====================

@router.patch("/projects/{project_id}")
async def deactivate_project(project_id: str, user_id: str = Depends(verify_token)):
    try:
        table = db_client.get_table("Projects")

        response = table.get_item(Key={"user_id": user_id, "project_id": project_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="Project not found")

        table.update_item(
            Key={"user_id": user_id, "project_id": project_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": False, ":time": datetime.now(timezone.utc).isoformat()}
        )
        return {"success": True, "data": {"message": "Record deactivated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/projects/{project_id}/activate")
async def activate_project(project_id: str, user_id: str = Depends(verify_token)):
    try:
        table = db_client.get_table("Projects")

        response = table.get_item(Key={"user_id": user_id, "project_id": project_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Project not found")

        table.update_item(
            Key={"user_id": user_id, "project_id": project_id},
            UpdateExpression="SET is_active = :val, updated_at = :time",
            ExpressionAttributeValues={":val": True, ":time": datetime.now(timezone.utc).isoformat()}
        )
        return {"success": True, "data": {"message": "Record activated successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





