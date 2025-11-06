# app/main.py
import os
import string
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.exc import SQLAlchemyError
from fastapi.staticfiles import StaticFiles


from app.db import SessionLocal, engine
from app.models import Base, Link

# Create tables if not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="URL Shortener")
ALPHABET = string.digits + string.ascii_letters  # base62: 0-9A-Za-z

def encode_base62(num: int) -> str:
    if num == 0:
        return ALPHABET[0]
    arr = []
    base = len(ALPHABET)
    while num:
        num, rem = divmod(num, base)
        arr.append(ALPHABET[rem])
    arr.reverse()
    return ''.join(arr)

class CreateReq(BaseModel):
    url: HttpUrl
    custom: str | None = None

@app.post("/shorten")
def create_short(req: CreateReq):
    db = SessionLocal()
    try:
        # If user provided custom short, verify uniqueness.
        if req.custom:
            existing = db.query(Link).filter_by(short=req.custom).first()
            if existing:
                raise HTTPException(status_code=400, detail="custom short already taken")
            link = Link(short=req.custom, target=str(req.url))
            db.add(link)
            db.commit()
            db.refresh(link)
            return {"short": link.short}
        # Otherwise, create placeholder row then set short to base62(id)
        placeholder = Link(short="", target=str(req.url))
        db.add(placeholder)
        db.commit()
        db.refresh(placeholder)
        short = encode_base62(placeholder.id)
        placeholder.short = short
        db.add(placeholder)
        db.commit()
        return {"short": short}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="db error")
    finally:
        db.close()

@app.get("/{short}")
def redirect_short(short: str):
    db = SessionLocal()
    try:
        link = db.query(Link).filter_by(short=short).first()
        if not link:
            raise HTTPException(status_code=404, detail="Not found")
        link.clicks = (link.clicks or 0) + 1
        db.add(link)
        db.commit()
        return RedirectResponse(url=link.target)
    finally:
        db.close()

@app.get("/admin/list")
def admin_list(limit: int = 100):
    db = SessionLocal()
    try:
        rows = db.query(Link).order_by(Link.created_at.desc()).limit(limit).all()
        return [{"id": r.id, "short": r.short, "target": r.target, "clicks": r.clicks} for r in rows]
    finally:
        db.close()

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
