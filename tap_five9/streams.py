import datetime
import inflection
import pytz
import re
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
    results_key = None

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

    def inflect_header(self, header):

        header = re.sub(r'[^a-zA-Z0-9]', '_', header)
        header = re.sub(r"([A-Z]+)_([A-Z][a-z])", r'\1__\2', header)
        header = re.sub(r"([a-z\d])_([A-Z])", r'\1__\2', header)
        return inflection.underscore(header)

    def sync(self, state):
        try:
            sync_thru = singer.get_bookmark(state, self.name, self.replication_key)
        except TypeError:
            sync_thru = self.start_date

        curr_synced_thru = sync_thru

        params = {
                'folder_name': self.folder_name,
                'report_name': self.report_name,
                'start': sync_thru,
                'end': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
            }

        resp = self.client.run_report(params)
        headers = [self.inflect_header(header) for header in resp['header']['values']['data']]
        data = resp[self.results_key]
        for row in data:
            values = row['values']['data']
            record = {headers[i]: self.transform_value(headers[i], values[i]) for i in range(len(headers))}
            yield(self.stream, record)

            bookmark_date = record.get(self.replication_key)
            curr_synced_thru = max(curr_synced_thru, bookmark_date)

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
    results_key = 'records'


STREAMS = {
    'call_log': CallLog
}
