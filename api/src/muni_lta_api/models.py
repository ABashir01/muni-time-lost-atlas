"""Pydantic models for the B4 historical/static FastAPI surface."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    """Base response model with a strict, immutable public shape."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class HealthResponse(ApiModel):
    status: Literal["ok"]
    app_name: str
    environment: str


class TimeWindow(str, Enum):
    ALL_DAY = "all_day"


class RankingMetric(str, Enum):
    TYPICAL_TRIP_LOSS_MINUTES = "typical_trip_loss_minutes"
    WAITING_LOSS_MINUTES = "waiting_loss_minutes"
    IN_VEHICLE_LOSS_MINUTES = "in_vehicle_loss_minutes"


class RankingMode(str, Enum):
    ROUTES = "routes"


class RouteSummary(ApiModel):
    route_id: str
    route_name: str
    route_short_name: str | None = None
    route_long_name: str | None = None
    window: TimeWindow
    direction_id: int | None = None
    direction_label: str | None = None
    typical_trip_loss_minutes: float | None = None
    waiting_loss_minutes: float | None = None
    in_vehicle_loss_minutes: float | None = None
    worst_time_band: str | None = None
    worst_stop_wait_label: str | None = None
    worst_segment_label: str | None = None
    matched_observed_stop_event_count: int
    resolved_unmatched_observation_count: int
    matched_headway_interval_count: int
    matched_full_trip_count: int
    metric_updated_at: datetime


class RankedRouteSummary(RouteSummary):
    rank: int


class RankingsResponse(ApiModel):
    window: TimeWindow
    metric: RankingMetric
    mode: RankingMode
    routes: list[RankedRouteSummary]


class CompareResponse(ApiModel):
    window: TimeWindow
    route_ids: list[str]
    routes: list[RouteSummary]


class PointGeometry(ApiModel):
    type: Literal["Point"]
    coordinates: tuple[float, float]


class LineStringGeometry(ApiModel):
    type: Literal["LineString"]
    coordinates: list[tuple[float, float]]


class MultiLineStringGeometry(ApiModel):
    type: Literal["MultiLineString"]
    coordinates: list[list[tuple[float, float]]]


RouteGeometry: TypeAlias = LineStringGeometry | MultiLineStringGeometry
SegmentGeometry: TypeAlias = LineStringGeometry


class SegmentFeatureProperties(ApiModel):
    route_id: str
    route_name: str
    route_short_name: str | None = None
    route_long_name: str | None = None
    window: TimeWindow
    direction_id: int
    direction_label: str | None = None
    shape_id: str
    segment_strategy: str
    segment_sequence: int
    from_stop_id: str
    from_stop_name: str
    to_stop_id: str
    to_stop_name: str
    segment_label: str
    scheduled_segment_minutes: float | None = None
    segment_in_vehicle_loss_minutes: float | None = None
    matched_trip_segment_count: int
    metric_updated_at: datetime


class SegmentFeature(ApiModel):
    type: Literal["Feature"] = "Feature"
    geometry: SegmentGeometry
    properties: SegmentFeatureProperties


class RouteSegmentsResponse(ApiModel):
    route_id: str
    route_name: str
    route_short_name: str | None = None
    route_long_name: str | None = None
    window: TimeWindow
    direction_id: int
    direction_label: str | None = None
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[SegmentFeature]
    metric_updated_at: datetime | None = None


class StopWaitFeatureProperties(ApiModel):
    route_id: str
    route_name: str
    route_short_name: str | None = None
    route_long_name: str | None = None
    window: TimeWindow
    direction_id: int
    direction_label: str | None = None
    stop_id: str
    stop_name: str
    stop_wait_label: str
    stop_wait_strategy: str
    scheduled_effective_wait_minutes: float | None = None
    observed_effective_wait_minutes: float | None = None
    waiting_loss_minutes: float | None = None
    matched_headway_interval_count: int
    metric_updated_at: datetime


class StopWaitFeature(ApiModel):
    type: Literal["Feature"] = "Feature"
    geometry: PointGeometry
    properties: StopWaitFeatureProperties


class RouteStopWaitResponse(ApiModel):
    route_id: str
    route_name: str
    route_short_name: str | None = None
    route_long_name: str | None = None
    window: TimeWindow
    direction_id: int
    direction_label: str | None = None
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[StopWaitFeature]
    metric_updated_at: datetime | None = None


class RouteMapFeatureProperties(RouteSummary):
    metric: RankingMetric
    metric_value: float | None = None


class RouteMapFeature(ApiModel):
    type: Literal["Feature"] = "Feature"
    geometry: RouteGeometry
    properties: RouteMapFeatureProperties


class MapRoutesResponse(ApiModel):
    window: TimeWindow
    metric: RankingMetric
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[RouteMapFeature]


class LiveVehicleFeatureProperties(ApiModel):
    agency_id: str
    entity_id: str
    vehicle_id: str | None = None
    vehicle_label: str | None = None
    route_id: str | None = None
    route_short_name: str | None = None
    trip_id: str | None = None
    stop_id: str | None = None
    current_stop_sequence: int | None = None
    current_status: str | None = None
    occupancy_status: str | None = None
    bearing: float | None = None
    speed_meters_per_second: float | None = None
    vehicle_timestamp: datetime | None = None
    feed_timestamp: datetime | None = None


class LiveVehicleFeature(ApiModel):
    type: Literal["Feature"] = "Feature"
    geometry: PointGeometry
    properties: LiveVehicleFeatureProperties


class LiveVehiclesResponse(ApiModel):
    agency_id: str
    route_id: str | None = None
    feed_timestamp: datetime | None = None
    vehicle_count: int
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[LiveVehicleFeature]
