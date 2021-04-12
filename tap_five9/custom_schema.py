import datetime
import dateutil.parser
import singer

from collections import defaultdict


LOGGER = singer.get_logger()


def create_observations(samples):
    observations = defaultdict(set)

    # everything comes back from five9 as a string
    for row in samples:
        for k, v in row.items():

            if not v:
                continue

            data = None

            # check if it's an integer
            try:
                data = int(v)
                observations[k].add('integer')
                continue
            except ValueError:
                pass

            # check if it's a number
            try:
                data = float(v)
                observations[k].add('number')
                continue
            except ValueError:
                pass

            # check if it's a date
            try:
                data = dateutil.parser.parse(v, default=datetime.datetime(1970, 1, 1, 0, 0))
                if data.year == 1970:
                    observations[k].add('timestamp')
                else:
                    observations[k].add('date-time')
                continue
            except (dateutil.parser.ParserError, OverflowError):
                pass

            # otherwise assume it's a string
            observations[k].add('string')

    return observations


def build_schema(client, report):

    # get a day's worth of data
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(days=1)
    params = {
        'folder_name': report['folder_name'],
        'report_name': report['report_name'],
        'start': start.strftime('%Y-%m-%dT00:00:00.000'),
        'end': end.strftime('%Y-%m-%dT00:00:00.000')
    }
    results = client.return_report_results(params)

    sample_selection = results[:10]
    observations = create_observations(sample_selection)

    json_schema = {
        'type': 'object',
        'additionalProperties': False,
        'properties': {}
    }
    headers = sample_selection[0].keys()
    for header in headers:
        if not observations.get(header) or len(observations.get(header)) > 1:
            LOGGER.info(f'Unknown value type for {header}, setting as string')
            prop = {header: {'type': ['null', 'string']}}

        else:
            data_type = observations[header].pop()

            if data_type in ['timestamp', 'date-time']:
                prop = {header: {'type': ['null', 'string'], 'format': data_type}}
            else:
                prop = {header: {'type': ['null', data_type]}}

        json_schema['properties'].update(prop)

    return json_schema
