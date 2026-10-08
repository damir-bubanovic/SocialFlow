# SocialFlow --- Architecture

## 1. Purpose

This document describes the technical architecture of SocialFlow.

SocialFlow is a cross-platform desktop application for creating,
managing, publishing, and updating content across multiple online
platforms.

Initial integrations:

-   Facebook
-   Instagram
-   WordPress

Target operating systems:

-   Linux
-   Windows

Architecture changes should be reflected in this document when they are
implemented or formally agreed upon.

------------------------------------------------------------------------

## 2. Technology Stack

### Language

-   Python 3.12+

Python is the primary application language.

### Desktop Framework

-   PySide6
-   Qt 6

PySide6 provides the cross-platform desktop user interface.

### Persistence

Current implementation:

-   UTF-8 JSON account storage through `JsonAccountRepository`
-   Python standard-library `json` and `pathlib`

Planned broader relational storage:

-   SQLite
-   SQLAlchemy

Application code accesses persistence through repository contracts rather than
spreading storage-specific logic throughout the UI or application services.

### HTTP Communication

-   HTTPX (planned; not yet a project dependency)

External API communication should be performed through dedicated
integration services.

### Image Processing

-   Pillow (implemented project dependency)

Image processing validates source attachments, reads image metadata, applies
destination profiles, resizes/converts when required, and generates temporary
platform-compatible prepared images without modifying source files.

### Testing

-   pytest
-   pytest-qt

Both are installed as development dependencies and are used for the
current application foundation.

Testing is part of normal feature development.

------------------------------------------------------------------------

## 3. Architectural Principles

SocialFlow should follow these principles:

1.  Keep the user interface separate from business logic.
2.  Keep platform-specific API behavior isolated from the rest of the
    application.
3.  Keep database access separate from UI code.
4.  Do not place authentication credentials directly in source code.
5.  Avoid unnecessary dependencies.
6.  Prefer clear and maintainable code over unnecessary abstraction.
7.  Design platform integrations so one platform can fail without
    corrupting operations for other platforms.
8.  Make important behavior testable without requiring live API calls.
9.  Preserve user content when remote operations fail.
10. Treat external APIs as unreliable boundaries.
11. Keep platform-specific restrictions out of the common domain logic
    where practical.
12. Do not introduce functionality outside the agreed project scope.
13. Prefer small, focused modules and classes over large multi-purpose
    files.
14. Use meaningful names that communicate a component's responsibility.
15. Organize code in a predictable hierarchy so developers can quickly
    locate the correct place for a change.
16. Favor reusable components when behavior is genuinely shared.
17. Apply object-oriented design where it improves responsibility
    boundaries, reuse, testability, and navigation without introducing
    unnecessary abstraction.

------------------------------------------------------------------------

## 4. High-Level Architecture

SocialFlow will use a layered architecture.

``` text
┌─────────────────────────────────────────────┐
│                 User Interface              │
│                PySide6 / Qt 6               │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│              Application Layer              │
│                                             │
│  Publishing / Posts / Accounts / Sync       │
└───────────────┬───────────────────┬─────────┘
                │                   │
        ┌───────▼────────┐   ┌──────▼─────────┐
        │ Platform Layer │   │ Persistence     │
        │                │   │ Layer           │
        │ Facebook       │   │                 │
        │ Instagram      │   │ SQLite          │
        │ WordPress      │   │ SQLAlchemy      │
        └───────┬────────┘   └────────────────┘
                │
        ┌───────▼────────┐
        │ External APIs  │
        └────────────────┘

Additional shared services:

- Image processing
- Language detection and identification
- Credential management
- Logging
- Error reporting
- Configuration
```

------------------------------------------------------------------------

## 5. Code Organization and Modularity

SocialFlow should have a predictable, hierarchical codebase inspired by
the navigability of well-structured application frameworks.

A developer should normally be able to determine where code belongs from
its responsibility.

Guidelines:

-   Prefer small, focused Python files.
-   Prefer classes and modules with one clear primary responsibility.
-   Split files when they begin coordinating unrelated responsibilities.
-   Use meaningful domain-oriented names for files, classes, methods,
    and directories.
-   Avoid generic dumping-ground modules such as `utils.py`,
    `helpers.py`, `misc.py`, or oversized `manager.py` files.
