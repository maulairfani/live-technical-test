import logging
from datetime import timedelta

import pandas as pd

from src.repositories.content_repo import ContentRepo
from src.exceptions import DataLoadException, NoRecommendationsAvailableException

from .schema import GlobalRecommendationRequest, GlobalRecommendationResponse

logger = logging.getLogger(__name__)


class GlobalRecommendationService:
    def __init__(self, data_path: str = "data/data_joined.csv"):
        self.content_repo = ContentRepo()
        try:
            self.df = pd.read_csv(data_path)
            self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])
        except FileNotFoundError as e:
            raise DataLoadException(file_path=data_path, reason="File not found") from e
        except pd.errors.EmptyDataError as e:
            raise DataLoadException(file_path=data_path, reason="File is empty") from e
        except pd.errors.ParserError as e:
            raise DataLoadException(
                file_path=data_path, reason="Invalid CSV format"
            ) from e

        # Calculate estimated rating
        self.df["rating"] = self.df.apply(self._calculate_quality_score, axis=1)

    def _calculate_quality_score(self, row) -> float:
        """
        Bobot interaksi:
        - Like/Complete/Save = 5 poin
        - Play lama (>60s) = 3 poin
        - Skip/Play bentar = 1 poin
        """
        if row["event_type"] in ["like", "complete", "save"]:
            return 5.0
        elif row["event_type"] == "play" and row["watch_seconds"] > 60:
            return 3.0
        return 1.0

    def recommend_popular(
        self, req: GlobalRecommendationRequest
    ) -> GlobalRecommendationResponse:
        # Set default date to latest date in data if not provided
        if req.date is None:
            req.date = self.df["timestamp"].max()

        # Get recent data based on lookback days
        cutoff_date = req.date - timedelta(days=req.lookback_days)
        recent_df = self.df[self.df["timestamp"] >= cutoff_date]

        if recent_df.empty:
            raise NoRecommendationsAvailableException(
                reason=f"No data found in the last {req.lookback_days} days"
            )

        # Filter based on requested content types
        recent_df = recent_df[recent_df["content_type"].isin(req.content_types)]

        if recent_df.empty:
            raise NoRecommendationsAvailableException(
                reason=f"No content found for types: {req.content_types}"
            )

        # Calculate total score per item (Aggregation)
        # Trending formula: Sum(Quality Score)
        # Items that are liked by many users recently will have high scores
        trending_scores = recent_df.groupby("item_id")["rating"].sum().reset_index()

        # Sort (Find Top K)
        top_items = trending_scores.sort_values("rating", ascending=False).head(
            req.top_k
        )

        # Format Output
        results = []
        for _, row in top_items.iterrows():
            item_id = row["item_id"]
            total_score = row["rating"]

            content = self.content_repo.get_content_by_id(item_id)
            if not content:
                logger.warning("Content not found for item_id: %s", item_id)
                continue

            content.score = total_score
            results.append(content)

        return GlobalRecommendationResponse(top_k=req.top_k, items=results)
