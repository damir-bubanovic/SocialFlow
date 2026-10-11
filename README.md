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
WordPress tags are explicitly rejected until remote tag integration exists.

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

The current tag provider is `NullTagProvider`; remote tag retrieval and creation
are not implemented. Remote post retrieval and updates, Facebook/Instagram API
publishing, centralized production logging, email error reporting, and release
packaging remain future work. Publishing currently runs synchronously from the
Posts page; unlike WordPress connection verification, it has not yet been moved
to a background worker.

**Testing checkpoint:** the developer reported **662 passing automated tests**
after the WordPress image-publishing and cleanup regression work. The tests use
mocked/fake network dependencies and do **not** establish successful publishing
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