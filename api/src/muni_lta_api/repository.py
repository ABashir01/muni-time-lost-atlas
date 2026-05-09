"""Targeted read queries for the historical/static FastAPI endpoints."""

from __future__ import annotations

import json
from typing import Any

from .db import Database
from .models import (
    CompareResponse,
    MapRoutesResponse,
    RankedRouteSummary,
    RankingMetric,
    RankingMode,
    RankingsResponse,
    RouteMapFeature,
    RouteSegmentsResponse,
    RouteSummary,
    SegmentFeature,
    TimeWindow,
)


_METRIC_COLUMNS = {
    RankingMetric.TYPICAL_TRIP_LOSS_MINUTES: "typical_trip_loss_minutes",
    RankingMetric.WAITING_LOSS_MINUTES: "waiting_loss_minutes",
    RankingMetric.IN_VEHICLE_LOSS_MINUTES: "in_vehicle_loss_minutes",
}


class HistoricalApiRepository:
    """Thin repository over the dbt-managed marts and serving relations."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def get_rankings(
        self,
        *,
        window: TimeWindow,
        metric: RankingMetric,
        mode: RankingMode,
    ) -> RankingsResponse:
        metric_column = _METRIC_COLUMNS[metric]
        rows = self._database.fetch_all(
            f"""
            SELECT
                summary.route_id,
                summary.route_name,
                summary.route_short_name,
                summary.route_long_name,
                summary.window_key,
                summary.typical_trip_loss_minutes,
                summary.waiting_loss_minutes,
                summary.in_vehicle_loss_minutes,
                hour_band.worst_time_band,
                summary.worst_stop_wait_label,
                summary.worst_segment_label,
                summary.matched_observed_stop_event_count,
                summary.resolved_unmatched_observation_count,
                summary.matched_headway_interval_count,
                summary.matched_full_trip_count,
                summary.metric_updated_at
            FROM marts.route_window_summary AS summary
            LEFT JOIN LATERAL (
                SELECT
                    CONCAT(
                        LPAD(hours.hour_local::TEXT, 2, '0'),
                        ':00-',
                        LPAD(hours.hour_local::TEXT, 2, '0'),
                        ':59'
                    ) AS worst_time_band
                FROM marts.route_hour_summary AS hours
                WHERE hours.route_id = summary.route_id
                ORDER BY
                    hours.typical_trip_loss_minutes DESC NULLS LAST,
                    hours.direction_id,
                    hours.hour_local
                LIMIT 1
            ) AS hour_band ON TRUE
            WHERE summary.window_key = %s
            ORDER BY summary.{metric_column} DESC NULLS LAST, summary.route_id
            """,
            [window.value],
        )

        ranked_routes = [
            RankedRouteSummary.model_validate(
                {
                    **self._normalize_route_summary_row(row),
                    "rank": index,
                }
            )
            for index, row in enumerate(rows, start=1)
        ]
        return RankingsResponse(
            window=window,
            metric=metric,
            mode=mode,
            routes=ranked_routes,
        )

    def get_route_summary(
        self,
        *,
        route_id: str,
        window: TimeWindow,
        direction_id: int | None,
    ) -> RouteSummary | None:
        if direction_id is None:
            row = self._database.fetch_one(
                """
                SELECT
                    summary.route_id,
                    summary.route_name,
                    summary.route_short_name,
                    summary.route_long_name,
                    summary.window_key,
                    summary.typical_trip_loss_minutes,
                    summary.waiting_loss_minutes,
                    summary.in_vehicle_loss_minutes,
                    hour_band.worst_time_band,
                    summary.worst_stop_wait_label,
                    summary.worst_segment_label,
                    summary.matched_observed_stop_event_count,
                    summary.resolved_unmatched_observation_count,
                    summary.matched_headway_interval_count,
                    summary.matched_full_trip_count,
                    summary.metric_updated_at
                FROM marts.route_window_summary AS summary
                LEFT JOIN LATERAL (
                    SELECT
                        CONCAT(
                            LPAD(hours.hour_local::TEXT, 2, '0'),
                            ':00-',
                            LPAD(hours.hour_local::TEXT, 2, '0'),
                            ':59'
                        ) AS worst_time_band
                    FROM marts.route_hour_summary AS hours
                    WHERE hours.route_id = summary.route_id
                    ORDER BY
                        hours.typical_trip_loss_minutes DESC NULLS LAST,
                        hours.direction_id,
                        hours.hour_local
                    LIMIT 1
                ) AS hour_band ON TRUE
                WHERE summary.route_id = %s
                  AND summary.window_key = %s
                """,
                [route_id, window.value],
            )
        else:
            row = self._database.fetch_one(
                """
                SELECT
                    summary.route_id,
                    summary.route_name,
                    summary.route_short_name,
                    summary.route_long_name,
                    summary.direction_id,
                    summary.direction_label,
                    summary.window_key,
                    summary.typical_trip_loss_minutes,
                    summary.waiting_loss_minutes,
                    summary.in_vehicle_loss_minutes,
                    hour_band.worst_time_band,
                    summary.worst_stop_wait_label,
                    summary.worst_segment_label,
                    summary.matched_observed_stop_event_count,
                    summary.resolved_unmatched_observation_count,
                    summary.matched_headway_interval_count,
                    summary.matched_full_trip_count,
                    summary.metric_updated_at
                FROM marts.route_direction_summary AS summary
                LEFT JOIN LATERAL (
                    SELECT
                        CONCAT(
                            LPAD(hours.hour_local::TEXT, 2, '0'),
                            ':00-',
                            LPAD(hours.hour_local::TEXT, 2, '0'),
                            ':59'
                        ) AS worst_time_band
                    FROM marts.route_hour_summary AS hours
                    WHERE hours.route_id = summary.route_id
                      AND hours.direction_id IS NOT DISTINCT FROM summary.direction_id
                    ORDER BY
                        hours.typical_trip_loss_minutes DESC NULLS LAST,
                        hours.hour_local
                    LIMIT 1
                ) AS hour_band ON TRUE
                WHERE summary.route_id = %s
                  AND summary.direction_id = %s
                  AND summary.window_key = %s
                """,
                [route_id, direction_id, window.value],
            )

        if row is None:
            return None
        return RouteSummary.model_validate(self._normalize_route_summary_row(row))

    def get_route_segments(
        self,
        *,
        route_id: str,
        window: TimeWindow,
        direction_id: int,
    ) -> RouteSegmentsResponse | None:
        rows = self._database.fetch_all(
            """
            SELECT
                segment.route_id,
                segment.route_name,
                segment.route_short_name,
                segment.route_long_name,
                segment.direction_id,
                segment.direction_label,
                segment.window_key,
                segment.shape_id,
                segment.segment_strategy,
                segment.segment_sequence,
                segment.from_stop_id,
                segment.from_stop_name,
                segment.to_stop_id,
                segment.to_stop_name,
                segment.segment_label,
                segment.scheduled_segment_minutes,
                segment.segment_in_vehicle_loss_minutes,
                segment.matched_trip_segment_count,
                segment.metric_updated_at,
                ST_AsGeoJSON(segment.geom)::TEXT AS geometry_json
            FROM serving.route_segment_layer AS segment
            WHERE segment.route_id = %s
              AND segment.direction_id = %s
              AND segment.window_key = %s
            ORDER BY segment.segment_sequence
            """,
            [route_id, direction_id, window.value],
        )
        if not rows:
            return None

        first_row = rows[0]
        features = [
            SegmentFeature.model_validate(
                {
                    "geometry": json.loads(row["geometry_json"]),
                    "properties": self._normalize_segment_properties_row(row),
                }
            )
            for row in rows
        ]

        return RouteSegmentsResponse(
            route_id=first_row["route_id"],
            route_name=first_row["route_name"],
            route_short_name=first_row["route_short_name"],
            route_long_name=first_row["route_long_name"],
            window=window,
            direction_id=first_row["direction_id"],
            direction_label=first_row["direction_label"],
            features=features,
            metric_updated_at=first_row["metric_updated_at"],
        )

    def get_compare(
        self,
        *,
        route_ids: list[str],
        window: TimeWindow,
    ) -> CompareResponse | None:
        placeholders = ", ".join(["%s"] * len(route_ids))
        rows = self._database.fetch_all(
            f"""
            SELECT
                summary.route_id,
                summary.route_name,
                summary.route_short_name,
                summary.route_long_name,
                summary.window_key,
                summary.typical_trip_loss_minutes,
                summary.waiting_loss_minutes,
                summary.in_vehicle_loss_minutes,
                hour_band.worst_time_band,
                summary.worst_stop_wait_label,
                summary.worst_segment_label,
                summary.matched_observed_stop_event_count,
                summary.resolved_unmatched_observation_count,
                summary.matched_headway_interval_count,
                summary.matched_full_trip_count,
                summary.metric_updated_at
            FROM marts.route_window_summary AS summary
            LEFT JOIN LATERAL (
                SELECT
                    CONCAT(
                        LPAD(hours.hour_local::TEXT, 2, '0'),
                        ':00-',
                        LPAD(hours.hour_local::TEXT, 2, '0'),
                        ':59'
                    ) AS worst_time_band
                FROM marts.route_hour_summary AS hours
                WHERE hours.route_id = summary.route_id
                ORDER BY
                    hours.typical_trip_loss_minutes DESC NULLS LAST,
                    hours.direction_id,
                    hours.hour_local
                LIMIT 1
            ) AS hour_band ON TRUE
            WHERE summary.window_key = %s
              AND summary.route_id IN ({placeholders})
            """,
            [window.value, *route_ids],
        )
        rows_by_route_id = {row["route_id"]: row for row in rows}
        missing_route_ids = [
            route_id for route_id in route_ids if route_id not in rows_by_route_id
        ]
        if missing_route_ids:
            return None

        ordered_routes = [
            RouteSummary.model_validate(
                self._normalize_route_summary_row(rows_by_route_id[route_id])
            )
            for route_id in route_ids
        ]
        return CompareResponse(
            window=window,
            route_ids=route_ids,
            routes=ordered_routes,
        )

    def get_map_routes(
        self,
        *,
        window: TimeWindow,
        metric: RankingMetric,
    ) -> MapRoutesResponse:
        metric_column = _METRIC_COLUMNS[metric]
        rows = self._database.fetch_all(
            f"""
            SELECT
                routes.route_id,
                routes.route_name,
                routes.route_short_name,
                routes.route_long_name,
                routes.window_key,
                routes.typical_trip_loss_minutes,
                routes.waiting_loss_minutes,
                routes.in_vehicle_loss_minutes,
                hour_band.worst_time_band,
                routes.worst_stop_wait_label,
                routes.worst_segment_label,
                summary.matched_observed_stop_event_count,
                summary.resolved_unmatched_observation_count,
                summary.matched_headway_interval_count,
                summary.matched_full_trip_count,
                routes.metric_updated_at,
                routes.{metric_column} AS metric_value,
                ST_AsGeoJSON(routes.geom)::TEXT AS geometry_json
            FROM serving.route_map_layer AS routes
            JOIN marts.route_window_summary AS summary
              ON summary.route_id = routes.route_id
             AND summary.window_key = routes.window_key
            LEFT JOIN LATERAL (
                SELECT
                    CONCAT(
                        LPAD(hours.hour_local::TEXT, 2, '0'),
                        ':00-',
                        LPAD(hours.hour_local::TEXT, 2, '0'),
                        ':59'
                    ) AS worst_time_band
                FROM marts.route_hour_summary AS hours
                WHERE hours.route_id = routes.route_id
                ORDER BY
                    hours.typical_trip_loss_minutes DESC NULLS LAST,
                    hours.direction_id,
                    hours.hour_local
                LIMIT 1
            ) AS hour_band ON TRUE
            WHERE routes.window_key = %s
            ORDER BY routes.{metric_column} DESC NULLS LAST, routes.route_id
            """,
            [window.value],
        )

        features = [
            RouteMapFeature.model_validate(
                {
                    "geometry": json.loads(row["geometry_json"]),
                    "properties": {
                        **self._normalize_route_map_properties_row(row),
                        "metric": metric,
                        "metric_value": row["metric_value"],
                    },
                }
            )
            for row in rows
        ]
        return MapRoutesResponse(
            window=window,
            metric=metric,
            features=features,
        )

    @staticmethod
    def _normalize_route_summary_row(row: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(row)
        normalized["window"] = normalized.pop("window_key")
        return normalized

    @staticmethod
    def _normalize_segment_properties_row(row: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(row)
        normalized.pop("geometry_json", None)
        normalized["window"] = normalized.pop("window_key")
        return normalized

    @staticmethod
    def _normalize_route_map_properties_row(row: dict[str, Any]) -> dict[str, Any]:
        normalized = HistoricalApiRepository._normalize_route_summary_row(row)
        normalized.pop("geometry_json", None)
        normalized.pop("metric_value", None)
        return normalized
