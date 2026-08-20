"""
HTTP adapter.

Run:
    uvicorn parser.api:app --reload

POST /parse
    {"text": "..."}
->  200 {"criteria": {...}}
->  422 {"detail": "..."}   on parse/schema failure
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .core import parse_brief, ParseError

app = FastAPI(title="Hiring Brief Parser")


class ParseRequest(BaseModel):
    text: str


class ParseResponse(BaseModel):
    criteria: dict


@app.post("/parse", response_model=ParseResponse)
def parse(req: ParseRequest) -> ParseResponse:
    try:
        result = parse_brief(req.text)
    except ParseError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return ParseResponse(criteria=result)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
