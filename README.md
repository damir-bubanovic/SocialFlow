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

SQLite/SQLAlchemy and HTTPX remain planned for the broader relational
persistence and live platform-integration work.

## Development Status

SocialFlow is currently under active development.

The Python/PySide6 application foundation and the local publishing-history
workflow are implemented. SocialFlow currently provides `Posts` and `Accounts`
navigation, local account add/list/update/remove workflows, UTF-8 JSON
persistence for configured accounts, manual Croatian/English language
selection, account-specific publishing selection, image attachment and preview,
destination-specific image preparation, and a tested tag-selection/tag-service
workflow.

Successful local publish operations can now be recorded as `Publication`
objects with stable UUID-backed `PublicationId` values and timestamps. Runtime
publication history is stored in `publications.json`, recent history can be
listed for the first selected account (up to five by default), and selecting a
historical publication loads its post back into the editor. The editor loading
path supports text, language, images, and tags when those values are present in
the `Publication` object. The current JSON publication serializer persists the
publication ID, account, text, language, and timestamp; persisted images and
tags are not yet included in that format. Legacy publication records without an
ID are migrated once and rewritten with a generated stable ID.

Posts can carry text, images, language, and tags. Images are validated and
prepared per destination before publishing, with temporary prepared files
cleaned up afterward. Tags can be displayed, selected, cleared, created, and
merged across selected accounts through application-level tag services.
Publishing results are reported independently per account, including partial
success/failure cases. The current runtime still uses `NullPublisher` and
`NullTagProvider`; live Facebook, Instagram, and WordPress API integrations and
remote post updates have not yet been implemented. The current automated
baseline is 350 passing tests. Additional quality tooling will be introduced as
development requires it.

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