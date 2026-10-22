# SocialFlow --- Features

## 1. Project Goal

SocialFlow is a cross-platform desktop application for creating,
managing, publishing, and updating content across multiple online
platforms from a single interface.

The initial supported platforms are:

-   Facebook
-   Instagram
-   WordPress

SocialFlow must run on:

-   Linux
-   Windows

The application will be developed in Python.

------------------------------------------------------------------------

## 2. Development Status

The project will be developed incrementally.

Feature status will use the following markers:

-   `[ ]` Not implemented
-   `[~]` In progress
-   `[x]` Implemented and tested

A feature is not considered complete until its relevant automated tests
pass.

------------------------------------------------------------------------

## 3. Application Foundation

-   [x] Create the initial Python project structure.
-   [x] Configure the Python virtual environment and dependencies.
-   [x] Implement the PySide6 / Qt desktop application foundation.
-   [ ] Implement application configuration management.
-   [x] Implement local account data storage using UTF-8 JSON in the platform-specific application data directory.
-   [~] Implement secure storage for credentials and access tokens; WordPress application passwords use OS-backed keyring storage, while other platform credentials remain pending.
-   [x] Initialize persistent rotating UTF-8 application logs at startup, with platform-specific storage and handler lifecycle tests.
-   [x] Implement automated testing infrastructure.
-   [ ] Implement development quality checks.
-   [~] Support Unicode throughout the application; account serialization and persistence are covered, while remaining future workflows still require verification.
-   [~] Support Croatian characters, including č, ć, ž, š, đ and their
    uppercase equivalents; account persistence is verified and remaining future workflows still require coverage.
-   [~] Support English content; manual language selection exists and remaining publishing/storage workflows are still in development.

------------------------------------------------------------------------

## 4. Account and Platform Connections

SocialFlow must allow users to configure and manage connections to
supported publishing platforms.

### Local account management

-   [x] Represent configured publishing accounts independently from platform types.
-   [x] Add, list, update, and remove configured accounts.
-   [x] Reject invalid and duplicate account entries.
-   [x] Persist configured accounts across application restarts.
-   [x] Store account data as readable UTF-8 JSON in a platform-specific application data directory.
-   [x] Keep the account form empty until an account is explicitly selected.
-   [x] Clear selection/form state after successful add, update, and remove operations.
-   [x] Synchronize account changes into the Posts page without restarting the application.

### Facebook

-   [ ] Connect SocialFlow to Facebook through the supported Meta APIs.
-   [ ] Authenticate and securely store the required authorization
    information.
-   [ ] Retrieve Facebook pages/accounts available to the authenticated
    user.
-   [ ] Allow the user to select the Facebook page used for publishing.
-   [ ] Detect and report expired or invalid authorization.

### Instagram

-   [ ] Connect SocialFlow to Instagram through the supported Meta APIs.
-   [ ] Authenticate and securely store the required authorization
    information.
-   [ ] Retrieve supported Instagram accounts available to the user.
-   [ ] Allow the user to select the Instagram account used for
    publishing.
-   [ ] Detect and report expired or invalid authorization.

### WordPress

-   [~] Integrate WordPress through its REST API; verification, text/image/tag publishing, tag listing/creation with confirmation for missing tags, recent-post retrieval, and text-only remote editing are implemented. Broader remote editing and live-site validation remain pending.
-   [x] Configure and persist the WordPress HTTPS site URL and username per account.
-   [x] Store WordPress application passwords in the OS credential store, not account JSON.
-   [x] Use stable account UUID-based credential keys and clean up secrets when accounts are removed or converted away from WordPress.
-   [x] Verify WordPress credentials with the authenticated REST API user endpoint.
-   [x] Report connected, invalid-credentials, unreachable, and error outcomes in the Accounts UI.
-   [x] Run verification in a background Qt worker and prevent concurrent checks.
-   [x] Defer main-window closing while verification runs and close automatically after thread cleanup.
-   [x] Route configured WordPress accounts to `WordPressPublisher` in the desktop runtime.
-   [x] Create WordPress posts with text through the authenticated HTTPS REST API.
-   [x] Upload prepared images to WordPress media and append Gutenberg image blocks.
-   [x] Validate HTTPS site URL, required text, prepared images, and available credentials before publishing.
-   [x] Resolve selected WordPress tags to remote IDs and assign them to new posts; reject missing or ambiguous matches at publishing time.
-   [x] Attempt reverse-order media cleanup after an upload failure; log deletion errors and preserve the original upload error.
-   [x] Preserve uploaded media if WordPress post creation subsequently fails (current deliberate behavior, not a remote rollback).
-   [x] Retrieve recent remote WordPress posts through authenticated REST API requests and a Qt background worker.
-   [x] Update existing remote WordPress post text through authenticated REST API requests and a Qt background worker.
-   [~] Integrate remote WordPress tags and metadata; listing, confirmed creation of missing tags, and assignment on new posts are implemented; editing existing remote metadata remains pending.
-   [ ] Verify publishing against a live WordPress installation.

