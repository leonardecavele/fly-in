from typing import Any

from src.error import ParseError


keys = [
    "nb_drones",
    "start_hub",
    "end_hub",
    "connection",
    "hub"
]

hub_metadata_keys = [
    "zone",
    "color",
    "max_drones"
]

connection_metadata_keys = [
    "max_link_capacity"
]

zone_types = [
    "normal",
    "blocked",
    "restricted",
    "priority"
]


def parse_connection_metadata(pre_metadata: list[str]) -> int:
    max_link_capacity: int = 1

    if not pre_metadata:
        return max_link_capacity

    # remove brackets
    if pre_metadata[0][0] != '[' or pre_metadata[-1][-1] != ']':
        raise ParseError("invalid metadata syntax (missing [])")
    pre_metadata[0] = pre_metadata[0][1:]
    pre_metadata[-1] = pre_metadata[-1][:-1]

    if pre_metadata and pre_metadata[0] == "":
        pre_metadata = pre_metadata[1:]
    if pre_metadata and pre_metadata[-1] == "":
        pre_metadata = pre_metadata[:-1]

    if not pre_metadata:
        raise ParseError("invalid metadata (empty)")

    # check metadata
    seen_keys: list[str] = []
    for m in pre_metadata:
        if m.count("=") != 1:
            raise ParseError("invalid metadata syntax (missing '=')")
        key, value = m.split("=")
        seen_keys.append(key)
        if key not in connection_metadata_keys:
            raise ParseError(f"invalid metadata key ({key})")
        elif key == "max_link_capacity":
            try:
                max_link_capacity = int(value)
            except ValueError:
                raise ParseError(f"invalid metadata value ({value})")

    if len(seen_keys) != len(set(seen_keys)):
        raise ParseError("invalid metadata (doubled keys)")

    return max_link_capacity


def parse_connection(
    seen: dict[str, list[str]], value: str, map_specs: dict[str, Any]
) -> tuple[str, str, int]:
    metadata: int = 0
    connection, *pre_metadata = value.split()
    # get hubs
    if connection.count("-") != 1:
        raise ParseError("invalid connection syntax (should have one '-')")
    from_hub, dest_hub = connection.split("-")
    if from_hub not in map_specs["hubs"] or dest_hub not in map_specs["hubs"]:
        raise ParseError("invalid connection (unexisting hub(s))")
    # check already seen connections
    reverse: str = "-".join([dest_hub, from_hub])
    if (connection in seen["connections"] or reverse in seen["connections"]):
        raise ParseError("invalid connection (already registered)")
    seen["connections"].append(connection)
    metadata = parse_connection_metadata(pre_metadata)

    return (from_hub, dest_hub, metadata)


def parse_hub_metadata(
    pre_metadata: list[str], nb_drones: int, hub_key: str
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}

    # default
    metadata["zone"] = "normal"
    metadata["color"] = None
    if hub_key == "start_hub" or hub_key == "end_hub":
        metadata[hub_key] = True
        metadata["max_drones"] = nb_drones
    else:
        metadata["max_drones"] = 1

    if not pre_metadata:
        return metadata

    # remove brackets
    if pre_metadata[0][0] != '[' or pre_metadata[-1][-1] != ']':
        raise ParseError("invalid metadata syntax (missing [])")
    pre_metadata[0] = pre_metadata[0][1:]
    pre_metadata[-1] = pre_metadata[-1][:-1]

    if pre_metadata and pre_metadata[0] == "":
        pre_metadata = pre_metadata[1:]
    if pre_metadata and pre_metadata[-1] == "":
        pre_metadata = pre_metadata[:-1]

    if not pre_metadata:
        raise ParseError("invalid metadata (empty)")

    # check metadata
    seen_keys: list[str] = []
    for m in pre_metadata:
        if m.count("=") != 1:
            raise ParseError("invalid metadata syntax (missing '=')")
        key, value = m.split("=")
        seen_keys.append(key)
        if key not in hub_metadata_keys:
            raise ParseError(f"invalid metadata key ({key})")
        elif key == "zone" and value not in zone_types:
            raise ParseError(f"invalid metadata value ({value})")
        elif key == "max_drones":
            try:
                metadata[key] = int(value)
            except ValueError:
                raise ParseError(f"invalid metadata value ({value})")
            if (
                (hub_key == "start_hub" or hub_key == "end_hub")
                and metadata[key] < nb_drones
            ):
                raise ParseError(
                    f"invalid metadata value ({value}), {hub_key} 'max_drones'"
                    " must be equal or superior to 'nb_drones'"
                )
        else:
            metadata[key] = value

    if len(seen_keys) != len(set(seen_keys)):
        raise ParseError("invalid metadata (doubled keys)")

    return metadata


def parse_hub(
    seen: dict[str, list[str]], key: str, value: str, nb_drones: int
) -> dict[str, dict[str, Any]]:
    splitted_values = value.split()
    if len(splitted_values) < 3:
        raise ParseError("invalid number of values")
    name, pre_x, pre_y, *pre_metadata = splitted_values

    # check validity
    if "-" in name:
        raise ParseError("invalid name (cant have dashes)")
    try:
        x: int = int(pre_x)
        y: int = int(pre_y)
    except ValueError:
        raise ParseError("invalid coordinates")
    metadata: dict[str, Any] = parse_hub_metadata(pre_metadata, nb_drones, key)

    # valid
    if name in seen["seen_names"]:
        raise ParseError(f"invalid name ({name}), already assigned")
    seen["seen_names"].append(name)
    return {name: {"x": x, "y": y} | metadata}


def parse(file_name: str) -> dict[str, Any]:
    map_specs: dict[str, Any] = {}
    map_specs["hubs"] = {}
    map_specs["connections"] = []

    seen: dict[str, list[str]] = {}
    seen["seen_keys"] = []
    seen["seen_names"] = []
    seen["connections"] = []
    with open(file_name, "r", encoding="utf-8") as f:
        nb_keys: int = 0
        for i, line in enumerate(f, start=1):
            try:
                # remove from line what's after first #
                comment_index: int = line.find('#')
                if comment_index != -1:
                    line = line[0:comment_index]
                # ignore empty lines
                if not line.strip():
                    continue
                # split key, value
                if line.count(":") != 1:
                    raise ParseError("invalid number of ':'")
                key, value = line.split(":")

                if not key.strip() or not value.strip():
                    raise ParseError("invalid line (empty key or value)")

                # parse key
                if key not in keys:
                    raise ParseError(f"invalid key ({key})")
                if nb_keys == 0 and key != "nb_drones":
                    raise ParseError(f"invalid first key ({key})")

                if "hub" in key:
                    map_specs[
                        "hubs"
                    ] |= parse_hub(seen, key, value, map_specs["nb_drones"])
                elif key == "connection":
                    map_specs[
                        "connections"
                    ].append(parse_connection(seen, value, map_specs))
                elif key == "nb_drones":
                    try:
                        nb_drones: int = int(value)
                        map_specs["nb_drones"] = nb_drones
                    except ValueError:
                        raise ParseError(f"invalid value ({value}) for {key}")
                seen["seen_keys"].append(key)
                nb_keys += 1

            except ParseError as e:
                raise ParseError(f"l{i}: {e}")

        # check keys validity
        if seen["seen_keys"].count("start_hub") != 1:
            raise ParseError(
                "invalid number of 'start_hub' keys (should be one)"
            )
        if seen["seen_keys"].count("end_hub") != 1:
            raise ParseError(
                "invalid number of 'end_hub' keys (should be one)"
            )

    return map_specs
