import datetime
import inflection
import singer
import time
import re
import zeep
from five9 import Five9

LOGGER = singer.get_logger()


class Five9API:
    URL_TEMPLATE = 'https://{}.gorgias.com'
    MAX_RETRIES = 10
    POLL_TIMEOUT = 600 # in seconds, maximum of 10 minutes of waiting for each report.
    POLL_DELAY = 5 # in seconds

    def __init__(self, config):
        self.client = Five9(config['username'], config['password'])

    def inflect_field(self, field):

        field = re.sub(r'[^a-zA-Z0-9]', '_', field)
        field = re.sub(r"([A-Z]+)_([A-Z][a-z])", r'\1__\2', field)
        field = re.sub(r"([a-z\d])_([A-Z])", r'\1__\2', field)
        return inflection.underscore(field)

    def run_report(self, params):
        folder_name = params['folder_name']
        report_name = params['report_name']
        start = params['start']
        end = params['end']
        criteria = {
            'time': {
                'start': start,
                'end': end
            }
        }

        for num_retries in range(self.MAX_RETRIES):
            LOGGER.info(f'five9 running report "{report_name}": {start} - {end}')
            identifier = self.client.configuration.runReport(
                folderName=folder_name,
                reportName=report_name,
                criteria=criteria
            )
            time.sleep(5)
            if identifier:
                return identifier

        LOGGER.exception('error running five9 report')

    def get_report_results(self, identifier, config=None):
        LOGGER.info(f'five9 report created with identifier: {identifier}')

        poll_timeout = self.POLL_TIMEOUT
        poll_delay = self.POLL_DELAY
        if config.get('poll_settings'):
            settings = config.get('poll_settings', {})
            poll_timeout = settings.get('timeout')
            poll_delay = settings.get('delay')

        is_running = True
        start_time = datetime.datetime.utcnow()
        elapsed_time = 0
        while is_running:
            if elapsed_time > poll_timeout:
                # Abort if the timeout occurred and return so we continue to the next stream
                LOGGER.exception(f'five9 timed out while running the report (max {poll_timeout} sec)')
                return []
            is_running = self.client.configuration.isReportRunning(identifier=identifier, timeout=poll_delay)
            elapsed_time = (datetime.datetime.utcnow() - start_time).total_seconds()
            LOGGER.info(f'five9 report is running ({elapsed_time} seconds), waiting {poll_delay} sec until next check.')

        LOGGER.info(f'five9 getting report results')
        try:
            response = self.client.configuration.getReportResult(identifier)
        except zeep.exceptions.Fault as e:
            LOGGER.info('Failed to get report results after report stopped running')
            raise e

        if response:
            fields = [self.inflect_field(field) for field in response.header['values']['data']]
            return self.client.parse_response(fields, response.records)

        LOGGER.exception(f'error getting five9 report for {identifier}')

    def return_report_results(self, params, config=None):
        identifier = self.run_report(params)
        return self.get_report_results(identifier, config=config)