-   Shared behavior should live in reusable services or components
    rather than being duplicated.
-   Platform-specific behavior should remain close to its platform
    integration.
-   UI components should remain focused on presentation and interaction.
-   Business workflows should remain outside widgets.
-   Persistence behavior should remain outside UI and platform clients.
-   Do not create abstractions solely to increase the number of classes
    or layers.

There is no fixed maximum number of lines for a Python file. File size
should be treated as a design signal rather than an arbitrary rule. When
a file becomes difficult to navigate or contains multiple independent
responsibilities, it should be decomposed into meaningful components.

Object-oriented programming should be used deliberately. Classes are
appropriate for components with state, lifecycle, replaceable behavior,
or a clear domain/service responsibility. Simple stateless behavior does
not need to be forced into unnecessary class hierarchies.

The goal is a codebase with the kind of discoverability found in
structured frameworks such as Laravel, while remaining appropriate for a
Python/Qt desktop application.

------------------------------------------------------------------------

## 6. Presentation Layer

The presentation layer contains the PySide6 user interface.

Responsibilities include:

-   Application windows
-   Dialogs
-   Forms
-   Post editor
-   Image previews
-   Platform selection
-   Tag selection
-   Recent-post views
-   Settings
-   User-facing validation messages
-   Progress indicators
-   User-facing error messages

The UI should not directly communicate with Facebook, Instagram,
WordPress, SQLite, SMTP, or other infrastructure.

Instead, it should call application services.

This keeps the interface testable and prevents platform-specific logic
from becoming embedded in widgets.

------------------------------------------------------------------------

## 7. Application Layer

The application layer coordinates user actions and application
workflows.

Examples include:

-   Create a post.
-   Publish a post.
-   Publish to multiple destinations.
-   Retrieve recent posts.
-   Update an existing post.
-   Synchronize tags.
-   Synchronize remote content.
-   Process images before publishing.
-   Handle partial publishing failures.

The application layer should coordinate operations but should not
contain low-level HTTP, database, or GUI implementation details.

------------------------------------------------------------------------

## 8. Platform Integration Layer

Each external publishing platform must have its own integration
implementation.

Initial integrations:

``` text
Platform interface
       │
       ├── Facebook integration
       ├── Instagram integration
       └── WordPress integration
```

Application code should use a common interface where the platforms share
concepts.

Platform-specific differences must remain inside the relevant
integration where practical.

For example, SocialFlow must not assume that:

-   every platform supports identical tags;
-   every platform supports identical image formats;
-   every platform allows the same fields to be edited;
-   every platform uses the same authentication method;
-   every platform has the same publishing restrictions.

Platform capabilities should be represented explicitly rather than
hidden behind assumptions.

------------------------------------------------------------------------

## 9. Facebook Integration

Facebook communication will use supported Meta APIs.

The Facebook integration will eventually be responsible for supported
operations such as:

-   authentication;
-   page discovery;
-   post retrieval;
-   publishing;
-   updating supported content;
-   media handling;
-   authorization validation.

Exact functionality will be determined against the current Meta APIs
before implementation.

------------------------------------------------------------------------

## 10. Instagram Integration

Instagram communication will use supported Meta APIs.

The Instagram integration will eventually be responsible for supported
operations such as:

-   authentication;
-   account discovery;
-   content retrieval;
-   publishing;
-   updating supported content where permitted;
-   media handling;
-   authorization validation.

Exact functionality will be determined against the current Meta APIs
before implementation.

------------------------------------------------------------------------

## 11. WordPress Integration

WordPress communication will use the WordPress REST API.

The WordPress integration will eventually be responsible for supported
operations such as:

-   site authentication;
-   connection verification;
-   retrieving posts;
-   creating posts;
-   updating posts;
-   uploading media;
-   retrieving tags;
-   creating tags;
-   assigning tags and other supported metadata.

------------------------------------------------------------------------

## 12. Image Processing

Image manipulation will be handled independently from the platform
integrations.

The image service will be responsible for operations such as:

-   reading image metadata;
-   validating formats;
-   determining dimensions;
-   resizing;
-   converting formats;
-   compression;
-   generating destination-specific versions.

Original source images should not be modified unnecessarily.

A typical flow will be:

