import re


def parse_bitrix_payload(data: dict) -> dict:
    """Bitrix outgoing webhooks POST form-encoded `root[child]`-style keys.
    Turns {'document_id[2]': ['CRM_ITEM_1052_60829']} into
    {'document_id': {'2': 'CRM_ITEM_1052_60829'}}."""
    result = {}

    for key, value in data.items():
        value = value[0]

        match = re.match(r"(\w+)\[(.+)\]", key)

        if not match:
            result[key] = value
            continue

        root, child = match.groups()

        if root not in result:
            result[root] = {}

        result[root][child] = value

    return result


def extract_trailing_id(value: str) -> int | None:
    """Pulls the numeric id off the end of a Bitrix composite string
    (e.g. document_id's "CRM_ITEM_1052_60829" -> 60829)."""
    match = re.search(r"(\d+)$", value)
    return int(match.group(1)) if match else None
