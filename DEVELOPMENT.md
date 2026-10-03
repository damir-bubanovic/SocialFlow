# SocialFlow --- Development Guide

## 1. Purpose

This document describes how to set up, develop, test, and verify
SocialFlow.

It should contain the commands and procedures needed by a developer
working on the project.

Update this document whenever the development workflow changes.

------------------------------------------------------------------------

## 2. Supported Development Platforms

SocialFlow targets:

-   Linux
-   Windows

The initial development environment is Linux Mint.

Platform-specific instructions will be added as they become necessary.

------------------------------------------------------------------------

## 3. Python

SocialFlow is developed in Python.

Initial development version:

``` text
Python 3.12
```

The project currently uses Python 3.12.3 on the primary Linux
development environment.

The minimum supported Python version will be formalized before release.

------------------------------------------------------------------------

## 4. IDE

The primary development IDE is PyCharm.

IDE-specific files are local development files and are not committed to
Git.

The project must not depend on PyCharm in order to build, test, or run.

------------------------------------------------------------------------

## 5. Repository

Remote repository:

``` text
https://github.com/damir-bubanovic/SocialFlow.git
```

Primary branch:

``` text
main
```

Normal development work should be performed from the local Git
repository and pushed after the relevant implementation and verification
steps are complete.

------------------------------------------------------------------------

## 6. Virtual Environment

SocialFlow uses a project-local Python virtual environment.

Expected directory:

``` text
.venv/
```

The virtual environment is excluded from Git.

### Linux

Create the environment:

``` bash
python3 -m venv .venv
```

Activate it:

``` bash
source .venv/bin/activate
```

### Windows

Create the environment:

``` powershell
py -m venv .venv
```

Activate it in PowerShell:

``` powershell
.\.venv\Scripts\Activate.ps1
```

The terminal prompt should normally indicate that `.venv` is active.

------------------------------------------------------------------------

## 7. Dependencies

Project dependencies are defined in the tracked `pyproject.toml`.

Do not treat the local `.venv` directory as the dependency definition.

Install SocialFlow in editable mode with development dependencies from
the project root:

``` bash
python -m pip install -e ".[dev]"
```

The current runtime dependency is PySide6. The current development
dependencies are pytest and pytest-qt.

Additional dependencies should only be added when implementation
requires them.

------------------------------------------------------------------------

## 8. Planned Core Dependencies

The initial architecture currently expects the following technologies:

-   PySide6 / Qt 6 --- desktop user interface
-   SQLAlchemy --- database access
-   HTTPX --- HTTP/API communication
-   Pillow --- image processing
-   pytest --- automated testing
-   pytest-qt --- Qt testing where appropriate

Dependencies should only be added when the implementation actually
requires them.

Do not install libraries merely because they may be useful later.

------------------------------------------------------------------------

## 9. Project Structure

The intended source layout begins with:

``` text
SocialFlow/
├── src/
│   └── socialflow/
├── tests/
├── ARCHITECTURE.md
├── DECISIONS.md
├── DEVELOPMENT.md
├── FEATURES.md
├── README.md
└── .gitignore
```

Additional directories should be introduced incrementally as
functionality is implemented.

See `ARCHITECTURE.md` for the architectural organization of application
code.

### Code Organization

SocialFlow favors a predictable, hierarchical project structure with
small, focused modules and classes.

Code should be placed according to its responsibility so developers can
quickly determine where functionality belongs.

Development should favor:

-   meaningful file, class, method, and directory names;
-   small modules with clear responsibilities;
-   reusable components for genuinely shared behavior;
-   deliberate object-oriented design where it improves structure and
    testability;
-   separation of UI, application logic, integrations, persistence, and
    shared services.

Avoid generic catch-all modules such as `utils.py`, `helpers.py`, or
`misc.py` for unrelated functionality.

The full directory hierarchy should not be created in advance.
Directories and modules should be introduced incrementally as
implementation requires them. ---

