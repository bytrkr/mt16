from fastapi import FastAPI
from .service import collect_evidence

def create_app() -> FastAPI:
    app = FastAPI(title="MT16 Evidence Service")

    @app.post("/evidence/collect")
    def collect(payload: dict):
        return collect_evidence(payload)

    return app

app = create_app()
