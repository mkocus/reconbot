import schedule
import time
import sqlite3

from reconbot.tasks import esi_notification_task
from reconbot.notifiers.caching import CachingNotifier
from reconbot.notifiers.discordwebhook import DiscordWebhookNotifier
from reconbot.notifiers.splitter import SplitterNotifier
from reconbot.notifiers.filter import FilterNotifier
from reconbot.apiqueue import ApiQueue
from reconbot.esi import ESI
from reconbot.sso import SSO

notification_caching_timer = 10

discord = {
    'my-webhook': {
        'url': ''
    }
}

sso_app = {
    'client_id': '',
    'secret_key': ''
}

eve_apis = {
    'logistics-team': {
        'notifications': {
            'whitelist': [
                'SovStructureDestroyed',
                'SovStructureReinforced',
                'StructureUnderAttack',
                'OwnershipTransferred',
                'StructureOnline',
                'StructureFuelAlert',
                'StructureAnchoring',
                'StructureServicesOffline',
                'StructureLostShields',
                'StructureLostArmor',
                'TowerAlertMsg',
                'StationServiceEnabled',
                'StationServiceDisabled',
                'OrbitalReinforced',
                'OrbitalAttacked',
                'SovAllClaimAquiredMsg',
                'SovStationEnteredFreeport',
                'SovAllClaimLostMsg',
                'SovStructureSelfDestructRequested',
                'SovStructureSelfDestructFinished',
                'StationConquerMsg',
                'notificationTypeMoonminingExtractionStarted',
                'MoonminingExtractionFinished',
                'MoonminingLaserFired',
            ],
        },
        'characters': {
            'ccp-example-3': {
                'character_name': 'CCP Example 3',
                'character_id': 55555555,
                'refresh_token': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
            },
            'ccp-example-4': {
                'character_name': 'CCP Example 4',
                'character_id': 77777777,
                'refresh_token': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
            },
        },
    }
}

my_discord_channels = CachingNotifier(
    SplitterNotifier([
        DiscordWebhookNotifier(
            discord['my-webhook']['url']
        )
    ]),
    duration=3600
)

def api_to_sso(api):
    return SSO(
        sso_app['client_id'],
        sso_app['secret_key'],
        api['refresh_token'],
        api['character_id']
    )

api_queue_logistics = ApiQueue(list(map(api_to_sso, eve_apis['logistics-team']['characters'].values())))

def notifications_job_logistics():
    esi_notification_task(
        eve_apis['logistics-team']['notifications'],
        api_queue_logistics,
        'discord',
        my_discord_channels
    )


def run_and_schedule(characters, notifications_job):
    notifications_job()
    schedule.every(notification_caching_timer/len(characters)).minutes.do(notifications_job)

run_and_schedule(eve_apis['fc-team']['characters'], notifications_job_fc)
run_and_schedule(eve_apis['logistics-team']['characters'], notifications_job_logistics)

while True:
    schedule.run_pending()
    time.sleep(1)