------------------------------------------------------------------------

## 5. Post Creation

-   [x] Provide a common post editor.
-   [x] Allow text content to be entered and edited.
-   [x] Allow images to be attached to posts.
-   [x] Allow applicable tags to be selected and carried by the post model; live platform metadata remains pending.
-   [x] Allow the user to choose one or more configured publishing accounts; each account retains its platform destination.
-   [~] Allow publishing to one configured account through the application publishing pipeline; WordPress is wired to a real REST publisher, while Facebook/Instagram remain unconfigured.
-   [~] Allow one publishing action to target multiple configured accounts; WordPress can publish while unconfigured Facebook/Instagram destinations report independent failures.
-   [x] Display the publishing result separately for each destination.
-   [x] Handle partial publishing failures when one destination succeeds
    and another fails.
-   [ ] Prevent accidental duplicate publishing where practical.

------------------------------------------------------------------------

## 6. Text Content

-   [x] Support Croatian text in the current editor and publishing pipeline.
-   [x] Support English text in the current editor and publishing pipeline.
-   [ ] Preserve Unicode characters during editing, storage,
    synchronization, and publishing.
-   [ ] Respect platform-specific text limitations.
-   [ ] Validate content before publishing when a destination has
    specific requirements.

### Language Detection and Identification

-   [x] Apply rule-based Croatian/English detection to post paragraphs,
    including unknown results when evidence is insufficient.
-   [x] Display the currently selected language clearly in the post editor.
-   [x] Allow manual Croatian/English publishing-language selection independently of automatic content-language detection.
-   [x] Visually distinguish detected Croatian and English paragraphs using
    colored underlines, and show overall English/Croatian/mixed/unknown status.
-   [x] Use an explicit language indicator such as `HR` or `EN` so
    language is not communicated by color or typography alone.
-   [x] Use colored paragraph underlines and editor borders as additional
    language cues; text labels remain available.
-   [x] Represent uncertain or unclassified content as unknown rather than
    forcing a language classification.
-   [ ] Preserve the selected or detected language with the relevant
    local post information where required.

------------------------------------------------------------------------

## 7. Image Management

-   [x] Select supported images from the local computer (`.jpg`, `.jpeg`, `.png`, `.webp`).
-   [x] Preview selected images before publishing and allow individual removal or clearing.
-   [x] Read image dimensions and format through Pillow-backed image processing.
-   [x] Validate selected image files before they enter the post.
-   [x] Apply destination image profiles before publishing.
-   [x] Resize images when they exceed configured destination dimensions.
-   [x] Enforce configured destination aspect-ratio limits where applicable.
-   [x] Convert prepared output to the configured destination format.
-   [x] Generate destination-specific prepared image files without modifying the source image.
-   [x] Carry prepared-image metadata separately from the source `ImageAttachment`.
-   [x] Clean up temporary prepared image files after each publish attempt.
-   [x] Attempt cleanup of every partially prepared file after a processing error, even if one deletion fails.
-   [x] Preserve the original processing error and log failed partial-file deletions.
-   [x] Reserve unique output filenames without overwriting existing prepared images.
-   [~] Display image-selection/validation errors in the editor; broader publishing/preparation error presentation remains to be expanded.
-   [ ] Verify live platform image requirements against official APIs before production integration.

------------------------------------------------------------------------

## 8. Tags and Platform Metadata

SocialFlow will provide a common interface for tags and similar metadata
while respecting the capabilities of each destination platform.

-   [~] Retrieve existing tags through `TagProvider`/`ListTags`; authenticated WordPress retrieval is implemented, with a null fallback for other platforms.
-   [x] Display available tags in the post editor.
-   [x] Allow existing tags to be selected and deselected.
-   [x] Allow manually entered tags to become part of the composed `Post`.
-   [~] Create tags through `CreateTag`; WordPress accounts use `WordPressTagProvider` for remote creation, while unsupported destinations use `NullTagProvider`.
-   [x] Merge available tags from multiple selected accounts without duplicates.
-   [x] Refresh available tags when account selection changes.
-   [x] Disable new-tag creation when no publishing account is selected.
-   [~] Implement destination-specific tag providers; WordPress listing/creation and new-post tag assignment exist, while other platforms and remote-post tag editing remain pending.
-   [ ] Keep remote/local tag information synchronized where practical.
-   [ ] Handle platform differences instead of assuming all platforms implement tags identically.

