# SocialFlow

SocialFlow is a cross-platform desktop application for creating, managing,
publishing, and updating content across multiple online platforms from a
single interface.

## Supported Platforms

SocialFlow is being designed to integrate with:

- Facebook
- Instagram
- WordPress

External integrations will use the officially supported APIs and capabilities
available for each platform.

## Features

SocialFlow is planned to provide:

- Create and edit posts from one desktop application.
- Publish content to one or multiple platforms.
- Work with text and images.
- Prepare images for platform-specific requirements.
- Retrieve and manage supported tags and metadata.
- Display the latest posts from connected pages, accounts, and websites.
- Edit and update existing posts where supported by the destination platform.
- Handle publishing results independently for each platform.
- Support Croatian and English content with language identification.
- Automatically detect Croatian or English content where reliable, with manual
  language selection when needed.
- Preserve Unicode characters, including Croatian characters such as
  č, ć, ž, š, and đ.
- Maintain application logs and production error reporting.
- Run on both Linux and Windows.

## Technology

SocialFlow is being developed with:

- Python
- PySide6 / Qt 6
- SQLite
- SQLAlchemy
- HTTPX
- Pillow
- pytest

## Development Status

SocialFlow is currently under active development.

The project is being developed incrementally, with automated testing and
quality checks performed as features are implemented.

## Documentation

Detailed project documentation is available in:

- [`FEATURES.md`](FEATURES.md) — feature requirements and project roadmap.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — current technical architecture.
- [`DECISIONS.md`](DECISIONS.md) — significant technical decisions and their
  reasoning.
- [`DEVELOPMENT.md`](DEVELOPMENT.md) — development environment, workflow,
  testing, and setup instructions.

## Operating Systems

Target operating systems:

- Linux
- Windows

Linux Mint is currently used as the primary development environment.

## Project Scope

SocialFlow focuses on providing a unified desktop workflow for managing
content across supported publishing platforms.

Platform-specific functionality depends on the capabilities and restrictions
of the official APIs provided by Facebook/Instagram and WordPress.