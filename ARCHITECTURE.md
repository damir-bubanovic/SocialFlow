# SocialFlow --- Architecture

> **Current development checkpoint — November 4, 2026:** Facebook Pages integration is implemented through **Phase 22.4E (text publishing end-to-end verification)** on `feature/facebook-pages-integration`. Latest verified commit: `f233571`, pushed to `origin/feature/facebook-pages-integration`; working tree clean; **2,598 pytest tests passed**. Facebook text publishing is covered using mocked HTTP transport; **live Facebook posting and GUI end-to-end validation have not been confirmed**. Next planned milestone: **Phase 22.5 — Facebook Publishing GUI Integration and Validation**. Historical sections below retain their original dates and should not be read as the current project status.

**Current implementation checkpoint:** See Section 42 for WordPress Categories, post lifecycle, and current asynchronous guards; earlier sections document historical evolution.


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

-   `urllib.request` with an HTTPS-only client (implemented for WordPress connection verification)
-   HTTPX (preferred for future integrations; not yet a project dependency)

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

WordPress uses the authenticated HTTPS REST API through separate, testable
connection-verification and publishing adapters.

`WordPressConnectionConfig` holds a normalized site URL and username on the
`Account` domain model. The OS-backed `KeyringCredentialStore` stores application
passwords under stable account-UUID-based keys. `SaveWordPressCredentials` and
`DeleteWordPressCredentials` manage credential lifecycle without writing secrets
to account JSON.

`WordPressConnectionVerifier` uses the `WordPressHttpClient` contract and
`UrllibWordPressHttpClient` to request `/wp-json/wp/v2/users/me`. The
`WordPressVerificationWorker` / `WordPressVerificationController` handle this
verification asynchronously, with safe deferred main-window shutdown.

**Publishing is implemented and connected to the UI composition root.**
`MainContent` configures `PublisherRouter.account_factories` so WordPress
accounts create `WordPressPublisher(account, credential_store, post_client)`.
`UrllibWordPressPostClient` implements `WordPressPostClient` using authenticated
HTTPS REST requests:

- `POST /wp-json/wp/v2/posts` creates a published text/HTML post and returns its HTTP status.
- `POST /wp-json/wp/v2/media` uploads prepared image bytes and returns validated `WordPressMedia(media_id, source_url)`.
- `DELETE /wp-json/wp/v2/media/{id}?force=true` permanently deletes media for best-effort upload rollback.

`WordPressPublisher` validates configuration, credentials, text, and prepared
image state. It resolves selected WordPress tags to remote numeric IDs, with missing-tag confirmation and creation coordinated by the Posts UI before publishing. For each
uploaded image, it HTML-escapes the returned URL and appends a Gutenberg
`wp:image` block to the post content. A successful post creation requires HTTP
201. An upload failure triggers reverse-order best-effort deletion of previously
uploaded media; deletion errors are logged, and the original upload exception
is re-raised. A post-creation failure does **not** delete successfully uploaded
media, so orphan media may require later cleanup.

The `urllib` clients use HTTPS certificate verification and disallow redirect
following with authorization credentials. Live publishing against a real
WordPress server has not yet been verified in live integration testing. Remote post retrieval, text and tag updates, WordPress tag listing/creation, and tag assignment during new-post publishing are implemented.

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

Implemented: WordPress application passwords are saved and deleted via
`KeyringCredentialStore` (the `keyring` dependency), while WordPress site URL
and username are persisted as non-secret account configuration. Keyring access
failures are translated into `CredentialStorageError`; the UI displays a generic
message rather than the underlying secret-storage exception.

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

SocialFlow maintains persistent application logs through `infrastructure/logging_config.py`.

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

Startup calls `configure_logging(data_directory() / "logs")`, creating a
UTF-8 `RotatingFileHandler` for `socialflow.log` (2 MiB maximum, three backups).
Repeated configuration with the same directory reuses the handler; switching
log directories removes and closes the previous rotating handler. Logging
initialization `OSError` is handled with a generic warning so startup can
continue. Module loggers under `socialflow.*` propagate to the configured
application logger. Publishing diagnostics record account/destination and
exception type, not post text or raw publishing exception messages.