------------------------------------------------------------------------

## 9. Recent Posts

-   [x] Record successful local publications with account, post, timestamp, and a stable `PublicationId`.
-   [x] Persist local publication history in UTF-8 `publications.json` storage.
-   [x] Migrate legacy publication-history records that do not yet contain an ID and persist the generated ID.
-   [x] Display up to the latest 5 locally recorded publications for the first selected configured account.
-   [x] Clearly identify the publication timestamp, platform, account, and post text in the recent-post list.
-   [x] Refresh local history after account selection changes and successful publish operations.
-   [x] Select a local historical publication and load its post into the editor.
-   [x] Restore text, selected language, images, and tags from an in-memory historical `Post` when loading it into the editor.
-   [~] Preserve publication history across restarts; ID/account/text/language/timestamp are persisted, while images and tags are not yet serialized in publication history.
-   [~] Retrieve recent posts from connected remote destinations; WordPress is implemented, Facebook/Instagram are pending.
-   [~] Refresh the remote-post list; WordPress loads on account selection and refreshes after successful edits, while other platforms are pending.

------------------------------------------------------------------------

## 10. Updating Existing Posts

-   [x] Load editable content from a selected locally recorded publication.
-   [~] Edit supported text fields; WordPress remote post content editing is implemented.
-   [ ] Edit supported images where the destination API permits it.
-   [ ] Edit supported tags or metadata.
-   [~] Send supported changes back to the original platform; WordPress text updates are implemented.
-   [~] Refresh the remote WordPress post list after a successful update; synchronization with local publication history remains pending.
-   [ ] Clearly report fields that cannot be changed because of platform
    API restrictions.
-   [x] Report WordPress remote-update failures and restore the editing controls without discarding the edited text.

------------------------------------------------------------------------

## 11. Synchronization

-   [ ] Synchronize supported account/page/site information.
-   [ ] Synchronize recent posts.
-   [ ] Synchronize tags and supported metadata.
-   [ ] Track the relationship between local data and remote platform
    objects.
-   [ ] Handle remote content that has been deleted.
-   [ ] Handle authorization expiration.
-   [ ] Handle temporary network failures.
-   [ ] Avoid silently overwriting conflicting or unexpected remote
    changes.

------------------------------------------------------------------------

## 12. Error Handling

-   [~] Handle application errors without unnecessarily terminating SocialFlow; per-account exceptions are isolated, logging filesystem errors do not prevent startup, and top-level startup failures return a nonzero exit code. Broader runtime exception handling remains pending.
-   [x] Display safe, categorized publishing failure messages for each account in the Posts UI.
-   [x] Record publishing failures with account/destination and exception type in application logs without including raw publishing exception messages or post text.
-   [x] Classify publishing errors as transient, permanent, or unknown; classification does not automatically control retry eligibility.
-   [~] Handle network and API failures; WordPress connection verification categorizes unreachable/error responses, while other operations remain pending.
-   [~] Handle authentication failures; WordPress connection verification reports invalid or missing credentials, while other platforms remain pending.
-   [ ] Handle platform rate limits where applicable.
-   [ ] Avoid exposing passwords, API secrets, access tokens, or other
    sensitive credentials in user-visible errors or logs.

------------------------------------------------------------------------

## 13. Error Email Notifications

-   [ ] Allow an error-report recipient email address to be configured.
-   [ ] Send notifications for important production/runtime errors.
-   [ ] Include useful diagnostic information in error notifications.
-   [ ] Never include passwords, access tokens, API secrets, or other
    sensitive credentials in error emails.
-   [ ] Prevent repeated identical failures from producing uncontrolled
    volumes of email.

------------------------------------------------------------------------

## 14. Logging and Audit

-   [x] Configure persistent UTF-8 rotating logs (2 MiB, three backups) at startup; prevent duplicate handlers and close replaced handlers.
-   [ ] Log important application operations.
-   [ ] Log publishing attempts and their results.
-   [ ] Log update attempts and their results.
-   [ ] Log synchronization failures.
-   [ ] Log unexpected errors and exceptions.
-   [ ] Keep sensitive authentication information out of logs.
-   [ ] Provide enough information to diagnose production problems.

------------------------------------------------------------------------

## 15. Testing

Testing is part of feature development rather than a final project
phase.

