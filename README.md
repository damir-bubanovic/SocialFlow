# SocialFlow

SocialFlow is a cross-platform desktop application for creating,
managing, publishing, and updating content across multiple online
platforms from a single interface.

## Supported Platforms

SocialFlow is being designed to integrate with:

-   Facebook
-   Instagram
-   WordPress

External integrations will use the officially supported APIs and
capabilities available for each platform.

## Features

SocialFlow is planned to provide:

-   Create and edit posts from one desktop application.
-   Publish content to one or multiple platforms.
-   Work with text and images.
-   Prepare images for platform-specific requirements.
-   Retrieve and manage supported tags and metadata.
-   Display the latest posts from connected pages, accounts, and
    websites.
-   Edit and update existing posts where supported by the destination
    platform.
-   Handle publishing results independently for each platform.
-   Support Croatian and English content with language identification.
-   Automatically detect Croatian or English content where reliable,
    with manual language selection when needed.
-   Preserve Unicode characters, including Croatian characters such as
    č, ć, ž, š, and đ.
-   Maintain application logs and production error reporting.
-   Run on both Linux and Windows.

## Technology

Current implemented dependencies:

-   Python 3.12+
-   PySide6 / Qt 6
-   Pillow
-   pytest
-   pytest-qt
-   keyring (OS-backed credential storage)

SQLite/SQLAlchemy and HTTPX are architectural preferences for future work,
not current runtime dependencies. WordPress REST communication currently uses
Python standard-library `urllib` over HTTPS.

## Development Status

SocialFlow is under active development. The current Python/PySide6 desktop
application has Posts and Accounts pages, persistent local accounts and
publication history, a common post editor, Croatian/English paragraph-language
indicators, destination selection, image attachment/preview/preparation, and
application-level tag selection services.

**WordPress publishing is implemented and wired into the running application.**
For a configured WordPress account, `MainContent` constructs a
`WordPressPublisher` through the account-aware `PublisherRouter`. The publisher
uses the account's HTTPS site URL and username, retrieves its application
password from the OS keyring, and creates published posts through the WordPress
REST API. Prepared images are uploaded to WordPress media, and their returned
URLs and IDs are inserted as Gutenberg image blocks in the post content.
WordPress publishing resolves selected tags to remote WordPress tag IDs and assigns them during post creation. Missing tags require explicit user confirmation before creation; ambiguous matches and failures prevent publishing.

WordPress connection verification also works through an authenticated REST API
endpoint and runs in a Qt background worker. The UI prevents overlapping
verification attempts and defers application closing until the worker finishes.

Image preparation preserves source files, avoids overwriting reserved output
names, and removes temporary outputs after publishing. On preparation failure,
cleanup attempts all partial outputs; deletion errors are logged without masking
the original processing error. On WordPress media-upload failure, the publisher
attempts to delete previously uploaded media in reverse order and logs any
failed deletion without hiding the upload error. **If post creation fails after
uploads succeed, uploaded media is retained**; it is not rolled back by the
current implementation.

Facebook and Instagram still use `UnconfiguredPublisher` and report failure
rather than pretending to publish. The application supports independent
per-account publishing results and local history of successful publisher calls.
History is stored in UTF-8 `publications.json`, including a stable publication
ID, account, text, language, and timestamp. Images and tags are not yet
serialized into publication history. Selecting a history entry reloads the
available post data into the editor; it does not update the remote post.

The runtime uses `RoutingTagProvider`: WordPress accounts use an authenticated
`WordPressTagProvider` for listing and creating remote tags, while other
destinations fall back to `NullTagProvider`. Selected WordPress tags are resolved and assigned during publishing. The Posts
page checks for missing tags before publishing, asks for confirmation, and
creates approved missing tags through background Qt workers. Unsupported
destinations still use the null provider.

**Remote WordPress post retrieval, text editing, and tag editing are implemented.** The Posts
page retrieves recent remote posts for the selected WordPress account in a
background Qt worker and displays them separately from local publication
history. Selecting a remote post opens its text content and assigned WordPress tags in a dedicated editor; tag names are shown as checkboxes while numeric IDs remain internal. Saving invokes the authenticated REST update operation in another worker.
Successful updates refresh the remote list. Failed updates report an error and
restore editing without discarding the user's changes. Account-switch and
shutdown guards prevent stale worker results from affecting another account.
Remote tag-only, text-only, and combined text/tag updates are supported; remote image and other metadata editing are not.

Facebook/Instagram API publishing, email error reporting, and release packaging
remain future work.
Publishing now runs in a Qt background worker, with per-account progress,
independent outcomes, guarded concurrent starts, and deferred window closing.
After partial failure, **Retry Failed** targets only failed accounts; editing the
draft or changing its accounts, images, language, or tags invalidates that retry.
A failed publisher does not prevent later accounts from being attempted.

