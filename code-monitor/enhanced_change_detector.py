import os
import git
import logging
import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ChangeContext:
    """Detailed context about a code change"""
    file_path: str
    change_type: str  # 'added', 'modified', 'removed'
    language: str
    functions_changed: List[str]
    classes_changed: List[str]
    imports_changed: List[str]
    lines_added: int
    lines_deleted: int
    complexity_score: float
    documentation_impact: float
    
class EnhancedChangeDetector:
    """Improved change detection with deeper code analysis"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)
        
        # Language patterns for function and class detection
        self.language_patterns = {
            'python': {
                'function': r'def\s+(\w+)\s*\(',
                'class': r'class\s+(\w+)',
                'import': r'(?:from\s+[\w.]+\s+)?import\s+[\w.]+',
            },
            'javascript': {
                'function': r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:\([^)]*\)\s*=>|function))',
                'class': r'class\s+(\w+)',
                'import': r'(?:import|require)\s*\(',
            },
            'java': {
                'function': r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(',
                'class': r'(?:public|private|protected)?\s*(?:abstract)?\s*class\s+(\w+)',
                'import': r'import\s+[\w.]+;',
            },
            'go': {
                'function': r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(',
                'class': r'type\s+(\w+)\s+struct',
                'import': r'import\s+(?:\(\s*[\s\S]*?\s*\)|"[^"]+"|`[^`]+`)',
            }
        }
        
    def detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        extension = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'javascript',
            '.tsx': 'javascript',
            '.java': 'java',
            '.go': 'go',
            '.cs': 'csharp',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.rb': 'ruby',
            '.php': 'php',
            '.md': 'markdown',
            '.rst': 'restructuredtext'
        }
        return language_map.get(extension, 'unknown')
    
    def analyze_python_changes(self, content: str, diff_content: str) -> Tuple[List[str], List[str], List[str]]:
        """Analyze Python code changes using AST"""
        functions_changed = []
        classes_changed = []
        imports_changed = []
        
        try:
            # Parse the AST
            tree = ast.parse(content)
            
            # Extract all functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if self._is_in_diff(node.name, diff_content):
                        functions_changed.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    if self._is_in_diff(node.name, diff_content):
                        classes_changed.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_str = ast.unparse(node)
                    if self._is_in_diff(import_str, diff_content):
                        imports_changed.append(import_str)
        except SyntaxError:
            # Fallback to regex if AST parsing fails
            functions_changed = re.findall(self.language_patterns['python']['function'], diff_content)
            classes_changed = re.findall(self.language_patterns['python']['class'], diff_content)
            imports_changed = re.findall(self.language_patterns['python']['import'], diff_content)
            
        return functions_changed, classes_changed, imports_changed
    
    def analyze_generic_changes(self, language: str, diff_content: str) -> Tuple[List[str], List[str], List[str]]:
        """Analyze code changes using regex patterns for non-Python languages"""
        patterns = self.language_patterns.get(language, {})
        
        functions_changed = []
        if 'function' in patterns:
            matches = re.findall(patterns['function'], diff_content)
            functions_changed = [m if isinstance(m, str) else next((x for x in m if x), '') 
                               for m in matches]
        
        classes_changed = []
        if 'class' in patterns:
            classes_changed = re.findall(patterns['class'], diff_content)
        
        imports_changed = []
        if 'import' in patterns:
            imports_changed = re.findall(patterns['import'], diff_content)
        
        return functions_changed, classes_changed, imports_changed
    
    def _is_in_diff(self, name: str, diff_content: str) -> bool:
        """Check if a name appears in the diff content"""
        return name in diff_content
    
    def calculate_complexity_score(self, change_context: ChangeContext) -> float:
        """Calculate complexity score based on change characteristics"""
        score = 0.0
        
        # Base score from lines changed
        total_lines = change_context.lines_added + change_context.lines_deleted
        score += min(total_lines / 100, 1.0) * 5  # Max 5 points for line changes
        
        # Score from structural changes
        score += len(change_context.functions_changed) * 2
        score += len(change_context.classes_changed) * 3
        score += len(change_context.imports_changed) * 1
        
        # Language complexity factor
        language_complexity = {
            'java': 1.5,
            'cpp': 1.8,
            'go': 1.2,
            'python': 1.0,
            'javascript': 1.1,
        }
        score *= language_complexity.get(change_context.language, 1.0)
        
        return min(score, 10.0)  # Cap at 10
    
    def calculate_documentation_impact(self, change_context: ChangeContext) -> float:
        """Calculate how much documentation might need updates"""
        impact = 0.0
        
        # High impact for class changes
        impact += len(change_context.classes_changed) * 3
        
        # Medium impact for function changes
        impact += len(change_context.functions_changed) * 2
        
        # Low impact for import changes
        impact += len(change_context.imports_changed) * 0.5
        
        # Consider file type
        if change_context.file_path.endswith(('api.py', 'interface.go', 'public.js')):
            impact *= 2  # Public APIs have higher documentation impact
        
        return min(impact, 10.0)  # Cap at 10
    
    def analyze_commit_changes(self, commit: git.Commit) -> List[ChangeContext]:
        """Analyze changes in a commit with detailed context"""
        change_contexts = []
        
        for diff in commit.diff(commit.parents[0] if commit.parents else None):
            file_path = diff.b_path or diff.a_path
            language = self.detect_language(file_path)
            
            # Skip non-code files
            if language in ['unknown', 'markdown', 'restructuredtext']:
                continue
            
            # Determine change type
            if diff.change_type == 'A':
                change_type = 'added'
            elif diff.change_type == 'D':
                change_type = 'removed'
            else:
                change_type = 'modified'
            
            # Get diff content
            diff_content = str(diff)
            
            # Count lines
            lines_added = sum(1 for line in str(diff).split('\n') if line.startswith('+'))
            lines_deleted = sum(1 for line in str(diff).split('\n') if line.startswith('-'))
            
            # Analyze structural changes
            if language == 'python' and diff.b_blob:
                try:
                    content = diff.b_blob.data_stream.read().decode('utf-8')
                    functions, classes, imports = self.analyze_python_changes(content, diff_content)
                except Exception as e:
                    logger.warning(f"Failed to analyze Python file {file_path}: {e}")
                    functions, classes, imports = self.analyze_generic_changes(language, diff_content)
            else:
                functions, classes, imports = self.analyze_generic_changes(language, diff_content)
            
            # Create change context
            context = ChangeContext(
                file_path=file_path,
                change_type=change_type,
                language=language,
                functions_changed=functions,
                classes_changed=classes,
                imports_changed=imports,
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                complexity_score=0.0,
                documentation_impact=0.0
            )
            
            # Calculate scores
            context.complexity_score = self.calculate_complexity_score(context)
            context.documentation_impact = self.calculate_documentation_impact(context)
            
            change_contexts.append(context)
        
        return change_contexts
    
    def get_changed_contexts(self, since_time: datetime) -> List[ChangeContext]:
        """Get detailed change contexts since the given time"""
        all_contexts = []
        
        try:
            # Get commits since the given time
            for commit in self.repo.iter_commits(since=since_time.strftime("%Y-%m-%d %H:%M:%S")):
                contexts = self.analyze_commit_changes(commit)
                all_contexts.extend(contexts)
        except Exception as e:
            logger.error(f"Error analyzing changes: {e}")
        
        return all_contexts