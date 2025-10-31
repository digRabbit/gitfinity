#!/usr/bin/env python3
"""
Daily GitHub Commit Script
Runs 8 times per day (every ~3 hours), creating 0-2 commits each run.
With adjusted weights, averages ~3-4 commits per day for realistic activity.
"""

import argparse
import logging
import random
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DailyCommitter:
    """Handles daily GitHub commit generation and management."""
    
    def __init__(self, repo_path: str = ".") -> None:
        """
        Initialize the DailyCommitter.
        
        Args:
            repo_path: Path to the git repository root
        """
        self.repo_path = Path(repo_path)
        self.activity_file = self.repo_path / config.ACTIVITY_LOG_FILE

    def get_s_curve_commits(self) -> int:
        """
        Generate random number of commits (0-2) using weighted distribution.

        Since the workflow runs 8 times per day with these weights:
        - 60% chance of 0 commits (most runs do nothing)
        - 35% chance of 1 commit (occasionally active)
        - 5% chance of 2 commits (rare bursts)

        Expected: ~3-4 commits per day (0.45 commits/run * 8 runs)
        
        Returns:
            Number of commits to create (0 to MAX_COMMITS_PER_RUN)
        """
        max_commits = config.MAX_COMMITS_PER_RUN + 1  # range is exclusive
        commits = random.choices(
            range(max_commits),
            weights=config.COMMIT_WEIGHTS,
            k=1
        )[0]
        return commits

    def run_git_command(self, command: List[str]) -> Optional[str]:
        """
        Execute a git command and return the result.
        
        Args:
            command: Git command as a list of strings (e.g., ["git", "add", "file"])
            
        Returns:
            Command stdout if successful, None otherwise
        """
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(command)}")
            logger.error(f"Error output: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error running git command: {e}")
            return None

    def truncate_log_file(self, max_lines: int = config.MAX_LOG_LINES) -> None:
        """
        Keep only the last max_lines in the activity log.
        
        Args:
            max_lines: Maximum number of lines to keep in the log file
        """
        if not self.activity_file.exists():
            return

        try:
            # Read all lines
            with open(self.activity_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # If we have more than max_lines, keep only the last max_lines
            if len(lines) > max_lines:
                with open(self.activity_file, "w", encoding="utf-8") as f:
                    f.writelines(lines[-max_lines:])
                logger.info(f"Truncated log file to {max_lines} lines")
        except IOError as e:
            logger.error(f"Error truncating log file: {e}")

    def update_activity_file(self) -> str:
        """
        Update the activity log file with a timestamp.
        
        Returns:
            Timestamp string that was logged
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Create or append to activity file
            with open(self.activity_file, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} - Activity logged\n")

            # Truncate if needed
            self.truncate_log_file()

            return timestamp
        except IOError as e:
            logger.error(f"Error updating activity file: {e}")
            raise

    def make_commit(self, commit_number: int) -> bool:
        """
        Create a single commit.
        
        Args:
            commit_number: Sequential number for this commit
            
        Returns:
            True if commit was successful, False otherwise
        """
        try:
            timestamp = self.update_activity_file()
        except Exception as e:
            logger.error(f"Failed to update activity file: {e}")
            return False

        # Stage the changes
        stage_result = self.run_git_command(["git", "add", config.ACTIVITY_LOG_FILE])
        if stage_result is None:
            logger.warning("Failed to stage activity.log file")
            return False

        # Create commit
        commit_message = config.COMMIT_MESSAGE_TEMPLATE.format(
            commit_number=commit_number,
            timestamp=timestamp
        )
        commit_result = self.run_git_command(["git", "commit", "-m", commit_message])

        if commit_result is not None:
            logger.info(f"Commit #{commit_number} created: {commit_message}")
            return True
        
        logger.warning(f"Failed to create commit #{commit_number}")
        return False

    def push_commits(self) -> bool:
        """
        Push all commits to GitHub.
        
        Returns:
            True if push was successful, False otherwise
        """
        logger.info("Pushing commits to GitHub...")
        result = self.run_git_command(["git", "push"])

        if result is not None:
            logger.info("Successfully pushed to GitHub!")
            return True
        
        logger.error("Failed to push to GitHub")
        return False

    def run(self, auto_push: bool = True, test_mode: bool = False) -> None:
        """
        Main execution: create 0-2 random commits and optionally push.
        
        Args:
            auto_push: Whether to automatically push commits after creation
            test_mode: If True, always create MAX_COMMITS_PER_RUN commits
        """
        # Random number of commits using S-curve distribution
        if test_mode:
            num_commits = config.MAX_COMMITS_PER_RUN  # Always create max commits in test mode
            logger.info("=== Daily GitHub Activity (TEST MODE) ===")
        else:
            num_commits = self.get_s_curve_commits()
            logger.info("=== Daily GitHub Activity ===")

        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        logger.info(f"Commits to create: {num_commits}")
        logger.info("=" * 30)

        if num_commits == 0:
            logger.info("No commits this run. Skipping...")
            return

        # Create the commits
        # Note: No delays needed since workflow runs multiple times per day
        successful_commits = 0
        for i in range(1, num_commits + 1):
            if self.make_commit(i):
                successful_commits += 1

        logger.info(f"\nCreated {successful_commits} commit(s)")

        # Push to GitHub if enabled
        if successful_commits > 0 and auto_push:
            self.push_commits()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Create 0-{config.MAX_COMMITS_PER_RUN} random commits for daily GitHub activity"
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Don't push commits to remote (useful for CI/CD)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: always create 2 commits instead of random (0-2)"
    )
    args = parser.parse_args()

    committer = DailyCommitter()
    committer.run(auto_push=not args.no_push, test_mode=args.test)
