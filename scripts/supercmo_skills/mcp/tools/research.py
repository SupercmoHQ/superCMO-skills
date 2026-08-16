"""Research tools — thin MCP binding over supercmo_skills.

Read-only structured public data from social platforms + ad libraries (profiles, posts, comments,
competitor ads). All catalog/routing/vendor logic lives in supercmo_skills; this only declares the
schemas (single-sourced from tool_specs) and forwards the call. `list_research_sources` is a free
discovery read straight off the catalog — no vendor call, no spend.
"""

from .. import registry
import supercmo_skills
from supercmo_skills import catalog, tool_specs


SOCIAL_RESEARCH = {
    "name": "social_research",
    "description": tool_specs.SOCIAL_RESEARCH_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.SOCIAL_RESEARCH_PROPERTIES, tool_specs.SOCIAL_RESEARCH_REQUIRED),
}


def social_research(args):
    return supercmo_skills.social_research(
        platform=args.get("platform"),
        endpoint=args.get("endpoint"),
        params=args.get("params"),
        dry_run=bool(args.get("dry_run", False)),
    )


registry.register(SOCIAL_RESEARCH, social_research)


LIST_RESEARCH_SOURCES = {
    "name": "list_research_sources",
    "description": tool_specs.LIST_RESEARCH_SOURCES_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.LIST_RESEARCH_SOURCES_PROPERTIES, tool_specs.LIST_RESEARCH_SOURCES_REQUIRED),
}


def list_research_sources(args):
    return catalog.research_sources_listing(args.get("query"))


registry.register(LIST_RESEARCH_SOURCES, list_research_sources)
