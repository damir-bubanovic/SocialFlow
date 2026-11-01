
"""Backward-compatible import for the remote tag creation plan."""

from socialflow.modules.posts.models.remote_tag_creation_plan import (
    RemoteTagCreationPlan,
)

WordPressTagCreationPlan = RemoteTagCreationPlan
