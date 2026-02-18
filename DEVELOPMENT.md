# Ewon Processor — Development Guide

This repository contains the Doover Ewon Processor, a cloud processor (`PRO`) app that fetches data from HMS Ewon gateways via the Talk2M DataMailbox API.

## Project Structure

```
README.md               <-- App description
DEVELOPMENT.md          <-- This file
pyproject.toml          <-- Python project configuration (including dependencies)
doover_config.json      <-- Doover app metadata and config schema
build.sh                <-- Build script for deployment package

src/ewon/               <-- Application source
  __init__.py            <-- Lambda handler entry point
  application.py         <-- Main EwonApplication processor logic
  app_config.py          <-- Configuration schema definition
  app_ui.py              <-- UI component definitions
  ewon_client.py         <-- Talk2M DataMailbox async client
  tags.py                <-- Tag, TagValue, and TagFrame data models

simulators/
  app_config.json        <-- Sample configuration for local testing

tests/
  test_imports.py        <-- Basic import validation tests
```

## Prerequisites

- Python 3.11 or later
- [uv](https://github.com/astral-sh/uv) for dependency management
- Doover CLI (`doover`) for publishing

## Setup

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/
```

## Building

This is a cloud processor deployed as a zip package (not a Docker image).

```bash
# Build the deployment package
./build.sh
# Produces package.zip
```

## Publishing

```bash
# Publish to Doover
doover app publish --profile dv2
```

## Configuration Schema

To regenerate `doover_config.json` after modifying `app_config.py`:

```bash
uv run export-config
```

## Architecture

The processor is triggered by:
- **Schedule events** — periodic data fetching (e.g. every 15 minutes)
- **Channel messages** — on-demand fetch triggers
- **Deployment events** — initial UI setup on first install

### Data Flow

```
Talk2M DataMailbox API
        │
        │ syncdata (incremental via transaction ID)
        ▼
┌─────────────────┐
│ Ewon Processor  │  ← Fetches tag history, creates 5-min frames
└─────────────────┘
        │
        │ push UI state + record logs
        ▼
┌─────────────────┐
│ Doover Platform │  ← Displays tags, multiplots, connection status
└─────────────────┘
```
