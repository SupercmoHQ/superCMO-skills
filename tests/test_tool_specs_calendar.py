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
