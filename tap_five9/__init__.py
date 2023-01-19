#!/usr/bin/env python3
import os
import json
import singer
from singer import utils, metadata
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema
from tap_five9.custom_schema import build_schema
from tap_five9.streams import STREAMS, CustomReport
from tap_five9.sync import sync_stream
from tap_five9.client import Five9API


LOGGER = singer.get_logger()
REQUIRED_CONFIG_KEYS = ["username", "password", "start_date"]


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schemas():
    """ Load schemas from schemas folder """
    schemas = {}
    for filename in os.listdir(get_abs_path('schemas')):
        path = get_abs_path('schemas') + '/' + filename
        file_raw = filename.replace('.json', '')
        with open(path) as file:
            schemas[file_raw] = Schema.from_dict(json.load(file))
    return schemas


def discover(client, config, custom_reports):
    raw_schemas = load_schemas()
    streams = []
    for stream_id, schema in raw_schemas.items():
        stream_instance = STREAMS[stream_id]
        stream_metadata = metadata.get_standard_metadata(
            schema=schema.to_dict(),
            key_properties=stream_instance.key_properties,
            valid_replication_keys=stream_instance.replication_key,
            replication_method=stream_instance.replication_method
        )
        streams.append(
            CatalogEntry(
                tap_stream_id=stream_id,
                stream=stream_id,
                schema=schema,
                key_properties=stream_instance.key_properties,
                metadata=stream_metadata,
                replication_key=stream_instance.replication_key,
                is_view=None,
                database=None,
                table=None,
                row_count=None,
                stream_alias=None,
                replication_method=stream_instance.replication_method,
            )
        )
    if custom_reports:
        for report in custom_reports:
            schema = build_schema(client, report, stream=stream_id, config=config)
            schema = Schema.from_dict(schema)
            key_properties = report.get('key_properties')
            replication_key = report.get('valid_replication_keys')
            stream_metadata = metadata.get_standard_metadata(
                schema=schema.to_dict(),
                key_properties=key_properties,
                valid_replication_keys=replication_key,
                replication_method=None
            )
            streams.append(
                CatalogEntry(
                    tap_stream_id=report['stream_id'],
                    stream=report['stream_id'],
                    schema=schema,
                    key_properties=report.get('key_properties'),
                    metadata=stream_metadata,
                    replication_key=report.get('valid_replication_keys'),
                    is_view=None,
                    database=None,
                    table=None,
                    row_count=None,
                    stream_alias=report,
                    replication_method=None,
                )
            )
    return Catalog(streams)


def stream_is_selected(mdata):
    return mdata.get((), {}).get('selected', False)


def get_selected_streams(catalog):
    selected_stream_names = []
    for stream in catalog.streams:
        mdata = metadata.to_map(stream.metadata)
        if stream_is_selected(mdata):
            selected_stream_names.append(stream.tap_stream_id)
    return selected_stream_names


def populate_class_schemas(catalog, selected_stream_names):
    for stream in catalog.streams:
        if stream.tap_stream_id in selected_stream_names and STREAMS.get(stream.tap_stream_id):
            STREAMS[stream.tap_stream_id].stream = stream


def do_sync(client, catalog, state, config, start_date):

    selected_stream_names = get_selected_streams(catalog)
    populate_class_schemas(catalog, selected_stream_names)

    for stream in catalog.streams:
        stream_name = stream.tap_stream_id
        if stream_name not in selected_stream_names:
            LOGGER.info("%s: Skipping - not selected", stream_name)
            continue

        singer.write_schema(
            stream_name,
            stream.schema.to_dict(),
            stream.key_properties
        )

        LOGGER.info("%s: Starting sync", stream_name)
        if STREAMS.get(stream_name):
            instance = STREAMS[stream_name](client, start_date)
        else:
            stream_alias = stream.stream_alias
            instance = CustomReport(
                name=stream.tap_stream_id,
                replication_method=stream_alias['replication_method'],
                replication_key=stream_alias['valid_replication_keys'],
                key_properties=stream_alias['key_properties'],
                folder_name=stream_alias['folder_name'],
                report_name=stream_alias['report_name'],
                datetime_fields=stream_alias.get('datetime_fields'),
                stream=stream,
                client=client,
                start_date=start_date
            )
        counter_value = sync_stream(state, config, start_date, instance)
        singer.write_state(state)
        LOGGER.info("%s: Completed sync (%s rows)", stream_name, counter_value)

    singer.write_state(state)
    LOGGER.info("Finished sync")


@utils.handle_top_exception(LOGGER)
def main():
    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)
    config = args.config
    client = Five9API(config)

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog = discover(client, config, config.get('custom_reports'))
        catalog.dump()
    # Otherwise run in sync mode
    else:
        if args.catalog:
            catalog = args.catalog
        else:
            catalog = discover(client, config, config.get('custom_reports'))
        start_date = config['start_date']
        do_sync(client, catalog, args.state, config, start_date)


if __name__ == "__main__":
    main()