``` text
Original Image
      │
      ▼
Image Validation
      │
      ▼
Destination Requirements
      │
      ▼
Image Processing
      │
      ├── Facebook-compatible version
      ├── Instagram-compatible version
      └── WordPress-compatible version
```

Generated files should be treated as application runtime data rather
than source-controlled project files.

------------------------------------------------------------------------

## 13. Persistence Layer

Persistence is accessed through application-facing repository interfaces; UI
components do not read or write storage directly.

Two JSON-backed repositories are currently implemented.

`JsonAccountRepository` stores configured `Account` values in UTF-8
`accounts.json` and uses `AccountSerializer` to translate between domain objects
and storage data. It creates parent directories when saving and converts
malformed JSON, missing fields, or unknown destinations into
`AccountStorageError`.

`JsonPublicationRepository` stores successful local publication history in
UTF-8 `publications.json`. `PublicationSerializer` persists the stable
`PublicationId`, account name/destination, post text/language, and publication
timestamp. The repository returns recent publications for a requested account,
ordered newest first with a default limit of five. Legacy records without an
`id` are assigned a UUID once and immediately rewritten so the migrated
identity remains stable on later loads. Images and tags contained by an
in-memory `Post` are not yet serialized into publication history.

`AppPaths` and `data_directory()` isolate storage-location policy from the
repositories. Current application-data paths include:

``` text
Linux:   $XDG_DATA_HOME/socialflow/accounts.json
         $XDG_DATA_HOME/socialflow/publications.json
         $XDG_DATA_HOME/socialflow/prepared_images/
         or the equivalent paths under ~/.local/share/socialflow/
Windows: %LOCALAPPDATA%\SocialFlow\accounts.json
         %LOCALAPPDATA%\SocialFlow\publications.json
         %LOCALAPPDATA%\SocialFlow\prepared_images\
         with the existing home-directory fallback
```

SQLite with SQLAlchemy remains the accepted direction for the broader local
application database once richer relational persistence is required. The JSON
stores are the current implemented solution for the limited local record shapes
and do not store credentials or access tokens.

Sensitive authentication material must use secure credential storage where
practical and must not be placed in `accounts.json`.

------------------------------------------------------------------------

## 14. Publication Identity and Local History

A successful publication is represented by the immutable `Publication` domain
value. It contains:

-   a stable `PublicationId`;
-   the configured `Account` used for the publication;
-   the source `Post`;
-   the publication timestamp.

New publication IDs are created through the application-facing
`PublicationIdGenerator` contract. Production composition injects
`UuidPublicationIdGenerator`, while tests can inject deterministic generators.
This keeps UUID generation out of the domain model and prevents reconstructed
publications from silently receiving a different identity.

`PublishPost` records a `Publication` only after a publisher reports success and
only when publication persistence and a clock are configured. `SystemClock`
provides production timestamps. `ListRecentPublications` reads through the
`PublicationRepository` abstraction rather than coupling the UI to JSON.

`RecentPostsPanel` displays history for the first selected account. Selecting a
history entry emits the actual `Publication`; `PostsPage` then loads its `Post`
through `PostEditor.load_post()`. The editor can restore text, language, images,
and tags from that domain object. This is currently a local history/editing
workflow only: it does not yet update an existing remote platform post.

------------------------------------------------------------------------

## 15. Credential Management

SocialFlow will interact with services requiring authentication.

Potential sensitive information includes:

-   access tokens;
-   refresh tokens;
-   WordPress credentials or application passwords;
-   email-service credentials;
-   API secrets.

Rules:

1.  Credentials must never be hard-coded.
2.  Credentials must never be committed to Git.
3.  Credentials must not appear in normal logs.
4.  Credentials must not appear in error-report emails.
5.  Secure operating-system credential storage should be used where
    practical.
6.  Development secrets must remain outside tracked source files.

------------------------------------------------------------------------

## 16. Configuration

Application configuration should distinguish between:

### Non-sensitive configuration

Examples:

-   UI preferences;
-   application behavior;
-   configured error-report recipient;
-   synchronization settings.

### Sensitive configuration

Examples:

-   API secrets;
-   access tokens;
-   authentication credentials.

Sensitive and non-sensitive configuration should not automatically share
the same storage mechanism.

