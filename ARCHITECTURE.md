# SocialFlow — Architecture

## 1. Purpose

This document describes the technical architecture of SocialFlow.

SocialFlow is a cross-platform desktop application for creating, managing,
publishing, and updating content across multiple online platforms.

Initial integrations:

- Facebook
- Instagram
- WordPress

Target operating systems:

- Linux
- Windows

Architecture changes should be reflected in this document when they are
implemented or formally agreed upon.

---

## 2. Technology Stack

### Language

- Python 3.12+

Python is the primary application language.

### Desktop Framework

- PySide6
- Qt 6

PySide6 provides the cross-platform desktop user interface.

### Local Database

- SQLite

SQLite provides local persistent application storage without requiring a
separate database server.

### Database Access

- SQLAlchemy

Application code should access the database through a defined persistence
layer rather than spreading SQL or database-specific logic throughout the
application.

### HTTP Communication

- HTTPX

External API communication should be performed through dedicated integration
services.

### Image Processing

- Pillow

Image processing is responsible for validation, resizing, conversion,
compression, and generation of platform-compatible image versions.

### Testing

- pytest
- pytest-qt where appropriate

Testing is part of normal feature development.

---

## 3. Architectural Principles

SocialFlow should follow these principles:

1. Keep the user interface separate from business logic.
2. Keep platform-specific API behavior isolated from the rest of the
   application.
3. Keep database access separate from UI code.
4. Do not place authentication credentials directly in source code.
5. Avoid unnecessary dependencies.
6. Prefer clear and maintainable code over unnecessary abstraction.
7. Design platform integrations so one platform can fail without corrupting
   operations for other platforms.
8. Make important behavior testable without requiring live API calls.
9. Preserve user content when remote operations fail.
10. Treat external APIs as unreliable boundaries.
11. Keep platform-specific restrictions out of the common domain logic where
    practical.
12. Do not introduce functionality outside the agreed project scope.
13. Prefer small, focused modules and classes over large multi-purpose files.
14. Use meaningful names that communicate a component's responsibility.
15. Organize code in a predictable hierarchy so developers can quickly locate
    the correct place for a change.
16. Favor reusable components when behavior is genuinely shared.
17. Apply object-oriented design where it improves responsibility boundaries,
    reuse, testability, and navigation without introducing unnecessary
    abstraction.

---

## 4. High-Level Architecture

SocialFlow will use a layered architecture.

```text
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

---

## 5. Code Organization and Modularity

SocialFlow should have a predictable, hierarchical codebase inspired by the
navigability of well-structured application frameworks.

A developer should normally be able to determine where code belongs from its
responsibility.

Guidelines:

- Prefer small, focused Python files.
- Prefer classes and modules with one clear primary responsibility.
- Split files when they begin coordinating unrelated responsibilities.
- Use meaningful domain-oriented names for files, classes, methods, and
  directories.
- Avoid generic dumping-ground modules such as `utils.py`, `helpers.py`,
  `misc.py`, or oversized `manager.py` files.
- Shared behavior should live in reusable services or components rather than
  being duplicated.
- Platform-specific behavior should remain close to its platform integration.
- UI components should remain focused on presentation and interaction.
- Business workflows should remain outside widgets.
- Persistence behavior should remain outside UI and platform clients.
- Do not create abstractions solely to increase the number of classes or
  layers.

There is no fixed maximum number of lines for a Python file. File size should
be treated as a design signal rather than an arbitrary rule. When a file
becomes difficult to navigate or contains multiple independent
responsibilities, it should be decomposed into meaningful components.

Object-oriented programming should be used deliberately. Classes are
appropriate for components with state, lifecycle, replaceable behavior, or a
clear domain/service responsibility. Simple stateless behavior does not need
to be forced into unnecessary class hierarchies.

The goal is a codebase with the kind of discoverability found in structured
frameworks such as Laravel, while remaining appropriate for a Python/Qt
desktop application.

---

## 6. Presentation Layer

The presentation layer contains the PySide6 user interface.

Responsibilities include:

- Application windows
- Dialogs
- Forms
- Post editor
- Image previews
- Platform selection
- Tag selection
- Recent-post views
- Settings
- User-facing validation messages
- Progress indicators
- User-facing error messages

The UI should not directly communicate with Facebook, Instagram, WordPress,
SQLite, SMTP, or other infrastructure.

Instead, it should call application services.

This keeps the interface testable and prevents platform-specific logic from
becoming embedded in widgets.

---

## 7. Application Layer

The application layer coordinates user actions and application workflows.

Examples include:

- Create a post.
- Publish a post.
- Publish to multiple destinations.
- Retrieve recent posts.
- Update an existing post.
- Synchronize tags.
- Synchronize remote content.
- Process images before publishing.
- Handle partial publishing failures.

The application layer should coordinate operations but should not contain
low-level HTTP, database, or GUI implementation details.

---

## 8. Platform Integration Layer

Each external publishing platform must have its own integration implementation.

Initial integrations:

```text
Platform interface
       │
       ├── Facebook integration
       ├── Instagram integration
       └── WordPress integration
