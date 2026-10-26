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

The current runtime dependencies are PySide6, Pillow, and keyring. The current
development dependencies are pytest and pytest-qt. JSON account persistence
uses Python's standard library and therefore adds no additional runtime
dependency.

Additional dependencies should only be added when implementation
requires them.

------------------------------------------------------------------------

## 8. Core and Planned Dependencies

Current technologies:

-   PySide6 / Qt 6 --- desktop user interface
-   Pillow --- image processing
-   keyring --- OS-backed WordPress application-password storage
-   Python `urllib.request` --- WordPress HTTPS verification (standard library)
-   pytest --- automated testing
-   pytest-qt --- Qt testing where appropriate

Planned when implementation requires them:

-   SQLAlchemy --- broader relational database access
-   HTTPX --- live HTTP/API communication

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

Configured accounts are currently stored outside the repository as
`accounts.json` in the platform application-data directory:

``` text
Linux:   $XDG_DATA_HOME/socialflow/accounts.json
         or ~/.local/share/socialflow/accounts.json
Windows: %LOCALAPPDATA%\SocialFlow\accounts.json
```

Tests that construct `MainContent` isolate `XDG_DATA_HOME` to a pytest temporary
directory so automated tests do not touch a developer's real account data.

Examples of runtime data include:

-   SQLite application databases;
-   logs;
-   caches;
-   temporary files;
-   downloaded content;
-   `publications.json` local publication history;
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

Tests currently cover Unicode/Croatian preservation through account serialization and JSON persistence. Additional future workflows must add equivalent coverage as they are implemented.

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

The current persistence implementation uses JSON-backed account and publication
repositories described in the Local Runtime Data section. They intentionally
require no database setup or general migration command. `JsonPublicationRepository`
contains a focused compatibility migration that assigns and persists IDs for
legacy publication records that predate stable `PublicationId` values.

SQLite with SQLAlchemy remains planned for the broader relational data layer,
but that database layer has not yet been implemented or added as a dependency.
When it is introduced, document:

-   database initialization commands;
-   schema-management strategy;
-   migration commands if migrations are adopted;
-   development reset procedures where safe;
-   testing database behavior.

Production/user data must not be committed to Git.

------------------------------------------------------------------------

## 24. Logging During Development

Application logging is configured in `src/socialflow/infrastructure/logging_config.py`
and initialized by `create_application()` in `src/socialflow/main.py`.
Logs are UTF-8 rotating files in `data_directory() / "logs" / "socialflow.log"`
(2 MiB per file, three backups). The data directory follows the existing
platform-specific Linux/Windows path logic. Startup tolerates filesystem
`OSError` from log setup with a generic warning. Never commit runtime logs.

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

## 28. Current Implementation Checkpoint

The latest user-reported green project checkpoint includes WordPress connection
configuration persistence, secure application-password storage and cleanup,
authenticated REST API connection verification, background Qt verification, and
responsive main-window shutdown, in addition to the earlier features.

The earlier checkpoint includes account CRUD/persistence, the
post editor, account-targeted publishing orchestration, image selection and
preview, destination-specific image preparation with cleanup, the generic tag
selection/retrieval/creation workflow, and local publication history with stable
identity, rule-based paragraph/post language detection, mixed-language UI
indicators, and publishing failure reporting. Only publishers that return
successfully can produce local publication records; live adapters are absent.
Successful publications can be persisted to `publications.json`,
listed by account, selected from the recent-post UI, and loaded back into the
editor. Legacy history without IDs is migrated in place. The developer reported **1081 passing tests** at the historical Phase 21.9.21 publishing-recovery checkpoint; the latest Phase 21.9.30 result is **1188 passing**. This is not a live API test.

Useful focused test commands include:

``` bash
pytest tests/ui/test_tag_selector.py
pytest tests/ui/test_post_editor.py tests/ui/test_posts_page.py
pytest tests/application/test_image_preparation_service.py
pytest tests/application/test_list_recent_publications.py
pytest tests/infrastructure/test_json_publication_repository.py
pytest tests/ui/test_recent_posts_list.py tests/ui/test_recent_posts_panel.py
pytest
```

The application can be launched from the activated project environment with:

``` bash
python -m socialflow
```

Live Facebook/Instagram integrations and live WordPress verification against
a real site remain outstanding. WordPress REST API connection verification and
text/image publishing are implemented. The current runtime composes
`WordPressPublisher` for WordPress accounts, `UnconfiguredPublisher` for
Facebook/Instagram, and `RoutingTagProvider` with a WordPress tag provider and null fallback. Unconfigured publishing
must fail visibly and must not be recorded as a successful publication. Platform API work should begin by implementing
adapters behind the existing application contracts rather than placing API
logic in UI classes. Local publication history
must not be described as remote synchronization: remote recent-post retrieval and text editing now exist for WordPress only, but they remain separate from local publication history.
The current publication JSON serializer also does not yet persist images or tags.

