def merge_data(old_data: dict, new_data: dict, fields_to_update: list[str]) -> dict:
    merged = old_data.copy()

    for field in fields_to_update:
        if field in new_data and new_data[field] is not None:
            merged[field] = new_data[field]

    return merged