**Testing checkpoint:** The developer reported **1,188 passing tests** after
Phase 21.9.30 remote-tag-editing regression coverage (October 2026).
This is a reported full-suite result, not a new test run performed while
updating these documents. Tests use mocked/fake network dependencies and do
**not** establish successful publishing, retrieval, tag creation, or editing
against a live WordPress site. Live API, Linux/Windows packaging, and platform
credential-backend checks remain outstanding.

## Documentation

Detailed project documentation is available in:

-   [`FEATURES.md`](FEATURES.md) --- feature requirements and project
    roadmap.
-   [`ARCHITECTURE.md`](ARCHITECTURE.md) --- current technical
    architecture.
-   [`DECISIONS.md`](DECISIONS.md) --- significant technical decisions
    and their reasoning.
-   [`DEVELOPMENT.md`](DEVELOPMENT.md) --- development environment,
    workflow, testing, and setup instructions.

## Operating Systems

Target operating systems:

-   Linux
-   Windows

Linux Mint is currently used as the primary development environment.

## Project Scope

SocialFlow focuses on providing a unified desktop workflow for managing
content across supported publishing platforms.

Platform-specific functionality depends on the capabilities and
restrictions of the official APIs provided by Facebook/Instagram and
WordPress.

## Publishing Reliability and Diagnostics

- Publishing results classify failures as **transient**, **permanent**, or
  **unknown** for user-facing status messages. This classification does not
  automatically determine retry eligibility.
- The publishing service logs account/destination and exception type rather
  than the raw publishing exception message or post text.
- Persistent UTF-8 rotating logs are initialized at application startup under
  the platform-specific application data directory in `logs/socialflow.log`.
  Rotation is configured at 2 MiB with three backups.
- Logging setup filesystem errors are handled with a generic warning; main
  window construction failures are logged and re-raised internally, while the
  top-level `run()` function returns exit code `1` on startup creation/display
  failure. A main-window construction error may currently produce two log
  entries (a known review item).
- Production-wide exception capture, email notifications, and validation of
  real platform integrations remain pending.

## Current WordPress Capability Boundaries

| Capability | Status |
| --- | --- |
| Connection verification | Implemented; background Qt worker |
| Create text/image posts | Implemented; live-site validation pending |
| Retrieve and create remote tags | Implemented; live-site validation pending |
| Assign tags to published posts | Implemented through remote tag ID resolution; live-site validation pending |
| Retrieve recent remote posts | Implemented; background Qt worker |
| Edit existing remote post text and tag assignments | Implemented; background Qt workers |
| Edit remote images or other metadata | Not implemented |
| Facebook / Instagram API publishing | Not implemented |

Local publication history and the separate remote WordPress post list must not
be confused: loading a local history entry into the composer does not update a
remote post.

## WordPress Tag Confirmation and Publishing Reliability (Phases 21.2–21.9.21)

For selected WordPress accounts, the Posts page prepares a tag-creation plan
before publishing. Existing tags are resolved using shared Unicode-aware name
normalization. Missing tags require an explicit confirmation dialog; declined
creation or lookup/creation errors cancel the pending publish. Approved missing
tags are created by Qt workers, and the publisher resolves remote IDs for the
post-creation request. Duplicate and ambiguous matches are guarded. These
operations have automated tests but have not been verified against a live site.

Publishing runs in a Qt worker/controller with safe user-facing error messages,
traceback logging for unexpected worker exceptions, progress reporting,
selective retry for failed accounts, and lifecycle cleanup. Regression tests
cover restarting after failures, clearing stale retry state, successful
subsequent publishing, and main-window closing after successful or failed
publishing (including repeated close requests). The **historical 1081-test checkpoint**
is developer-reported; this documentation update did not run pytest.

## WordPress Remote Tag Editing (Phase 21.9.30)

Remote WordPress posts now retain assigned tag IDs from the REST response.
The editor loads the active WordPress account's tag catalog asynchronously and
displays tag **names** in a checkbox list. IDs remain the source of truth when
saving. Assigned tags missing from the catalog are shown as **Unknown WordPress
tag (ID N)** and remain removable.

Text-only saves omit the optional `tags` update field; changing tag membership
sends the selected numeric IDs (including an empty list to clear all tags).
The remote-post update uses the selected account's credentials and post ID.
The page clears stale tag names on account changes and ignores outdated
background results. Failed saves restore the editing controls without
discarding the unsaved selection.

This selector is separate from the tag selector used when publishing new
posts. Live WordPress validation, remote media/other metadata editing, and
Facebook/Instagram integrations are still pending.

**Latest developer-reported test result:** 1,188 passing tests after Phase
21.9.30. This is not a fresh test run performed during documentation editing.