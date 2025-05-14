import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

from ..models import Task, TaskCreate
from ..services.task_service import TaskService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])

def get_task_service():
    """Dependency to get task service."""
    return TaskService()

class TaskRouter:
    """Router for task endpoints."""
    
    def __init__(self):
        """Initialize the task router."""
        
        # Register routes
        @router.post("/", response_model=Task)
        def create_task_endpoint(task: TaskCreate, service: TaskService = Depends(get_task_service)):
            """Create a new task."""
            try:
                result = service.create_task(task.title, task.description, task.document_id, task.code_path)
                if result.get("status") == "error":
                    raise HTTPException(status_code=500, detail=result.get("message"))
                
                # Get created task
                tasks = service.get_tasks()
                for t in tasks:
                    if t["id"] == result.get("task_id"):
                        return t
                
                raise HTTPException(status_code=500, detail="Failed to retrieve created task")
            except Exception as e:
                logger.error(f"Error creating task: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.get("/", response_model=List[Task])
        def read_tasks(status: Optional[str] = None, service: TaskService = Depends(get_task_service)):
            """Get tasks, optionally filtered by status."""
            try:
                return service.get_tasks(status)
            except Exception as e:
                logger.error(f"Error reading tasks: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.put("/{task_id}", response_model=Task)
        def update_task_status(task_id: int, status: str, service: TaskService = Depends(get_task_service)):
            """Update task status."""
            try:
                result = service.update_task_status(task_id, status)
                if not result:
                    raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
                return result
            except Exception as e:
                logger.error(f"Error updating task status: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))