------------------------------------------------------------------------

## 17. Logging

SocialFlow will maintain application logs.

Logs should support diagnosis of:

-   application startup problems;
-   publishing failures;
-   synchronization failures;
-   API errors;
-   database errors;
-   image-processing failures;
-   unexpected exceptions.

Logs must avoid storing authentication credentials and other sensitive
data.

Logging should be centralized rather than implemented independently by
every UI component.

------------------------------------------------------------------------

## 18. Error Reporting

Unexpected or important production errors may trigger email
notifications.

The error-reporting system should:

1.  Capture the relevant exception.
2.  Log the complete locally appropriate diagnostic information.
3.  Sanitize sensitive information.
4.  Determine whether the error requires notification.
5.  Send an error report to the configured recipient.
6.  Avoid uncontrolled repeated notifications for identical failures.

Error reporting must not replace local logging.

------------------------------------------------------------------------

## 19. Background Operations

Network operations and expensive image processing must not freeze the
desktop interface.

Operations that may require background execution include:

-   publishing;
-   retrieving remote posts;
-   synchronizing metadata;
-   uploading images;
-   image processing;
-   authentication operations;
-   sending error reports.

Qt-compatible background execution mechanisms should be used where
necessary.

UI updates must remain safe with respect to Qt's threading rules.

The exact concurrency mechanism will be selected when background
processing is implemented.

------------------------------------------------------------------------

## 20. Failure Isolation

Publishing to multiple platforms must not be treated as one indivisible
remote transaction.

Example:

``` text
Publish
   │
   ├── Facebook  -> Success
   ├── Instagram -> Failure
   └── WordPress -> Success
```

SocialFlow should preserve and display the individual result for each
destination.

A failure on Instagram should not falsely report that Facebook and
WordPress also failed.

The application should retain enough information to let the user
understand what happened and take an appropriate next action.

------------------------------------------------------------------------

## 21. Unicode and Language Support

SocialFlow must use Unicode throughout the application.

Initial content languages:

-   Croatian
-   English

Croatian characters must be preserved correctly, including:

``` text
č ć ž š đ
Č Ć Ž Š Đ
```

Unicode handling applies to:

-   UI input;
-   database storage;
-   API requests;
-   API responses;
-   logs where appropriate;
-   post content;
-   tags;
-   filenames where supported.

UTF-8 should be used for project text files and external textual data
where applicable.

------------------------------------------------------------------------

## 22. Language Service

Language handling should be a dedicated application capability rather
than logic embedded directly in the post editor.

Initial supported content languages are:

-   Croatian (`HR`)
-   English (`EN`)

A language service may be responsible for:

-   detecting Croatian or English content where detection is
    sufficiently reliable;
-   representing uncertain detection;
-   supporting an explicit user override;
-   providing language information to the application/UI;
-   remaining independently testable.

Automatic detection must not be treated as infallible. Short captions,
hashtags, names, URLs, mixed-language text, and other ambiguous content
may not provide enough evidence for reliable classification.

The post editor should display an explicit language indicator such as
`HR` or `EN`. Color, typography, or other visual styling may reinforce
this state but must not be the only indication of language.

Language detection logic must not be implemented directly inside Qt
widgets. The UI should consume the result of the language capability
through the application/service boundary.

------------------------------------------------------------------------

## 23. Testing Architecture

Tests should be organized according to what they verify.

The test suite will eventually include:

-   unit tests;
-   application/service tests;
-   persistence tests;
-   platform integration tests using mocks/fakes;
-   image-processing tests;
-   selected UI tests;
-   regression tests.

Live external APIs should not be required for the normal automated test
suite.

Platform clients should therefore be designed so their external
communication can be replaced or mocked during testing.

Real API verification may be performed separately as integration testing
when appropriate.

------------------------------------------------------------------------

## 24. Development Workflow

Development should proceed incrementally.

For each logical feature or section:

``` text
Define requirement
       │
       ▼
Design implementation
       │
       ▼
Implement
       │
       ▼
Add/update tests
       │
       ▼
Run relevant tests
       │
       ▼
Run required quality checks
       │
       ▼
Review changes
       │
       ▼
Commit
       │
       ▼
Push to GitHub
```

A feature is not considered complete merely because the UI appears to
work.