The logging setup is implemented; comprehensive production exception reporting,
secret-redaction audits, and email delivery are not.

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

WordPress verification currently uses `WordPressVerificationWorker` moved to a
`QThread`, with `WordPressVerificationController` owning thread lifecycle and
forwarding result/error/completion signals. The Accounts page disables repeated
verification while a worker is active. `MainWindow.closeEvent()` defers closure
without blocking the UI and retries after verification completes and the thread
is cleaned up. Direct `AccountsPage.shutdown()` waits for an active worker when
the page itself is closed. The underlying `urllib` socket timeout defaults to
10 seconds, but is not a guaranteed total-request deadline; active requests
are not forcibly cancelled. Publishing, remote-post retrieval/updating, WordPress tag preparation/creation, and remote-tag catalog loading also use dedicated Qt worker/controller paths.

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
│   ├── connections/    # connection verifier contract
│   ├── credentials/    # credential storage contract + save/delete services
│   ├── images/         # validation, profiles, processing, preparation, cleanup
│   ├── publishing/     # prepared posts, router, publishers, PublishPost
│   └── tags/           # TagProvider, ListTags, CreateTag, NullTagProvider
├── domain/
│   ├── account/        # Account + stable AccountId
│   ├── connections/    # WordPressConnectionConfig, ConnectionResult/Status
│   ├── language/       # Language
│   ├── post/           # Post, ImageAttachment, Tag
│   └── publishing/     # PublishingDestination + PublishRequest
├── infrastructure/
│   ├── accounts/       # JSON repository, serializer, storage errors
│   ├── credentials/    # keyring credential storage
│   ├── wordpress/      # HTTPS REST verification, post/media client and publisher
│   └── storage/        # cross-platform data paths + prepared-image path
└── ui/
    ├── accounts/       # account form/list/status/page, verification worker/controller
    └── posts/          # editor, destinations, images, tags, language, status
