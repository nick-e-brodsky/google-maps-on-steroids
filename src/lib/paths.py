"""Per-location path layout: data/<location>/{input,output,state.json,category_overrides.json}.

Keeps each Google Maps saved list (New York, Paris, Tokyo, ...) self-contained
so the pipeline can be pointed at any of them independently.
"""

import os


def data_dir(location: str) -> str:
    return os.path.join("data", location)


def state_path(location: str) -> str:
    return os.path.join(data_dir(location), "state.json")


def overrides_path(location: str) -> str:
    return os.path.join(data_dir(location), "category_overrides.json")


def config_path(location: str) -> str:
    return os.path.join(data_dir(location), "config.json")


def output_path(location: str) -> str:
    return os.path.join(data_dir(location), "output", "places.csv")