## 10. Running SocialFlow

With the virtual environment activated and dependencies installed, run
SocialFlow from the project root with:

``` bash
python -m socialflow
```

The module entry point is `src/socialflow/__main__.py`. Application
creation and startup behavior live in `src/socialflow/main.py`.

------------------------------------------------------------------------

## 11. Testing

Testing is part of normal SocialFlow development.

The primary test framework is:

``` text
pytest
```

Qt-specific tests may use:

``` text
pytest-qt
```

The testing infrastructure is installed and active.

Run the complete test suite with:

``` bash
python -m pytest
```

Run a single test file by passing its path, for example:

``` bash
python -m pytest tests/ui/test_main_window.py
```

Run multiple focused test files by passing each path to pytest.

A feature is not considered complete until its relevant tests pass.

Bug fixes should include regression tests where practical.

------------------------------------------------------------------------

## 12. External API Testing

The normal automated test suite should not require live Facebook,
Instagram, or WordPress services.

Platform integrations should be designed so external communication can
be mocked, faked, or otherwise isolated during normal automated testing.

Real external API verification may be performed separately when
required.

Tests must never contain production credentials or committed access
tokens.

------------------------------------------------------------------------

## 13. Quality Checks

The project will establish automated quality checks as the Python
application foundation is created.

The final development workflow should include appropriate checks for:

-   automated tests;
-   code formatting;
-   linting;
-   type checking where adopted.

The exact tools and commands will be documented only after they are
selected and configured.

A quality tool should not be added without a clear project purpose.

------------------------------------------------------------------------

## 14. Standard Feature Workflow

Development should normally follow this sequence:

1.  Confirm the requirement in `FEATURES.md`.
2.  Review relevant architecture and decisions.
3.  Design the smallest appropriate implementation.
4.  Implement the feature.
5.  Add or update automated tests.
6.  Run the relevant tests.
7.  Fix failures.
8.  Run the required broader quality checks.
9.  Review the changes.
10. Update project documentation when necessary.
11. Commit the completed logical change.
12. Push it to GitHub.

Do not mark a feature complete simply because it appears to work
manually.

------------------------------------------------------------------------

## 15. Git Workflow

Before committing a completed development section, inspect the working
tree:

``` bash
git status
```

Review the changes when appropriate:

``` bash
git diff
```

Stage only the intended files.

Example:

``` bash
git add <files>
```

Commit with a concise message describing the completed logical change:

``` bash
git commit -m "<commit message>"
```

Push the current tracked branch:

``` bash
git push
```

The AI assistant should provide an appropriate commit message after the
feature or logical development section has been implemented and
verified.

The user normally performs the commit and push.

------------------------------------------------------------------------

## 16. Commit Guidelines

Commits should represent meaningful, verified units of work.

Prefer messages that describe the purpose of the change.

Examples of the intended style:

``` text
docs: add initial project architecture
feat: add application startup window
test: add image validation tests
fix: preserve Croatian characters in post content
```

Do not create commits solely to hide unfinished or failing work.

Do not push knowingly failing completed-feature commits to `main`.

------------------------------------------------------------------------

## 17. Documentation Workflow

The primary project documentation has separate responsibilities.

### `README.md`

Public introduction to SocialFlow.

### `FEATURES.md`

Functional requirements and project roadmap.

### `ARCHITECTURE.md`

Current technical architecture.

### `DECISIONS.md`

Significant technical and development decisions and their reasoning.

### `DEVELOPMENT.md`

Developer setup, commands, testing, and workflow.

### `AGENTS.md`

Local instructions for AI coding agents.

`AGENTS.md` is intentionally not committed to the public repository.

Documentation should be updated when implementation changes make
existing documentation inaccurate.

------------------------------------------------------------------------

## 18. Secrets and Credentials

Never commit sensitive information.

Examples include:

-   Facebook/Meta credentials;
-   Instagram/Meta credentials;
-   WordPress credentials;
-   OAuth tokens;
-   access tokens;
-   refresh tokens;
-   API secrets;
-   email-service passwords or tokens;
-   private keys.

Secrets must not be placed directly in source code.

They must also be excluded from:

-   tests committed to Git;
-   application logs;
-   error-report emails;
-   screenshots or sample configuration committed to the repository.

Use placeholders in documentation and example configuration.

------------------------------------------------------------------------

## 19. Local Runtime Data

Runtime data should not be committed.

Examples include:

-   SQLite application databases;
-   logs;
-   caches;
-   temporary files;
-   downloaded content;
-   generated image variants;
-   authentication tokens;
-   local user configuration where inappropriate for source control.

Relevant paths and extensions should be protected through `.gitignore`.

------------------------------------------------------------------------

## 20. Unicode and File Encoding

Project text files should use UTF-8.

SocialFlow must correctly handle Croatian and English content.

Important Croatian characters include:

``` text
č ć ž š đ
Č Ć Ž Š Đ
```

Developers should avoid conversions or file encodings that can corrupt
Unicode content.

Tests should eventually cover Unicode preservation through important
application workflows.

------------------------------------------------------------------------

## 21. Linux Development

Linux Mint is the initial development platform.

Current project location on the primary development machine:

``` text
~/Software/SocialFlow
```

This path is machine-specific and must not be assumed by application
code.

Linux-specific setup, packaging, and verification commands will be added
as those parts of the project are implemented.

------------------------------------------------------------------------

## 22. Windows Development

Windows is a required target platform.

Windows-specific development and testing instructions will be added when
the Windows environment is established.

Application code must avoid assumptions about:

-   Unix-only filesystem paths;
-   Linux-only commands;
-   path separators;
-   Linux-specific credential storage;
-   Linux-specific process behavior.

Use cross-platform Python and Qt facilities where practical.

------------------------------------------------------------------------

## 23. Database Development

SocialFlow will use SQLite with SQLAlchemy.

The database layer has not yet been implemented.

When persistence work begins, this document should be expanded with:

-   database initialization commands;
-   schema-management strategy;
-   migration commands if migrations are adopted;
-   development reset procedures where safe;
-   testing database behavior.

Production/user data must not be committed to Git.

------------------------------------------------------------------------

## 24. Logging During Development

Application logging will be centralized when implemented.

Development logs should provide enough information to diagnose failures
without exposing secrets.

Runtime log files are not source files and should remain outside Git.

------------------------------------------------------------------------

## 25. Error Reporting During Development

Production error email reporting will be implemented as a dedicated
application service.

Development and automated tests must not accidentally send real
production error emails.

Testing should use a fake, mock, or otherwise controlled delivery
mechanism.

------------------------------------------------------------------------

## 26. Building and Packaging

The final packaging technology has not yet been selected.

SocialFlow must eventually produce distributable applications for:

-   Linux;
-   Windows.

The packaging decision will be made after the application foundation and
core dependencies are sufficiently stable.

Once selected, exact build commands and release procedures will be
documented here.

------------------------------------------------------------------------

## 27. Release Verification

Before a production release, development documentation should provide a
repeatable verification process covering at least:

-   complete automated tests;
-   formatting/linting/type checks that have been adopted;
-   Linux build;
-   Windows build;
-   application startup;
-   database behavior;
-   image processing;
-   authentication handling;
-   supported platform integrations;
-   logging;
-   production error reporting;
-   credential/security review.

Release procedures will be expanded as SocialFlow approaches its first
distributable version.

------------------------------------------------------------------------

## 28. Keep This Document Practical

`DEVELOPMENT.md` should describe commands and workflows that actually
exist.

When tools or commands are introduced:

1.  Configure them in the project.
2.  Verify that they work.
3.  Add their exact usage here.

Avoid documenting speculative commands or development processes that
have not yet been established.