Its relevant automated tests must pass.

Before major completed sections are pushed, the broader project test and
quality checks should also pass.

------------------------------------------------------------------------

## 25. Source Control

Git is used for source control.

GitHub hosts the remote repository.

Primary branch:

``` text
main
```

The repository should contain:

-   source code;
-   tests;
-   public project documentation;
-   dependency definitions;
-   build configuration.

The repository must not contain:

-   virtual environments;
-   credentials;
-   access tokens;
-   production databases;
-   runtime logs;
-   generated caches;
-   temporary media;
-   local IDE configuration;
-   local AI-agent instructions.

------------------------------------------------------------------------

## 26. Packaging

SocialFlow must eventually be distributed as a standalone desktop
application.

Target platforms:

### Linux

The final packaging method will be selected after the application
foundation is stable.

### Windows

The final packaging method will be selected after the application
foundation is stable.

Packaging should allow end users to run SocialFlow without manually
configuring the development environment.

Packaging technology will be evaluated separately rather than assumed at
this stage.

------------------------------------------------------------------------

## 27. Current Implemented Foundation

The implemented application spans domain, application, infrastructure, and UI
layers. The important current structure is:

``` text
src/socialflow/
├── application/
│   ├── accounts/       # repository contract + add/list/update/remove services
│   ├── images/         # validation, profiles, processing, preparation, cleanup
│   ├── publishing/     # prepared posts, router, publishers, PublishPost
│   └── tags/           # TagProvider, ListTags, CreateTag, NullTagProvider
├── domain/
│   ├── account/        # Account
│   ├── language/       # Language
│   ├── post/           # Post, ImageAttachment, Tag
│   └── publishing/     # PublishingDestination + PublishRequest
├── infrastructure/
│   ├── accounts/       # JSON repository, serializer, storage errors
│   └── storage/        # cross-platform data paths + prepared-image path
└── ui/
    ├── accounts/       # account form/list/status/page
    └── posts/          # editor, destinations, images, tags, language, status
```

Current responsibility boundaries include:

-   `MainContent` is the composition root for account services, publishing,
    image preparation, and the current null tag provider.
-   `Post` contains text, language, source `ImageAttachment` values, and `Tag`
    values. `Post.has_content()` treats text or images as publishable content.
-   `ImageSelector` validates local image selections, prevents duplicate paths,
    displays thumbnails, and supports removal/clearing.
-   `ImageProfileProvider` supplies destination profiles. `PublishPost` invokes
    `ImagePreparationService` per selected account destination and publishes a
    `PreparedPost` containing `PreparedImage` values. Prepared files are cleaned
    in a `finally` path after each publisher attempt.
-   `AppPaths.prepared_images_directory` keeps generated images under runtime
    application data rather than the repository.
-   `TagSelector` displays available tags, tracks selected tags, supports manual
    entry/removal/clearing, and emits `tag_created` only for genuinely new tags.
-   `PostsPage` reacts to account-selection changes, uses `ListTags` to merge
    unique tags across selected accounts, and uses `CreateTag` for each selected
    account. New-tag entry is disabled when no account is selected.
-   `TagProvider` is the platform-facing tag contract. `NullTagProvider` is the
    current runtime implementation; real destination-specific providers remain
    pending.
-   `DestinationSelector` selects configured `Account` objects. `PublishRequest`
    carries those accounts and `PublishPost` resolves publishers by destination.
-   Account CRUD remains isolated behind `AccountRepository`;
    `JsonAccountRepository` persists UTF-8 account data and account changes are
    propagated to the Posts page with Qt signals.
-   `MainContent` registers `UnconfiguredPublisher` for Facebook, Instagram,
    and WordPress. It raises `PublisherNotConfiguredError` rather than claiming
    external delivery. `NullPublisher` remains available as a test/no-op utility.
    Live authentication and API publishing are not implemented.
-   Manual Croatian/English publishing-language selection remains independent
    of automatic rule-based detection. `LanguageDetector`,
    `ParagraphLanguageDetector`, and `PostLanguageClassifier` support English,
    Croatian, mixed, and unknown classification. The editor highlights paragraphs
    and displays a labeled content-language indicator.

The current main window title is `SocialFlow` and its initial size is 1200 ×
800.

------------------------------------------------------------------------

