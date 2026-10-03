# SocialFlow --- Architecture Decisions

## Purpose

This document records significant technical and development decisions
for SocialFlow.

`ARCHITECTURE.md` describes the current system design. This document
records important decisions behind that design so future development
does not lose the reasoning that established the project direction.

Decisions may be revised when requirements or external platform
capabilities change. When that happens, the existing decision should
remain documented and a new decision should record the change.

------------------------------------------------------------------------

## ADR-001 --- Python as the Primary Language

**Status:** Accepted

### Decision

SocialFlow will be developed primarily in Python.

The initial development environment uses Python 3.12.

### Context

SocialFlow is a desktop application that requires:

-   cross-platform support;
-   HTTP API integrations;
-   image processing;
-   local persistence;
-   background operations;
-   automated testing;
-   application packaging.

Python provides mature libraries for these requirements and is already
available in the development environment.

### Alternatives Considered

-   PHP / Laravel
-   Java
-   C#
-   JavaScript / TypeScript with Electron

### Consequences

The project can use a single primary language for the application logic,
platform integrations, image processing, persistence, and desktop UI.

------------------------------------------------------------------------

## ADR-002 --- PySide6 and Qt 6 for the Desktop Interface

**Status:** Accepted

### Decision

SocialFlow will use PySide6 with Qt 6 for its desktop user interface.

### Context

The application must run on both Linux and Windows and requires a full
desktop interface.

### Consequences

The UI remains within the Python ecosystem while using a mature
cross-platform desktop framework.

Qt-specific implementation details should remain in the presentation
layer and should not spread into application or platform-integration
logic.

------------------------------------------------------------------------

## ADR-003 --- Linux and Windows Are First-Class Targets

**Status:** Accepted

### Decision

SocialFlow will support:

-   Linux, including Linux Mint;
-   Windows.

### Context

Development currently takes place on Linux Mint, but the finished
application must also operate on Windows.

### Consequences

Dependencies, filesystem behavior, credential storage, packaging, and
other platform-specific functionality must be evaluated for both
operating systems.

Code should not assume Linux-only paths or behavior.

------------------------------------------------------------------------

## ADR-004 --- SQLite for Local Persistent Storage

**Status:** Accepted

### Decision

SocialFlow will use SQLite for its local application database.

### Context

SocialFlow is a desktop application and does not currently require a
separate database server.

### Consequences

Installation remains simpler because users do not need to install and
manage a database service.

SQLite should contain application data and synchronization metadata, but
sensitive credentials should use secure credential storage where
practical.

------------------------------------------------------------------------

## ADR-005 --- SQLAlchemy for Database Access

**Status:** Accepted

### Decision

SQLAlchemy will be used as the primary database access layer.

### Context

Database logic should not be distributed throughout UI widgets or
unrelated application code.

### Consequences

Persistence behavior can be organized behind a defined persistence layer
and tested independently from the UI.

------------------------------------------------------------------------

## ADR-006 --- Separate Platform Integrations

**Status:** Accepted

### Decision

Facebook, Instagram, and WordPress will each have separate integration
implementations.

### Context

The platforms do not expose identical APIs or capabilities.

They can differ in:

-   authentication;
-   publishing rules;
-   editable fields;
-   media requirements;
-   tags and metadata;
-   rate limits;
-   post retrieval;
-   account/page/site concepts.

### Consequences

SocialFlow may expose common application concepts where appropriate, but
it must not pretend all platforms behave identically.

Platform-specific behavior belongs inside the relevant integration
whenever practical.

------------------------------------------------------------------------

## ADR-007 --- Verify External API Capabilities Before Implementation

**Status:** Accepted

### Decision

Features involving Facebook, Instagram, or WordPress must be verified
against the current supported APIs before their platform-specific
implementation is finalized.

### Context

External APIs, permissions, authentication requirements, and supported
operations can change independently of SocialFlow.

### Consequences

The project documentation may describe desired behavior broadly, but
actual integration work must respect current platform capabilities.

Unsupported operations must not be simulated or silently presented as
supported functionality.

------------------------------------------------------------------------

## ADR-008 --- HTTPX for HTTP Communication

**Status:** Accepted

### Decision

HTTPX will be the preferred HTTP client for external API communication.

### Context

SocialFlow requires structured communication with multiple HTTP APIs.

### Consequences

HTTP behavior should be concentrated in integration/service code rather
than performed directly from UI components.

The design should allow HTTP communication to be replaced or mocked
during automated testing.

------------------------------------------------------------------------

## ADR-009 --- Pillow for Image Processing

**Status:** Accepted

### Decision