```

Current responsibility boundaries include:

-   `MainContent` constructs the shared keyring-backed WordPress credential
    services and verifier, injecting them into `AccountsPage`.
-   `Account.wordpress_config` persists a normalized HTTPS site URL and username;
    application passwords are stored separately in the OS keyring.
-   WordPress connection verification is asynchronous and uses Qt signals for UI results and deferred main-window shutdown. WordPress publishing is separately implemented through an account-aware publisher factory.
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
-   `TagProvider` is the platform-facing tag contract. `RoutingTagProvider` uses `WordPressTagProvider` for WordPress and `NullTagProvider` for unsupported destinations; post tag assignment is supported for new WordPress posts after remote ID resolution.
-   `DestinationSelector` selects configured `Account` objects. `PublishRequest`
    carries those accounts and `PublishPost` resolves publishers by destination.
-   Account CRUD remains isolated behind `AccountRepository`;
    `JsonAccountRepository` persists UTF-8 account data and account changes are
    propagated to the Posts page with Qt signals.
-   `MainContent` registers `UnconfiguredPublisher` for Facebook and Instagram;
    WordPress uses an account-aware `WordPressPublisher` backed by an authenticated
    REST client. `NullPublisher` remains a test/no-op utility. Live WordPress
    server verification and Facebook/Instagram API publishing remain pending.
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

## 29A. WordPress Publishing and Image Cleanup (Implemented)

The composition root wires `UrllibWordPressPostClient` and the shared credential
store into `WordPressPublisher` for WordPress accounts. Facebook and Instagram
continue to resolve to `UnconfiguredPublisher`. `PublishPost` prepares images per
account and destination, dispatches the publisher, records local success only
after publisher return, and reports independent account results.

`ImagePreparationService.prepare_all()` reserves destination-specific output
filenames with exclusive creation and UUID suffixes on collisions. If processing
fails, it attempts to unlink every reserved output path. An `OSError` during
partial cleanup is logged and does not replace the original processing error;
cleanup continues to subsequent files. Normal post-publish cleanup is performed
by `PublishPost`, with cleanup errors reported separately in `PublishResult`.

The Posts page invokes publishing asynchronously through
`PublishingController` and `PublishingWorker`. WordPress connection verification
uses a separate worker/controller. Network publishing and media uploads now
execute in the publishing worker; live-platform validation remains pending.

Automated tests cover WordPress post/media requests, publisher validation,
Gutenberg content, upload rollback, and cleanup failures. Live server tests
remain outstanding.

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

Paragraph-level classification distinguishes Croatian, English, mixed, and
unknown content without changing the manual publishing language or splitting
posts. UI indicators provide explicit labels as well as visual cues.

Unconfigured Facebook and Instagram publishers fail explicitly, while WordPress
uses an account-specific REST publisher for text and prepared-image posts.
Successful publisher returns may be persisted to local history; remote post retrieval and text/tag editing are implemented through a separate WordPress workflow; publication-history image/tag serialization remains pending. The historical developer-reported Phase 21.9.21 checkpoint was 1081 passing tests; the latest Phase 21.9.30 checkpoint is 1188. This does not replace live WordPress API verification.

## 32. Background Publishing and Selective Retry (Implemented)

`ui/posts/publishing_controller.py` owns the publishing `QThread` and worker
lifecycle. `ui/posts/publishing_worker.py` calls
`application/publishing/publish_post.py` outside the UI thread and emits
per-account progress and a final result. The Posts page disables overlapping
publishing and restores controls after worker cleanup. `MainWindow.closeEvent`
defers shutdown while publishing or WordPress verification is running.

`PublishPost.execute()` attempts each selected account independently and
continues after account-specific exceptions. It emits progress via an optional
callback. Success is recorded in local history only after the publisher call
succeeds. Temporary prepared images are cleaned up after each attempt.

`application/publishing/build_retry_request.py` builds a new request containing
only failed accounts from the previous request/results. The Posts page retains
retry state until it is invalidated by draft changes (text, language, accounts,
images, tags, or starting a new post). Retry is not automatic and is not
restricted to transient errors. A successful retry does not republish accounts
that already succeeded.

## 33. Publishing Error Classification and Presentation (Implemented)

`application/publishing/error_classifier.py` maps `ConnectionError` and
`TimeoutError` to `TRANSIENT`; known invalid-content/configuration exceptions
to `PERMANENT`; and other exceptions to `UNKNOWN`. `PublishResult.error_category`
exposes this classification. `ui/posts/publishing_error_formatter.py` turns it
into generic user-facing status text. The original exception remains available
internally, but its raw message is not displayed in the per-account status.

`PublishPost` records a safe technical log message with account name,
destination, and exception class. Some other existing module loggers use
exception tracebacks; a comprehensive logging/redaction review is still
required before production release.

## 34. Application Startup and Logging Failure Handling (Implemented)

`main.create_application()` configures persistent logs after setting Qt
application identity. It catches `OSError` from log setup, emits a generic
warning, and continues. If `MainWindow()` construction fails, it logs the
exception type and re-raises. `main.run()` catches application creation and
window-display failures, logs the exception type, and returns `1`; normal
non-event-loop startup returns `0`.

The construction failure can currently be logged both by `create_application()`
and by `run()`. Deduplication, startup resource cleanup, and a reliable fallback
diagnostic when file logging is unavailable remain review items, not completed
features.

## 35. WordPress Tag Routing (Implemented, Limited Scope)

`ui/main_content.py` composes `RoutingTagProvider` with a
`WordPressTagProvider` backed by `UrllibWordPressTagClient` and the credential
store. `ListTags` and `CreateTag` use the application `TagProvider` contract.
WordPress tag listing and creation are authenticated operations; the fallback
for unsupported destinations is `NullTagProvider`. For new WordPress posts,
selected tags are resolved to remote IDs and passed to the post client. Missing
tags are created only after confirmation; this is not remote-post metadata
synchronization or remote-tag editing.

## 36. Remote WordPress Post Retrieval (Implemented)

The remote-post pipeline is separate from local `Publication` history:

- `domain/post/remote_post.py` models a remote post and its remote identifier.
- `application/publishing/remote_post_provider.py` and
  `list_remote_posts.py` define the provider boundary and use case.
- `infrastructure/wordpress/wordpress_post_client.py`,
  `urllib_wordpress_post_client.py`, `wordpress_post_parser.py`,
  `wordpress_post_retriever.py`, and `wordpress_post_provider.py`
  implement authenticated retrieval and conversion.
- `ui/workers/remote_post_loading_worker.py` and
  `remote_post_loading_controller.py` keep REST I/O off the UI thread.
- `ui/posts/remote_posts_panel.py` displays the retrieved posts;
  `posts_page.py` coordinates account selection, pending loads, stale results,
  and UI state.

The Posts page tracks which account produced the loaded results and rejects
results from outdated account selections. This does not backfill or replace
the locally stored `publications.json` history.

## 37. Remote WordPress Text Updating (Implemented)

`application/publishing/remote_post_updater.py` and
`update_remote_post.py` define the update boundary and use case.
`infrastructure/wordpress/wordpress_post_updater.py` uses the WordPress post
client and OS-backed application password to update a remote post by ID.

`ui/workers/remote_post_updating_worker.py` executes the operation off the UI
thread and distinguishes `succeeded`, `failed`, and terminal `finished`
signals. `remote_post_updating_controller.py` manages its `QThread`, forwards
success/errors, and emits completion after cleanup. `PostsPage` coordinates
account-scoped updates; the remote-post panel disables editing while a save is
in progress, restores it after errors, and refreshes the remote list on success.

Account identity, stale callbacks, concurrent starts, and shutdown are
explicitly guarded. Current scope is **remote post text and tag assignments**; remote image
editing, other metadata editing, and reconciliation with local
publication history are not implemented.

**Verification:** The developer reported 1081 passing tests after Phase 21.9.21,
including Qt worker/controller lifecycle regressions. This does not establish
live-server interoperability or cross-platform packaging readiness.

## 38. WordPress Tag Preparation, Confirmation, and Creation (Implemented)

`PostsPage` orchestrates tag preparation before invoking publishing.
`WordPressTagPreparationController` and its worker retrieve remote tags and
construct a `WordPressTagCreationPlan` through `WordPressTagResolver`.
`WordPressTagNameNormalizer` provides shared Unicode-aware comparison keys.
Existing selected tags must resolve unambiguously; missing tags are presented
through `WordPressTagConfirmationDialog`. Declining confirmation or encountering
a preparation error cancels the pending publish.

On approval, `WordPressTagCreationController` and
`WordPressTagCreationWorker` create missing tags through `WordPressTagClient`,
validating returned identities. `PostsPage` then resumes publishing.
`WordPressPublisher` re-fetches remote tags, resolves selected tags to numeric
IDs, and passes those IDs to `WordPressPostClient.create_post()`. It fails
explicitly if selected tags require an unavailable client or cannot be
resolved. Qt guards prevent overlapping preparation/creation/publishing and
prevent stale queued work during shutdown. The flow is covered by tests with
fake clients; live-site behavior remains unverified.

## 39. Publishing Worker, Controller, and UI Recovery (Implemented)

`PublishingWorker` invokes the publishing use case in a background Qt thread,
emits per-account progress and final results, and catches unexpected exceptions.
Unexpected failures are logged with tracebacks, while UI-facing messages avoid
exposing internal exception details. `PublishingController` manages thread
lifecycle, refuses overlapping starts, and supports synchronous, idempotent
shutdown. `PostsPage` clears stale retry state on an unexpected error and
restores publish controls after the controller finishes; selective retry
remains available only for known failed account results.

`MainWindow.closeEvent()` defers closing while verification or publishing is
active. A pending close is completed only when those operations finish;
repeated close requests do not cause premature or duplicate page shutdown.
Tests cover successful publishing, ordinary errors, unexpected worker
exceptions, restarting after failures, and close/shutdown ordering.

**Verification:** 1081 tests passing, as reported by the developer after
Phase 21.9.21. This documentation update did not execute pytest or test live
platform integrations.

## 40. WordPress Remote Tag Identity and Editing (Implemented — Phase 21.9.30)

**Domain and application.** `RemotePost.tag_ids` holds the WordPress numeric
IDs parsed from remote post responses. `RemoteTag` is an immutable value with
`remote_id` and display `name`. `RemoteTagProvider` and `ListRemoteTags` expose
the account-specific remote catalog independently from the generic `Tag` /
`TagProvider` path used to publish new posts.

**Infrastructure.** `WordPressTagProvider` implements both the generic
`TagProvider` and the remote-tag-specific `RemoteTagProvider`. The existing
WordPress post client, `WordPressPostUpdater`, and `UpdateRemotePost` accept an
optional tuple of numeric tag IDs. `tags=None` means **do not include the tags
field** in the REST update, whereas `tags=()` means **replace assignments with
none**. Positive integer validation protects the update boundary. Remote
media and arbitrary metadata updates are not implemented.

**Presentation.** `RemotePostsPanel` uses `RemoteTagSelector` (`QListWidget`
checkable items) for name-based selection, retaining IDs in Qt user data.
Unresolved assigned IDs appear as checked **Unknown WordPress tag (ID N)**
entries; loading or failing to load the catalog does not silently discard
them. Content-only saves emit `save_requested`; membership changes emit
`save_with_tags_requested`. The former omits tags, and the latter passes the
selected ID tuple. A failed save restores content and tag controls.

**Concurrency and account safety.** `RemoteTagLoadingWorker` and
`RemoteTagLoadingController` perform catalog retrieval off the GUI thread.
`PostsPage` clears catalog names when the WordPress account changes, queues
the latest request while an existing worker finishes, and discards stale
responses using account identity and pending-request checks. The remote-post
update remains bound to the account that loaded the selected post.

**Separation.** The remote editing selector is distinct from the existing
new-post `TagSelector`, whose tag preparation, confirmation, creation, and
name-to-ID resolution workflows are unchanged.

**Verification.** Developer-reported full suite: **1,188 passing tests** after
Phase 21.9.30. This documentation update does not rerun tests or validate a
live WordPress site.

## 41. Asynchronous Controller Ownership and Shutdown (Phases 21.9.31–21.9.59)

The Posts page coordinates several independent Qt worker/controller
lifecycles: publishing, WordPress tag preparation/creation, remote post
loading/updating, remote tag loading, and remote media selection. Request
identity, selected account, dialog lifecycle, and cancellation state are
checked before applying asynchronous results to UI state.

**Worker-to-controller signals must not bypass shutdown guards.**
`PublishingController`, `WordPressTagPreparationController`,
`WordPressTagCreationController`, and `RemotePostLoadingController` use
controller-owned `@Slot` forwarding methods that check `_shutting_down`
before emitting public result/error signals (and publishing progress).
Their thread-finished cleanup remains separate from business-result
delivery; valid normal results precede the controller's `finished`
notification. Regression tests exercise real queued Qt delivery after
shutdown, not only direct synchronous callback invocation.

`PostsPage` also prevents a cancelled WordPress tag-preparation request
from resuming publishing and accepts a fresh request after cancellation.
Remote editing, tag catalogs, and featured-media selection reject stale
callbacks when the selected account or operation changes.

These are local lifecycle guarantees. A shutdown or cancellation does not
undo WordPress network side effects already performed.

**Latest developer-reported full-suite checkpoint:** **1,478 tests passed** after Phase 21.9.59 (October 26, 2026). This documentation review did not execute pytest. The uploaded archive contains the three new remote-post-loading controller tests and the guarded-slot implementation.

## 42. WordPress Post Lifecycle and Categories (Phases 21.9.60–21.9.72, October 2026)

This section is the current implementation checkpoint and supersedes older feature-boundary statements above that described titles, excerpts, featured media, Trash/Restore, or categories as unavailable.

### Presentation and workflow

`PostsPage` coordinates the **Create Post**, **My Posts**, and **Trash** sub-tabs. `PostEditor` is the shared composer; `RemotePostsPanel` is the selected remote-post editor; `RemoteTrashedPostsPanel` handles trashed posts. WordPress publishing requires a nonempty title. The My Posts editor supports title, content, excerpt, status, tags, featured media, and category assignments. The Accounts UI has a master/detail layout, explicit New/Edit modes, and a masked stored Application Password toggle.

### Categories — domain, infrastructure, application

- `RemoteCategory` carries a WordPress numeric ID, name, and parent relationship; category parsers and WordPress HTTP clients/providers translate REST payloads.
- `ListRemoteCategories` and the remote-category provider load the selected account's catalog; a separate WordPress category creation path supports confirmed creation with an optional parent.
- `RemoteCategoryLoadingWorker`/`RemoteCategoryLoadingController` and `WordPressCategoryCreationWorker`/`WordPressCategoryCreationController` keep network work off the GUI thread.
- `RemoteCategorySelector` displays a hierarchical multi-select UI while retaining numeric IDs. `WordPressCategoryDialog` collects the new category name and optional parent.
- Create Post passes selected IDs through the WordPress publishing path. My Posts reads existing IDs from `RemotePost` and sends changed IDs through the remote-post update path.

### Remote update semantics and UI signals

`categories: tuple[int, ...] | None = None` is carried through the remote-post update boundary. `None` omits `categories` from the REST update; `()` explicitly requests an empty assignment; `(id, ...)` replaces assignments. Validate positive integer IDs, excluding bool. The panel compares category membership as sets; when changed, it emits `save_with_categories_requested`, carrying the other edited fields as well. Unchanged category assignments preserve the existing save paths.

### Account and asynchronous safety

`PostsPage` tracks category loading generation/account, successful catalog account, and loaded posts account. Editing is authorized only when both catalogs and posts belong to the same selected WordPress account. An empty successful catalog is valid; a failed catalog is not. Refresh and account changes revoke editing; stale callbacks are rejected. Category controls are locked while saving/trashing, and failed updates restore editing only under the current permission state. Post-loading failures clear loaded-post identity and disable category editing.

### WordPress post lifecycle

Recent remote posts are deliberately limited to a small set (about 5–10); pagination and full historical retrieval are outside scope. My Posts can update existing posts and move them to Trash. The Trash tab retrieves trashed posts and restores selected posts as drafts. Operations use account/generation guards and asynchronous Qt controllers.

### Verification boundary

The developer reported that the complete automated test suite passed after Phase 21.9.72D2-C2 and pushed the changes. A live WordPress REST connection and Application Password authentication had been established previously. The final live category publishing/editing and integrated lifecycle checks remain pending; documentation preparation did not rerun pytest. Facebook/Instagram integrations remain future work.

## 43. Target Architecture — Feature-First, Laravel-Inspired (Approved November 1, 2026)

**Design only: NOT YET IMPLEMENTED.** This section supersedes earlier *proposed* source layouts, but the current code still uses the existing `domain/`, `application/`, `infrastructure/`, and `ui/` organization. Preserve existing behavior and clean dependency direction during migration.

```text
src/socialflow/
├── core/
│   ├── contracts/           # pure ports/interfaces, including platform contracts
│   ├── exceptions/
│   ├── events/              # framework-independent event definitions
│   └── services/            # genuinely cross-feature logic
├── modules/
│   ├── accounts/
│   │   ├── models/
│   │   ├── requests/
│   │   ├── controllers/
│   │   ├── services/
│   │   └── views/
│   ├── posts/
│   │   ├── models/
│   │   ├── requests/
│   │   ├── controllers/
│   │   ├── services/
│   │   ├── views/
│   │   ├── components/
│   │   └── workers/
│   ├── wordpress/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── requests/
│   │   ├── services/
│   │   ├── mappers/
│   │   └── adapters/
│   ├── instagram/           # FUTURE; not implemented
│   └── facebook/            # FUTURE; not implemented
├── infrastructure/
│   ├── persistence/
│   ├── storage/
│   └── security/
├── config/
├── bootstrap/
└── main.py
```

This is an illustrative ownership map, not a mandate to create every directory. Only create folders for actual responsibilities. Tests can remain centrally under `tests/` (mirroring modules) to preserve pytest discovery; do not move tests into production packages by default. Concrete file ownership is decided after dependency mapping.

### Dependency rules

- Pure models, request values, contracts, and business rules must not import PySide6, concrete HTTP clients, or persistence implementations.
- UI controllers coordinate views and application services; Qt workers run I/O off the GUI thread and preserve guarded signal delivery, shutdown, cancellation, and account/request-generation checks.
- Platform adapters implement core contracts and declare supported capabilities; common publishing logic depends on interfaces, not on WordPress/Instagram/Facebook implementations.
- WordPress-specific REST payloads, Application Password auth, category/tag/media semantics, and mappers stay in the WordPress module. Instagram/Facebook API and OAuth design requires separate official API review later.
- Avoid cyclic feature imports, duplicate models, unnecessary compatibility shims, and premature generic frameworks. Use explicit dependency registration in bootstrap where useful.
- Keep WordPress's small recent-post scope, ID-based category assignments, omitted-vs-empty update semantics, and title requirement.

### Migration sequence and acceptance gates

1. Audit actual imports, dependencies, tests, Qt worker lifetimes, and Git status; establish baseline.
2. Define contracts/module boundaries and compatibility approach before moving files.
3. Migrate Accounts and Posts feature files in cohesive, testable batches.
4. Move WordPress-specific integration behind its adapter; keep REST behavior identical.
5. Add capability/adapter registration for future platforms, without claiming Instagram/Facebook functionality.
6. Update imports and tests per batch, run full pytest at milestones, verify WordPress live smoke tests after migration, then commit and document.

**Estimate:** 35–55 engineering hours, provisional, excluding Instagram/Facebook implementation. Do not mistake structural reorganization for performance optimization or a guarantee of fewer bugs.

### November 1 verification checkpoint

Developer reported six passing live WordPress tests: category load, multi-category publish, category edit, category clear, Trash, and Restore as Draft. Developer reported complete headless pytest suite passing; numeric count unknown. This documentation edit did not execute tests. The prior October 31 pending-live-verification statements are historical for these six flows; additional failure recovery/account switching and packaging remain separate checks.

---

## November 1, 2026 — Feature-Aligned Test Architecture (Approved Target)

**This section extends the feature-first modular target above; it is not the current implemented file layout.**

```text
src/socialflow/                     tests/
├── core/                            ├── core/
├── modules/                         ├── modules/
│   ├── accounts/                    │   ├── accounts/
│   ├── posts/                       │   ├── posts/
│   ├── wordpress/                   │   ├── wordpress/
│   ├── instagram/ (future)          │   ├── instagram/ (future)
│   └── facebook/ (future)           │   └── facebook/ (future)
├── infrastructure/                  ├── infrastructure/
├── config/                          ├── integration/
├── bootstrap/                       ├── fixtures/ (as needed)
└── main.py                          └── conftest.py
```

Within a module, use Laravel-inspired, Python-appropriate responsibilities (`models`, `requests`, `controllers`, `services`, `views`, `components`, `workers`, `api`, `adapters`) **only where needed**. Example: a `modules/posts/controllers/publishing_controller.py` test may live in `tests/modules/posts/controllers/test_publishing_controller.py`. Cross-platform publishing and Trash/Restore workflows belong in `tests/integration/` when they span modules.

**Test boundary rules:**
- Unit tests should isolate domain/application behavior from PySide6 and network adapters where possible.
- Platform adapter tests should use mocked HTTP boundaries; live WordPress checks remain explicitly controlled smoke tests.
- Keep Qt UI/worker tests with the owning feature and retain thread cleanup, signal lifetime, and stale-result coverage.
- Prefer feature-local fixtures; use shared fixtures only for genuinely shared setup.
- Do not rename tests or rewrite assertions merely to achieve cosmetic symmetry.
- Preserve pytest discovery and collected-test coverage across every migration batch.

**Migration:** inspect source and test dependencies first; migrate cohesive source/test slices together; run focused tests, full-suite collection checks, and final WordPress live smoke checks. Current snapshot has **not** been refactored. Total provisional estimate is **41–67 engineering hours**, excluding Instagram/Facebook implementation. See ADR-078.

---

## 44. Implemented Feature-First Architecture — November 1, 2026

**Status: implemented.** This section supersedes the earlier *target-only* and *migration-pending* wording in Sections 43 and the feature-aligned test architecture handoff. Those sections remain as historical design context.

### Verified source and test ownership

```text
src/socialflow/
├── modules/
│   ├── accounts/           # Account models, repositories, services, UI
│   ├── posts/              # Composer, publishing, publications, tags, UI
│   └── wordpress/          # WordPress API, adapters, platform behavior
├── ui/
│   └── main_content.py     # Feature composition
├── core/                   # Shared contracts and primitives
├── application/            # Shared credential and clock contracts
└── infrastructure/         # Keyring, logging, paths, system clock

