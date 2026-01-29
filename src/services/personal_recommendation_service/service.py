import logging

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from src.schemas.content import Content
from src.repositories.content_repo import ContentRepo
from src.exceptions import (
    DataLoadException,
    SimilarUsersNotFoundException,
    NoRecommendationsAvailableException,
)

from .schema import PersonalRecommendationRequest, PersonalRecommendationResponse

logger = logging.getLogger(__name__)


class PersonalRecommendationService:
    def __init__(self, data_path: str = "data/data_joined.csv"):
        self.content_repo = ContentRepo()
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

        # Calculate estimated rating
        self.df["rating"] = self.df.apply(self._calculate_implicit_rating, axis=1)

        self.data_clean = (
            self.df.groupby(["user_id", "item_id", "age", "content_type", "genre"])[
                "rating"
            ]
            .max()
            .reset_index()
        )

        self.user_top_genre = {}
        user_groups = self.data_clean.groupby("user_id")
        for user_id, group in user_groups:
            top_genre = group.groupby("genre")["rating"].sum().idxmax()
            self.user_top_genre[user_id] = top_genre

        self.matrix = self.data_clean.pivot(
            index="user_id", columns="item_id", values="rating"
        ).fillna(0)

        self.user_ids = self.matrix.index.tolist()
        self.item_ids = self.matrix.columns.tolist()

        self.user_to_idx = {uid: i for i, uid in enumerate(self.user_ids)}
        self.idx_to_user = {i: uid for i, uid in enumerate(self.user_ids)}

        # Create similarity matrix based on estimated rating
        sim_interaction = cosine_similarity(self.matrix)

        user_meta = (
            self.data_clean[["user_id", "age"]]
            .drop_duplicates("user_id")
            .set_index("user_id")
        )
        ages = user_meta.reindex(self.user_ids)["age"].values

        # Create similarity matrix based on age
        age_diff = np.abs(ages.reshape(-1, 1) - ages.reshape(1, -1))
        sim_age = 1 / (1 + (age_diff / 10.0))

        # Combine similarity matrix based on estimated rating and age
        self.similarity_matrix = (0.7 * sim_interaction) + (0.3 * sim_age)

    def _calculate_implicit_rating(self, row) -> float:
        if row["event_type"] in ["like", "complete", "save"]:
            return 5.0
        elif row["event_type"] == "play" and row["watch_seconds"] > 60:
            return 3.0
        return 1.0

    def recommend_for_user(
        self, req: PersonalRecommendationRequest
    ) -> PersonalRecommendationResponse:
        user_id = req.user_id

        if user_id not in self.user_to_idx:
            # Fallback to global recommendations for new users
            from src.services.global_recommendation_service.service import (
                GlobalRecommendationService,
                GlobalRecommendationRequest,
            )

            logger.info(
                "User %s not found, falling back to global recommendations", user_id
            )
            global_service = GlobalRecommendationService()
            _res = global_service.recommend_popular(
                GlobalRecommendationRequest(
                    top_k=req.top_k,
                    date=None,
                    content_types=req.content_types,
                )
            )
            return PersonalRecommendationResponse(
                user_id=user_id,
                top_k=req.top_k,
                items=_res.items,
                fallback_used=True,
            )

        u_idx = self.user_to_idx[user_id]
        sim_scores = self.similarity_matrix[u_idx]

        # Get top P neighbors
        neighbor_indices = np.argsort(sim_scores)[-req.top_p : -1][::-1]

        if len(neighbor_indices) == 0:
            raise SimilarUsersNotFoundException(user_id=user_id)

        # Get watched items of user_id
        watched_items = set(
            self.data_clean[self.data_clean["user_id"] == user_id]["item_id"]
        )

        # Get favorite genre of user_id
        fav_genre = self.user_top_genre.get(user_id)

        candidates = {}
        for nb_idx in neighbor_indices:
            similarity = sim_scores[nb_idx]

            nb_ratings = self.matrix.iloc[nb_idx]
            liked_items = nb_ratings[nb_ratings > 0].index.tolist()

            for item_id in liked_items:
                # Skip if item already watched
                if item_id in watched_items:
                    continue

                content = self.content_repo.get_content_by_id(item_id)
                if not content:
                    logger.warning("Content not found for item_id: %s", item_id)
                    continue

                # Skip if content type not in request
                if content.content_type not in req.content_types:
                    continue

                rating_val = nb_ratings[item_id]
                score = similarity * rating_val

                # Boost if favorite genre
                if fav_genre and content.genre == fav_genre:
                    score *= 1.2

                if item_id not in candidates:
                    candidates[item_id] = 0
                candidates[item_id] += score

        if not candidates:
            raise NoRecommendationsAvailableException(
                reason=f"No unwatched content found for user '{user_id}'"
            )

        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)

        results = []
        for item_id, score in sorted_candidates[: req.top_k]:
            content = self.content_repo.get_content_by_id(item_id)
            if not content:
                logger.warning("Content not found for item_id: %s", item_id)
                continue

            content.score = score
            results.append(content)

        return PersonalRecommendationResponse(
            user_id=user_id,
            top_k=req.top_k,
            items=results,
            fallback_used=False,
        )
