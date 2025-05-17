import os
import logging
import json
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from queue import Queue
import git
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class RepositoryConfig:
    """Configuration for individual repository monitoring"""
    name: str
    path: str
    url: Optional[str] = None
    branch: str = "main"
    enabled: bool = True
    check_interval: int = 300  # seconds
    last_check: Optional[datetime] = None
    file_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    priority_boost: float = 1.0  # Multiplier for task priority
    custom_settings: Dict[str, any] = field(default_factory=dict)

class MultiRepositoryMonitor:
    """Monitor multiple Git repositories concurrently"""
    
    def __init__(self, config_file: str = "repos_config.json"):
        self.config_file = config_file
        self.repositories: Dict[str, RepositoryConfig] = {}
        self.task_queue = Queue()
        self.monitoring_threads: Dict[str, threading.Thread] = {}
        self.stop_flag = threading.Event()
        
        # Load repository configurations
        self.load_configurations()
        
    def load_configurations(self):
        """Load repository configurations from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    
                for repo_config in config_data.get('repositories', []):
                    repo = RepositoryConfig(**repo_config)
                    self.repositories[repo.name] = repo
                    
                logger.info(f"Loaded {len(self.repositories)} repository configurations")
            else:
                # Create default configuration
                self.create_default_config()
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            "repositories": [
                {
                    "name": "main-repo",
                    "path": "/app/repo",
                    "branch": "main",
                    "enabled": True,
                    "check_interval": 300,
                    "file_patterns": ["*.py", "*.js", "*.go", "*.java"],
                    "exclude_patterns": ["test_*", "*_test.*", "*.min.js"],
                    "priority_boost": 1.0
                }
            ]
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default configuration file: {self.config_file}")
            
            # Load the default config
            self.load_configurations()
        except Exception as e:
            logger.error(f"Error creating default config: {e}")
    
    def add_repository(self, repo_config: RepositoryConfig):
        """Add a new repository to monitor"""
        self.repositories[repo_config.name] = repo_config
        self.save_configurations()
        
        # Start monitoring if enabled
        if repo_config.enabled:
            self.start_monitoring_repository(repo_config.name)
    
    def remove_repository(self, repo_name: str):
        """Remove a repository from monitoring"""
        if repo_name in self.repositories:
            # Stop monitoring thread if running
            if repo_name in self.monitoring_threads:
                # Signal thread to stop (handled in monitor_repository)
                del self.monitoring_threads[repo_name]
            
            del self.repositories[repo_name]
            self.save_configurations()
    
    def save_configurations(self):
        """Save current repository configurations to JSON file"""
        try:
            config_data = {
                "repositories": [
                    {
                        "name": repo.name,
                        "path": repo.path,
                        "url": repo.url,
                        "branch": repo.branch,
                        "enabled": repo.enabled,
                        "check_interval": repo.check_interval,
                        "file_patterns": repo.file_patterns,
                        "exclude_patterns": repo.exclude_patterns,
                        "priority_boost": repo.priority_boost,
                        "custom_settings": repo.custom_settings
                    }
                    for repo in self.repositories.values()
                ]
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            logger.info("Saved repository configurations")
        except Exception as e:
            logger.error(f"Error saving configurations: {e}")
    
    def clone_repository(self, repo_config: RepositoryConfig) -> bool:
        """Clone a repository if it doesn't exist locally"""
        if not os.path.exists(repo_config.path):
            if repo_config.url:
                try:
                    logger.info(f"Cloning repository {repo_config.name} from {repo_config.url}")
                    git.Repo.clone_from(
                        repo_config.url, 
                        repo_config.path,
                        branch=repo_config.branch
                    )
                    return True
                except Exception as e:
                    logger.error(f"Error cloning repository {repo_config.name}: {e}")
                    return False
            else:
                logger.error(f"Repository {repo_config.name} doesn't exist and no URL provided")
                return False
        return True
    
    def validate_repository(self, repo_config: RepositoryConfig) -> bool:
        """Validate that a repository exists and is accessible"""
        try:
            # Check if path exists
            if not os.path.exists(repo_config.path):
                # Try to clone if URL is provided
                if not self.clone_repository(repo_config):
                    return False
            
            # Check if it's a valid git repository
            repo = git.Repo(repo_config.path)
            
            # Check if the specified branch exists
            if repo_config.branch not in [ref.name for ref in repo.references]:
                logger.warning(f"Branch {repo_config.branch} not found in {repo_config.name}")
                # Try to checkout default branch
                repo_config.branch = repo.active_branch.name
                self.save_configurations()
            
            return True
        except git.InvalidGitRepositoryError:
            logger.error(f"Invalid git repository: {repo_config.path}")
            return False
        except Exception as e:
            logger.error(f"Error validating repository {repo_config.name}: {e}")
            return False
    
    def monitor_repository(self, repo_name: str):
        """Monitor a single repository in a thread"""
        repo_config = self.repositories.get(repo_name)
        if not repo_config:
            logger.error(f"Repository {repo_name} not found")
            return
        
        # Validate repository
        if not self.validate_repository(repo_config):
            logger.error(f"Repository validation failed for {repo_name}")
            return
        
        logger.info(f"Starting monitoring for repository: {repo_name}")
        
        try:
            repo = git.Repo(repo_config.path)
            
            while not self.stop_flag.is_set() and repo_name in self.monitoring_threads:
                try:
                    # Update repository
                    origin = repo.remotes.origin
                    origin.pull(repo_config.branch)
                    
                    # Check for changes since last check
                    if repo_config.last_check:
                        changes = self.detect_changes(repo, repo_config)
                        
                        if changes:
                            # Add changes to task queue with repository info
                            self.task_queue.put({
                                'repository': repo_name,
                                'changes': changes,
                                'priority_boost': repo_config.priority_boost,
                                'timestamp': datetime.now()
                            })
                    
                    # Update last check time
                    repo_config.last_check = datetime.now()
                    
                except git.GitCommandError as e:
                    logger.error(f"Git error in {repo_name}: {e}")
                except Exception as e:
                    logger.error(f"Error monitoring {repo_name}: {e}")
                
                # Wait for next check interval
                self.stop_flag.wait(repo_config.check_interval)
                
        except Exception as e:
            logger.error(f"Fatal error monitoring {repo_name}: {e}")
        finally:
            logger.info(f"Stopped monitoring repository: {repo_name}")
    
    def detect_changes(self, repo: git.Repo, repo_config: RepositoryConfig) -> List[Dict]:
        """Detect changes in repository since last check"""
        changes = []
        
        try:
            # Get commits since last check
            since_time = repo_config.last_check.strftime("%Y-%m-%d %H:%M:%S")
            
            for commit in repo.iter_commits(repo_config.branch, since=since_time):
                # Analyze each changed file
                for diff in commit.diff(commit.parents[0] if commit.parents else None):
                    file_path = diff.b_path or diff.a_path
                    
                    # Check if file matches patterns
                    if self.should_monitor_file(file_path, repo_config):
                        changes.append({
                            'commit': commit.hexsha,
                            'file_path': file_path,
                            'change_type': diff.change_type,
                            'author': commit.author.name,
                            'message': commit.message,
                            'timestamp': datetime.fromtimestamp(commit.committed_date)
                        })
        except Exception as e:
            logger.error(f"Error detecting changes in {repo_config.name}: {e}")
        
        return changes
    
    def should_monitor_file(self, file_path: str, repo_config: RepositoryConfig) -> bool:
        """Check if a file should be monitored based on patterns"""
        path = Path(file_path)
        
        # Check exclude patterns first
        for pattern in repo_config.exclude_patterns:
            if path.match(pattern):
                return False
        
        # Check include patterns
        if repo_config.file_patterns:
            for pattern in repo_config.file_patterns:
                if path.match(pattern):
                    return True
            return False  # If patterns specified, must match one
        
        # Default to monitoring all code files
        return path.suffix in ['.py', '.js', '.go', '.java', '.cs', '.ts', '.jsx', '.tsx']
    
    def start_monitoring_repository(self, repo_name: str):
        """Start monitoring a specific repository"""
        if repo_name in self.monitoring_threads:
            logger.warning(f"Repository {repo_name} is already being monitored")
            return
        
        repo_config = self.repositories.get(repo_name)
        if not repo_config or not repo_config.enabled:
            logger.warning(f"Repository {repo_name} is not enabled or doesn't exist")
            return
        
        # Create and start monitoring thread
        thread = threading.Thread(
            target=self.monitor_repository,
            args=(repo_name,),
            name=f"monitor-{repo_name}"
        )
        thread.daemon = True
        thread.start()
        
        self.monitoring_threads[repo_name] = thread
    
    def start_all_monitoring(self):
        """Start monitoring all enabled repositories"""
        for repo_name, repo_config in self.repositories.items():
            if repo_config.enabled:
                self.start_monitoring_repository(repo_name)
        
        logger.info(f"Started monitoring {len(self.monitoring_threads)} repositories")
    
    def stop_all_monitoring(self):
        """Stop monitoring all repositories"""
        logger.info("Stopping all repository monitoring...")
        self.stop_flag.set()
        
        # Wait for all threads to finish
        for thread in self.monitoring_threads.values():
            thread.join(timeout=5)
        
        self.monitoring_threads.clear()
        logger.info("All repository monitoring stopped")
    
    def get_monitoring_status(self) -> Dict[str, Dict]:
        """Get status of all repositories"""
        status = {}
        
        for repo_name, repo_config in self.repositories.items():
            status[repo_name] = {
                'enabled': repo_config.enabled,
                'last_check': repo_config.last_check.isoformat() if repo_config.last_check else None,
                'monitoring': repo_name in self.monitoring_threads,
                'path': repo_config.path,
                'branch': repo_config.branch,
                'check_interval': repo_config.check_interval
            }
        
        return status
    
    def process_tasks(self):
        """Process tasks from the queue (to be called by main application)"""
        processed_tasks = []
        
        while not self.task_queue.empty():
            try:
                task_data = self.task_queue.get_nowait()
                processed_tasks.append(task_data)
            except:
                break
        
        return processed_tasks