```

Application code should use a common interface where the platforms share
concepts.

Platform-specific differences must remain inside the relevant integration
where practical.

For example, SocialFlow must not assume that:

- every platform supports identical tags;
- every platform supports identical image formats;
- every platform allows the same fields to be edited;
- every platform uses the same authentication method;
- every platform has the same publishing restrictions.

Platform capabilities should be represented explicitly rather than hidden
behind assumptions.

---

## 9. Facebook Integration

Facebook communication will use supported Meta APIs.

The Facebook integration will eventually be responsible for supported
operations such as:

- authentication;
- page discovery;
- post retrieval;
- publishing;
- updating supported content;
- media handling;
- authorization validation.

Exact functionality will be determined against the current Meta APIs before
implementation.

---

## 10. Instagram Integration

Instagram communication will use supported Meta APIs.

The Instagram integration will eventually be responsible for supported
operations such as:

- authentication;
- account discovery;
- content retrieval;
- publishing;
- updating supported content where permitted;
- media handling;
- authorization validation.

Exact functionality will be determined against the current Meta APIs before
implementation.

---

## 11. WordPress Integration

WordPress communication will use the WordPress REST API.

The WordPress integration will eventually be responsible for supported
operations such as:

- site authentication;
- connection verification;
- retrieving posts;
- creating posts;
- updating posts;
- uploading media;
- retrieving tags;
- creating tags;
- assigning tags and other supported metadata.

---

## 12. Image Processing

Image manipulation will be handled independently from the platform
integrations.

The image service will be responsible for operations such as:

- reading image metadata;
- validating formats;
- determining dimensions;
- resizing;
- converting formats;
- compression;
- generating destination-specific versions.

Original source images should not be modified unnecessarily.

A typical flow will be:

```text
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

Generated files should be treated as application runtime data rather than
source-controlled project files.

---

## 13. Persistence Layer

SocialFlow will use SQLite for local persistent data.

Potential locally stored information includes:

- application configuration;
- configured accounts;
- destination identifiers;
- cached post metadata;
- cached tags;
- synchronization metadata;
- relationships between local and remote objects.

Sensitive authentication material should not be stored in plain text in the
normal application database when secure credential storage is available.

Database access should occur through the persistence layer.

UI components should not execute database operations directly.

---

## 14. Credential Management

SocialFlow will interact with services requiring authentication.

Potential sensitive information includes:

- access tokens;
- refresh tokens;
- WordPress credentials or application passwords;
- email-service credentials;
- API secrets.

Rules:

1. Credentials must never be hard-coded.
2. Credentials must never be committed to Git.
3. Credentials must not appear in normal logs.
4. Credentials must not appear in error-report emails.
5. Secure operating-system credential storage should be used where practical.
6. Development secrets must remain outside tracked source files.

---

## 15. Configuration

Application configuration should distinguish between:

### Non-sensitive configuration

Examples:

- UI preferences;
- application behavior;
- configured error-report recipient;
- synchronization settings.

### Sensitive configuration

Examples:

- API secrets;
- access tokens;
- authentication credentials.

Sensitive and non-sensitive configuration should not automatically share the
same storage mechanism.

---

## 16. Logging

SocialFlow will maintain application logs.

Logs should support diagnosis of:

- application startup problems;
- publishing failures;
- synchronization failures;
- API errors;
- database errors;
- image-processing failures;
- unexpected exceptions.

Logs must avoid storing authentication credentials and other sensitive data.

Logging should be centralized rather than implemented independently by every
UI component.

---

## 17. Error Reporting

Unexpected or important production errors may trigger email notifications.

The error-reporting system should:

1. Capture the relevant exception.
2. Log the complete locally appropriate diagnostic information.
3. Sanitize sensitive information.
4. Determine whether the error requires notification.
5. Send an error report to the configured recipient.
6. Avoid uncontrolled repeated notifications for identical failures.

Error reporting must not replace local logging.

---

## 18. Background Operations

Network operations and expensive image processing must not freeze the desktop
interface.

Operations that may require background execution include:

- publishing;
- retrieving remote posts;
- synchronizing metadata;
- uploading images;
- image processing;
- authentication operations;
- sending error reports.

Qt-compatible background execution mechanisms should be used where necessary.

UI updates must remain safe with respect to Qt's threading rules.

The exact concurrency mechanism will be selected when background processing is
implemented.

