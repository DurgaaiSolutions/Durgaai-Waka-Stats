from os import getenv, environ


class EnvironmentManager:
    _TRUTHY = ["true", "1", "t", "y", "yes"]

    # Required tokens
    GH_TOKEN = environ["INPUT_GH_TOKEN"]
    WAKATIME_API_KEY = environ["INPUT_WAKATIME_API_KEY"]

    # Section and branch configuration
    SECTION_NAME = getenv("INPUT_SECTION_NAME", "waka")
    PULL_BRANCH_NAME = getenv("INPUT_PULL_BRANCH_NAME", "")
    PUSH_BRANCH_NAME = getenv("INPUT_PUSH_BRANCH_NAME", "")

    # Display options
    SHOW_OS = getenv("INPUT_SHOW_OS", "False").lower() in _TRUTHY
    SHOW_PROJECTS = getenv("INPUT_SHOW_PROJECTS", "True").lower() in _TRUTHY
    SHOW_EDITORS = getenv("INPUT_SHOW_EDITORS", "True").lower() in _TRUTHY
    SHOW_TIMEZONE = getenv("INPUT_SHOW_TIMEZONE", "True").lower() in _TRUTHY
    SHOW_COMMIT = getenv("INPUT_SHOW_COMMIT", "True").lower() in _TRUTHY
    SHOW_LANGUAGE = getenv("INPUT_SHOW_LANGUAGE", "True").lower() in _TRUTHY
    SHOW_LINES_OF_CODE = getenv("INPUT_SHOW_LINES_OF_CODE", "False").lower() in _TRUTHY
    SHOW_LANGUAGE_PER_REPO = getenv("INPUT_SHOW_LANGUAGE_PER_REPO", "True").lower() in _TRUTHY
    SHOW_LOC_CHART = getenv("INPUT_SHOW_LOC_CHART", "True").lower() in _TRUTHY
    SHOW_DAYS_OF_WEEK = getenv("INPUT_SHOW_DAYS_OF_WEEK", "True").lower() in _TRUTHY
    SHOW_PROFILE_VIEWS = getenv("INPUT_SHOW_PROFILE_VIEWS", "True").lower() in _TRUTHY
    SHOW_SHORT_INFO = getenv("INPUT_SHOW_SHORT_INFO", "True").lower() in _TRUTHY
    SHOW_UPDATED_DATE = getenv("INPUT_SHOW_UPDATED_DATE", "True").lower() in _TRUTHY
    SHOW_TOTAL_CODE_TIME = getenv("INPUT_SHOW_TOTAL_CODE_TIME", "True").lower() in _TRUTHY

    # Commit settings
    COMMIT_BY_ME = getenv("INPUT_COMMIT_BY_ME", "False").lower() in _TRUTHY
    COMMIT_MESSAGE = getenv("INPUT_COMMIT_MESSAGE", "Updated with Dev Metrics")
    COMMIT_USERNAME = getenv("INPUT_COMMIT_USERNAME", "")
    COMMIT_EMAIL = getenv("INPUT_COMMIT_EMAIL", "")
    COMMIT_SINGLE = getenv("INPUT_COMMIT_SINGLE", "False").lower() in _TRUTHY

    # Miscellaneous settings
    UPDATED_DATE_FORMAT = getenv("INPUT_UPDATED_DATE_FORMAT", "%d/%m/%Y %H:%M:%S")
    IGNORED_REPOS = getenv("INPUT_IGNORED_REPOS", "").replace(" ", "").split(",")
    SYMBOL_VERSION = int(getenv("INPUT_SYMBOL_VERSION", "1"))

    # Debugging
    DEBUG_LOGGING = getenv("INPUT_DEBUG_LOGGING", "0").lower() in _TRUTHY
    DEBUG_RUN = getenv("DEBUG_RUN", "False").lower() in _TRUTHY
