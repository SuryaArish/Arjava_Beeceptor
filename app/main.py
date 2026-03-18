from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from routes import router

app = FastAPI(
    title="DynamoDB REST API",
    description="Production-ready FastAPI with AWS DynamoDB",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": str(exc.errors()[0]["msg"])}
    )

app.include_router(router)

@app.get("/")
async def root():
    return {"success": True, "data": {"message": "DynamoDB API is running", "status": "healthy"}}
