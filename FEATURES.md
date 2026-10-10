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
-   [ ] Implement application logging.
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

-   [~] Integrate WordPress through its REST API; authenticated connection verification is implemented, but publishing and other content operations are pending.
-   [x] Configure and persist the WordPress HTTPS site URL and username per account.
-   [x] Store WordPress application passwords in the OS credential store, not account JSON.
-   [x] Use stable account UUID-based credential keys and clean up secrets when accounts are removed or converted away from WordPress.
-   [x] Verify WordPress credentials with the authenticated REST API user endpoint.
-   [x] Report connected, invalid-credentials, unreachable, and error outcomes in the Accounts UI.
-   [x] Run verification in a background Qt worker and prevent concurrent checks.
-   [x] Defer main-window closing while verification runs and close automatically after thread cleanup.
-   [ ] Publish, retrieve, or update WordPress content through live APIs.

------------------------------------------------------------------------

## 5. Post Creation

-   [x] Provide a common post editor.
-   [x] Allow text content to be entered and edited.
-   [x] Allow images to be attached to posts.
-   [x] Allow applicable tags to be selected and carried by the post model; live platform metadata remains pending.
-   [x] Allow the user to choose one or more configured publishing accounts; each account retains its platform destination.
-   [~] Allow publishing to one configured account through the application publishing pipeline; live platform publishers are not implemented yet.
-   [~] Allow one publishing action to target multiple configured accounts; live platform publishers are not implemented yet.
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
-   [~] Display image-selection/validation errors in the editor; broader publishing/preparation error presentation remains to be expanded.
-   [ ] Verify live platform image requirements against official APIs before production integration.

------------------------------------------------------------------------

## 8. Tags and Platform Metadata

SocialFlow will provide a common interface for tags and similar metadata
while respecting the capabilities of each destination platform.

-   [~] Retrieve existing tags through the `TagProvider`/`ListTags` boundary; live platform providers are not implemented yet.
-   [x] Display available tags in the post editor.
-   [x] Allow existing tags to be selected and deselected.
-   [x] Allow manually entered tags to become part of the composed `Post`.
-   [~] Create new tags through `CreateTag` for every selected account; the current runtime uses `NullTagProvider`, so remote persistence is pending.
-   [x] Merge available tags from multiple selected accounts without duplicates.
-   [x] Refresh available tags when account selection changes.
-   [x] Disable new-tag creation when no publishing account is selected.
-   [ ] Implement destination-specific tag providers and verify each platform's actual tag/metadata semantics.
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
-   [ ] Retrieve recent posts from connected remote destinations.
-   [ ] Refresh the recent-post list from the remote platform.

------------------------------------------------------------------------

## 10. Updating Existing Posts

-   [x] Load editable content from a selected locally recorded publication.
-   [ ] Edit supported text fields.
-   [ ] Edit supported images where the destination API permits it.
-   [ ] Edit supported tags or metadata.
-   [ ] Send supported changes back to the original platform.
-   [ ] Refresh the local representation after a successful update.
-   [ ] Clearly report fields that cannot be changed because of platform
    API restrictions.
-   [ ] Report update failures without losing the user's local changes.

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

-   [~] Handle application errors without unnecessarily terminating
    SocialFlow; per-account publisher exceptions are captured, but broader
    exception handling remains to be completed.
-   [x] Display publishing failure reasons for each account in the Posts UI.
-   [ ] Record technical error information in application logs.
-   [~] Distinguish unconfigured publishers explicitly; broader error
    categorization is pending.
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

-   [ ] Maintain application logs.
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
-   [ ] Add tests for platform integration services using mocks/fakes
    where appropriate.
-   [x] Add tests for the implemented JSON/storage behavior.
-   [x] Add UI tests for the implemented PySide6 workflows.
-   [~] Add tests for important failure scenarios; unconfigured publishing,
    failure reporting, and partial publishing results are covered.
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
-   [x] Use `UnconfiguredPublisher` for destinations without live adapters;
    never report these attempts as successful external publishing.
-   [x] Avoid writing failed unconfigured attempts into successful local history.
-   [x] Display per-account failure reasons and cover the full UI-to-repository
    failure path with tests.
-   [ ] Implement authenticated live publisher adapters for Facebook, Instagram,
    and WordPress, with mocked API tests before live testing.

**Latest reported test checkpoint:** the full suite passed after the
asynchronous WordPress verification and shutdown work (exact count not recorded
in this archive). Automated HTTP tests use isolated clients/mocks; passing tests
do not constitute verification against a live WordPress website.

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