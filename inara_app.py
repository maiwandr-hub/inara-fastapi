from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Hello FastAPI App")

class TriangleInput(BaseModel):
    message: str = "hello world"
    height: int = 4

def build_triangle(message: str, height: int) -> str:
    if not message.strip():
        raise ValueError("message must be non-empty")
    if height < 0:
        raise ValueError("height must be >= 0")
    lines = [message]
    for i in range(height):
        spaces = " " * (height - i - 1)
        lines.append(f"{spaces}/")
    return "\n".join(lines)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/triangle")
def triangle(body: TriangleInput):
    try:
        result = build_triangle(body.message, body.height)
        return {"ok": True, "triangle": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
