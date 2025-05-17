import os
import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import requests
import json

logger = logging.getLogger(__name__)

@dataclass
class ChangeSummary:
    """Structured summary of code changes"""
    executive_summary: str
    detailed_changes: List[str]
    impact_analysis: str
    documentation_suggestions: List[str]
    code_examples: List[Dict[str, str]] = field(default_factory=list)
    migration_notes: Optional[str] = None
    related_files: List[str] = field(default_factory=list)
    
class ChangeSummaryGenerator:
    """Generate human-readable summaries of code changes"""
    
    def __init__(self, llm_api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.llm_api_url = llm_api_url or os.environ.get("LLM_API_URL")
        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        
        # Template patterns for different types of changes
        self.change_templates = {
            'api_change': "API endpoint {name} was {action} affecting {impact}",
            'function_change': "Function {name} was {action} in {file}",
            'class_change': "Class {name} was {action} in {file}",
            'security_change': "Security-related change in {file}: {description}",
            'config_change': "Configuration change in {file}: {description}",
            'dependency_change': "Dependency {name} was {action}"
        }
    
    def generate_summary(self, change_contexts: List, repository_name: str = "repository") -> ChangeSummary:
        """Generate comprehensive summary from change contexts"""
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(change_contexts, repository_name)
        
        # Generate detailed changes
        detailed_changes = self._generate_detailed_changes(change_contexts)
        
        # Analyze impact
        impact_analysis = self._analyze_impact(change_contexts)
        
        # Generate documentation suggestions
        doc_suggestions = self._generate_doc_suggestions(change_contexts)
        
        # Extract code examples
        code_examples = self._extract_code_examples(change_contexts)
        
        # Generate migration notes if needed
        migration_notes = self._generate_migration_notes(change_contexts)
        
        # Collect related files
        related_files = self._collect_related_files(change_contexts)
        
        return ChangeSummary(
            executive_summary=executive_summary,
            detailed_changes=detailed_changes,
            impact_analysis=impact_analysis,
            documentation_suggestions=doc_suggestions,
            code_examples=code_examples,
            migration_notes=migration_notes,
            related_files=related_files
        )
    
    def _generate_executive_summary(self, change_contexts: List, repository_name: str) -> str:
        """Generate high-level executive summary"""
        total_files = len(change_contexts)
        languages = set(ctx.language for ctx in change_contexts if hasattr(ctx, 'language'))
        
        if hasattr(change_contexts[0], 'functions_changed'):
            total_functions = sum(len(ctx.functions_changed) for ctx in change_contexts)
            total_classes = sum(len(ctx.classes_changed) for ctx in change_contexts)
        else:
            total_functions = 0
            total_classes = 0
        
        summary_parts = []
        
        # Basic statistics
        summary_parts.append(
            f"Changes detected in {repository_name}: {total_files} files modified"
        )
        
        if languages:
            summary_parts.append(f"Languages affected: {', '.join(sorted(languages))}")
        
        if total_functions > 0 or total_classes > 0:
            summary_parts.append(
                f"Structural changes: {total_functions} functions, {total_classes} classes"
            )
        
        # Check for critical changes
        critical_changes = self._identify_critical_changes(change_contexts)
        if critical_changes:
            summary_parts.append(f"Critical changes detected: {', '.join(critical_changes)}")
        
        return ". ".join(summary_parts)
    
    def _generate_detailed_changes(self, change_contexts: List) -> List[str]:
        """Generate detailed list of changes"""
        detailed_changes = []
        
        for ctx in change_contexts:
            if hasattr(ctx, 'change_type'):
                # Format: "Modified api/endpoints.py: Updated authentication functions"
                change_desc = f"{ctx.change_type.title()} {ctx.file_path}"
                
                if hasattr(ctx, 'functions_changed') and ctx.functions_changed:
                    functions = ", ".join(ctx.functions_changed[:3])
                    if len(ctx.functions_changed) > 3:
                        functions += f" and {len(ctx.functions_changed)-3} more"
                    change_desc += f": Functions [{functions}]"
                
                if hasattr(ctx, 'classes_changed') and ctx.classes_changed:
                    classes = ", ".join(ctx.classes_changed[:3])
                    if len(ctx.classes_changed) > 3:
                        classes += f" and {len(ctx.classes_changed)-3} more"
                    change_desc += f": Classes [{classes}]"
                
                detailed_changes.append(change_desc)
            else:
                # Simple format for basic change info
                detailed_changes.append(f"Modified {ctx.get('file_path', 'unknown file')}")
        
        return detailed_changes
    
    def _analyze_impact(self, change_contexts: List) -> str:
        """Analyze the impact of changes"""
        impact_parts = []
        
        # Check for API changes
        api_files = [ctx for ctx in change_contexts 
                    if hasattr(ctx, 'file_path') and 'api' in ctx.file_path.lower()]
        if api_files:
            impact_parts.append(f"API changes in {len(api_files)} files may affect external integrations")
        
        # Check for configuration changes
        config_files = [ctx for ctx in change_contexts 
                       if hasattr(ctx, 'file_path') and any(
                           pattern in ctx.file_path.lower() 
                           for pattern in ['config', 'settings', '.env', '.yml', '.yaml']
                       )]
        if config_files:
            impact_parts.append(f"Configuration changes in {len(config_files)} files may require deployment updates")
        
        # Check for breaking changes
        breaking_changes = [ctx for ctx in change_contexts 
                           if hasattr(ctx, 'change_type') and ctx.change_type == 'removed']
        if breaking_changes:
            impact_parts.append(f"{len(breaking_changes)} files removed - potential breaking changes")
        
        # Check complexity
        high_complexity = [ctx for ctx in change_contexts 
                          if hasattr(ctx, 'complexity_score') and ctx.complexity_score > 7]
        if high_complexity:
            impact_parts.append(f"{len(high_complexity)} highly complex changes require careful review")
        
        return ". ".join(impact_parts) if impact_parts else "Minimal impact expected from these changes"
    
    def _generate_doc_suggestions(self, change_contexts: List) -> List[str]:
        """Generate documentation update suggestions"""
        suggestions = []
        
        # Check for undocumented public APIs
        api_changes = [ctx for ctx in change_contexts 
                      if hasattr(ctx, 'file_path') and 'api' in ctx.file_path.lower()]
        if api_changes:
            suggestions.append("Update API documentation to reflect new endpoints and changes")
        
        # Check for new classes that need documentation
        new_classes = []
        for ctx in change_contexts:
            if hasattr(ctx, 'classes_changed') and ctx.classes_changed:
                new_classes.extend(ctx.classes_changed)
        
        if new_classes:
            suggestions.append(f"Document {len(new_classes)} new or modified classes: {', '.join(new_classes[:5])}")
        
        # Check for configuration changes
        config_changes = [ctx for ctx in change_contexts 
                         if hasattr(ctx, 'file_path') and 'config' in ctx.file_path.lower()]
        if config_changes:
            suggestions.append("Update configuration documentation and deployment guides")
        
        # General suggestions based on file types
        if any(ctx.file_path.endswith(('.py', '.js', '.java')) for ctx in change_contexts 
               if hasattr(ctx, 'file_path')):
            suggestions.append("Update code examples in documentation to match new implementations")
        
        return suggestions
    
    def _extract_code_examples(self, change_contexts: List) -> List[Dict[str, str]]:
        """Extract relevant code examples from changes"""
        examples = []
        
        # For now, create placeholder examples - in real implementation,
        # this would extract actual code snippets from the diffs
        for ctx in change_contexts[:3]:  # Limit to 3 examples
            if hasattr(ctx, 'functions_changed') and ctx.functions_changed:
                examples.append({
                    'title': f"Changed function in {ctx.file_path}",
                    'description': f"Function {ctx.functions_changed[0]} was modified",
                    'code': f"# Example change in {ctx.functions_changed[0]}\n# [Code diff would be shown here]"
                })
        
        return examples
    
    def _generate_migration_notes(self, change_contexts: List) -> Optional[str]:
        """Generate migration notes for breaking changes"""
        breaking_changes = []
        
        for ctx in change_contexts:
            if hasattr(ctx, 'change_type') and ctx.change_type == 'removed':
                breaking_changes.append(f"Removed: {ctx.file_path}")
            elif hasattr(ctx, 'functions_changed'):
                # Check for potentially breaking function changes
                for func in ctx.functions_changed:
                    if any(pattern in func.lower() for pattern in ['deprecated', 'removed', 'legacy']):
                        breaking_changes.append(f"Deprecated function: {func} in {ctx.file_path}")
        
        if not breaking_changes:
            return None
        
        notes = ["Migration Required:", ""]
        notes.extend(f"- {change}" for change in breaking_changes)
        notes.append("")
        notes.append("Please update dependent code before deploying these changes.")
        
        return "\n".join(notes)
    
    def _collect_related_files(self, change_contexts: List) -> List[str]:
        """Collect related files that might need attention"""
        related = set()
        
        for ctx in change_contexts:
            if hasattr(ctx, 'file_path'):
                base_name = Path(ctx.file_path).stem
                
                # Look for test files
                test_patterns = [f"test_{base_name}", f"{base_name}_test", f"{base_name}.test"]
                for pattern in test_patterns:
                    related.add(f"*{pattern}*")
                
                # Look for documentation files
                related.add(f"*{base_name}.md")
                related.add(f"*{base_name}.rst")
        
        return sorted(list(related))
    
    def _identify_critical_changes(self, change_contexts: List) -> List[str]:
        """Identify critical changes that need immediate attention"""
        critical = []
        
        for ctx in change_contexts:
            if hasattr(ctx, 'file_path'):
                # Security-related files
                if any(pattern in ctx.file_path.lower() 
                      for pattern in ['auth', 'security', 'password', 'token', 'key']):
                    critical.append("Security-related changes")
                
                # API changes
                if 'api' in ctx.file_path.lower() and ctx.change_type != 'added':
                    critical.append("API modifications")
                
                # Database changes
                if any(pattern in ctx.file_path.lower() 
                      for pattern in ['migration', 'schema', 'database', 'db']):
                    critical.append("Database schema changes")
                
                # Configuration changes
                if any(pattern in ctx.file_path.lower() 
                      for pattern in ['config', 'settings', '.env']):
                    critical.append("Configuration updates")
        
        return list(set(critical))  # Remove duplicates
    
    def generate_llm_summary(self, change_contexts: List, prompt: str = None) -> Optional[str]:
        """Generate summary using LLM API if configured"""
        if not self.llm_api_url or not self.api_key:
            return None
        
        try:
            # Prepare context for LLM
            context = {
                'changes': [
                    {
                        'file': ctx.file_path,
                        'type': ctx.change_type,
                        'functions': getattr(ctx, 'functions_changed', []),
                        'classes': getattr(ctx, 'classes_changed', []),
                        'complexity': getattr(ctx, 'complexity_score', 0)
                    }
                    for ctx in change_contexts
                ]
            }
            
            # Default prompt if none provided
            if not prompt:
                prompt = """Analyze the following code changes and provide:
                1. A concise summary of what changed
                2. The potential impact of these changes
                3. Any documentation that needs updating
                4. Migration steps if there are breaking changes
                
                Changes: {context}"""
            
            # Call LLM API
            response = requests.post(
                self.llm_api_url,
                headers={'Authorization': f'Bearer {self.api_key}'},
                json={
                    'prompt': prompt.format(context=json.dumps(context, indent=2)),
                    'max_tokens': 500,
                    'temperature': 0.3
                }
            )
            
            if response.status_code == 200:
                return response.json().get('text', '')
            else:
                logger.error(f"LLM API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            return None