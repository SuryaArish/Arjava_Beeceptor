from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Dict, Any

class UserCreate(BaseModel):
    userId: Optional[str] = None
    user_name: str
    role: str
    email: EmailStr
    login_type: str
    subscription: str
    is_active: bool = True
    created_by: str
    updated_by: str
    
    @field_validator('userId')
    @classmethod
    def reject_user_id(cls, v):
        if v is not None:
            raise ValueError("Primary key is auto-generated. Do not provide it.")
        return v

class UserUpdate(BaseModel):
    user_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[EmailStr] = None
    login_type: Optional[str] = None
    subscription: Optional[str] = None
    is_active: Optional[bool] = None
    updated_by: str

class ProjectCreate(BaseModel):
    user_id: str
    project_id: Optional[str] = None
    project_name: str
    visibility: str
    environment_type: str
    is_active: bool = True
    created_by: str
    updated_by: str
    
    @field_validator('project_id')
    @classmethod
    def reject_project_id(cls, v):
        if v is not None:
            raise ValueError("Primary key is auto-generated. Do not provide it.")
        return v

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    visibility: Optional[str] = None
    environment_type: Optional[str] = None
    updated_by: str

class GlobalVariableCreate(BaseModel):
    project_id: str
    variable_id: Optional[str] = None
    variable_name: str
    environment_names: Dict[str, Any]
    created_by: str
    updated_by: str
    
    @field_validator('variable_id')
    @classmethod
    def reject_variable_id(cls, v):
        if v is not None:
            raise ValueError("Primary key is auto-generated. Do not provide it.")
        return v

class GlobalVariableUpdate(BaseModel):
    variable_name: Optional[str] = None
    environment_names: Optional[Dict[str, Any]] = None
    updated_by: str

class ResponseCreate(BaseModel):
    api_id: str
    response_id: Optional[str] = None
    response_type: str
    response_delay: int
    status: str
    response_header: Dict[str, Any]
    response_body: Dict[str, Any]
    
    @field_validator('response_id')
    @classmethod
    def reject_response_id(cls, v):
        if v is not None:
            raise ValueError("Primary key is auto-generated. Do not provide it.")
        return v

class ResponseUpdate(BaseModel):
    response_type: Optional[str] = None
    response_delay: Optional[int] = None
    status: Optional[str] = None
    response_header: Optional[Dict[str, Any]] = None
    response_body: Optional[Dict[str, Any]] = None

class MockApiCreate(BaseModel):
    project_id: str
    api_id: Optional[str] = None
    method: str
    request_condition: Dict[str, Any]
    expression: Dict[str, Any]
    state_condition: Dict[str, Any]
    query_header: Dict[str, Any]
    description: str
    is_active: bool = True
    created_by: str
    updated_by: str
    
    @field_validator('api_id')
    @classmethod
    def reject_api_id(cls, v):
        if v is not None:
            raise ValueError("Primary key is auto-generated. Do not provide it.")
        return v

class MockApiUpdate(BaseModel):
    method: Optional[str] = None
    request_condition: Optional[Dict[str, Any]] = None
    expression: Optional[Dict[str, Any]] = None
    state_condition: Optional[Dict[str, Any]] = None
    query_header: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    updated_by: str
