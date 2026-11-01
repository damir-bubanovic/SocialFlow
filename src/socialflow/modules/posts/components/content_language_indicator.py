from PySide6.QtWidgets import QLabel

from socialflow.application.language.post_language_classifier import (
    PostLanguageClassification,
)


class ContentLanguageIndicator(QLabel):
    """Display the detected language classification of a post."""

    _LABELS = {
        PostLanguageClassification.ENGLISH: "EN",
        PostLanguageClassification.CROATIAN: "HR",
        PostLanguageClassification.MIXED: "HR + EN",
        PostLanguageClassification.UNKNOWN: "?",
    }

    _COLORS = {
        PostLanguageClassification.ENGLISH: "#16a34a",
        PostLanguageClassification.CROATIAN: "#2563eb",
        PostLanguageClassification.MIXED: "#9333ea",
        PostLanguageClassification.UNKNOWN: "#6b7280",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setObjectName("contentLanguageIndicator")
        self.setToolTip("Automatically detected content language")
        self.setAccessibleName("Detected content language")

        self.set_classification(
            PostLanguageClassification.UNKNOWN
        )

    def set_classification(
        self,
        classification: PostLanguageClassification,
    ) -> None:
        """Update the displayed language and its visual styling."""
        self.setText(self._LABELS[classification])
        self.setAccessibleDescription(
            f"Detected content language: {self._LABELS[classification]}"
        )

        color = self._COLORS[classification]

        self.setStyleSheet(
            f"""
            QLabel#contentLanguageIndicator {{
                color: {color};
                border: 1px solid {color};
                border-radius: 4px;
                padding: 3px 8px;
                font-weight: 600;
            }}
            """
        )