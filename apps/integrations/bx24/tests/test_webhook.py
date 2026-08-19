from apps.integrations.bx24.lib.services.webhook import parse_bitrix_payload, extract_trailing_id


def test_parse_bitrix_payload_unpacks_bracket_keys():
    raw = {
        "document_id[0]": ["crm"],
        "document_id[1]": ["CRM_ITEM_1052"],
        "document_id[2]": ["CRM_ITEM_1052_60829"],
        "event": ["ONCRMDYNAMICITEMUPDATE"],
    }

    parsed = parse_bitrix_payload(raw)

    assert parsed["document_id"] == {
        "0": "crm",
        "1": "CRM_ITEM_1052",
        "2": "CRM_ITEM_1052_60829",
    }
    assert parsed["event"] == "ONCRMDYNAMICITEMUPDATE"


def test_extract_trailing_id_pulls_numeric_suffix():
    assert extract_trailing_id("CRM_ITEM_1052_60829") == 60829


def test_extract_trailing_id_returns_none_without_digits():
    assert extract_trailing_id("CRM_ITEM_NO_ID") is None
