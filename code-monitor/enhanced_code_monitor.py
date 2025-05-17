import os
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv

# Import our enhanced modules
from enhanced_change_detector import EnhancedChangeDetector, ChangeContext
from task_prioritizer import TaskPrioritizer, PriorityLevel
from multi_repo_monitor import MultiRepositoryMonitor, RepositoryConfig
from change_summary_generator import ChangeSummaryGenerator
from task_assigner import TaskAssigner

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedCodeMonitor:
    """Enhanced code monitoring system with all advanced features"""
    
    def __init__(self):
        # Configuration
        self.api_url = os.environ.get("API_URL", "http://api:9000")
        self.check_interval = int(os.environ.get("CHECK_INTERVAL", 300))
        
        # Initialize components
        self.multi_repo_monitor = MultiRepositoryMonitor()
        self.task_prioritizer = TaskPrioritizer()
        self.summary_generator = ChangeSummaryGenerator()
        self.task_assigner = TaskAssigner()
        
        # Webhook support
        self.webhook_enabled = os.environ.get("WEBHOOK_ENABLED", "false").lower() == "true"
        self.webhook_url = os.environ.get("WEBHOOK_URL")
        
        # Statistics tracking
        self.stats = {
            'tasks_created': 0,
            'repositories_monitored': 0,
            'changes_detected': 0,
            'start_time': datetime.now()
        }
    
    def create_documentation_task(self, change_context: ChangeContext, 
                                repo_name: str, priority) -> Dict:
        """Create documentation task from change context"""
        
        # Generate comprehensive summary
        summary = self.summary_generator.generate_summary([change_context], repo_name)
        
        # Get task assignment recommendation
        assignment = self.task_assigner.recommend_assignment(change_context, priority)
        
        # Create task
        task = {
            'title': f"Documentation update for {change_context.file_path}",
            'description': summary.executive_summary,
            'detailed_changes': summary.detailed_changes,
            'impact_analysis': summary.impact_analysis,
            'documentation_suggestions': summary.documentation_suggestions,
            'code_path': change_context.file_path,
            'repository': repo_name,
            'priority': priority.level.value,
            'priority_score': priority.score,
            'priority_reasoning': priority.reasoning,
            'assigned_to': assignment.developer,
            'assignment_confidence': assignment.confidence_score,
            'assignment_reasons': assignment.assignment_reasons,
            'estimated_hours': assignment.estimated_time,
            'backup_assignees': assignment.backup_developers,
            'complexity_score': change_context.complexity_score,
            'documentation_impact': change_context.documentation_impact,
            'change_type': change_context.change_type,
            'language': change_context.language,
            'functions_changed': change_context.functions_changed,
            'classes_changed': change_context.classes_changed,
            'migration_notes': summary.migration_notes,
            'related_files': summary.related_files
        }
        
        return task
    
    def process_repository_changes(self, repo_name: str, changes: List[Dict]) -> List[Dict]:
        """Process changes from a repository and create tasks"""
        tasks_created = []
        
        # Get enhanced change detector for the repository
        repo_config = self.multi_repo_monitor.repositories.get(repo_name)
        if not repo_config:
            logger.error(f"Repository config not found for {repo_name}")
            return tasks_created
        
        detector = EnhancedChangeDetector(repo_config.path)
        
        # Analyze changes
        change_contexts = []
        for change in changes:
            # Create simple change context from change data
            context = ChangeContext(
                file_path=change['file_path'],
                change_type=change['change_type'],
                language=detector.detect_language(change['file_path']),
                functions_changed=[],  # Would be populated by actual diff analysis
                classes_changed=[],
                imports_changed=[],
                lines_added=0,
                lines_deleted=0,
                complexity_score=5.0,  # Default score
                documentation_impact=5.0
            )
            change_contexts.append(context)
        
        # Get existing documentation mapping
        existing_docs = self.get_existing_documentation_mapping()
        
        # Prioritize all changes
        prioritized_changes = self.task_prioritizer.batch_prioritize(
            change_contexts, 
            existing_docs
        )
        
        # Create tasks for high-priority changes
        for change_context, priority in prioritized_changes:
            if priority.level in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
                task = self.create_documentation_task(
                    change_context,
                    repo_name,
                    priority
                )
                
                # Submit task to API
                if self.submit_task_to_api(task):
                    tasks_created.append(task)
                    self.stats['tasks_created'] += 1
        
        return tasks_created
    
    def get_existing_documentation_mapping(self) -> Dict[str, int]:
        """Get mapping of file paths to existing documentation IDs"""
        mapping = {}
        
        try:
            response = requests.get(f"{self.api_url}/documents/")
            if response.status_code == 200:
                documents = response.json()
                for doc in documents:
                    # Simple mapping based on path matching
                    if 'path' in doc:
                        file_name = os.path.basename(doc['path'])
                        mapping[file_name] = doc['id']
        except Exception as e:
            logger.error(f"Error fetching documentation mapping: {e}")
        
        return mapping
    
    def submit_task_to_api(self, task: Dict) -> bool:
        """Submit task to the API"""
        try:
            # Prepare task for API (remove some internal fields)
            api_task = {
                'title': task['title'],
                'description': task['description'],
                'code_path': task['code_path'],
                'priority': task['priority'],
                'assigned_to': task.get('assigned_to'),
                'metadata': json.dumps({
                    'repository': task['repository'],
                    'priority_score': task['priority_score'],
                    'complexity_score': task['complexity_score'],
                    'estimated_hours': task['estimated_hours'],
                    'change_type': task['change_type'],
                    'language': task['language']
                })
            }
            
            response = requests.post(f"{self.api_url}/tasks/", json=api_task)
            
            if response.status_code == 200:
                logger.info(f"Task created successfully: {task['title']}")
                
                # Send webhook notification if enabled
                if self.webhook_enabled and self.webhook_url:
                    self.send_webhook_notification(task, response.json())
                
                return True
            else:
                logger.error(f"Error creating task: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error submitting task: {e}")
            return False
    
    def send_webhook_notification(self, task: Dict, api_response: Dict):
        """Send webhook notification about new task"""
        try:
            webhook_data = {
                'event': 'task_created',
                'task_id': api_response.get('task_id'),
                'title': task['title'],
                'repository': task['repository'],
                'priority': task['priority'],
                'assigned_to': task['assigned_to'],
                'file_path': task['code_path'],
                'timestamp': datetime.now().isoformat()
            }
            
            requests.post(self.webhook_url, json=webhook_data, timeout=5)
            logger.info(f"Webhook notification sent for task: {task['title']}")
            
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
    
    def generate_monitoring_report(self) -> Dict:
        """Generate comprehensive monitoring report"""
        uptime = datetime.now() - self.stats['start_time']
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'uptime': str(uptime),
            'statistics': self.stats,
            'repository_status': self.multi_repo_monitor.get_monitoring_status(),
            'team_capacity': self.task_assigner.get_team_capacity(),
            'recent_task_summary': {
                'total_created': self.stats['tasks_created'],
                'by_priority': {
                    'critical': 0,
                    'high': 0,
                    'medium': 0,
                    'low': 0
                }
            }
        }
        
        # Add team expansion suggestions if we have task history
        if self.stats['tasks_created'] > 20:
            # This would need actual task history
            report['team_suggestions'] = self.task_assigner.suggest_team_expansion([])
        
        return report
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Enhanced Code Monitor started")
        logger.info(f"Monitoring {len(self.multi_repo_monitor.repositories)} repositories")
        
        # Start monitoring all repositories
        self.multi_repo_monitor.start_all_monitoring()
        self.stats['repositories_monitored'] = len(self.multi_repo_monitor.repositories)
        
        try:
            while True:
                # Process tasks from all repositories
                tasks_data = self.multi_repo_monitor.process_tasks()
                
                for task_data in tasks_data:
                    repo_name = task_data['repository']
                    changes = task_data['changes']
                    
                    if changes:
                        logger.info(f"Processing {len(changes)} changes from {repo_name}")
                        self.stats['changes_detected'] += len(changes)
                        
                        # Create documentation tasks
                        tasks_created = self.process_repository_changes(repo_name, changes)
                        
                        logger.info(f"Created {len(tasks_created)} tasks for {repo_name}")
                
                # Generate and log report periodically
                if self.stats['tasks_created'] % 10 == 0 and self.stats['tasks_created'] > 0:
                    report = self.generate_monitoring_report()
                    logger.info(f"Monitoring Report: {json.dumps(report, indent=2)}")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Shutting down Enhanced Code Monitor")
            self.multi_repo_monitor.stop_all_monitoring()
        except Exception as e:
            logger.error(f"Fatal error in monitoring loop: {e}")
            self.multi_repo_monitor.stop_all_monitoring()
            raise
        
        # Final report
        final_report = self.generate_monitoring_report()
        logger.info(f"Final Report: {json.dumps(final_report, indent=2)}")

if __name__ == "__main__":
    monitor = EnhancedCodeMonitor()
    monitor.run()