import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class PriorityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class TaskPriority:
    score: float
    level: PriorityLevel
    factors: Dict[str, float]
    reasoning: str
    
class TaskPrioritizer:
    """Intelligent task prioritization based on various factors"""
    
    # Critical file patterns (highest importance)
    CRITICAL_PATTERNS = [
        'api/', 'public/', 'interface/', 'endpoint/', 'auth/', 'security/'
    ]
    
    # Important file patterns
    IMPORTANT_PATTERNS = [
        'service/', 'model/', 'core/', 'utils/', 'config/', 'database/'
    ]
    
    # File importance scores
    FILE_IMPORTANCE = {
        'production': 10.0,
        'staging': 8.0,
        'development': 5.0,
        'test': 3.0,
        'docs': 2.0,
    }
    
    # Keywords that indicate critical changes
    CRITICAL_KEYWORDS = [
        'security', 'auth', 'password', 'token', 'key', 'secret',
        'vulnerability', 'exploit', 'injection', 'xss', 'csrf'
    ]
    
    # Breaking change indicators
    BREAKING_CHANGE_PATTERNS = [
        'remove', 'delete', 'deprecate', 'break', 'incompatible',
        'major', 'v2', 'v3', 'refactor', 'rewrite'
    ]
    
    def __init__(self):
        self.file_criticality_cache = {}
    
    def calculate_file_importance(self, file_path: str) -> float:
        """Calculate importance score based on file path and patterns"""
        
        # Check cache
        if file_path in self.file_criticality_cache:
            return self.file_criticality_cache[file_path]
        
        score = 5.0  # Base score
        
        # Check for critical patterns
        for pattern in self.CRITICAL_PATTERNS:
            if pattern in file_path.lower():
                score = 10.0
                break
        
        # Check for important patterns
        if score < 10.0:
            for pattern in self.IMPORTANT_PATTERNS:
                if pattern in file_path.lower():
                    score = 8.0
                    break
        
        # Check file extension
        if file_path.endswith(('.py', '.java', '.go', '.cs')):
            score *= 1.2  # Backend code is often more critical
        elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
            score *= 1.1  # Frontend code
        elif file_path.endswith(('.yaml', '.yml', '.json', '.toml')):
            score *= 1.3  # Configuration files can be very critical
        elif file_path.endswith(('.md', '.txt', '.rst')):
            score *= 0.5  # Documentation is less critical
        
        # Cache the result
        self.file_criticality_cache[file_path] = score
        return score
    
    def check_critical_keywords(self, change_context) -> bool:
        """Check if change contains critical security-related keywords"""
        text_to_check = " ".join([
            change_context.file_path,
            " ".join(change_context.functions_changed),
            " ".join(change_context.classes_changed),
        ]).lower()
        
        for keyword in self.CRITICAL_KEYWORDS:
            if keyword in text_to_check:
                return True
        return False
    
    def check_breaking_changes(self, change_context) -> bool:
        """Check if change might be a breaking change"""
        # Check if functions or classes were removed
        if change_context.change_type == 'removed':
            return True
        
        # Check function/class names for breaking change patterns
        all_names = (change_context.functions_changed + 
                    change_context.classes_changed)
        
        for name in all_names:
            for pattern in self.BREAKING_CHANGE_PATTERNS:
                if pattern in name.lower():
                    return True
        
        return False
    
    def calculate_coverage_gap(self, change_context, existing_doc_id: Optional[int]) -> float:
        """Calculate documentation coverage gap score"""
        # If no documentation exists, higher gap
        if not existing_doc_id:
            return 1.0
        
        # If documentation exists but changes are significant
        if change_context.documentation_impact > 5.0:
            return 0.7
        
        # Minor changes with existing documentation
        return 0.3
    
    def _calculate_priority(self, change_context, existing_doc_id: Optional[int]) -> TaskPriority:
        """Calculate priority score using multiple factors"""
        factors = {}
        
        # Factor 1: File importance (0-10 scale, normalized to 0-25)
        file_importance = self.calculate_file_importance(change_context.file_path)
        factors['file_importance'] = file_importance * 2.5
        
        # Factor 2: Change complexity (0-10 scale, normalized to 0-20)
        factors['complexity'] = change_context.complexity_score * 2.0
        
        # Factor 3: Documentation impact (0-10 scale, normalized to 0-20)
        factors['doc_impact'] = change_context.documentation_impact * 2.0
        
        # Factor 4: Critical keywords (boolean, 0 or 15)
        has_critical_keywords = self.check_critical_keywords(change_context)
        factors['critical_keywords'] = 15.0 if has_critical_keywords else 0.0
        
        # Factor 5: Breaking changes (boolean, 0 or 10)
        is_breaking = self.check_breaking_changes(change_context)
        factors['breaking_change'] = 10.0 if is_breaking else 0.0
        
        # Factor 6: Documentation coverage gap (0-1 scale, normalized to 0-10)
        coverage_gap = self.calculate_coverage_gap(change_context, existing_doc_id)
        factors['coverage_gap'] = coverage_gap * 10.0
        
        # Calculate total score (max 100)
        total_score = sum(factors.values())
        
        # Determine priority level
        if total_score >= 75:
            level = PriorityLevel.CRITICAL
        elif total_score >= 50:
            level = PriorityLevel.HIGH
        elif total_score >= 25:
            level = PriorityLevel.MEDIUM
        else:
            level = PriorityLevel.LOW
        
        # Generate reasoning
        reasoning_parts = []
        if factors['file_importance'] >= 20:
            reasoning_parts.append(f"Critical file path: {change_context.file_path}")
        if factors['critical_keywords'] > 0:
            reasoning_parts.append("Contains security-related keywords")
        if factors['breaking_change'] > 0:
            reasoning_parts.append("Potential breaking change detected")
        if factors['doc_impact'] >= 15:
            reasoning_parts.append("High documentation impact")
        if factors['coverage_gap'] >= 8:
            reasoning_parts.append("No existing documentation")
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Standard priority task"
        
        return TaskPriority(
            score=total_score,
            level=level,
            factors=factors,
            reasoning=reasoning
        )
    
    def prioritize_task(self, change_context, existing_doc_id: Optional[int] = None) -> TaskPriority:
        """Calculate priority for a documentation task based on change context"""
        try:
            return self._calculate_priority(change_context, existing_doc_id)
        except Exception as e:
            logger.error(f"Error calculating priority: {e}")
            # Return default medium priority on error
            return TaskPriority(
                score=50.0,
                level=PriorityLevel.MEDIUM,
                factors={"error": 50.0},
                reasoning="Error calculating priority - defaulting to medium"
            )
    
    def batch_prioritize(self, change_contexts: List, 
                        existing_docs: Optional[Dict[str, int]] = None) -> List[Tuple[object, TaskPriority]]:
        """Prioritize multiple tasks and return sorted by priority"""
        prioritized_tasks = []
        existing_docs = existing_docs or {}
        
        for context in change_contexts:
            doc_id = existing_docs.get(context.file_path)
            priority = self.prioritize_task(context, doc_id)
            prioritized_tasks.append((context, priority))
        
        # Sort by priority score (descending)
        prioritized_tasks.sort(key=lambda x: x[1].score, reverse=True)
        
        return prioritized_tasks