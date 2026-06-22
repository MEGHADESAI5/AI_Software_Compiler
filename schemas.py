from pydantic import BaseModel
from typing import List, Optional

class Field(BaseModel):
    name: str
    type: str  # string, integer, uuid, datetime, boolean
    required: bool = False
    unique: bool = False

class Table(BaseModel):
    name: str
    columns: List[Field]

class Endpoint(BaseModel):
    path: str
    method: str  # GET, POST, PUT, DELETE
    auth_required: bool = True
    request_schema: Optional[dict] = None
    response_schema: dict

class Page(BaseModel):
    route: str
    components: List[str]

class Role(BaseModel):
    name: str
    permissions: List[str]

class AppConfig(BaseModel):
    app_name: str
    tables: List[Table]
    endpoints: List[Endpoint]
    pages: List[Page]
    roles: List[Role]
    assumptions: List[str] = []  # Track what you guessed