tests/
├── modules/
│   ├── accounts/
│   ├── posts/
│   └── wordpress/
└── integration/            # Cross-feature workflows
```

This is a *representative* ownership map, not an exhaustive directory listing. Keep existing shared folders and test infrastructure as implemented; do not create empty Instagram/Facebook placeholders.

### Enforced dependency direction

- **Accounts → Posts/WordPress:** forbidden.
- **Posts → WordPress:** forbidden; platform-specific behavior is supplied through contracts/adapters.
- **WordPress → Posts:** permitted for shared Posts models and service contracts, not Posts UI, controllers, workers, or repositories.
- **Posts → Accounts:** permitted for account models, account lookup, and account serialization used in publication history and migration.
- **WordPress → Accounts:** permitted for account/credential contracts.
- **Composition:** `socialflow.ui.main_content` connects Accounts, Posts, and WordPress.
- **Shared infrastructure:** credential store, clock, keyring, logging, and paths stay outside feature modules.

Posts owns `RemoteTagCreationPlan` and `RemoteTagCreationService`; WordPress supplies its platform adapter. The historical `WordPressTagCreationPlan` name is retained as a compatibility alias.

### Verification and limits

The developer reported **2,151 passing pytest tests**, **zero forbidden feature dependency violations**, clean Git checks, and a successful manual application GUI smoke test on `refactor/feature-first-architecture`. This establishes completion of the planned structural migration; it is not a guarantee that every possible runtime scenario or external WordPress API failure has been tested. Instagram/Facebook remain future work. Earlier migration estimates are historical planning figures, not actual recorded effort.

---

## 45. Facebook Pages Runtime Publishing Architecture — November 4, 2026

**Implemented through Phase 22.4E.** The earlier feature-first diagram and statements describing Facebook as future-only are historical; `src/socialflow/modules/facebook/` and `tests/modules/facebook/` now exist.

### Ownership and flow

```text
Posts publishing workflow
  PublishRequest -> PublishPost -> PublisherRouter
                                    |
                                    +-- account factory (FACEBOOK)
                                          -> FacebookPublisher
                                               |-- Account.facebook_config (Page ID)
                                               |-- CredentialStore / FacebookCredentialKeys
                                               +-- FacebookPublishingService
                                                     -> FacebookGraphClient
                                                          -> FacebookHttpTransport
                                                               -> HTTPS Graph API
