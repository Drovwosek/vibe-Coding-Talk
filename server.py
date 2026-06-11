#!/usr/bin/env python3
"""Compatibility entry point for the Postovaya web application."""

from postovaya.http_app import AppHandler, run
from postovaya.openai_service import (
    demo_post,
    extract_output_text,
    extract_sources,
    generate_post,
    openai_request,
    research_venue,
)
from postovaya.prompts import (
    VENUE_PROFILE_SCHEMA,
    build_prompt,
    text,
    validate_venue_audience,
)


if __name__ == "__main__":
    run()
