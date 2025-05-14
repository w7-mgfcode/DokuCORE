import logging
from typing import List, Dict, Any, Optional

from ..utils.db import get_db_connection

logger = logging.getLogger(__name__)

class TaskService:
    """Service for task operations."""
    
    def get_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get tasks, optionally filtered by status.
        
        Args:
            status (Optional[str]): Filter tasks by this status if provided.
            
        Returns:
            List[Dict[str, Any]]: List of tasks.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            if status:
                cursor.execute("SELECT * FROM tasks WHERE status = %s", (status,))
            else:
                cursor.execute("SELECT * FROM tasks")

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting tasks: {str(e)}")
            return []
    
    def create_task(self, title: str, description: str, document_id: Optional[int] = None, code_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new task.
        
        Args:
            title (str): Task title.
            description (str): Task description.
            document_id (Optional[int]): Associated document ID, if any.
            code_path (Optional[str]): Associated code path, if any.
            
        Returns:
            Dict[str, Any]: Result of the task creation.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            cursor.execute(
                """INSERT INTO tasks (title, description, document_id, code_path)
                VALUES (%s, %s, %s, %s) RETURNING id""",
                (title, description, document_id, code_path)
            )

            task_id = cursor.fetchone()["id"]
            conn.commit()
            cursor.close()
            conn.close()

            return {"status": "success", "message": f"Task created with ID {task_id}", "task_id": task_id}
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def update_task_status(self, task_id: int, status: str) -> Optional[Dict[str, Any]]:
        """
        Update a task's status.
        
        Args:
            task_id (int): Task ID.
            status (str): New status.
            
        Returns:
            Optional[Dict[str, Any]]: Updated task data or None if failed.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            cursor.execute(
                """UPDATE tasks SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s RETURNING *""",
                (status, task_id)
            )

            result = cursor.fetchone()

            if not result:
                conn.close()
                return None

            conn.commit()
            cursor.close()
            conn.close()

            return dict(result)
        except Exception as e:
            logger.error(f"Error updating task status: {str(e)}")
            return None