Pillow will be used for application-level image processing.

### Context

SocialFlow must prepare images for destinations that may have different
image requirements.

Required operations may include:

-   reading image metadata;
-   validation;
-   resizing;
-   conversion;
-   compression;
-   generation of destination-specific versions.

### Consequences

Original user images should not be modified unnecessarily.

Processed images should normally be generated as temporary/runtime
artifacts.

------------------------------------------------------------------------

## ADR-010 --- Layered Application Architecture

**Status:** Accepted

### Decision

SocialFlow will separate major responsibilities into layers.

The primary conceptual layers are:

-   presentation;
-   application;
-   platform integrations;
-   persistence;
-   shared services.

### Context

Directly mixing UI, HTTP APIs, database access, image processing, and
business logic would make the application difficult to test and
maintain.

### Consequences

UI components should coordinate with application services rather than
directly performing HTTP or database operations.

External integrations should be replaceable by test doubles where
practical.

------------------------------------------------------------------------

## ADR-011 --- Use a `src` Project Layout

**Status:** Accepted

### Decision

Application source code will live beneath:

``` text
src/socialflow/
```

Tests will live separately beneath:

``` text
tests/
```

### Context

The project should clearly separate application packages from tests,
documentation, configuration, and repository-level files.

### Consequences

Directories will be introduced incrementally as their functionality is
implemented rather than creating a large empty hierarchy immediately.

------------------------------------------------------------------------

## ADR-012 --- pytest as the Primary Test Framework

**Status:** Accepted

### Decision

SocialFlow will use pytest as its primary automated testing framework.

`pytest-qt` may be used where Qt-specific testing provides meaningful
value.

### Context

Testing is a normal part of feature development and not a final cleanup
phase.

### Consequences

New behavior should normally include appropriate tests.

Bug fixes should include regression tests where practical.

Live external services should not be required for the normal automated
test suite.

------------------------------------------------------------------------

## ADR-013 --- Features Must Be Tested Before Completion

**Status:** Accepted

### Decision

A feature or logical development section is not considered complete
until its relevant automated tests pass.

Before major completed sections are committed and pushed, the broader
required test and quality-check suite should also pass.

### Context

SocialFlow integrates with remote systems and handles user content,
making regressions potentially difficult to diagnose after release.

### Consequences

The normal development sequence is:

``` text
Requirement
    ↓
Design
    ↓
Implementation
    ↓
Tests
    ↓
Relevant checks
    ↓
Review
    ↓
Commit
    ↓
Push
```

------------------------------------------------------------------------

## ADR-014 --- Incremental Git Workflow

**Status:** Accepted

### Decision

Development should be committed in logical, verified units.

After a feature or development section is complete and checks are green,
the AI assistant should provide an appropriate Git commit message.

The user normally performs the commit and push unless another workflow
is explicitly requested.

### Consequences

Git history should reflect meaningful project changes rather than
arbitrary editing checkpoints.

Failing or knowingly incomplete changes should not be treated as
completed feature commits.

------------------------------------------------------------------------

## ADR-015 --- No Credentials or Secrets in Git

**Status:** Accepted

### Decision

Credentials and sensitive authentication material must never be
committed to the repository.

This includes, where applicable:

-   API secrets;
-   access tokens;
-   refresh tokens;
-   passwords;
-   private keys;
-   OAuth credentials;
-   production authentication data.

### Consequences

Sensitive values must use appropriate local or operating-system
credential storage.

`.gitignore` provides an additional safeguard but is not a substitute
for proper secret handling.

Logs and error emails must also avoid leaking sensitive values.

------------------------------------------------------------------------

## ADR-016 --- Preserve Unicode and Croatian Characters

**Status:** Accepted

### Decision

SocialFlow will use Unicode throughout the application and UTF-8 for
project text files and textual external data where applicable.

The application must correctly preserve Croatian characters such as:

``` text
č ć ž š đ
Č Ć Ž Š Đ
```

### Context

SocialFlow will initially manage content written in Croatian and
English.

### Consequences

Unicode handling must be considered across:

-   UI input;
-   persistence;
-   API requests and responses;
-   tags and metadata;
-   logs;
-   file handling where applicable.

------------------------------------------------------------------------

## ADR-017 --- Isolate Multi-Platform Publishing Failures

**Status:** Accepted

### Decision

Publishing to multiple destinations will not be treated as a single
remote transaction.

Each destination must have an independently recorded result.

### Example

``` text
Facebook   -> Success
Instagram  -> Failure
WordPress  -> Success
```

### Consequences

Failure on one platform must not incorrectly report successful
destinations as failed.

