import os
import uuid
import threading
import redis
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
from typing import Optional, Dict


redis_url = 'redis://default:aBovTmTNorEMzEEISFITigtlmkSBaDbL@junction.proxy.rlwy.net:32124'

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.redis_client = redis.from_url(redis_url)
        self.model = WhisperModel('base', device='cpu', compute_type='int8')

    def process_transcription(self, task_id: str, file_path: str, language: Optional[str] = None):
        try:
            transcribe_kwargs = {"language": language} if language else {}
            segments, info = self.model.transcribe(file_path, **transcribe_kwargs)
            
            transcription = " ".join([segment.text for segment in segments])
            
            self.tasks[task_id].update({
                'status': 'COMPLETED',
                'transcription': transcription,
                'language': info.language
            })
            
            self.redis_client.hmset(f"task:{task_id}", {
                'status': 'COMPLETED',
                'transcription': transcription,
                'language': info.language
            })
        
        except Exception as e:
            self.tasks[task_id]['status'] = 'FAILED'
            self.tasks[task_id]['error'] = str(e)
        
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)

task_manager = TaskManager()

app = FastAPI(title="Speech-to-Text Transcription API")

# Comprehensive CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Explicitly allow all methods
    allow_headers=["*"],  # Allow all headers
)

@app.post("/transcribe/")
async def start_transcription(
    file: UploadFile = File(...), 
    language: Optional[str] = None
):
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    task_id = str(uuid.uuid4())
    temp_filename = f"/tmp/{task_id}_{file.filename}"
    
    with open(temp_filename, "wb") as buffer:
        buffer.write(await file.read())
    
    task_manager.tasks[task_id] = {
        'status': 'PENDING',
        'original_filename': file.filename
    }
    
    thread = threading.Thread(
        target=task_manager.process_transcription, 
        args=(task_id, temp_filename, language)
    )
    thread.start()
    
    return {
        "task_id": task_id,
        "status": "Task queued"
    }

@app.get("/task/{task_id}")
def get_task_status(task_id: str):
    task = task_manager.tasks.get(task_id)
    
    if not task:
        task_data = task_manager.redis_client.hgetall(f"task:{task_id}")
        if task_data:
            task = {k.decode(): v.decode() for k, v in task_data.items()}
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "status": task.get('status', 'PENDING'),
        "transcription": task.get('transcription', ''),
        "language": task.get('language', ''),
        "error": task.get('error', '')
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Run with: uvicorn backend:app --port 8000 --host 0.0.0.0