------------------------------------------------------------------------

## 29. Current Publishing Safety Regression Checks

Use these focused tests after changes to publisher configuration, publishing
status, or the Posts UI:

```bash
python -m pytest tests/application/test_unconfigured_publisher.py -v
python -m pytest tests/application/test_publish_post.py -v
python -m pytest tests/ui/test_publish_status.py tests/ui/test_posts_page.py tests/ui/test_main_content.py -v
python -m pytest -q
```

The latest developer-reported full-suite checkpoint is 1188 passing tests after Phase 21.9.30. This is not evidence of successful publishing against a live
WordPress server. Never substitute
`NullPublisher` in the production composition root to simulate success.

------------------------------------------------------------------------

## 30. WordPress Connection and Shutdown Regression Checks

WordPress account configuration (`site_url`, `username`) is persisted in account
JSON; application passwords are stored through the operating-system keyring.
The current verifier uses HTTPS `urllib` and the WordPress REST API current-user
endpoint. Its 10-second default socket timeout is not a guaranteed whole-request
deadline. WordPress text/image publishing is implemented through a separate REST client and publisher; live-server validation remains pending.

Run focused tests after changing WordPress connection settings, credentials,
verification, worker/controller signals, or shutdown:

```bash
python -m pytest tests/domain/connections -v
python -m pytest tests/application/test_save_wordpress_credentials.py tests/application/test_delete_wordpress_credentials.py -v
python -m pytest tests/infrastructure/wordpress -v
python -m pytest tests/ui/test_account_form.py tests/ui/test_accounts_page.py -v
python -m pytest tests/ui/test_wordpress_verification_worker.py tests/ui/test_wordpress_verification_controller.py -v
python -m pytest tests/ui/test_main_content.py tests/ui/test_main_window.py -v
python -m pytest -q
git diff --check
```

The normal test suite uses fake or mocked HTTP and credential dependencies; it
must not require a live WordPress site or real application passwords. On Linux
and Windows, separately verify that the configured OS keyring backend works.
Do not commit `AGENTS.md`, runtime credentials, or other local secrets.

------------------------------------------------------------------------

## 30A. WordPress Publishing and Media Cleanup Regression Checks

The production composition root (`src/socialflow/ui/main_content.py`) routes
WordPress accounts to `WordPressPublisher` with `UrllibWordPressPostClient` and
the shared OS keyring store. Facebook and Instagram still use
`UnconfiguredPublisher`. WordPress post creation supports text and prepared
images; media uploads generate Gutenberg image blocks. WordPress tag listing, confirmed creation of missing tags, and new-post tag assignment are implemented; remote-post retrieval and text editing use separate services. Editing existing remote tag assignments is implemented; remote images and other metadata remain pending.

After changing WordPress publishing, media handling, image preparation, or
publisher routing, run:

```bash
python -m pytest -q tests/infrastructure/wordpress/
python -m pytest -q tests/application/test_image_preparation_service.py
python -m pytest -q tests/application/test_publish_post.py
python -m pytest -q tests/ui/test_main_content.py
python -m pytest -q
git diff --check
```

Regression coverage includes preserving the original image-processing error
when partial-file deletion fails, continuing cleanup of remaining files,
reverse-order deletion of previously uploaded WordPress media on upload failure,
and logging media deletion failures. Post-creation failures do not trigger media
rollback. Do not use real credentials or a live WordPress site in the normal
pytest suite; live integration testing is a separate manual/controlled step.

**Historical test reporting:** The developer reported 1081 passing tests after Phase 21.9.21.
Documentation maintenance does not itself execute the full test suite.

WordPress publishing is invoked through the Posts page's Qt background
`PublishingController`/`PublishingWorker`. WordPress connection verification
uses its own worker/controller. The main window defers closing while either
operation is active.

------------------------------------------------------------------------

## 31. Keep This Document Practical

`DEVELOPMENT.md` should describe commands and workflows that actually
exist.

When tools or commands are introduced:

1.  Configure them in the project.
2.  Verify that they work.
3.  Add their exact usage here.

Avoid documenting speculative commands or development processes that
have not yet been established.

## 32. Background Publishing and Retry Regression Checks

After changes to publishing concurrency, progress, retry state, or worker
shutdown, run:

```bash
python -m pytest -q tests/application/test_build_retry_request.py
python -m pytest -q tests/application/test_publish_post.py
python -m pytest -q tests/ui/test_publishing_worker.py tests/ui/test_publishing_controller.py
python -m pytest -q tests/ui/test_posts_page.py tests/ui/test_main_window.py
python -m pytest -q
```

The retry request includes failed accounts only; changing text, publishing
language, accounts, images, or tags invalidates retry state. Background
publishing must not block the UI, overlap with itself, or cause the main
window to close before worker cleanup.