-   [x] Configure pytest and pytest-qt.
-   [x] Add unit tests for implemented application logic.
-   [x] Add tests for the implemented image-processing and preparation behavior.
-   [x] Add mocked/fake HTTP tests for the implemented WordPress verification, publishing, and media operations; future platform integrations still need tests.
-   [x] Add tests for the implemented JSON/storage behavior.
-   [x] Add UI tests for the implemented PySide6 workflows.
-   [~] Add tests for important failure scenarios; unconfigured publishing, partial results, WordPress upload/cleanup failures, and image-preparation exception preservation are covered; future integrations need coverage.
-   [~] Add regression tests for completed publishing safety and UI changes;
    continue for future fixes.
-   [x] Run relevant tests while developing each implemented feature.
-   [~] Run the full pytest suite at feature checkpoints; additional quality
    tooling is not yet configured.

No feature should be marked complete until its relevant tests pass.

------------------------------------------------------------------------

## 16. Security

-   [ ] Never store passwords or API secrets directly in source code.
-   [ ] Never commit credentials or access tokens to Git.
-   [~] Store sensitive credentials securely; WordPress application passwords use OS keyring, other platforms pending.
-   [ ] Protect locally stored authentication information.
-   [ ] Avoid sensitive information in logs.
-   [ ] Avoid sensitive information in error-report emails.
-   [ ] Validate data received from remote services.
-   [ ] Validate user-controlled input where necessary.

------------------------------------------------------------------------

## 17. Linux Support

-   [x] Develop and test SocialFlow on Linux.
-   [~] Support Linux Mint as the primary development environment; distributable-build verification remains pending.
-   [ ] Produce a distributable Linux application.
-   [ ] Verify application behavior outside the development environment.

------------------------------------------------------------------------

## 18. Windows Support

-   [ ] Support SocialFlow on Windows.
-   [ ] Test platform-specific behavior on Windows.
-   [ ] Produce a distributable Windows application.
-   [ ] Provide a practical Windows installation/distribution method.
-   [ ] Verify application behavior outside the development environment.

------------------------------------------------------------------------

## 19. Documentation

-   [x] Maintain the public README.
-   [x] Maintain the feature roadmap.
-   [x] Maintain architecture documentation.
-   [x] Record significant architecture and technology decisions.
-   [x] Maintain development/setup instructions.
-   [x] Keep documentation synchronized at development checkpoints; continue updating it as implementation evolves.

------------------------------------------------------------------------

## 20. Release Readiness

Before SocialFlow is considered ready for a production release:

-   [ ] All required features for the release are implemented.
-   [ ] Relevant automated tests pass.
-   [ ] Full test suite passes.
-   [ ] Quality checks pass.
-   [ ] Linux build is tested.
-   [ ] Windows build is tested.
-   [ ] Authentication and credential handling are reviewed.
-   [ ] Application logging is reviewed.
-   [ ] Production error reporting is tested.
-   [ ] Platform integrations are tested against their supported APIs.
-   [ ] Documentation is up to date.
-   [ ] No credentials, tokens, private user data, or development
    artifacts are included in the repository or application package.

------------------------------------------------------------------------


### Current language and publishing-safety checkpoint

-   [x] Classify full posts as English, Croatian, mixed, or unknown using
    paragraph-level language detection.
-   [x] Show an explicit detected-content label (`EN`, `HR`, `HR + EN`, `?`)
    with accessible descriptions; manual publishing-language selection is separate.
-   [x] Preserve mixed-language text, paragraph breaks, and Croatian characters
    as one intact post per selected destination; do not translate or split.
-   [x] Use `UnconfiguredPublisher` for Facebook/Instagram, while routing configured WordPress accounts to the live REST publisher; never report unconfigured attempts as successful external publishing.
-   [x] Avoid writing failed unconfigured attempts into successful local history.
-   [x] Display per-account failure reasons and cover the full UI-to-repository
    failure path with tests.
-   [~] Implement authenticated live publisher adapters: WordPress post/media publishing is implemented with mocked API tests; Facebook and Instagram remain pending, and live WordPress testing is outstanding.

**Test checkpoint:** The developer reported **1081 passing tests** after Phase 21.9.21. This documentation update does not rerun tests. Mocked HTTP tests do not prove live WordPress behavior.
------------------------------------------------------------------------

## 21. Scope Management

New functionality should not be added simply because it may be useful.

A new feature should first be:

1.  Discussed.
2.  Added to this document if accepted.
3.  Designed where architectural changes are required.
4.  Implemented.
5.  Tested.
6.  Marked complete only after verification.

