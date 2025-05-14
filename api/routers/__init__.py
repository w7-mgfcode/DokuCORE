from .document_router import router as document_router
from .task_router import router as task_router
from .search_router import router as search_router
from .auth_router import router as auth_router
from .version_router import router as version_router
from .document_router import DocumentRouter
from .task_router import TaskRouter
from .search_router import SearchRouter
from .version_router import VersionRouter

__all__ = [
    'document_router',
    'task_router',
    'search_router',
    'auth_router',
    'version_router',
    'DocumentRouter',
    'TaskRouter', 
    'SearchRouter',
    'VersionRouter'
]