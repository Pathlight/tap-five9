import singer
import time

import zeep
from five9 import Five9

LOGGER = singer.get_logger()


class Five9API:
    URL_TEMPLATE = 'https://{}.gorgias.com'
    MAX_RETRIES = 10

    def __init__(self, config):
        self.client = Five9(config['username'], config['password'])

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
            LOGGER.info(f'five9 running report {report_name}: {start} - {end}')
            identifier = self.client.configuration.runReport(
                folderName=folder_name,
                reportName=report_name,
                criteria=criteria
            )
            time.sleep(15)
            results = self.client.configuration.getReportResult(identifier)
            if results:
                return zeep.helpers.serialize_object(results)

        LOGGER.exception('error retrieving five9 report')
