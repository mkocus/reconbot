from unittest import TestCase
from unittest.mock import Mock

import yaml

from reconbot.notificationprinters.esi.printer import Printer, parse_notification_text


class ParseNotificationTextTest(TestCase):
    def test_parses_regular_notification_body(self):
        text = 'allianceID: 99000001\ncorpID: 98000001\nsolarSystemID: 30000142\n'

        self.assertEqual(
            {'allianceID': 99000001, 'corpID': 98000001, 'solarSystemID': 30000142},
            parse_notification_text(text),
        )

    def test_parses_anchors_and_nested_values(self):
        text = 'a: &id001\n- 1\n- 2\nb: *id001\nwants:\n- quantity: 10\n  typeID: 4051\n'

        result = parse_notification_text(text)

        self.assertEqual([1, 2], result['b'])
        self.assertEqual([{'quantity': 10, 'typeID': 4051}], result['wants'])

    def test_empty_body_becomes_empty_dict(self):
        self.assertEqual({}, parse_notification_text('{}\n'))
        self.assertEqual({}, parse_notification_text(''))

    def test_python_object_tags_are_not_executed(self):
        for payload in (
            'x: !!python/object/apply:os.system ["touch /tmp/pwned"]',
            'x: !!python/object/new:subprocess.Popen [["id"]]',
            'x: !!python/name:os.system',
        ):
            with self.subTest(payload=payload):
                result = parse_notification_text(payload)
                # The tagged node is loaded as inert data, never as a callable/object.
                self.assertIsInstance(result['x'], (str, list, dict))

    def test_unknown_tags_are_loaded_as_plain_data(self):
        result = parse_notification_text('t: !!python/tuple [1, 2]\ns: !custom value\n')

        self.assertEqual({'t': [1, 2], 's': 'value'}, result)

    def test_plain_safe_load_would_reject_tags(self):
        with self.assertRaises(yaml.constructor.ConstructorError):
            yaml.safe_load('x: !!python/object/apply:os.getcwd []')


class PrinterTransformTest(TestCase):
    def test_renders_notification(self):
        printer = Printer(Mock())
        printer.get_corporation = lambda corp_id: 'Corp %d' % corp_id
        printer.get_system = lambda system_id: 'System %d' % system_id

        text = printer.get_notification_text({
            'type': 'SovAllClaimLostMsg',
            'text': 'corpID: 98000001\nsolarSystemID: 30000142\n',
            'timestamp': '2026-11-01T12:00:00Z',
        })

        self.assertEqual('SOV lost in System 30000142 by Corp 98000001', text)

    def test_eve_timestamp_to_date(self):
        printer = Printer(Mock())
        # 2026-11-01 12:00:00 UTC as a Windows FILETIME (100ns ticks since 1601)
        filetime = (1793534400 + 11644473600) * 10000000

        self.assertEqual('2026-11-01 12:00:00', printer.eve_timestamp_to_date(filetime))
