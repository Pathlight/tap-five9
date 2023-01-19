# tap-five9

This is a [Singer](https://singer.io) tap that produces JSON-formatted data
following the [Singer
spec](https://github.com/singer-io/getting-started/blob/master/docs/SPEC.md#singer-specification).

This tap:

- Pulls raw data from [Five9](https://www.five9.com/)
- Extracts the following resources:
  - [Call Logs](https://webapps.five9.com/assets/files/for_customers/documentation/vcc-applications/reporting/dashboard-reporting-users-guide.pdf#Call%20Log%20Reports)
  - [Agent Login Logout](https://webapps.five9.com/assets/files/for_customers/documentation/vcc-applications/reporting/dashboard-reporting-users-guide.pdf#Agent%20Reports)
  - [Agent Occupancy](https://webapps.five9.com/assets/files/for_customers/documentation/vcc-applications/reporting/dashboard-reporting-users-guide.pdf#Agent%20Reports)
  - [Agent Information](https://webapps.five9.com/assets/files/for_customers/documentation/vcc-applications/reporting/dashboard-reporting-users-guide.pdf#Agent%20Reports)
- Outputs the schema for each resource
- Incrementally pulls data based on the input state

```bash
git clone git@github.com:Pathlight/tap-five9.git
cd tap-five9
pip install .
```

## Config

See [Five9 Configuration](https://webapps.five9.com/assets/files/for_customers/documentation/apis/config-webservices-api-reference-guide.pdf) for more API detalis.

The tap accepts the following config items:

| field | type | required | description |
| :---- | :--: | :------: | :---------- |
| `start_date` | string | yes | RFC3339 date string "2017-01-01T00:00:00Z" |
| `password` | string | yes | Five9 password credentials |
| `username` | string | yes | Five9 username credentials |
| `custom_reports` | object | no | Stream specific reporting periods (see [below](#Custom%20Reports)) |
| `poll_settings` | object | no | Polling used for data extraction jobs (see [below](#Polling%20Behavior)) |


Example config:

```json
{
  "start_date": "2017-01-01T00:00:00Z",
  "password": "<Five9 password>",
  "username": "<Five9 username>",
  "custom_reports": [
    {
      "stream_id": "custom_agent_reason_code_summary",
      "folder_name": "Pathlight Custom",
      "report_name": "Agent Reason Code Summary (Pathlight)",
      "key_properties": [
        "agent",
        "date"
      ],
      "datetime_fields": [
        "date",
        "timestamp"
      ],
      "replication_method": "INCREMENTAL",
      "valid_replication_keys": "date"
    }
  ],
}
```

## Custom Reports
For `periods` the structure is as follows:

| stream | reporting period |
| :----: | :--------------- | 
| `stream_name` | the tap supports 1 `days`, 1 `hours`, and 5 `minutes` |


## Polling Behavior

For reports, we need to poll for the report status to see when it is completed. You can change these settings in order to adjust polling behavior.

| stream | reporting period |
| :----: | :--------------- | 
| `delay` | How long to wait between status requests, defaults to 5 seconds |
| `timeout` | How long to wait for the status request, defaults to 300 seconds | 

---

Copyright &copy; 2018 Stitch
