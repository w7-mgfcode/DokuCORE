import os
import time
import git
import requests
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
REPO_PATH = os.environ.get("REPO_PATH", "/app/repo")
API_URL = os.environ.get("API_URL", "http://api:9000")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 300))  # 5 minutes

def get_changed_files(repo, since_time):
    """Get files modified since the given time"""
    changed_files = []

    try:
        # Get commits since the given time
        for commit in repo.iter_commits(since=since_time.strftime("%Y-%m-%d %H:%M:%S")):
            # Add affected files to the list
            for file in commit.stats.files:
                if file.endswith((".py", ".js", ".ts", ".java", ".cs", ".go", ".md", ".txt")) and file not in changed_files:
                    changed_files.append(file)

        return changed_files
    except Exception as e:
        logger.error(f"Error retrieving changes: {str(e)}")
        return []

def suggest_doc_update(file_path, content):
    """Create documentation update suggestion"""
    # Here we can integrate an LLM API (e.g., Anthropic Claude API or OpenAI API)
    # Simplified example:
    file_name = os.path.basename(file_path)

    return {
        "title": f"Documentation update needed: {file_name}",
        "description": f"The {file_path} file has been modified. Please check and update the corresponding documentation to match the current implementation.",
        "code_path": file_path
    }

def find_related_doc_id(file_path):
    """Find related document ID based on file path"""
    try:
        # API call to find related document
        response = requests.get(f"{API_URL}/documents/")
        if response.status_code == 200:
            documents = response.json()

            # Simple check - if the document path contains the file name
            file_name = os.path.basename(file_path)
            for doc in documents:
                # Check if file_name is in the doc['path'] OR doc['title'] (case-insensitive)
                if file_name.lower() in doc["path"].lower() or file_name.split('.')[0].lower() in doc['title'].lower():
                    return doc["id"]

        return None
    except Exception as e:
        logger.error(f"Error finding related document: {str(e)}")
        return None

def main():
    logger.info("Code Monitor Service started")
    logger.info(f"Git repository path: {REPO_PATH}")
    logger.info(f"API URL: {API_URL}")

    # Check if repository directory exists
    if not os.path.exists(REPO_PATH):
        logger.error(f"The specified repository path does not exist: {REPO_PATH}")
        return

    # Check if the directory is a git repository
    try:
        repo = git.Repo(REPO_PATH)
    except git.InvalidGitRepositoryError:
        logger.error(f"The specified directory is not a valid git repository: {REPO_PATH}")
        return

    last_check_time = datetime.now() - timedelta(days=1)  # Start by checking changes in the last 24 hours

    while True:
        current_time = datetime.now()
        logger.info(f"Checking: {current_time}")

        try:
            # Update git repo
            origin = repo.remotes.origin
            origin.pull()
            logger.info("Git repository successfully updated")

            # Get modified files
            changed_files = get_changed_files(repo, last_check_time)
            logger.info(f"Number of modified files: {len(changed_files)}")

            for file_path in changed_files:
                logger.info(f"Processing modified file: {file_path}")

                # Get file content
                full_path = os.path.join(REPO_PATH, file_path)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Find related document
                        doc_id = find_related_doc_id(file_path)

                        # Create documentation update suggestion
                        task = suggest_doc_update(file_path, content)
                        if doc_id:
                            task["document_id"] = doc_id

                        # Create task via API
                        logger.info(f"Creating task: {task['title']}")
                        response = requests.post(
                            f"{API_URL}/tasks/",
                            json=task
                        )

                        if response.status_code == 200:
                            logger.info(f"Task successfully created: {response.json().get('task_id')}") # Use task_id from response
                        else:
                            logger.error(f"Error creating task: {response.text}")
                    except Exception as e:
                        logger.error(f"Error processing file: {str(e)}")

            last_check_time = current_time
        except git.GitCommandError as e:
             logger.error(f"Git command error: {str(e)}")
        except requests.exceptions.ConnectionError as e:
             logger.error(f"API connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Error running code monitor: {str(e)}")

        # Wait until next check
        logger.info(f"Waiting {CHECK_INTERVAL} seconds until next check...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()