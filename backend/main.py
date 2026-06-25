"""
HDFS Explorer — FastAPI Backend
================================
提供 HDFS 文件浏览、目录遍历、文件上传功能。
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from hdfs import InsecureClient

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
HDFS_URL = os.getenv("HDFS_URL", "http://localhost:9870")
HDFS_USER = os.getenv("HDFS_USER", "liu")  # 默认使用目录拥有者，确保有写入权限
HDFS_ROOT = os.getenv("HDFS_ROOT", "/")

UPLOAD_STAGING = Path(__file__).resolve().parent / "uploads"
UPLOAD_STAGING.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# App & CORS
# ---------------------------------------------------------------------------
app = FastAPI(title="HDFS Explorer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# HDFS Client (lazy)
# ---------------------------------------------------------------------------
_hdfs_client: Optional[InsecureClient] = None


def get_hdfs_client() -> InsecureClient:
    global _hdfs_client
    if _hdfs_client is None:
        _hdfs_client = InsecureClient(HDFS_URL, user=HDFS_USER)
    return _hdfs_client


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class FileItem(BaseModel):
    name: str
    path: str
    kind: str  # "file" | "directory"
    size: int = 0
    modification_time: Optional[str] = None


class DirectoryListing(BaseModel):
    current_path: str
    items: list[FileItem]


class UploadResult(BaseModel):
    success: bool
    message: str
    remote_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health():
    """健康检查"""
    try:
        client = get_hdfs_client()
        client.status(HDFS_ROOT)
        hdfs_status = "connected"
    except Exception as exc:
        hdfs_status = f"error: {exc}"
    return {"status": "ok", "hdfs": hdfs_status}


@app.get("/api/browse", response_model=DirectoryListing)
async def browse(path: str = Query("/", description="HDFS 路径")):
    """列出指定 HDFS 路径下的所有文件和文件夹。"""
    client = get_hdfs_client()
    try:
        statuses = client.list(path, status=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"无法访问 HDFS 路径 {path}: {exc}")

    items: list[FileItem] = []
    for name, meta in statuses:
        kind = meta.get("type", "FILE").lower()
        if kind not in ("file", "directory"):
            kind = "file"
        mod_time = meta.get("modificationTime")
        if mod_time is not None:
            mod_time = str(mod_time)

        items.append(
            FileItem(
                name=name,
                path=f"{path.rstrip('/')}/{name}",
                kind=kind,
                size=meta.get("length") or meta.get("spaceConsumed") or 0,
                modification_time=mod_time,
            )
        )

    items.sort(key=lambda x: (0 if x.kind == "directory" else 1, x.name.lower()))
    return DirectoryListing(current_path=path, items=items)


@app.get("/api/download")
async def download_file(path: str = Query(..., description="HDFS 文件完整路径")):
    """从 HDFS 下载文件。"""
    client = get_hdfs_client()
    local_path = UPLOAD_STAGING / Path(path).name

    try:
        client.download(path, str(local_path), overwrite=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"下载失败: {exc}")

    return FileResponse(
        path=str(local_path),
        filename=Path(path).name,
        media_type="application/octet-stream",
    )


@app.post("/api/upload", response_model=UploadResult)
async def upload_file(
    file: UploadFile = File(...),
    remote_dir: str = Query("/", description="HDFS 目标目录"),
):
    """上传文件到 HDFS 指定目录。"""
    # 1) 暂存到本地
    safe_name = Path(file.filename).name
    local_dest = UPLOAD_STAGING / safe_name
    try:
        with open(local_dest, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"本地暂存失败: {exc}")

    # 2) 上传到 HDFS
    client = get_hdfs_client()
    remote_path = f"{remote_dir.rstrip('/')}/{safe_name}"
    try:
        client.upload(remote_path, str(local_dest), overwrite=True)
    except Exception as exc:
        local_dest.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"HDFS 上传失败: {exc}")

    # 3) 清理本地文件
    local_dest.unlink(missing_ok=True)

    return UploadResult(
        success=True,
        message=f"文件 {safe_name} 已上传至 {remote_path}",
        remote_path=remote_path,
    )


@app.delete("/api/delete")
async def delete_item(path: str = Query(..., description="HDFS 文件或目录路径")):
    """删除 HDFS 上的文件或目录。"""
    client = get_hdfs_client()
    try:
        status = client.status(path)
        if status["type"] == "DIRECTORY":
            client.delete(path, recursive=True)
        else:
            client.delete(path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"删除失败: {exc}")
    return {"success": True, "message": f"已删除 {path}"}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
