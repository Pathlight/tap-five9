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

---

Copyright &copy; 2018 Stitch
