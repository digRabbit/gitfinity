"""
Configuration constants for gitfinity.
"""

# Commit distribution weights (0, 1, 2 commits per run)
# [60, 35, 5] means:
# - 60% chance of 0 commits
# - 35% chance of 1 commit
# - 5% chance of 2 commits
COMMIT_WEIGHTS = [60, 35, 5]

# Maximum number of commits per run
MAX_COMMITS_PER_RUN = 2

# Activity log settings
ACTIVITY_LOG_FILE = "activity.log"
MAX_LOG_LINES = 100

# Commit message format
COMMIT_MESSAGE_TEMPLATE = "Daily activity update #{commit_number} - {timestamp}"

# Number of scheduled runs per day
RUNS_PER_DAY = 8

# Expected average commits per day (approximate)
EXPECTED_DAILY_COMMITS = 3.4