The user should be able to determine which destinations succeeded and
which require further action.

------------------------------------------------------------------------

## ADR-018 --- Network Work Must Not Freeze the UI

**Status:** Accepted

### Decision

Long-running network operations and expensive processing must not block
the Qt user interface.

### Context

Publishing, synchronization, uploads, downloads, authentication, and
some image processing may take noticeable time.

### Consequences

A Qt-compatible background execution approach will be selected when this
functionality is implemented.

The exact mechanism is intentionally not fixed yet because it should be
chosen against concrete requirements rather than prematurely.

------------------------------------------------------------------------

## ADR-019 --- Centralized Logging and Production Error Reporting

**Status:** Accepted

### Decision

SocialFlow will have centralized application logging.

Important production/runtime failures will also be capable of generating
an email notification to a configured recipient.

### Consequences

Error email is supplemental reporting and does not replace local
logging.

Error reports must be sanitized before transmission.

The system should prevent uncontrolled repeated notifications for the
same failure.

------------------------------------------------------------------------

## ADR-020 --- Scope Is Controlled by Project Documentation

**Status:** Accepted

### Decision

Features should not be implemented merely because they appear useful.

New functionality must first be discussed and accepted.

Accepted functional requirements belong in `FEATURES.md`.

Significant technical decisions belong in this document.

Current system structure belongs in `ARCHITECTURE.md`.

### Consequences

Speculative "version 2" functionality and unrelated enhancements should
not be introduced during implementation unless explicitly accepted.

This keeps development aligned with the agreed SocialFlow scope.

------------------------------------------------------------------------

## ADR-021 --- Documentation Is Part of the Project

**Status:** Accepted

### Decision

Project documentation will be maintained alongside the source code.

Tracked documentation initially includes:

-   `README.md`
-   `FEATURES.md`
-   `ARCHITECTURE.md`
-   `DECISIONS.md`
-   `DEVELOPMENT.md`

Local AI-agent instructions will be maintained separately in `AGENTS.md`
and will not be committed to the repository.

### Consequences

Significant implementation changes should update relevant documentation
when the existing documentation would otherwise become inaccurate.

------------------------------------------------------------------------

## ADR-022 --- Packaging Technology Will Be Chosen Later

**Status:** Accepted

### Decision

SocialFlow must ultimately be distributable on Linux and Windows, but
the specific packaging technology will not be selected during initial
project setup.

### Context

Packaging requirements are easier to evaluate once the application
foundation, dependencies, assets, and runtime behavior are established.

### Consequences

The project avoids prematurely locking itself into a packaging solution.

Packaging will be evaluated as a deliberate project decision before
release work begins.

------------------------------------------------------------------------

## ADR-023 --- Prefer Small, Focused Modules and Classes

**Status:** Accepted

### Decision

SocialFlow will favor small, focused Python modules and classes with
clear responsibilities instead of large multi-purpose `.py` files.

There is no arbitrary maximum line count. File size is a design signal:
when a module becomes difficult to navigate or contains multiple
independent responsibilities, it should be decomposed into meaningful
components.

### Context

The project should remain easy to understand and modify as integrations,
UI, persistence, image processing, synchronization, and other
capabilities grow.

### Consequences

Related behavior should be separated according to responsibility.

Splitting code should improve discoverability and cohesion rather than
create many tiny files with no meaningful boundary.

------------------------------------------------------------------------

## ADR-024 --- Use a Predictable, Laravel-Inspired Project Hierarchy

**Status:** Accepted

### Decision

SocialFlow will use a predictable hierarchical organization inspired by
the discoverability of well-structured frameworks such as Laravel, while
remaining appropriate for a Python/PySide6 desktop application.

Laravel itself will not be introduced as part of the Python desktop
stack.

### Context

A developer should be able to infer where code belongs and where an
existing behavior is likely implemented.

### Consequences

Code should be grouped by clear responsibility and domain, including
areas such as:

-   application workflows;
-   domain concepts;
-   platform integrations;
-   persistence;
-   shared services;
-   user interface.

Directories should be introduced as needed rather than creating an
extensive empty hierarchy at project startup.

------------------------------------------------------------------------

## ADR-025 --- Use Meaningful, Responsibility-Oriented Names

**Status:** Accepted

### Decision

Files, directories, classes, methods, and services should use names that
communicate their purpose.

Generic dumping-ground modules should be avoided.

Examples of names to avoid as catch-all locations include:

``` text
utils.py
helpers.py
misc.py
manager.py
```

A name such as:

``` text
language_detector.py
```

is preferable when it accurately describes the responsibility.

### Consequences

