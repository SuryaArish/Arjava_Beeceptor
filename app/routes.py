from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import Response
from datetime import datetime, timezone
from decimal import Decimal
import uuid
from app.database import get_db_client
from boto3.dynamodb.conditions import Attr
from app.auth import verify_token
from app.models import (
    UserCreate, UserUpdate,
    ProjectCreate, ProjectUpdate,
    EnvironmentVariableCreate, EnvironmentVariableUpdate,
    ResponseCreate, ResponseUpdate,
    MockApiCreate, MockApiUpdate, MockApiBulkImport,
    BulkImportResponse, FailedRecord,
)
from app.export_import_service import (
    export_json, export_csv, export_pdf,
    parse_import_file, validate_and_build_items,
)

router = APIRouter(dependencies=[Depends(verify_token)])

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    return obj

# ==================== PROJECTS ====================

@router.get("/projects")
async def get_projects(user_id: str = Depends(verify_token), project_id: str = None):
    try:
        table = get_db_client().get_table("projects")
        if project_id:
            response = table.get_item(Key={"user_id": user_id, "project_id": project_id})
            if "Item" not in response:
                raise HTTPException(status_code=404, detail="Project not found")
            return {"success": True, "data": decimal_to_float(response["Item"])}

        response = table.scan(FilterExpression=Attr("user_id").eq(user_id))
        items = decimal_to_float(response.get("Items", []))
        mock_api_table = get_db_client().get_table("mock_api")
        for item in items:
            api_response = mock_api_table.scan(FilterExpression=Attr("project_id").eq(str(item["project_id"]).strip()))
            item["api_count"] = len(api_response.get("Items", []))
        return {"success": True, "data": items}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects")
