"""
Generate SQL for MDS Provider database CRUD.
"""

from ..schemas import STATUS_CHANGES, TRIPS
from ..versions import UnsupportedVersionError, Version


_COMMON_INSERTS= [
    "provider_id",
    "provider_name",
    "device_id",
    "vehicle_id",
    "vehicle_type",
    "propulsion_type"
]

_COMMON_SELECTS = [
    "cast(provider_id as uuid)",
    "provider_name",
    "cast(device_id as uuid)",
    "vehicle_id,"
    "cast(vehicle_type as vehicle_types)",
    "cast(propulsion_type as propulsion_types[])",
]


def on_conflict_statement(on_conflict_update=None):
    """
    Generate an appropriate "ON CONFLICT..." statement.

    Parameters:
        on_conflict_update: tuple (condition: str, actions: str, list, dict), optional
            Generate a statement like "ON CONFLICT condition DO UPDATE SET actions"
            actions may be a SQL str, a list of column action str, or a dict of column=value pairs.

    Return:
        str
    """
    if on_conflict_update:
        if isinstance(on_conflict_update, tuple):
            condition, actions = on_conflict_update
            if isinstance(actions, list):
                actions = ",".join(actions)
            elif isinstance(actions, dict):
                actions = ",".join([f"{k} = {v}" for k,v in actions.items()])
            return f"ON CONFLICT {condition} DO UPDATE SET {actions}"

    return "ON CONFLICT DO NOTHING"


def insert_status_changes_from(source_table, dest_table=STATUS_CHANGES, **kwargs):
    """
    Generate an "INSERT INTO... SELECT...FROM" statement for status_changes.

    Parameters:
        source_table: str
            The name of the table to SELECT FROM.

        dest_table: str, optional
            The name of the table to INSERT INTO, by default status_changes.

        on_conflict_update: tuple (condition: str, actions: list), dict, optional
            See on_conflict_statement().

        version: str, Version, optional
            The MDS version to target. By default, Version.mds_lower().

    Return:
        str
    """
    version = Version(kwargs.pop("version", Version.mds_lower()))
    if version.unsupported:
        raise UnsupportedVersionError(version)

    on_conflict_update = kwargs.pop("on_conflict_update", None)
    on_conflict = on_conflict_statement(on_conflict_update)

    inserts = list(_COMMON_INSERTS)
    inserts.extend([
        "event_type",
        "event_type_reason",
        "event_location",
        "battery_pct"
    ])

    selects = list(_COMMON_SELECTS)
    selects.extend([
        "cast(event_type as event_types)",
        "cast(event_type_reason as event_type_reasons)",
        "cast(event_location as jsonb)",
        "battery_pct"
    ])

    if version < Version("0.3.0"):
        inserts.extend([
            "event_time",
            "associated_trips"
        ])

        selects.extend([
            "to_timestamp(event_time) at time zone 'UTC'",
            "cast(associated_trips as uuid[])"
        ])
    else:
        inserts.extend([
            "event_time",
            "publication_time",
            "associated_trip"
        ])

        selects.extend([
            "to_timestamp(cast(event_time as double precision) / 1000.0) at time zone 'UTC'",
            "to_timestamp(cast(publication_time as double precision) / 1000.0) at time zone 'UTC'",
            "cast(associated_trip as uuid)"
        ])

    inserts = ",".join(inserts)
    selects = ",".join(selects)

    return f"""
    INSERT INTO "{dest_table}"
    ({inserts})
    SELECT {selects}
    FROM "{source_table}"
    { on_conflict }
    ;
    """


def insert_trips_from(source_table, dest_table=TRIPS, **kwargs):
    """
    Generate an "INSERT INTO... SELECT...FROM" statement for trips.

    Parameters:
        source_table: str
            The name of the table to SELECT FROM.

        dest_table: str, optional
            The name of the table to INSERT INTO, by default trips.

        on_conflict_update: tuple (condition: str, actions: list), dict, optional
            See on_conflict_statement().

        version: str, Version, optional
            The MDS version to target. By default, Version.mds_lower().

    Return:
        str
    """
    version = Version(kwargs.pop("version", Version.mds_lower()))
    if version.unsupported:
        raise UnsupportedVersionError(version)

    on_conflict_update = kwargs.pop("on_conflict_update", None)
    on_conflict = on_conflict_statement(on_conflict_update)

    inserts = list(_COMMON_INSERTS)
    inserts.extend([
        "trip_id",
        "trip_duration",
        "trip_distance",
        "route",
        "accuracy",
        "parking_verification_url",
        "standard_cost",
        "actual_cost"
    ])

    selects = list(_COMMON_SELECTS)
    selects.extend([
        "cast(trip_id as uuid)",
        "trip_duration",
        "trip_distance",
        "cast(route as jsonb)",
        "accuracy",
        "parking_verification_url,"
        "standard_cost,"
        "actual_cost"
    ])

    if version < Version("0.3.0"):
        inserts.extend([
            "start_time",
            "end_time"
        ])

        selects.extend([
            "to_timestamp(start_time) at time zone 'UTC'",
            "to_timestamp(end_time) at time zone 'UTC'"
        ])
    else:
        inserts.extend([
            "start_time",
            "end_time",
            "publication_time",
        ])

        selects.extend([
            "to_timestamp(cast(start_time as double precision) / 1000.0) at time zone 'UTC'",
            "to_timestamp(cast(end_time as double precision) / 1000.0) at time zone 'UTC'",
            "to_timestamp(cast(publication_time as double precision) / 1000.0) at time zone 'UTC'",
        ])

    inserts = ",".join(inserts)
    selects = ",".join(selects)

    return f"""
    INSERT INTO "{dest_table}"
    ({inserts})
    SELECT {selects}
    FROM "{source_table}"
    { on_conflict }
    ;
    """
