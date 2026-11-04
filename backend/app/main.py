from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Manpower ERP API", version="0.1.0")


class Bootstrap(BaseModel):
    name: Literal["Manpower ERP"] = "Manpower ERP"
    stage: Literal["bootstrap"] = "bootstrap"


@app.get("/api/bootstrap", response_model=Bootstrap)
def bootstrap() -> Bootstrap:
    return Bootstrap()
