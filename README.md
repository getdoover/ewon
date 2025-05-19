# Netbiter Processor

Processor to extract data from netbiter devices and display it in a Doover dashboard.

## Config

| **Config Key**    | **Description**                                  | **Default/Example** |
|-------------------|--------------------------------------------------|---------------------| 
| `API_TOKEN`       | List of tag configurations to include in the UI. | `abcdef12345`       |
| `DEVICE_ID`       | List of tag configurations to include in the UI. | `123456788`         |
| `DEVICE_NAME`     | Name of the device.                              | `Test Pit 1`        |
| `DEVICE_CLOCK_TZ` | Timezone for the device.                         | `Australia/Sydney`  |
| `UI_CONFIG`       | See below for UI config layout.                  | See below           |

## UI Config Layout
| **Config Key** | **Description**                                                         | **Default/Example**                  |
|----------------|-------------------------------------------------------------------------|--------------------------------------|
| `auto_include` | Whether to automatically include tags not explicitly defined in `tags`. | `True`                               |
| `tags`         | A tag configuration. See below for an example.                          | See `tags` example below             |
| `exclude`      | List of tag names to exclude from the UI.                               | `["excluded_tag"]`                   |
| `multiplots`   | List of multiplot configurations for the UI.                            | See `multiplot` example below.       |
| `multiplot`    | A single multiplot configuration to append to `multiplots`.             | `{"name": "plot1", "series": [...]}` |

### Example `multiplot` Configuration
```json
{
  "name": "multiplot1",
  "title": "Example Multiplot",
  "series": ["series1", "series2"],
  "default_active": [true, false],
  "series_colours": ["#FF0000", "#00FF00"]
}
```

### Example `tags` Configuration
```json
{
  "tags": [
    {
      "tag_name": "example_tag",
      "display_name": "Example Tag",
      "dec_precision": 2,
      "ranges": {"min": 0, "max": 100},
      "form": "slider"
    }
  ]
}
```