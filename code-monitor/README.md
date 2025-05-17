# Enhanced Code Monitor

The Enhanced Code Monitor is a sophisticated system for monitoring code changes across multiple repositories and automatically generating documentation tasks with intelligent prioritization and assignment.

## Features

### 1. Enhanced Change Detection
- **AST Parsing**: Uses Abstract Syntax Tree parsing for Python files to accurately detect function, class, and import changes
- **Language Support**: Supports Python, JavaScript, Java, Go, and more with configurable patterns
- **Complexity Scoring**: Calculates change complexity based on lines changed, structural changes, and language
- **Documentation Impact**: Estimates the documentation impact of each change

### 2. Intelligent Task Prioritization
- **Multi-Factor Scoring**: Considers file importance, change complexity, documentation impact, critical keywords, breaking changes, and coverage gaps
- **Priority Levels**: CRITICAL, HIGH, MEDIUM, LOW based on calculated scores
- **File Pattern Recognition**: Recognizes critical patterns (API, security, auth) for priority boosting
- **Breaking Change Detection**: Identifies potential breaking changes and deprecated functions

### 3. Multi-Repository Support
- **Concurrent Monitoring**: Monitors multiple repositories simultaneously using threading
- **Repository Configuration**: JSON-based configuration for each repository with custom settings
- **Remote Repository Support**: Can clone and monitor remote Git repositories
- **Pattern Filtering**: Include/exclude patterns for files to monitor

### 4. Change Summary Generation
- **Executive Summaries**: High-level summaries of changes detected
- **Detailed Change Lists**: Comprehensive lists of all modifications
- **Impact Analysis**: Analysis of potential impact on external systems
- **Documentation Suggestions**: AI-generated suggestions for documentation updates
- **Migration Notes**: Automatic generation of migration notes for breaking changes

### 5. Task Assignment Recommendations
- **Developer Profiles**: Tracks developer expertise, languages, and specializations
- **Expertise Matching**: Matches tasks to developers based on language and domain expertise
- **Workload Balancing**: Considers current developer workload when making assignments
- **Backup Assignments**: Suggests backup developers for critical tasks
- **Team Capacity Analysis**: Provides insights into team capacity and expansion needs

## Configuration

### Repository Configuration (`config/repos_config.json`)
```json
{
  "repositories": [
    {
      "name": "main-repo",
      "path": "/app/repo",
      "url": "https://github.com/example/repo.git",
      "branch": "main",
      "enabled": true,
      "check_interval": 300,
      "file_patterns": ["*.py", "*.js", "*.go"],
      "exclude_patterns": ["test_*", "*.min.js"],
      "priority_boost": 1.0
    }
  ]
}
```

### Developer Profiles (`config/developer_profiles.json`)
```json
{
  "alice": {
    "username": "alice",
    "email": "alice@example.com",
    "expertise_areas": {
      "api": 0.9,
      "backend": 0.8,
      "database": 0.7
    },
    "languages": {
      "python": 0.9,
      "javascript": 0.6
    },
    "availability": "available",
    "quality_score": 0.92
  }
}
```

### Environment Variables
```bash
# API Configuration
API_URL=http://api:9000
CHECK_INTERVAL=300

# Webhook Configuration
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://hooks.slack.com/services/...

# LLM Configuration (for summary generation)
LLM_API_URL=https://api.openai.com/v1/completions
LLM_API_KEY=your-api-key-here

# Repository Path (default for single-repo mode)
REPO_PATH=/app/repo
```

## Usage

### Running the Enhanced Monitor
```bash
# Using Docker
docker-compose up code-monitor

# Running locally
cd code-monitor
python enhanced_code_monitor.py
```

### API Integration
The monitor automatically creates tasks through the DokuCORE API:
- Creates documentation tasks for high-priority changes
- Includes detailed metadata about changes
- Assigns tasks based on developer expertise
- Sends webhook notifications when configured

### Monitoring Report
The monitor generates periodic reports including:
- Statistics (tasks created, changes detected)
- Repository status
- Team capacity analysis
- Priority distribution of tasks

## Architecture

```
EnhancedCodeMonitor
├── MultiRepositoryMonitor (manages multiple repos)
├── EnhancedChangeDetector (analyzes code changes)
├── TaskPrioritizer (calculates task priorities)
├── ChangeSummaryGenerator (creates summaries)
└── TaskAssigner (recommends assignments)
```

## Extending the System

### Adding New Languages
To add support for new languages:
1. Update language patterns in `enhanced_change_detector.py`
2. Add file extension mapping
3. Define complexity factors

### Custom Priority Rules
To add custom priority rules:
1. Extend `TaskPrioritizer` class
2. Add new factors to `_calculate_priority`
3. Update scoring weights

### Integration with Other Systems
The monitor supports webhooks for integration:
- Slack notifications
- GitHub/GitLab integration
- JIRA task creation
- Custom integrations

## Troubleshooting

### Common Issues
1. **Repository not found**: Check path in `repos_config.json`
2. **Git authentication**: Configure SSH keys or credentials
3. **API connection**: Verify `API_URL` environment variable
4. **LLM timeouts**: Increase timeout or use local models

### Logs
Monitor logs are available at:
```bash
docker-compose logs -f code-monitor
```

### Performance Tuning
- Adjust `CHECK_INTERVAL` for monitoring frequency
- Configure thread pool size for multi-repo monitoring
- Tune AST parsing depth for large files
- Cache developer profiles for better performance