## 33. Publishing Diagnostics and Startup Regression Checks

After changes to classification, status formatting, persistent logging,
or startup behavior, run:

```bash
python -m pytest -q tests/application/test_error_classifier.py
python -m pytest -q tests/ui/test_publishing_error_formatter.py tests/ui/test_publish_status.py
python -m pytest -q tests/infrastructure/test_logging_config.py tests/test_main.py
python -m pytest -q
git diff --check
```

The startup tests cover log file creation, safe handling of log-directory
`OSError`, safe constructor diagnostics, and nonzero return values from
`run()` on startup failures. The logging tests cover repeated initialization
and switching directories. Publishing logs intentionally omit post text and
raw publishing exception messages.

**Open review items:** avoid duplicate startup log entries, examine resource
cleanup on startup failure, and ensure useful fallback diagnostics if file
logging cannot initialize. Production email reporting is not implemented.

## 33A. Phase 19 WordPress Remote Post Regression Checks

The application composes WordPress tag listing/creation, remote-post retrieval,
and remote-post text/tag updating in `src/socialflow/ui/main_content.py`.
Remote posts appear in a dedicated panel and are not the same records as
locally persisted publication history.

Run focused tests after changing WordPress post retrieval, editing, REST
adapters, or the Posts page:

```bash
python -m pytest tests/infrastructure/wordpress/test_urllib_wordpress_post_client.py -q
python -m pytest tests/infrastructure/wordpress/test_wordpress_post_retriever.py tests/infrastructure/wordpress/test_wordpress_post_provider.py tests/infrastructure/wordpress/test_wordpress_post_updater.py -q
python -m pytest tests/application/test_list_remote_posts.py tests/application/publishing/test_update_remote_post.py -q
python -m pytest tests/ui/test_remote_post_loading_worker.py tests/ui/test_remote_post_loading_controller.py -q
python -m pytest tests/ui/test_remote_post_updating_worker.py tests/ui/test_remote_post_updating_controller.py -q
python -m pytest tests/ui/test_remote_posts_panel.py tests/ui/test_remote_posts_panel_editing.py tests/ui/test_posts_page_remote_post_editing.py -q
python -m pytest -q
```

For WordPress tags, run:

```bash
python -m pytest tests/infrastructure/wordpress/test_wordpress_tag_provider.py tests/infrastructure/wordpress/test_wordpress_tag_client.py tests/infrastructure/wordpress/test_urllib_wordpress_tag_client.py -q
python -m pytest tests/application/test_routing_tag_provider.py tests/application/test_tag_services.py -q
```

The latest developer-reported full-suite checkpoint is **1188 passing tests** after Phase 21.9.30. These documents
were updated from the project ZIP and were not accompanied by a fresh test
execution.

### Manual smoke-test scope

With a controlled WordPress test account, verify authenticated remote-post
listing, account switching, selecting and editing text, successful save and
refresh, and a failed save that preserves the editor text. Verify that a
different WordPress account cannot update a post from an earlier selection.
Do not use production credentials in automated tests.

### Git documentation checkpoint

Keep `AGENTS.md` local and unstaged. After replacing the five public Markdown
files, review the diff before committing:

```bash
git diff --check
git diff -- README.md FEATURES.md ARCHITECTURE.md DECISIONS.md DEVELOPMENT.md
```

Commit only with explicit approval.

## 34. WordPress Tag Workflow Regression Checks (Phases 21.2–21.9.14)

WordPress publishing now resolves selected tags to remote IDs. Missing tags
are prepared and explicitly confirmed before creation. The UI coordinates
preparation, confirmation, creation, and publishing with separate Qt workers.
Run focused checks after changing the workflow:

```bash
python -m pytest tests/infrastructure/wordpress/test_wordpress_tag_resolver.py -v
python -m pytest tests/infrastructure/wordpress/test_wordpress_tag_name_normalizer.py -v
python -m pytest tests/ui/test_wordpress_tag_workflow.py -v
python -m pytest tests/ui/test_wordpress_tag_preparation_controller.py -v
python -m pytest tests/ui/test_wordpress_tag_creation_controller.py -v
python -m pytest tests/infrastructure/wordpress/test_wordpress_publisher.py -v
python -m pytest -q
```

These tests use controlled fakes/mocks; they do not prove live WordPress tag
creation or assignment.

## 35. Publishing Recovery and Window Lifecycle Checks (Phases 21.9.15–21.9.21)

Publishing worker/controller tests cover safe unexpected-error handling,
traceback logging, thread cleanup, idempotent shutdown, and restart after
failure. Posts-page tests cover stale retry-state clearing and a successful
second attempt after a worker exception. Main-window tests cover closing
after publishing success or failure and repeated close requests.

