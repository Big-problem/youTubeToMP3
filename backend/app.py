import os
import subprocess
import threading
import uuid
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import shutil

def get_windows_download_dir():
  try:
    # 呼叫 Windows cmd 取得使用者名稱
    win_user = (
        subprocess.check_output(["cmd.exe", "/c", "echo %USERNAME%"], text=True)
        .strip()
        .replace("\r", "")
    )
    win_download = f"/mnt/c/Users/{win_user}/Downloads"
    if os.path.exists(win_download):
      return win_download
  except Exception:
    pass
  # 若抓取失敗則使用預設 WSL 目錄
  return os.path.join(os.getcwd(), "downloads")

def get_valid_cookie_path():
    secret_cookie = '/etc/secrets/cookies.txt'
    writable_cookie = '/tmp/cookies.txt'
    local_cookie = 'cookies.txt'

    # 如果是 Render 雲端環境
    if os.path.exists(secret_cookie):
        # 將唯讀的 /etc/secrets/cookies.txt 複製到可讀寫的 /tmp/cookies.txt
        shutil.copyfile(secret_cookie, writable_cookie)
        return writable_cookie
    # 如果是本機測試環境
    elif os.path.exists(local_cookie):
        return local_cookie
    
    return None

app = FastAPI(title="YouTube to MP3 Backend API")

# 1. 允許 Windows 端 Chrome 跨域呼叫 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 下載檔案暫存目錄
DOWNLOAD_DIR = get_windows_download_dir()
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 記憶體中的任務隊列字典
tasks: Dict[str, Dict[str, Any]] = {}


class ConvertRequest(BaseModel):
  url: str
  quality: str = "192"


# 2. 下載進度回報 Hook
def progress_hook(d, task_id: str):
  if d['status'] == 'downloading':
    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
    downloaded = d.get('downloaded_bytes', 0)
    percent = (downloaded / total * 100) if total > 0 else 0

    tasks[task_id].update({
        "status": "downloading",
        "progress": round(percent, 1),
        "speed_mbps": (
            round(d.get('speed', 0) / (1024 * 1024), 2) if d.get('speed') else 0
        ),
    })
  elif d['status'] == 'finished':
    tasks[task_id].update({"status": "converting", "progress": 99.0})


# 3. 背景執行緒：負責真正下載與 FFmpeg 轉檔
def process_download(task_id: str, url: str, quality: str):
  ydl_opts = {
      'format': 'bestaudio/best',
      'cookiefile': get_valid_cookie_path(),
      'postprocessors': [
          {
              'key': 'FFmpegExtractAudio',
              'preferredcodec': 'mp3',
              'preferredquality': quality,
          },
          {'key': 'FFmpegMetadata', 'add_metadata': True},
      ],
      'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
      'progress_hooks': [lambda d: progress_hook(d, task_id)],
      'js_runtimes': ['node', 'nodejs'],
      'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
      'quiet': True,
  }

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(url, download=True)

      base_path = os.path.splitext(ydl.prepare_filename(info))[0]
      mp3_file = f'{base_path}.mp3'

      if os.path.exists(mp3_file):
        tasks[task_id].update({
            "status": "completed",
            "progress": 100.0,
            "title": info.get('title', 'Audio'),
            "file_path": mp3_file,
            "file_name": os.path.basename(mp3_file),
        })
  except Exception as e:
    tasks[task_id].update({"status": "failed", "error": str(e)})


# --- API 路由定義 ---


# 觸發轉檔：建立 Task 並開背景線程
@app.post("/api/convert")
def convert_video(req: ConvertRequest):
  task_id = str(uuid.uuid4())[:8]
  tasks[task_id] = {"task_id": task_id, "status": "queued", "progress": 0.0}

  thread = threading.Thread(target=process_download, args=(task_id, req.url, req.quality))
  thread.daemon = True
  thread.start()
  return {"task_id": task_id, "status": "queued"}


# 輪詢狀態：讓前端查詢下載進度
@app.get("/api/status/{task_id}")
def get_status(task_id: str):
  return tasks.get(task_id, {"error": "Task not found"})


# 下載檔案：將 MP3 串流傳回給前端
@app.get("/api/download/{task_id}")
def download_file(task_id: str):
  task = tasks.get(task_id)
  if task and task.get("status") == "completed":
    return FileResponse(
        task["file_path"], filename=task["file_name"], media_type="audio/mpeg"
    )
  raise HTTPException(status_code=400, detail="檔案尚未準備好")

