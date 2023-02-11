import abc
import requests
from reconbot.notificationprinters.esi.printer import Printer

class Discord(Printer):

    def get_corporation(self, corporation_id):
        corporation = self.eve.get_corporation(corporation_id)
        result = '[%s](<https://zkillboard.com/corporation/%d/>)' % (corporation['name'], corporation_id)

        if 'alliance_id' in corporation:
            result = '[%s] [%s]' % (result, self.get_alliance(corporation['alliance_id']))

        return result

    def get_alliance(self, alliance_id):
        alliance = self.eve.get_alliance(alliance_id)
        return '[%s](<https://zkillboard.com/alliance/%d/>)' % (alliance['name'], alliance_id)

    def get_system(self, system_id):
        system = self.eve.get_system(system_id)
        return '**[%s](<http://evemaps.dotlan.net/system/%s>)**' % (system['name'], system['name'])

    def get_character(self, character_id):
        if not character_id:
            return 'Unknown character'
        if character_id == 1000127 or character_id == 1000134:
            npc_corp_name = self.get_corporation(character_id)
            return '**Some Dickhead NPC** %s' % (npc_corp_name)

        try:
            character = self.eve.get_character(character_id)
        except requests.HTTPError as ex:
            # Patch for character being unresolvable and ESI throwing internal errors
            # Temporarily stub character to not break our behavior.
            if ex.response.status_code in [404, 500]:
                character = { 'name': 'Unknown character', 'corporation_id': 98356193 }
            else:
                raise

        return '**[%s](<https://zkillboard.com/character/%d/>)** %s' % (
            character['name'],
            character_id,
            self.get_corporation(character['corporation_id'])
        )

    def get_killmail(self, killmail_id, killmail_hash):
        killmail = self.eve.get_killmail(killmail_id, killmail_hash)
        victim = self.get_character(killmail['victim']['character_id'])
        ship = self.get_item(killmail['victim']['ship_type_id'])
        system = self.get_system(killmail['solar_system_id'])

        return '%s lost a(n) %s in %s (<https://zkillboard.com/kill/%d/>)' % (
            victim,
            ship,
            system,
            killmail_id
        )
