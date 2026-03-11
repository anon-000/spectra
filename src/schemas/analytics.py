from datetime import date

from schemas.common import SpectraBase


class TimeSeriesPoint(SpectraBase):
    date: str
    opened: int
    resolved: int


class SeverityCount(SpectraBase):
    severity: str
    count: int


class CategoryCount(SpectraBase):
    category: str
    count: int


class TopRule(SpectraBase):
    rule_id: str
    tool: str
    count: int


class TopRepo(SpectraBase):
    full_name: str
    count: int


class MTTRBySeverity(SpectraBase):
    severity: str
    avg_hours: float


class AnalyticsResponse(SpectraBase):
    total_open: int
    total_resolved: int
    total_suppressed: int
    time_series: list[TimeSeriesPoint]
    by_severity: list[SeverityCount]
    by_category: list[CategoryCount]
    top_rules: list[TopRule]
    top_repos: list[TopRepo]
    mttr_by_severity: list[MTTRBySeverity]
