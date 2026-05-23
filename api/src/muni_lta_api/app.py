"""FastAPI application bootstrap and B4 historical/static endpoints."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from .config import ApiSettings, get_api_settings
from .db import Database
from .models import (
    CompareResponse,
    HealthResponse,
    LiveVehiclesResponse,
    MapRoutesResponse,
    RankingMetric,
    RankingMode,
    RankingsResponse,
    RouteStopWaitResponse,
    RouteSegmentsResponse,
    RouteSummary,
    TimeWindow,
)
from .repository import HistoricalApiRepository


def _parse_compare_ids(ids: str) -> list[str]:
    route_ids = [segment.strip() for segment in ids.split(",") if segment.strip()]
    if len(route_ids) < 2 or len(route_ids) > 4:
        raise HTTPException(
            status_code=422,
            detail="ids must contain between 2 and 4 route ids",
        )
    if len(set(route_ids)) != len(route_ids):
        raise HTTPException(status_code=422, detail="ids must not contain duplicates")
    return route_ids


def create_app(settings: ApiSettings | None = None):
    """Create the FastAPI application for the static historical API surface."""
    active_settings = settings or get_api_settings()
    app = FastAPI(title=active_settings.app_name)
    app.state.settings = active_settings
    app.state.repository = (
        HistoricalApiRepository(Database(active_settings.database_url))
        if active_settings.database_url
        else None
    )

    def repository() -> HistoricalApiRepository:
        active_repository = app.state.repository
        if active_repository is None:
            raise HTTPException(
                status_code=500,
                detail="DATABASE_URL or POSTGRES_* settings are required for API reads",
            )
        return active_repository

    @app.get(
        "/health",
        response_model=HealthResponse,
        response_model_exclude_none=True,
    )
    def get_health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            app_name=active_settings.app_name,
            environment=active_settings.environment,
        )

    @app.get(
        "/rankings",
        response_model=RankingsResponse,
        response_model_exclude_none=True,
    )
    def get_rankings(
        window: TimeWindow = Query(default=TimeWindow.ALL_DAY),
        metric: RankingMetric = Query(
            default=RankingMetric.TYPICAL_TRIP_LOSS_MINUTES
        ),
        mode: RankingMode = Query(default=RankingMode.ROUTES),
    ) -> RankingsResponse:
        return repository().get_rankings(window=window, metric=metric, mode=mode)

    @app.get(
        "/routes/{route_id}/summary",
        response_model=RouteSummary,
        response_model_exclude_none=True,
    )
    def get_route_summary(
        route_id: str,
        window: TimeWindow = Query(default=TimeWindow.ALL_DAY),
        direction: int | None = Query(default=None, ge=0, le=1),
    ) -> RouteSummary:
        summary = repository().get_route_summary(
            route_id=route_id,
            window=window,
            direction_id=direction,
        )
        if summary is None:
            raise HTTPException(
                status_code=404,
                detail=f"No summary found for route_id={route_id}",
            )
        return summary

    @app.get(
        "/routes/{route_id}/segments",
        response_model=RouteSegmentsResponse,
        response_model_exclude_none=True,
    )
    def get_route_segments(
        route_id: str,
        window: TimeWindow = Query(default=TimeWindow.ALL_DAY),
        direction: int = Query(..., ge=0, le=1),
    ) -> RouteSegmentsResponse:
        segments = repository().get_route_segments(
            route_id=route_id,
            window=window,
            direction_id=direction,
        )
        if segments is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No segments found for route_id={route_id} and direction={direction}"
                ),
            )
        return segments

    @app.get(
        "/routes/{route_id}/stops/wait",
        response_model=RouteStopWaitResponse,
        response_model_exclude_none=True,
    )
    def get_route_stop_wait(
        route_id: str,
        window: TimeWindow = Query(default=TimeWindow.ALL_DAY),
        direction: int = Query(..., ge=0, le=1),
    ) -> RouteStopWaitResponse:
        stop_wait = repository().get_route_stop_wait(
            route_id=route_id,
            window=window,
            direction_id=direction,
        )
        if stop_wait is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "No stop wait hotspots found for "
                    f"route_id={route_id} and direction={direction}"
                ),
            )
        return stop_wait

    @app.get(
        "/routes/compare",
        response_model=CompareResponse,
        response_model_exclude_none=True,
    )
    def get_routes_compare(
        ids: str = Query(
            ...,
            description="Comma-separated list of 2-4 route ids.",
        ),
        window: TimeWindow = Query(default=TimeWindow.ALL_DAY),
    ) -> CompareResponse:
        route_ids = _parse_compare_ids(ids)
        comparison = repository().get_compare(route_ids=route_ids, window=window)
        if comparison is None:
            raise HTTPException(
                status_code=404,
                detail="One or more requested route ids were not found",
            )
        return comparison

    @app.get(
        "/map/routes",
        response_model=MapRoutesResponse,
        response_model_exclude_none=True,
    )
    def get_map_routes(
        window: TimeWindow = Query(default=TimeWindow.ALL_DAY),
        metric: RankingMetric = Query(
            default=RankingMetric.TYPICAL_TRIP_LOSS_MINUTES
        ),
    ) -> MapRoutesResponse:
        return repository().get_map_routes(window=window, metric=metric)

    @app.get(
        "/live/vehicles",
        response_model=LiveVehiclesResponse,
        response_model_exclude_none=True,
    )
    def get_live_vehicles(
        agency: str = Query(default="SF", min_length=1),
        route_id: str | None = Query(default=None),
    ) -> LiveVehiclesResponse:
        return repository().get_live_vehicles(agency_id=agency, route_id=route_id)

    return app
