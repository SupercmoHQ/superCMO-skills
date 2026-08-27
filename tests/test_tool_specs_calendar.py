from supercmo_skills.tool_specs import CALENDAR_TOOL_SPECS


def test_calendar_specs_present_and_shaped():
    names = [s["name"] for s in CALENDAR_TOOL_SPECS]
    assert names == ["calendar_list", "calendar_add", "calendar_update", "calendar_remove"]
    add = next(s for s in CALENDAR_TOOL_SPECS if s["name"] == "calendar_add")
    props = add["input_schema"]["properties"]
    assert {"kind", "title", "at", "rrule", "prompt", "content", "media",
            "channel", "publish_tool", "timezone"} <= set(props)
    assert add["input_schema"]["required"] == ["kind", "title"]
    assert props["kind"]["enum"] == ["task", "post"]


def test_calendar_list_full_filter_set():
    listing = next(s for s in CALENDAR_TOOL_SPECS if s["name"] == "calendar_list")
    list_props = listing["input_schema"]["properties"]
    assert set(list_props) == {"window_start", "window_end", "kind", "channel", "status", "limit"}
    assert list_props["limit"]["default"] == 50


def test_calendar_update_drops_kind():
    update = next(s for s in CALENDAR_TOOL_SPECS if s["name"] == "calendar_update")
    update_props = update["input_schema"]["properties"]
    assert "kind" not in update_props
