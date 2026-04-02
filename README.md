# Ewon Processor

<img src="https://doover.com/wp-content/uploads/Doover-Logo-Landscape-Navy-padded-small.png" alt="Doover" style="max-width: 300px;">

**A Doover processor for fetching tag data from HMS Ewon industrial gateways via the Talk2M DataMailbox API.**

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/getdoover/ewon)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/getdoover/ewon/blob/main/LICENSE)

[Getting Started](#-getting-started) • [Configuration](#configuration) • [Developer](https://github.com/getdoover/ewon/blob/main/DEVELOPMENT.md) • [Need Help?](#need-help)

<br/>

## 📖 Overview

The Ewon Processor is a Doover cloud processor (`PRO`) that connects to HMS Ewon industrial gateways through the Talk2M DataMailbox API. It periodically fetches tag data from Ewon devices, organises it into time-bucketed frames, and pushes the values to the Doover platform UI for visualisation and logging.

### How It Works

1. **Scheduled fetch** — The processor runs on a configurable schedule (or in response to a channel message) and calls the Talk2M DataMailbox `syncdata` endpoint.
2. **Incremental sync** — Uses transaction IDs to only retrieve new data since the last successful fetch.
3. **Frame creation** — Groups tag values into 5-minute frames for consistent time-series display.
4. **UI update** — Pushes each frame to the Doover UI with timestamped record logs, populating configured numeric variables and multiplots.
5. **Connection status** — Reports the device as online based on the most recent data timestamp, with configurable offline thresholds.

<br/>

## 🚀 Getting Started

### How to Use

This app is a Doover cloud processor. Install it onto a device via the Doover admin panel or CLI.

#### Prerequisites

- A Talk2M DataMailbox account with API access
- A DataMailbox API token and Developer ID
- The Ewon device name or ID

#### Quick Start

1. Install the **Ewon Processor** app on your device via the Doover platform.
2. Configure the required settings (see below).
3. Set a schedule (e.g. `rate(15 minutes)`) to periodically fetch data.
4. Tag data will appear on the device dashboard automatically.

### Configuration

#### Settings Overview

| Setting | Description | Default |
|---------|-------------|---------|
| **Channel Subscription** | Channel to subscribe to for trigger messages | *required* |
| **Schedule** | Schedule expression (e.g. `rate(15 minutes)`) | *required* |
| **Data Mailbox API Token** | Talk2M DataMailbox API token | *required* |
| **Data Mailbox Developer ID** | Talk2M Developer ID | *required* |
| **Ewon ID** | Numeric ID of the Ewon gateway (auto-populated if name is provided) | *required* |
| **Ewon Name** | Name of the Ewon gateway | *required* |
| **Ewon Clock Timezone** | Timezone of the Ewon device clock | `Australia/Brisbane` |
| **Tags** | Array of tags to display — each with tag name, display name, and decimal precision | *required* |
| **Multiplots** | Array of multiplot configurations — each with a title and series elements | *required* |
| **Exclude** | Tag names to exclude from the UI | `[]` |

#### Tag Configuration

Each tag entry requires:

| Field | Description |
|-------|-------------|
| **Tag Name** | The exact tag name as it appears on the Ewon device |
| **Display Name** | Human-readable label shown in the Doover UI |
| **Decimal Precision** | Number of decimal places to display (default: 2) |

#### Multiplot Configuration

Each multiplot entry requires:

| Field | Description |
|-------|-------------|
| **Title** | Chart title |
| **Series Elements** | Array of series — each with a name (matching a tag name), colour, and active flag |

<br/>

## 🔗 Integrations

### Tags

This app exposes the following internal tags:

| Tag | Description |
|-----|-------------|
| **last_ewon_transaction_id** | The last DataMailbox transaction ID used for incremental sync |

<br/>

### Connections

This app works with:

- **🔌 Talk2M DataMailbox API** — HMS Networks' cloud API for retrieving historical tag data from Ewon gateways
- **🔌 Doover UI Manager** — Pushes tag values and multiplots to the Doover device dashboard

<br/>

### Need Help?

- 📧 Email: support@doover.com
- 📖 [Doover Documentation](https://docs.doover.com)
- 👨‍💻 [App Developer Documentation](https://github.com/getdoover/ewon/blob/main/DEVELOPMENT.md)

<br/>

## 🔄 Version History

### v0.1.0 (Current)
- 🎉 Initial doover-2 release
- ✨ Cloud processor using `pydoover.cloud.processor`
- ✨ Async Talk2M DataMailbox client (`aiohttp`)
- ✨ Configurable tags, multiplots, and timezone
- ✨ Incremental sync via transaction IDs
- ✨ Connection status reporting
- ✨ Auto-discovery of Ewon ID from name

<br/>

## 📄 License

This app is licensed under the [Apache License 2.0](https://github.com/getdoover/ewon/blob/main/LICENSE).
