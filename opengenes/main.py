import uvicorn
from os import getenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from opengenes.api import gene, disease
from opengenes.config import CONFIG,VERSION
from typing import Optional
from pydantic import BaseModel


def assembling_endpoints(app: FastAPI):
    app.include_router(
        gene.router,
        tags=["gene"],
    )
    app.include_router(
        disease.router,
        tags=["disease"],
    )


def init():
    app = FastAPI(
        debug=CONFIG['DEBUG'],
        title='Open Genes backend API',
        root_path=getenv('ROOT_PATH')
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    assembling_endpoints(app)
    return app


app = init()


class Version(BaseModel):
    major: str
    minor: str
    build: Optional[str]
    date:Optional[str]
    revision:Optional[str]

@app.get("/version",tags=["version"],summary="Version info",response_model=Version)
def version()->dict:
    """
    Version information for the running application instance
    """
    return VERSION

def custom_openapi():
    if app.openapi_schema: return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=str(VERSION.get('major','0'))+'.'+str(VERSION.get('minor','0'))+'.'+VERSION.get('build','-'),
        routes=app.routes,
        servers=[{'url':CONFIG.get('API_URL','')}],
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=CONFIG['API_HOST'],
        port=int(CONFIG['API_PORT']),
        reload=True,
        debug=CONFIG['DEBUG'],
    )
