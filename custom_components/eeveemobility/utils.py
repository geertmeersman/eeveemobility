"""EeveeMobility utils."""
from __future__ import annotations


def sensor_name(string: str) -> str:
    """Format sensor name."""
    string = string.strip().replace("_", " ").title()
    return string


def filter_json(json_data, exclude_substrings=None):
    """Remove objects with null or where the key is in the substring list."""
    if exclude_substrings is None:
        exclude_substrings = []

    if isinstance(json_data, dict):
        # Create a copy of the dictionary to avoid modifying the original
        result = json_data.copy()

        for key, value in list(
            json_data.items()
        ):  # Using list() to iterate over a copy of items
            if (
                any(substring in key for substring in exclude_substrings)
                or value is None
            ):
                # Remove the object
                del result[key]
            elif isinstance(value, dict | list):
                # Recursively call the function for nested dictionaries
                nested_result = filter_json(value, exclude_substrings)
                if not nested_result:
                    # Remove the key if the nested result is an empty dictionary (all null values)
                    del result[key]
                else:
                    result[key] = nested_result
        return result
    elif isinstance(json_data, list):
        # Process each item in the list
        filtered_list = [filter_json(item, exclude_substrings) for item in json_data]
        # Remove None items (list items that had all null values)
        return [item for item in filtered_list if item is not None]
    else:
        return json_data