```

- **Composition:** `src/socialflow/ui/main_content.py` creates the Facebook Graph client and publishing service, and registers a Facebook account-specific publisher factory alongside existing routing.
- **Accounts:** `src/socialflow/modules/accounts/models/facebook_page_config.py`, account persistence, and Facebook credential services own non-secret Page configuration and token-key management.
- **Facebook:** `modules/facebook/api/` owns Graph HTTP behavior and structured `FacebookApiError`; `modules/facebook/adapters/facebook_publisher.py` implements the Posts publishing contract. The publisher supports text-only posts and rejects images/tags.
- **Posts:** `PublishPost` handles per-account results; `PublisherRouter` resolves publishers. `modules/posts/services/error_classifier.py` classifies `FacebookApiError` as transient when `is_transient` is true, otherwise permanent. It does not implement retries.
- **Integration boundary:** `tests/integration/test_facebook_text_publishing.py` exercises real application/publisher/API components with a mocked HTTP transport; it does not make live Facebook calls.

### Verification and limitations

Phase 22.4D: runtime registration and configuration-error behavior, commit `2af2717`. Phase 22.4E: success/OAuth rejection/HTTP 503 integration tests and classifier support, commit `f233571`. Full developer-reported suite: **2,598 passed**; latest branch synchronized and clean. **Phase 22.5** will validate user-facing Posts publishing GUI behavior. No live Facebook post or completed GUI end-to-end validation is asserted here.

Preserve the feature-first dependency direction: Posts may use Accounts models/contracts but must not import Facebook platform implementation; composition and the platform adapter bridge those boundaries.