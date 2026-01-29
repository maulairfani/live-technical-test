"""
Custom exceptions for the Recommendation System.
"""

from fastapi import status


class RecommendationException(Exception):
    """Base exception for all recommendation system errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# ============ User Related Exceptions ============


class UserNotFoundException(RecommendationException):
    """Raised when a user is not found in the system."""

    def __init__(self, user_id: str):
        super().__init__(
            message=f"User with ID '{user_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class InsufficientUserDataException(RecommendationException):
    """Raised when user doesn't have enough interaction data for personalization."""

    def __init__(self, user_id: str, min_interactions: int = 5):
        super().__init__(
            message=f"User '{user_id}' has insufficient interaction data. Minimum required: {min_interactions}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# ============ Content Related Exceptions ============


class ContentNotFoundException(RecommendationException):
    """Raised when content/item is not found."""

    def __init__(self, content_id: str):
        super().__init__(
            message=f"Content with ID '{content_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class InvalidContentTypeException(RecommendationException):
    """Raised when an invalid content type is requested."""

    def __init__(self, content_type: str, valid_types: list):
        super().__init__(
            message=f"Invalid content type '{content_type}'. Valid types: {valid_types}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


# ============ Recommendation Related Exceptions ============


class NoRecommendationsAvailableException(RecommendationException):
    """Raised when no recommendations can be generated."""

    def __init__(self, reason: str = "No matching content found"):
        super().__init__(
            message=f"Unable to generate recommendations: {reason}",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class SimilarUsersNotFoundException(RecommendationException):
    """Raised when no similar users can be found for collaborative filtering."""

    def __init__(self, user_id: str):
        super().__init__(
            message=f"No similar users found for user '{user_id}'",
            status_code=status.HTTP_404_NOT_FOUND,
        )


# ============ Data Related Exceptions ============


class DataLoadException(RecommendationException):
    """Raised when there's an error loading data files."""

    def __init__(self, file_path: str, reason: str = ""):
        message = f"Failed to load data from '{file_path}'"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class InvalidDataFormatException(RecommendationException):
    """Raised when data format is invalid or corrupted."""

    def __init__(self, details: str = ""):
        message = "Invalid data format"
        if details:
            message += f": {details}"
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============ Model Related Exceptions ============


class ModelNotReadyException(RecommendationException):
    """Raised when recommendation model is not initialized or ready."""

    def __init__(self, model_name: str = "Recommendation Model"):
        super().__init__(
            message=f"{model_name} is not ready. Please try again later.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