Developers should be able to navigate the project by meaning rather than
by remembering where unrelated helper functions were accumulated.

Generic names remain acceptable only when they describe a genuinely
cohesive concept and do not become containers for unrelated behavior.

------------------------------------------------------------------------

## ADR-026 --- Favor Reuse Without Premature Abstraction

**Status:** Accepted

### Decision

Shared behavior should be implemented as reusable components when there
is a real shared responsibility.

Object-oriented programming should be used deliberately to establish
clear boundaries, state, lifecycle, replaceable behavior, and
testability.

The project will not force every operation into a class hierarchy merely
to appear object-oriented.

### Context

SocialFlow should have strong modularity and reuse while avoiding an
over-engineered architecture.

### Consequences

Duplication between platform integrations or UI components should be
reduced when a genuine common abstraction exists.

Platform differences must not be hidden behind an abstraction that
falsely implies identical behavior.

Simple stateless behavior may remain simple when a class provides no
practical benefit.

------------------------------------------------------------------------

## ADR-027 --- Language Detection Is a Dedicated Capability

**Status:** Accepted

### Decision

Croatian/English language detection will be implemented outside the Qt
post editor as a dedicated application/service capability.

Initial recognized content languages are:

-   Croatian (`HR`);
-   English (`EN`).

### Context

Language awareness affects UI presentation and post information, but
language detection is not a presentation responsibility.

Keeping it outside widgets makes the behavior reusable and independently
testable.

### Consequences

The UI consumes language information rather than implementing detection
logic itself.

The implementation may evolve independently from the post editor.

------------------------------------------------------------------------

## ADR-028 --- Automatic Language Detection Must Allow Uncertainty and Override

**Status:** Accepted

### Decision

Automatic Croatian/English detection will not be treated as infallible.

The application must support:

-   a detected language when sufficiently reliable;
-   an uncertain/undetermined state when appropriate;
-   manual user override.

### Context

Short captions, hashtags, product names, URLs, proper names, and
mixed-language content may not provide enough evidence for reliable
automatic classification.

### Consequences

Publishing must not depend on blindly accepting a language detector's
guess.

Tests should cover clear Croatian/English examples as well as ambiguous
input when the language service is implemented.

------------------------------------------------------------------------

## ADR-029 --- Language Identification Must Not Depend on Color Alone

**Status:** Accepted

### Decision

The post editor should use an explicit textual language indicator such
as:

``` text
HR
EN
```

Color, typography, or other visual styling may additionally distinguish
languages but must not be the only indication.

### Context

Visual styling can improve quick recognition, but color or font alone
can be ambiguous and less accessible.

### Consequences

The language state remains understandable without relying on a
particular color perception, font rendering, or theme.

The final visual treatment will be designed when the post editor UI is
implemented.

------------------------------------------------------------------------

## ADR-030 --- Separate Stable Constants from Environment Configuration

**Status:** Accepted

### Decision

Stable values that are intrinsic to the SocialFlow application may be
centralized in focused code modules such as `socialflow.constants`.

Environment-specific configuration, credentials, access tokens, secrets,
and machine-specific values must be handled separately and must not be
placed in the constants module.

### Context

Values such as the application name and default window dimensions are
stable application facts. Credentials and deployment-specific settings
have different security and lifecycle requirements.

### Consequences

Current stable constants include the application name, Qt organization
name, and default main-window dimensions.

A dedicated configuration mechanism will be introduced when
environment-based configuration is implemented.

------------------------------------------------------------------------

## ADR-031 --- Separate Main Window and Main Content Responsibilities

**Status:** Accepted

### Decision

The Qt main window and its primary content area will remain separate UI
components.

`MainWindow` owns top-level window behavior. `MainContent` owns the
primary content container and its internal layout.

### Context

The UI should remain modular from the beginning rather than allowing the
main window class to accumulate navigation, editors, platform controls,
and other unrelated responsibilities.

### Consequences

New UI areas should be introduced as focused components and composed
into the appropriate parent component.

The agreed initial top-level navigation sections are `Posts`,
`Accounts`, and `Settings`. Their navigation component will be
implemented separately rather than embedded directly into `MainWindow`.

------------------------------------------------------------------------

## Decision Maintenance

When a significant technical decision is proposed:

1.  Discuss the requirement or problem.
2.  Consider reasonable alternatives.
3.  Record the accepted decision when it materially affects the project.
4.  Implement the decision.
5.  Update `ARCHITECTURE.md` if the current architecture changes.

If an existing decision is replaced, do not silently rewrite project
history. Mark the previous decision as superseded where appropriate and
record the new decision separately.
