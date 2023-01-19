import datetime

import pytz

import singer
import dateutil.parser as parser

from singer.utils import strftime as singer_strftime

LOGGER = singer.get_logger()


class ReportStream():
    name = None
    stream = None
    replication_method = None
    replication_key = None
    key_properties = None
    folder_name = None
    report_name = None
    results_key = 'records'

    def __init__(self, client=None, start_date=None):
        self.client = client
        if start_date:
            self.start_date = start_date
        else:
            self.start_date = datetime.datetime.min.strftime('%Y-%m-%dT%H:%M:%S')

    def is_selected(self):
        return self.stream is not None

    def update_bookmark(self, state, value):
        current_bookmark = singer.get_bookmark(state, self.name, self.replication_key)
        if value and value > current_bookmark:
            singer.write_bookmark(state, self.name, self.replication_key, value)

    def transform_value(self, key, value):
        if key in self.datetime_fields and value:
            value = parser.parse(value)
            value = value.replace(tzinfo=pytz.utc)
            # reformat to use RFC3339 format
            value = singer_strftime(value)

        return value

    def sync(self, state, config):
        try:
            sync_thru = singer.get_bookmark(state, self.name, self.replication_key)
        except TypeError:
            sync_thru = self.start_date
        
        if not self.replication_key:
            sync_thru = self.start_date

        curr_synced_thru = sync_thru

        params = {
                'folder_name': self.folder_name,
                'report_name': self.report_name,
                'start': sync_thru,
                'end': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
            }

        data = self.client.return_report_results(params, config=config)
        for row in data:
            record = {k: self.transform_value(k, v) for (k, v) in row.items()}
            yield(self.stream, record)

            bookmark_date = record.get(self.replication_key)
            if bookmark_date:
                curr_synced_thru = max(curr_synced_thru, bookmark_date)

        if self.replication_key:
            self.update_bookmark(state, curr_synced_thru)


class CallLog(ReportStream):
    name = 'call_log'
    stream = 'call_log'
    replication_method = 'INCREMENTAL'
    replication_key = 'timestamp'
    key_properties = 'call_id'
    folder_name = 'Call Log Reports'
    report_name = 'Call Log'
    datetime_fields = set(['timestamp'])


class AgentLoginLogout(ReportStream):
    name = 'agent_login_logout'
    stream = 'agent_login_logout'
    replication_method = 'INCREMENTAL'
    replication_key = 'date'
    key_properties = ['agent', 'date']
    folder_name = 'Agent Reports'
    report_name = 'Agent Login-Logout'
    datetime_fields = set(['date', 'login_timestamp', 'logout_timestamp'])


class AgentOccupancy(ReportStream):
    name = 'agent_occupancy'
    stream = 'agent_occupancy'
    replication_method = 'INCREMENTAL'
    replication_key = 'date'
    key_properties = ['agent', 'date']
    folder_name = 'Agent Reports'
    report_name = 'Agent Occupancy'
    datetime_fields = set(['date'])


class AgentInformation(ReportStream):
    name = 'agent_information'
    stream = 'agent_information'
    replication_method = 'FULL_TABLE'
    key_properties = ['agent_id', 'agent']
    folder_name = 'Agent Reports'
    report_name = 'Agents Information'
    datetime_fields = set()


class CustomReport(ReportStream):
    def __init__(self, name, replication_method, replication_key, key_properties, folder_name, report_name, datetime_fields, stream, client, start_date):
        self.name = name
        self.replication_method = replication_method
        self.replication_key = replication_key
        self.key_properties = key_properties
        self.folder_name = folder_name
        self.report_name = report_name
        self.datetime_fields = set(datetime_fields)
        self.stream = stream
        super().__init__(client, start_date)


STREAMS = {
    'call_log': CallLog,
    'agent_login_logout': AgentLoginLogout,
    'agent_occupancy': AgentOccupancy,
    'agent_information': AgentInformation,
}
