"""
Background worker which polls the 511 API to generate alerts based on rules
configured by users.
"""
from collections import defaultdict
from optparse import OptionParser
import os.path
import sys
import time

from muni import MuniClient
from notifications import notify

from boto.dynamodb2.table import Table


def get_notifications_table(table_name):
    table = Table(table_name)
    return table


def import_rules(table):
    notification_rules = {}
    for notification in table.scan():
        notification_rules[notification['watch_id']] = dict(notification.items())

    return notification_rules


def get_rules_by_stop(table):
    notification_rules = import_rules(table)
    notifications_by_stop = defaultdict(list)
    for notification_id, rule in notification_rules.iteritems():
        notifications_by_stop[rule['stop_code']].append(rule)

    return notifications_by_stop


def check_and_notify(dynamo_table, muni_token):
    dynamo_table = get_notifications_table(dynamo_table)
    muni = MuniClient(token=muni_token)

    notifications_by_stop = get_rules_by_stop(dynamo_table)
    for stop_code, rules in notifications_by_stop.iteritems():
        departures = muni.get_next_departures_by_stop_code(stop_code)
        for rule in rules:
            route = rule['route_code']
            if int(rule['threshold']) in departures[route]['times']:
                # TODO: This should probably try to detect and pass through the
                # departure that's causing it to be triggered
                trigger(dynamo_table, rule['watch_id'], departures)
            else:
                untrigger(dynamo_table, rule['watch_id'])
            print "%s: %s" % (route, ','.join([str(t) for t in departures[route]['times']]))


def trigger(table, rule_id, departures):
    rule = table.get_item(watch_id=rule_id)

    if rule['triggered']:
        return

    print "Triggering rule %s" % rule_id

    notify(dict(rule['notification_settings']), departures)
    rule['triggered'] = True
    rule.save()


def untrigger(table, rule_id):
    rule = table.get_item(watch_id=rule_id)

    if not rule['triggered']:
        return

    print "Un-triggering rule %s" % rule_id

    rule['triggered'] = False
    rule.save()


def daemon_loop(options):
    dynamo_table = options.dynamo_table
    muni_token = get_muni_token(options)

    while True:
        start_time = time.time()

        check_and_notify(dynamo_table, muni_token)

        end_time = time.time()
        elapsed = end_time - start_time
        print "One iteration ran %.02f seconds" % elapsed

        if elapsed < options.interval:
            sleep_time = options.interval - elapsed
            print "Sleeping %.02f seconds" % sleep_time
            time.sleep(sleep_time)


def get_muni_token(options):
    if options.token:
        return options.token
    elif options.token_file:
        return read_muni_token_file(options.token_file)
    else:
        raise Exception("Couldn't get muni token because no token or file specified.")


def read_muni_token_file(token_file):
    with open(token_file) as f:
        token = f.read().strip()
    return token


def validate_options(options):
    """Does some basic validation of the options provided, including looking
    for invalid option combinations and non-existent files.
    """
    if options.token and options.token_file:
        die("You may only specify one of --token and --token-file, not both.")

    if not options.token and not options.token_file:
        die("You must specify either --token or --token-file!")

    if not os.path.exists(options.token_file):
        die("Failed to find token file at %s" % options.token_file)

    if not options.dynamo_table:
        die("You must specify a Dynamo table to read from")


def die(message):
    print >> sys.stderr, message
    sys.exit(1)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-d", "--dynamo-table", dest="dynamo_table", default=None, help="Which Dynamo table to read from")
    parser.add_option("-i", "--interval", dest="interval", type=int, default=10)
    parser.add_option("--token", dest="token", type=str, default=None, help="A 511.org token to be used with the Muni API")
    parser.add_option("--token-file", dest="token_file", type=str, default=None, help="A file containing a 511.org token")
    options, args = parser.parse_args()

    validate_options(options)

    daemon_loop(options)
