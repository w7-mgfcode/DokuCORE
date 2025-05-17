import os
import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class DeveloperProfile:
    """Profile for tracking developer expertise and availability"""
    username: str
    email: Optional[str] = None
    expertise_areas: Dict[str, float] = field(default_factory=dict)  # skill -> proficiency (0-1)
    languages: Dict[str, float] = field(default_factory=dict)  # language -> proficiency (0-1)
    completed_tasks: int = 0
    average_task_time: float = 0.0  # in hours
    current_workload: int = 0  # number of active tasks
    availability: str = "available"  # available, busy, unavailable
    preferred_files: List[str] = field(default_factory=list)
    review_history: Dict[str, int] = field(default_factory=dict)  # file -> review count
    last_active: Optional[datetime] = None
    quality_score: float = 0.8  # 0-1, based on past task completions

@dataclass
class TaskAssignment:
    """Task assignment recommendation"""
    developer: str
    confidence_score: float  # 0-100
    assignment_reasons: List[str]
    estimated_time: float  # hours
    backup_developers: List[str] = field(default_factory=list)
    
class TaskAssigner:
    """Intelligent task assignment based on developer expertise"""
    
    def __init__(self, profiles_file: str = "developer_profiles.json"):
        self.profiles_file = profiles_file
        self.developer_profiles: Dict[str, DeveloperProfile] = {}
        self.load_profiles()
        
        # Expertise areas mapping
        self.EXPERTISE_CATEGORIES = {
            'api': ['rest', 'graphql', 'websocket', 'endpoint', 'swagger'],
            'frontend': ['react', 'vue', 'angular', 'css', 'html', 'ui', 'ux'],
            'backend': ['server', 'database', 'microservice', 'queue', 'cache'],
            'security': ['auth', 'encryption', 'oauth', 'jwt', 'security'],
            'database': ['sql', 'nosql', 'migration', 'schema', 'query'],
            'infrastructure': ['docker', 'kubernetes', 'ci', 'cd', 'deployment'],
            'testing': ['test', 'unit', 'integration', 'e2e', 'coverage']
        }
    
    def load_profiles(self):
        """Load developer profiles from JSON file"""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, 'r') as f:
                    profiles_data = json.load(f)
                    
                for username, profile_data in profiles_data.items():
                    # Convert last_active string to datetime if present
                    if 'last_active' in profile_data and profile_data['last_active']:
                        profile_data['last_active'] = datetime.fromisoformat(profile_data['last_active'])
                    
                    self.developer_profiles[username] = DeveloperProfile(**profile_data)
                
                logger.info(f"Loaded {len(self.developer_profiles)} developer profiles")
            else:
                self.create_sample_profiles()
        except Exception as e:
            logger.error(f"Error loading profiles: {e}")
            self.create_sample_profiles()
    
    def save_profiles(self):
        """Save developer profiles to JSON file"""
        try:
            profiles_data = {}
            
            for username, profile in self.developer_profiles.items():
                profile_dict = {
                    'username': profile.username,
                    'email': profile.email,
                    'expertise_areas': profile.expertise_areas,
                    'languages': profile.languages,
                    'completed_tasks': profile.completed_tasks,
                    'average_task_time': profile.average_task_time,
                    'current_workload': profile.current_workload,
                    'availability': profile.availability,
                    'preferred_files': profile.preferred_files,
                    'review_history': profile.review_history,
                    'last_active': profile.last_active.isoformat() if profile.last_active else None,
                    'quality_score': profile.quality_score
                }
                profiles_data[username] = profile_dict
            
            with open(self.profiles_file, 'w') as f:
                json.dump(profiles_data, f, indent=2)
                
            logger.info("Saved developer profiles")
        except Exception as e:
            logger.error(f"Error saving profiles: {e}")
    
    def create_sample_profiles(self):
        """Create sample developer profiles for demonstration"""
        self.developer_profiles = {
            'alice': DeveloperProfile(
                username='alice',
                email='alice@example.com',
                expertise_areas={'api': 0.9, 'backend': 0.8, 'database': 0.7},
                languages={'python': 0.9, 'javascript': 0.6, 'go': 0.4},
                completed_tasks=47,
                average_task_time=3.5,
                current_workload=2,
                availability='available',
                quality_score=0.92
            ),
            'bob': DeveloperProfile(
                username='bob',
                email='bob@example.com',
                expertise_areas={'frontend': 0.9, 'ui': 0.8, 'testing': 0.6},
                languages={'javascript': 0.9, 'typescript': 0.8, 'python': 0.5},
                completed_tasks=34,
                average_task_time=4.0,
                current_workload=3,
                availability='busy',
                quality_score=0.88
            ),
            'charlie': DeveloperProfile(
                username='charlie',
                email='charlie@example.com',
                expertise_areas={'infrastructure': 0.8, 'security': 0.7, 'backend': 0.6},
                languages={'go': 0.8, 'python': 0.7, 'bash': 0.9},
                completed_tasks=28,
                average_task_time=5.0,
                current_workload=1,
                availability='available',
                quality_score=0.85
            )
        }
        self.save_profiles()
    
    def update_developer_profile(self, username: str, task_info: Dict):
        """Update developer profile based on completed task"""
        if username not in self.developer_profiles:
            return
        
        profile = self.developer_profiles[username]
        
        # Update completed tasks count
        profile.completed_tasks += 1
        
        # Update average task time
        if 'completion_time' in task_info:
            profile.average_task_time = (
                (profile.average_task_time * (profile.completed_tasks - 1) + 
                 task_info['completion_time']) / profile.completed_tasks
            )
        
        # Update expertise based on task
        if 'file_path' in task_info:
            file_path = task_info['file_path']
            
            # Update language expertise
            ext = Path(file_path).suffix.lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.go': 'go',
                '.java': 'java',
                '.cs': 'csharp'
            }
            
            if ext in language_map:
                lang = language_map[ext]
                current_proficiency = profile.languages.get(lang, 0.5)
                # Increase proficiency slightly
                profile.languages[lang] = min(1.0, current_proficiency + 0.02)
            
            # Update expertise areas
            for area, keywords in self.EXPERTISE_CATEGORIES.items():
                if any(keyword in file_path.lower() for keyword in keywords):
                    current_expertise = profile.expertise_areas.get(area, 0.5)
                    profile.expertise_areas[area] = min(1.0, current_expertise + 0.03)
            
            # Update review history
            profile.review_history[file_path] = profile.review_history.get(file_path, 0) + 1
        
        # Update last active time
        profile.last_active = datetime.now()
        
        # Save updated profiles
        self.save_profiles()
    
    def calculate_assignment_score(self, developer: DeveloperProfile, 
                                 change_context, priority) -> Tuple[float, List[str]]:
        """Calculate assignment score for a developer"""
        score = 0.0
        reasons = []
        
        # Availability check
        if developer.availability == 'unavailable':
            return 0.0, ["Developer is unavailable"]
        
        availability_multiplier = 1.0 if developer.availability == 'available' else 0.7
        
        # Language expertise
        if hasattr(change_context, 'language'):
            lang_proficiency = developer.languages.get(change_context.language, 0.3)
            language_score = lang_proficiency * 30
            score += language_score
            
            if lang_proficiency > 0.7:
                reasons.append(f"Strong {change_context.language} expertise ({lang_proficiency:.1%})")
        
        # File expertise (has worked on this file before)
        if hasattr(change_context, 'file_path'):
            file_path = change_context.file_path
            
            # Direct file experience
            if file_path in developer.review_history:
                review_count = developer.review_history[file_path]
                file_score = min(20, review_count * 5)
                score += file_score
                reasons.append(f"Has reviewed this file {review_count} times")
            
            # Expertise area matching
            for area, keywords in self.EXPERTISE_CATEGORIES.items():
                if any(keyword in file_path.lower() for keyword in keywords):
                    if area in developer.expertise_areas:
                        area_score = developer.expertise_areas[area] * 15
                        score += area_score
                        if developer.expertise_areas[area] > 0.7:
                            reasons.append(f"Expert in {area} ({developer.expertise_areas[area]:.1%})")
        
        # Workload consideration
        workload_penalty = min(developer.current_workload * 5, 20)
        score -= workload_penalty
        if developer.current_workload > 3:
            reasons.append(f"High current workload ({developer.current_workload} tasks)")
        
        # Quality score bonus
        quality_bonus = developer.quality_score * 10
        score += quality_bonus
        if developer.quality_score > 0.9:
            reasons.append(f"Excellent quality track record ({developer.quality_score:.1%})")
        
        # Priority boost for critical tasks
        if hasattr(priority, 'level') and priority.level.value in ['critical', 'high']:
            if developer.quality_score > 0.85:
                score += 10
                reasons.append("Trusted for high-priority tasks")
        
        # Apply availability multiplier
        score *= availability_multiplier
        
        return max(0, min(100, score)), reasons
    
    def recommend_assignment(self, change_context, priority, 
                           team_size: int = 3) -> TaskAssignment:
        """Recommend best developer for a task"""
        scores = []
        
        # Calculate scores for all developers
        for username, developer in self.developer_profiles.items():
            score, reasons = self.calculate_assignment_score(developer, change_context, priority)
            scores.append((username, score, reasons))
        
        # Sort by score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top developer
        if not scores or scores[0][1] == 0:
            return TaskAssignment(
                developer="unassigned",
                confidence_score=0.0,
                assignment_reasons=["No suitable developer available"],
                estimated_time=8.0
            )
        
        top_developer = scores[0][0]
        top_score = scores[0][1]
        top_reasons = scores[0][2]
        
        # Get backup developers
        backup_developers = [s[0] for s in scores[1:4] if s[1] > 50]
        
        # Estimate time based on developer's average and task complexity
        estimated_time = self.estimate_task_time(
            self.developer_profiles[top_developer],
            change_context,
            priority
        )
        
        return TaskAssignment(
            developer=top_developer,
            confidence_score=top_score,
            assignment_reasons=top_reasons,
            estimated_time=estimated_time,
            backup_developers=backup_developers
        )
    
    def estimate_task_time(self, developer: DeveloperProfile, 
                          change_context, priority) -> float:
        """Estimate time required for task completion"""
        base_time = developer.average_task_time
        
        # Adjust based on complexity
        if hasattr(change_context, 'complexity_score'):
            complexity_factor = 1 + (change_context.complexity_score / 10)
            base_time *= complexity_factor
        
        # Adjust based on developer's expertise
        if hasattr(change_context, 'language'):
            lang_proficiency = developer.languages.get(change_context.language, 0.5)
            expertise_factor = 2 - lang_proficiency  # Less time if more proficient
            base_time *= expertise_factor
        
        # Priority adjustment (urgent tasks might take longer due to pressure)
        if hasattr(priority, 'level') and priority.level.value == 'critical':
            base_time *= 1.2
        
        return round(base_time, 1)
    
    def get_team_capacity(self) -> Dict[str, any]:
        """Get current team capacity and availability"""
        capacity = {
            'total_developers': len(self.developer_profiles),
            'available': 0,
            'busy': 0,
            'unavailable': 0,
            'total_workload': 0,
            'average_workload': 0.0,
            'expertise_coverage': {}
        }
        
        workloads = []
        
        for developer in self.developer_profiles.values():
            capacity[developer.availability] += 1
            capacity['total_workload'] += developer.current_workload
            workloads.append(developer.current_workload)
            
            # Track expertise coverage
            for area, level in developer.expertise_areas.items():
                if area not in capacity['expertise_coverage']:
                    capacity['expertise_coverage'][area] = []
                if level > 0.6:  # Only count decent expertise
                    capacity['expertise_coverage'][area].append(developer.username)
        
        capacity['average_workload'] = (
            sum(workloads) / len(workloads) if workloads else 0.0
        )
        
        return capacity
    
    def suggest_team_expansion(self, recent_tasks: List[Dict]) -> List[str]:
        """Suggest areas where team expansion might be needed"""
        suggestions = []
        
        # Analyze recent tasks for patterns
        language_demand = {}
        expertise_demand = {}
        
        for task in recent_tasks:
            # Track language demand
            if 'language' in task:
                language_demand[task['language']] = language_demand.get(task['language'], 0) + 1
            
            # Track expertise demand
            if 'file_path' in task:
                for area, keywords in self.EXPERTISE_CATEGORIES.items():
                    if any(keyword in task['file_path'].lower() for keyword in keywords):
                        expertise_demand[area] = expertise_demand.get(area, 0) + 1
        
        # Check for understaffed areas
        team_capacity = self.get_team_capacity()
        
        for area, demand in expertise_demand.items():
            coverage = len(team_capacity['expertise_coverage'].get(area, []))
            if demand > 5 and coverage < 2:
                suggestions.append(f"Consider hiring {area} specialist (high demand, low coverage)")
        
        for language, demand in language_demand.items():
            lang_experts = sum(1 for dev in self.developer_profiles.values() 
                             if dev.languages.get(language, 0) > 0.7)
            if demand > 10 and lang_experts < 2:
                suggestions.append(f"Consider hiring {language} developer (high demand, few experts)")
        
        # Check overall workload
        if team_capacity['average_workload'] > 4:
            suggestions.append("Consider expanding team size (high average workload)")
        
        return suggestions