## 28. Proposed Source Organization

The exact structure will evolve as implementation begins. SocialFlow
should favor a predictable hierarchy with responsibilities grouped by
purpose and domain.

The intended direction is approximately:

``` text
SocialFlow/
├── src/
│   └── socialflow/
│       ├── application/
│       │   ├── accounts/
│       │   ├── posts/
│       │   ├── publishing/
│       │   └── synchronization/
│       │
│       ├── domain/
│       │   ├── media/
│       │   ├── platforms/
│       │   └── posts/
│       │
│       ├── integrations/
│       │   ├── facebook/
│       │   ├── instagram/
│       │   └── wordpress/
│       │
│       ├── persistence/
│       │   ├── models/
│       │   └── repositories/
│       │
│       ├── services/
│       │   ├── credentials/
│       │   ├── error_reporting/
│       │   ├── images/
│       │   ├── language/
│       │   └── logging/
│       │
│       ├── ui/
│       │   ├── accounts/
│       │   ├── posts/
│       │   ├── settings/
│       │   └── shared/
│       │
│       └── main.py
│
├── tests/
│
├── ARCHITECTURE.md
├── DECISIONS.md
├── DEVELOPMENT.md
├── FEATURES.md
├── README.md
└── ...
```

This hierarchy is an architectural direction, not an instruction to
create every directory immediately.

Directories should be introduced only when implementation requires them.

Within these areas, prefer specific names that describe responsibility.
For example, `language_detector.py` communicates substantially more than
a generic `utils.py`.

The hierarchy may evolve as real implementation reveals better
boundaries. Significant changes should be reflected in this document
and, when appropriate, `DECISIONS.md`.

------------------------------------------------------------------------

## 29. Architecture Boundaries

The following dependencies should generally flow inward:

``` text
UI
 │
 ▼
Application
 │
 ├──────────────► Platform interfaces
 │
 ├──────────────► Persistence interfaces
 │
 └──────────────► Shared services
```

Platform implementations depend on external APIs.

Persistence implementations depend on infrastructure details. The current account repository uses JSON; the future broader database layer is planned to use SQLite/SQLAlchemy.

The core application should not need to know HTTP endpoint details, SQL
statements, Qt widget implementation details, or credential-storage
implementation details.

------------------------------------------------------------------------

## 30. Architecture Evolution

This architecture is expected to evolve as SocialFlow is implemented.

Changes should follow these rules:

1.  Do not introduce architectural complexity without a concrete
    requirement.
2.  Significant architecture changes should be discussed before
    implementation.
3.  Accepted significant decisions should be recorded in `DECISIONS.md`.
4.  `ARCHITECTURE.md` should describe the current agreed architecture.
5.  `FEATURES.md` should remain focused on functional requirements
    rather than implementation details.
6.  Tests should protect important architectural and behavioral
    assumptions where practical.

------------------------------------------------------------------------

## 31. Language Classification and Publishing Safety (Implemented)

`application/language/` contains the rule-based `LanguageDetector`,
`ParagraphLanguageDetector`, and `PostLanguageClassifier`. The post-level
classification is English, Croatian, mixed, or unknown. `PostEditor` connects
these services to `ParagraphLanguageHighlighter` and
`ContentLanguageIndicator`. Detected language is advisory; the manually chosen
`Post.language` remains the publishing-language field. Mixed-language posts
are passed unchanged as one post per selected account. The application does
not split, duplicate, or translate the text.

`Publisher` is the application contract and `PublisherRouter` maps platform
destinations to implementations. `MainContent` currently maps Facebook,
Instagram, and WordPress to `UnconfiguredPublisher`, which raises
`PublisherNotConfiguredError`. `PublishPost` converts publisher exceptions into
per-account failed `PublishResult` values. It records local publication history
only after a publisher returns successfully. `PublishStatus.show_results()`
displays the account, outcome, and available error reason. The UI-to-repository
failure path has regression coverage.

`NullPublisher` remains present but is **not** used for runtime external
publishing. Real platform adapters, credentials, network communication, and
remote identifiers are future work. Current successful publishing tests use
test publishers; they do not establish live platform connectivity.

**Verification checkpoint:** 433 passing automated tests reported for the
latest snapshot; no live platform API tests have been completed.