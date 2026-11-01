import requests
import functools
import datetime
import time

REQUEST_TIMEOUT = 30

class ESI:
    def __init__(self, sso):
        self.sso = sso
        self.esi_server = 'https://esi.evetech.net'

    @functools.lru_cache()
    def get_alliance(self, alliance_id):
        url = '/latest/alliances/%d/' % alliance_id
        return self.esi_get(url)

    @functools.lru_cache()
    def get_corporation(self, corporation_id):
        url = '/latest/corporations/%d/' % corporation_id
        return self.esi_get(url)

    @functools.lru_cache()
    def get_character(self, character_id):
        url = '/latest/characters/%d/' % character_id
        return self.esi_get(url)

    def get_notifications(self):
        url = '/latest/characters/%d/notifications/' % self.sso.character_id
        return self.esi_get(url)

    def get_new_notifications(self, max_age=None):
        notifications = self.get_notifications()
        return sorted(
            filter(
                lambda notification: self.is_recent_notification(notification['timestamp'], max_age) is True,
                notifications),
            key=lambda notification: notification['timestamp'])

    def is_recent_notification(self, timestamp, max_age=None):
        if not max_age:
            return True

        now = datetime.datetime.now(datetime.timezone.utc)
        event_time = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        difference = now - event_time
        return difference.total_seconds() < max_age

    @functools.lru_cache()
    def get_structure(self, structure_id):
        url = '/latest/universe/structures/%d/' % structure_id
        return self.esi_get(url)

    @functools.lru_cache()
    def get_moon(self, moon_id):
        return self.esi_get(
            '/latest/universe/moons/%d/' % moon_id
        )

    @functools.lru_cache()
    def get_planet(self, planet_id):
        return self.esi_get(
            '/latest/universe/planets/%d/' % planet_id
        )

    @functools.lru_cache()
    def get_system(self, system_id):
        return self.esi_get(
            '/latest/universe/systems/%d/' % system_id
        )

    @functools.lru_cache()
    def get_item(self, item_id):
        return self.esi_get(
            '/latest/universe/types/%d/' % item_id
        )

    @functools.lru_cache()
    def get_killmail(self, killmail_id, killmail_hash):
        return self.esi_get(
            '/latest/killmails/%d/%s/' % (killmail_id, killmail_hash)
        )

    def esi_get(self, endpoint, query=None):
        max_attempts = 3
        failed_request_delay = 10

        params = dict(query or {})
        params['datasource'] = 'tranquility'
        # Send the token as a header rather than a query parameter, so it
        # doesn't end up in URLs, proxies or exception messages.
        headers = {'Authorization': 'Bearer %s' % self.sso.get_access_token()}

        url = '%s%s' % (self.esi_server, endpoint)

        for attempt in range(1, max_attempts + 1):
            r = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)

            if r.status_code == 200:
                response = r.json()
                return response
            elif r.status_code >= 500 and r.status_code < 600 and attempt < max_attempts:
                try:
                    json = r.json()
                except ValueError:
                    json = {}
                if r.status_code == 500 and isinstance(json, dict) and 'response' in json:
                    return json['response']
                print('Delaying as server recovery attempt')
                time.sleep(failed_request_delay)
                continue
            else:
                print(r.headers)
                r.raise_for_status()