---

## 19. Failure Isolation

Publishing to multiple platforms must not be treated as one indivisible remote
transaction.

Example:

```text
Publish
   │
   ├── Facebook  -> Success
   ├── Instagram -> Failure
   └── WordPress -> Success
```

SocialFlow should preserve and display the individual result for each
destination.

A failure on Instagram should not falsely report that Facebook and WordPress
also failed.

The application should retain enough information to let the user understand
what happened and take an appropriate next action.

---

## 20. Unicode and Language Support

SocialFlow must use Unicode throughout the application.

Initial content languages:

- Croatian
- English

Croatian characters must be preserved correctly, including:

```text
č ć ž š đ
Č Ć Ž Š Đ
```

Unicode handling applies to:

- UI input;
- database storage;
- API requests;
- API responses;
- logs where appropriate;
- post content;
- tags;
- filenames where supported.

UTF-8 should be used for project text files and external textual data where
applicable.

---

## 21. Language Service

Language handling should be a dedicated application capability rather than
logic embedded directly in the post editor.

Initial supported content languages are:

- Croatian (`HR`)
- English (`EN`)

A language service may be responsible for:

- detecting Croatian or English content where detection is sufficiently
  reliable;
- representing uncertain detection;
- supporting an explicit user override;
- providing language information to the application/UI;
- remaining independently testable.

Automatic detection must not be treated as infallible. Short captions,
hashtags, names, URLs, mixed-language text, and other ambiguous content may
not provide enough evidence for reliable classification.

The post editor should display an explicit language indicator such as `HR` or
`EN`. Color, typography, or other visual styling may reinforce this state but
must not be the only indication of language.

Language detection logic must not be implemented directly inside Qt widgets.
The UI should consume the result of the language capability through the
application/service boundary.

---

## 22. Testing Architecture

Tests should be organized according to what they verify.

The test suite will eventually include:

- unit tests;
- application/service tests;
- persistence tests;
- platform integration tests using mocks/fakes;
- image-processing tests;
- selected UI tests;
- regression tests.

Live external APIs should not be required for the normal automated test suite.

Platform clients should therefore be designed so their external communication
can be replaced or mocked during testing.

Real API verification may be performed separately as integration testing when
appropriate.

---

## 23. Development Workflow

Development should proceed incrementally.

For each logical feature or section:

```text
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

A feature is not considered complete merely because the UI appears to work.

Its relevant automated tests must pass.

Before major completed sections are pushed, the broader project test and
quality checks should also pass.

---

## 24. Source Control

Git is used for source control.

GitHub hosts the remote repository.

Primary branch:

```text
main
```

The repository should contain:

- source code;
- tests;
- public project documentation;
- dependency definitions;
- build configuration.

The repository must not contain:

- virtual environments;
- credentials;
- access tokens;
- production databases;
- runtime logs;
- generated caches;
- temporary media;
- local IDE configuration;
- local AI-agent instructions.

---

## 25. Packaging

SocialFlow must eventually be distributed as a standalone desktop
application.

Target platforms:

### Linux

The final packaging method will be selected after the application foundation
is stable.

### Windows

The final packaging method will be selected after the application foundation
is stable.

Packaging should allow end users to run SocialFlow without manually
configuring the development environment.

Packaging technology will be evaluated separately rather than assumed at this
stage.

---

## 26. Proposed Source Organization

The exact structure will evolve as implementation begins. SocialFlow should
favor a predictable hierarchy with responsibilities grouped by purpose and
domain.

The intended direction is approximately:

```text
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

This hierarchy is an architectural direction, not an instruction to create
every directory immediately.

Directories should be introduced only when implementation requires them.

Within these areas, prefer specific names that describe responsibility. For
example, `language_detector.py` communicates substantially more than a generic
`utils.py`.

The hierarchy may evolve as real implementation reveals better boundaries.
Significant changes should be reflected in this document and, when
appropriate, `DECISIONS.md`.

---

## 27. Architecture Boundaries

The following dependencies should generally flow inward:

```text
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

Persistence implementations depend on SQLite/SQLAlchemy.

The core application should not need to know HTTP endpoint details, SQL
statements, Qt widget implementation details, or credential-storage
implementation details.

---

## 28. Architecture Evolution

This architecture is expected to evolve as SocialFlow is implemented.

Changes should follow these rules:

1. Do not introduce architectural complexity without a concrete requirement.
2. Significant architecture changes should be discussed before implementation.
3. Accepted significant decisions should be recorded in `DECISIONS.md`.
4. `ARCHITECTURE.md` should describe the current agreed architecture.
5. `FEATURES.md` should remain focused on functional requirements rather than
   implementation details.
6. Tests should protect important architectural and behavioral assumptions
   where practical.