```bash
python -m pytest tests/ui/test_publishing_worker.py -v
python -m pytest tests/ui/test_publishing_controller.py -v
python -m pytest tests/ui/test_posts_page.py -v
python -m pytest tests/ui/test_main_window.py -v
python -m pytest -q
git diff --check
```

**Historical checkpoint:** The developer reported **1081 passing tests** after
Phase 21.9.21 and pushed those changes; a later result is documented in Section 37. Documentation editing does not count as
a test run. Keep `AGENTS.md` local-only; never stage or push it.

## 36. Remote WordPress Tag Editing Regression Checks (Phases 21.9.22–21.9.30)

The current WordPress remote-post editor supports changing content and tag
assignments. `RemoteTagSelector` displays names; REST updates use numeric IDs.
Do not conflate this selector with the new-post publishing `TagSelector`.

Relevant code:

- `src/socialflow/domain/post/remote_tag.py`
- `src/socialflow/domain/post/remote_post.py`
- `src/socialflow/application/tags/remote_tag_provider.py`
- `src/socialflow/application/tags/list_remote_tags.py`
- `src/socialflow/infrastructure/wordpress/wordpress_tag_provider.py`
- `src/socialflow/infrastructure/wordpress/wordpress_post_updater.py`
- `src/socialflow/infrastructure/wordpress/urllib_wordpress_post_client.py`
- `src/socialflow/ui/posts/remote_tag_selector.py`
- `src/socialflow/ui/posts/remote_posts_panel.py`
- `src/socialflow/ui/posts/posts_page.py`
- `src/socialflow/ui/workers/remote_tag_loading_worker.py`
- `src/socialflow/ui/workers/remote_tag_loading_controller.py`

Relevant tests include:

- `tests/domain/test_remote_tag.py`
- `tests/application/tags/test_list_remote_tags.py`
- `tests/infrastructure/wordpress/test_wordpress_post_parser.py`
- `tests/infrastructure/wordpress/test_wordpress_post_updater.py`
- `tests/infrastructure/wordpress/test_wordpress_tag_provider.py`
- `tests/ui/test_remote_tag_selector.py`
- `tests/ui/test_remote_posts_panel_editing.py`
- `tests/ui/test_remote_tag_loading_controller.py`
- `tests/ui/test_posts_page.py`
- `tests/ui/test_posts_page_remote_post_editing.py`

Run targeted UI checks:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/ui/test_remote_tag_selector.py tests/ui/test_remote_posts_panel_editing.py tests/ui/test_remote_tag_loading_controller.py tests/ui/test_posts_page.py -q
```

Run the complete suite:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q
```

Regression scope: text-only saves omit tags; tag-only/combined saves send IDs;
empty tuples clear tags; checkbox changes update Save state; unknown IDs
remain selectable; delayed/failed catalog loads preserve assigned IDs;
account switching clears stale names; failed updates restore editing.

**Historical developer-reported full-suite checkpoint:** **1,188 passing tests**
after Phase 21.9.30, followed by a Git commit/push. The documentation update
did not rerun tests. Live WordPress integration remains unverified.

## 37. Qt Callback Lifecycle Regression Checks (Phases 21.9.31–21.9.59)

Later Phase 21.9 work strengthened asynchronous ownership and shutdown
behavior without expanding live platform coverage. In particular, the
publishing controller, WordPress tag-preparation controller, WordPress
tag-creation controller, and remote-post-loading controller forward worker
results/errors through guarded Qt slots. Do not reconnect worker signals
directly to public `.emit` methods: queued notifications could bypass
`_shutting_down` after a synchronous shutdown.

The three WordPress/remote loading controller suites each verify that
queued success and error signals are suppressed after shutdown and that
normal successful results precede `finished`. Publishing controller tests
also cover shutdown, callback ordering, request boundaries, and reuse.
PostsPage tests cover stale account callbacks, media-picker lifecycles,
publishing/retry state, and WordPress preparation cancellation/recovery.

Run these focused checks when changing those boundaries:

```bash
python -m pytest -q tests/ui/test_publishing_controller.py tests/ui/test_publishing_worker.py
python -m pytest -q tests/ui/test_wordpress_tag_preparation_controller.py tests/ui/test_wordpress_tag_creation_controller.py
python -m pytest -q tests/ui/test_remote_post_loading_controller.py tests/ui/test_posts_page.py
python -m pytest -q
git diff --check
```

For headless Linux Qt runs, prefix pytest with
`QT_QPA_PLATFORM=offscreen` if needed. Test doubles do not replace
live-site WordPress integration tests. Do not stage or commit `AGENTS.md`.

**Latest developer-reported full-suite checkpoint:** **1,478 tests passed** after Phase 21.9.59 (October 26, 2026). This documentation review did not execute pytest. The uploaded archive contains the three new remote-post-loading controller tests and the guarded-slot implementation.