This document represents the agreed functional scope and roadmap for
SocialFlow.

## 22. Background Publishing, Retry, and Startup Reliability (Implemented)

-   [x] Execute publishing in a Qt worker/controller instead of blocking the Posts UI.
-   [x] Report per-account progress and final results through Qt signals.
-   [x] Prevent overlapping publish requests while a worker is active.
-   [x] Defer main-window closing until active publishing/verification workers finish.
-   [x] Isolate individual account failures, including unexpected publisher exceptions.
-   [x] Build a retry request containing only accounts that failed in the previous attempt.
-   [x] Disable **Retry Failed** when there are no failed accounts or after retry succeeds.
-   [x] Invalidate retry state when draft text, language, accounts, images, or tags change.
-   [x] Format transient/permanent/unknown failures into safe user-facing messages.
-   [x] Log safe per-account technical diagnostics.
-   [x] Handle persistent-log setup `OSError` without aborting application startup.
-   [x] Log main-window initialization failures and propagate the original exception.
-   [x] Return nonzero from `run()` when application creation or window display fails.
-   [ ] Review duplicate diagnostics for main-window construction failures.
-   [ ] Review startup resource cleanup and fallback logging behavior.
-   [ ] Add production email error notifications and configuration.

**Remaining product work:** Facebook/Instagram adapters, live WordPress
validation, remote image/metadata editing,
publication-history image/tag serialization, production-grade credential/backend
checks, and Linux/Windows packaging remain separate tasks. Publishing error classification does **not**
automatically limit manual retry to transient errors.

## 23. WordPress Remote Posts and Editing (Phase 19)

-   [x] Introduce typed remote-post models, REST retrieval/parser components, and application use cases.
-   [x] Retrieve recent WordPress posts asynchronously and display them in a dedicated panel separate from local history.
-   [x] Track the WordPress account associated with loaded remote posts.
-   [x] Discard stale remote-load results after account changes.
-   [x] Select a remote post and edit its text content in a dedicated editor.
-   [x] Reject empty or unchanged content and prevent overlapping updates.
-   [x] Update the selected remote post through the account's credentials and remote ID.
-   [x] Refresh remote posts after a successful save.
-   [x] Preserve edited text and restore controls after failed updates.
-   [x] Guard against cross-account updates, stale completions, and new starts during shutdown.
-   [x] Test success/error signal ordering, worker cleanup, and QThread shutdown paths.
-   [ ] Support editing remote images, tags, or other metadata.
-   [ ] Verify retrieval and editing against a live WordPress site.

**Historical Phase 19 full-suite checkpoint:** 905 passing tests. **Latest developer-reported checkpoint:** 1081 passing tests after Phase 21.9.21.

## 24. WordPress Tag Confirmation and Assignment (Phases 21.2–21.9.14)

-   [x] Resolve selected WordPress tags to remote numeric IDs when creating posts.
-   [x] Normalize Unicode tag names consistently for lookup, duplicate detection, and creation.
-   [x] Detect missing tags and prepare a creation plan before publishing.
-   [x] Require explicit user confirmation before creating missing WordPress tags.
-   [x] Cancel publishing when missing-tag creation is declined or preparation fails.
-   [x] Create approved tags through a Qt worker/controller before publishing.
-   [x] Validate returned tag IDs and names and reject ambiguous remote matches.
-   [x] Prevent duplicate publish requests during tag preparation or creation.
-   [x] Cover successful, rejected, duplicate, and error workflows with automated tests.
-   [ ] Verify tag lookup, creation, and post assignment against a live WordPress site.
-   [ ] Support editing tags on existing remote WordPress posts.

## 25. Publishing Lifecycle and Recovery (Phases 21.9.15–21.9.21)

-   [x] Log unexpected worker exceptions with traceback while displaying safe UI errors.
-   [x] Forward publishing progress and completion through the Qt controller.
-   [x] Clean up worker threads on success, failure, and shutdown.
-   [x] Reject starts after shutdown and prevent overlapping operations.
-   [x] Allow publishing again after ordinary and unexpected failures.
-   [x] Make controller shutdown idempotent and test repeated shutdown paths.
-   [x] Defer main-window closing during active publishing and complete closing after success or failure.
-   [x] Ignore repeated close requests until publishing finishes, without duplicate page shutdown.
-   [x] Clear stale Posts-page retry state after unexpected worker errors.
-   [x] Verify that a subsequent publish can succeed after an unexpected worker error.

**Latest developer-reported full-suite checkpoint:** **1081 passing tests**
(October 22, 2026). This is not a fresh test run or live integration result.