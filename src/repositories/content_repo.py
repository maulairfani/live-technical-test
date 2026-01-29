import pandas as pd

from src.schemas.content import Content
from src.exceptions import DataLoadException


class ContentRepo:
    """Content Repository for accessing content data."""

    def __init__(self, data_path: str = "data/items.csv"):
        try:
            self.df = pd.read_csv(data_path)
        except FileNotFoundError as e:
            raise DataLoadException(file_path=data_path, reason="File not found") from e
        except pd.errors.EmptyDataError as e:
            raise DataLoadException(file_path=data_path, reason="File is empty") from e
        except pd.errors.ParserError as e:
            raise DataLoadException(
                file_path=data_path, reason="Invalid CSV format"
            ) from e

    def get_content_by_id(self, content_id: str) -> Content | None:
        content_row = self.df[self.df["item_id"] == content_id]
        if content_row.empty:
            return None
        return Content(**content_row.iloc[0].to_dict())
