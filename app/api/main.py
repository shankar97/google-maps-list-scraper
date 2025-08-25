from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, HttpUrl

from lib.map_content.fetch import fetch_places

class FetchRequest(BaseModel):
    url: HttpUrl

class Place(BaseModel):
    name: str | None
    rating: str | None
    description: str | None
    price: str | None

class FetchResponse(BaseModel):
    list_description: Optional[str] = None
    items: List[Place]


app = FastAPI(title="Maps Extractor API")

@app.post("/fetch", response_model=FetchResponse)
def fetch(request: FetchRequest) -> Any:
    try:
        print(f'fetching url #{request.url}')
        result = fetch_places(str(request.url))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load URL: {e}")