async def create_project(project: ProjectCreate, user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("projects")
        timestamp = datetime.now(timezone.utc).isoformat()

        item = project.model_dump(exclude={"project_id"})
        item["project_id"] = str(uuid.uuid4())
        item["user_id"] = user_id
        item["created_at"] = timestamp
        item["updated_at"] = timestamp
        item["is_active"] = True

        table.put_item(Item=item)
        return {"success": True, "data": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/projects")
async def update_project(project: ProjectUpdate, project_id: str = Query(...), user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("projects")

        response = table.get_item(Key={"user_id": user_id, "project_id": project_id})
        if "Item" not in response or not response["Item"].get("is_active", False):
            raise HTTPException(status_code=404, detail="Project not found")

        update_data = project.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
        expr_attr_names = {f"#{k}": k for k in update_data.keys()}
        expr_attr_values = {f":{k}": v for k, v in update_data.items()}

        table.update_item(
            Key={"user_id": user_id, "project_id": project_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )

        updated = table.get_item(Key={"user_id": user_id, "project_id": project_id})
        return {"success": True, "data": decimal_to_float(updated["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/projects")
async def delete_project(project_id: str = Query(...), user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("projects")
        response = table.get_item(Key={"user_id": user_id, "project_id": project_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Project not found")
        table.delete_item(Key={"user_id": user_id, "project_id": project_id})
        return {"success": True, "data": {"message": "Project deleted successfully"}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENVIRONMENT VARIABLES ====================

@router.get("/environment_variables")
async def get_all_environment_variables(project_id: str, env_id: str = None, user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("environment_variable")
        filter_expr = Attr("project_id").eq(project_id)
        if env_id:
            filter_expr = filter_expr & Attr("env_id").eq(env_id)
        response = table.scan(FilterExpression=filter_expr)
        return {"status": "success", "data": decimal_to_float(response.get("Items", []))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/environment_variables/{env_id}")
async def get_environment_variable(env_id: str, project_id: str, user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("environment_variable")
        response = table.get_item(Key={"project_id": project_id, "env_id": env_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Environment variable not found")
        return {"status": "success", "data": decimal_to_float(response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/environment_variables")
async def create_environment_variable(variable: EnvironmentVariableCreate, user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("environment_variable")
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "project_id": variable.project_id,
            "env_id": str(uuid.uuid4()),
            "environment_name": variable.environment_name,
            "environment_values": variable.environment_values,
            "created_at": now,
            "updated_at": now,
            "created_by": variable.created_by,
            "updated_by": variable.updated_by,
        }
        table.put_item(Item=item)
        return {"status": "success", "message": "Environment created successfully", "data": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/environment_variables/{env_id}")
async def update_environment_variable(env_id: str, project_id: str, variable: EnvironmentVariableUpdate, user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("environment_variable")
        response = table.get_item(Key={"project_id": project_id, "env_id": env_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Environment variable not found")

        update_data = variable.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data])
        table.update_item(
            Key={"project_id": project_id, "env_id": env_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={f"#{k}": k for k in update_data},
            ExpressionAttributeValues={f":{k}": v for k, v in update_data.items()},
        )
        updated = table.get_item(Key={"project_id": project_id, "env_id": env_id})
        return {"status": "success", "message": "Environment updated successfully", "data": decimal_to_float(updated["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/environment_variables/{env_id}")
async def delete_environment_variable(env_id: str, project_id: str, user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("environment_variable")
        response = table.get_item(Key={"project_id": project_id, "env_id": env_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Environment variable not found")
        table.delete_item(Key={"project_id": project_id, "env_id": env_id})
        return {"status": "success", "message": "Environment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MOCK APIS ====================

@router.get("/mock_apis")
async def get_all_mock_apis(project_id: str, env_id: str = None, user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("mock_api")
        filter_expr = Attr("project_id").eq(project_id)
        if env_id:
            filter_expr = filter_expr & Attr("env_id").eq(env_id)
        response = table.scan(FilterExpression=filter_expr)
        return {"status": "success", "data": decimal_to_float(response.get("Items", []))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mock_apis/{api_id}")
async def get_mock_api(api_id: str, project_id: str, user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("mock_api")
        response = table.get_item(Key={"project_id": project_id, "api_id": api_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Mock API not found")
        return {"status": "success", "data": decimal_to_float(response["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mock_apis")
async def create_mock_api(mock_api: MockApiCreate, user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("mock_api")
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "project_id": mock_api.project_id,
            "api_id": str(uuid.uuid4()),
            "env_id": mock_api.env_id,
            "method": mock_api.method,
            "request_condition": mock_api.request_condition,
            "expression": mock_api.expression,
            "state_condition": mock_api.state_condition,
            "query_header": mock_api.query_header,
            "response": mock_api.response,
            "description": mock_api.description,
            "is_active": mock_api.is_active,
            "created_at": now,
            "updated_at": now,
            "created_by": mock_api.created_by,
            "updated_by": mock_api.updated_by,
        }
        table.put_item(Item=item)
        return {"status": "success", "message": "Mock API created successfully", "data": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/mock_apis/{api_id}")
async def update_mock_api(api_id: str, project_id: str, mock_api: MockApiUpdate, user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("mock_api")
        response = table.get_item(Key={"project_id": project_id, "api_id": api_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Mock API not found")

        update_data = mock_api.model_dump(exclude_unset=True)
        if "env_id" in update_data:
            update_data["env_id"] = update_data.pop("env_id")
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        # DynamoDB reserved words that need aliasing
        reserved = {"method", "expression", "response", "status", "name"}
        expr_names, expr_values, parts = {}, {}, []
        for k, v in update_data.items():
            if k in reserved:
                expr_names[f"#{k}"] = k
                expr_values[f":{k}"] = v
                parts.append(f"#{k} = :{k}")
            else:
                expr_values[f":{k}"] = v
                parts.append(f"{k} = :{k}")

        kwargs = {
            "Key": {"project_id": project_id, "api_id": api_id},
            "UpdateExpression": "SET " + ", ".join(parts),
            "ExpressionAttributeValues": expr_values,
        }
        if expr_names:
            kwargs["ExpressionAttributeNames"] = expr_names

        table.update_item(**kwargs)
        updated = table.get_item(Key={"project_id": project_id, "api_id": api_id})
        return {"status": "success", "message": "Mock API updated successfully", "data": decimal_to_float(updated["Item"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/mock_apis/{api_id}")
async def delete_mock_api(api_id: str, project_id: str, user_id: str = Depends(verify_token)):
    try:
        table = get_db_client().get_table("mock_api")
        response = table.get_item(Key={"project_id": project_id, "api_id": api_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Mock API not found")
        table.delete_item(Key={"project_id": project_id, "api_id": api_id})
        return {"status": "success", "message": "Mock API deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.post("/mock_apis/bulk_import")
# async def bulk_import_mock_apis(payload: MockApiBulkImport, user_id: str = Depends(verify_token)):
#     table = get_db_client().get_table("mock_api")
#     now = datetime.now(timezone.utc).isoformat()
#     successful, failed = 0, 0

#     # DynamoDB batch_write_item supports max 25 items per batch
#     items = []
#     for mock_api in payload.items:
#         items.append({
#             "project_id": mock_api.project_id,
#             "api_id": str(uuid.uuid4()),
#             "env_id": mock_api.env_id,
#             "method": mock_api.method,
#             "request_condition": mock_api.request_condition,
#             "expression": mock_api.expression,
#             "state_condition": mock_api.state_condition,
#             "query_header": mock_api.query_header,
#             "response": mock_api.response,
#             "description": mock_api.description,
#             "is_active": mock_api.is_active,
#             "created_at": now,
#             "updated_at": now,
#             "created_by": mock_api.created_by,
#             "updated_by": mock_api.updated_by,
#         })

#     # Process in chunks of 25 (DynamoDB batch limit)
#     for i in range(0, len(items), 25):
#         chunk = items[i:i + 25]
#         try:
#             response = get_db_client().dynamodb.batch_write_item(
#                 RequestItems={
#                     "mock_api": [{"PutRequest": {"Item": item}} for item in chunk]
#                 }
#             )
#             # Handle unprocessed items
#             unprocessed = response.get("UnprocessedItems", {}).get("mock_api", [])
#             successful += len(chunk) - len(unprocessed)
#             failed += len(unprocessed)
#         except Exception:
#             failed += len(chunk)

#     return {
#         "status": "success",
#         "message": "Bulk import completed",
#         "total_records": len(items),
#         "successful_imports": successful,
#         "failed_imports": failed,
#     }

# ==================== Additional APIS ====================


# ── Bulk Export ───────────────────────────────────────────────────────────────

@router.get("/mock_apis/export/{project_id}")
async def export_mock_apis(
    project_id: str,
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    user_id: str = Depends(verify_token),
):
    """Export all Mock APIs for a project as JSON, CSV, or PDF."""
    try:
        table = get_db_client().get_table("mock_api")
        response = table.scan(FilterExpression=Attr("project_id").eq(project_id))
        items = response.get("Items", [])

        # Paginate through all results
        while "LastEvaluatedKey" in response:
            response = table.scan(
                FilterExpression=Attr("project_id").eq(project_id),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        if not items:
            raise HTTPException(status_code=404, detail="No APIs found for this project")

        # Convert Decimal → float for serialization
        items = decimal_to_float(items)

        if format == "json":
            return Response(
                content=export_json(items),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={project_id}_apis.json"},
            )
        if format == "csv":
            return Response(
                content=export_csv(items),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={project_id}_apis.csv"},
            )
        # pdf
        return Response(
            content=export_pdf(items, project_id),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={project_id}_apis.pdf"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Enhanced Bulk Import ──────────────────────────────────────────────────────

@router.post("/mock_apis/bulk_import", response_model=BulkImportResponse)
async def bulk_import_mock_apis_v2(
    payload: list[MockApiCreate],
    user_id: str = Depends(verify_token),
):
    """Bulk import Mock APIs from a JSON array with per-record validation."""
    now = datetime.now(timezone.utc).isoformat()
    valid_items, failed_records = validate_and_build_items(
        [r.model_dump() for r in payload], now
    )

    successful = 0
    if valid_items:
        dynamodb = get_db_client().dynamodb
        for i in range(0, len(valid_items), 25):
            chunk = valid_items[i:i + 25]
            try:
                resp = dynamodb.batch_write_item(
                    RequestItems={
                        "mock_api": [{"PutRequest": {"Item": item}} for item in chunk]
                    }
                )
                unprocessed = resp.get("UnprocessedItems", {}).get("mock_api", [])
                successful += len(chunk) - len(unprocessed)
                for up in unprocessed:
                    failed_records.append(
                        FailedRecord(index=-1, reason="DynamoDB unprocessed", data=up)
                    )
            except Exception as e:
                for item in chunk:
                    failed_records.append(FailedRecord(index=-1, reason=str(e), data=item))

    return BulkImportResponse(
        total=len(payload),
        successful=successful,
        failed=len(failed_records),
        failed_records=failed_records,
    )
