Reconbot for Eve Online [![CircleCI](https://circleci.com/gh/flakas/reconbot.svg?style=svg)](https://circleci.com/gh/flakas/reconbot)
=======================

Reconbot is a notification relay bot for an MMO game [Eve Online](http://secure.eveonline.com/signup/?invc=905e73a0-eb57-49ab-8fe5-9759c2ba5e99&action=buddy).
It fetches character notifications from the EVE API, filters irrelevant ones out and sends relevant ones to set Slack or Discord channels.
Notifications like SOV changes, SOV/POS/POCO/Citadel attacks.

# Setup

Reconbot was intended to be used as a base for further customizations, or integration with other systems, but it can be run via `run.py` as well. Check it out for an example. In this version it can also be run in Docker container, using simple `docker-compose` command.

## 1. EVE Developer Application

This tool is ready to be used with [Eve's ESI API](https://esi.tech.ccp.is/). You will need to register your application on [EVE Developers page](https://developers.eveonline.com/applications).

When registering your EVE Application, please pick `Authentication & API Access` connection type, and make sure your application requests these permissions:

- `esi-universe.read_structures.v1` - necessary to fetch names of any linked structures;
- `esi-characters.read_notifications.v1` - necessary to fetch character level notifications.

Reconbot does not provide a way to authenticate an account to an application, so you will need to do so via some other means. First two sections of Fuzzysteve's guide on [Using ESI with Google Sheets](https://www.fuzzwork.co.uk/2017/03/14/using-esi-google-sheets/) explain how to do that via [Postman](https://www.getpostman.com/). 

When registering the application take note of the `Client ID` and `Secret Key`, as they are necessary for Reconbot to establish communication with ESI API.

### Postman settings

Reconbot uses ESI 2.0 API, but the Fuzzysteve's guide uses API v1. Please use below settings for Postman. `<>` means that you should insert something there.

- Authorization: `Oauth 2.0`
- Auth URL: `https://login.eveonline.com/v2/oauth/authorize`
- Access Token URL: `https://login.eveonline.com/v2/oauth/token`
- Client ID: `<app client id>`
- Client Secret: `<app secret>`
- Scope: `esi-universe.read_structures.v1 esi-characters.read_notifications.v1`
- State: `<anything, cannot be empty>`

Please write `refresh token` from the results, it will be used later.

## 2. Slack or Discord chat tools

### Slack

To add a Slack integration, check out [this Slack documentation page on Bot Users](https://api.slack.com/bot-users) (or [create bot user for your workspace](https://my.slack.com/services/new/bot)). Take note of the API token.

### Discord

__If you wish to use a Discord webhook:__

Webhooks are the easiest way to integrate Reconbot with Discord. Simply follow [this Discord guide](https://support.discordapp.com/hc/en-us/articles/228383668-Intro-to-Webhooks) to create a webhook for your channel.
You should now have a URL like this:
```
https://discordapp.com/api/webhooks/496014874437332490/5783au24jzyEFIaWnfTvJn0gFzh5REEEE3ee3e3eNKeFee3We2cIe_6e7e36ugUj5zEm
```

Use it with `DiscordWebhookNotifier` as seen in `run.py` example.

__If you wish to use a Discord bot user:__ (not recommended)

To add a Discord integration, check out [this Discord documentation page on Bot accounts](https://discordapp.com/developers/docs/topics/oauth2#bots).
You will need to [create an application](https://discordapp.com/developers/applications/me#top) and add it to your discord server.
See [this guide](https://github.com/Chikachi/DiscordIntegration/wiki/How-to-get-a-token-and-channel-ID-for-Discord) for more visual step-by-step instructions.
You will need a `Token` for your Bot User, and `Channel ID` where to post messages in.
Use it with `DiscordNotifier` as seen in `run.py` example.

## 3. Reconbot setup

This one uses docker-compose, over raw python execution.

1. Clone this repository
2. Copy `.env.example` to `.env` and modify it using your settings. More on that below. Do the same with `characters.yaml.example` -> `characters.yaml`. Take character ID from zkillboard, use refresh token from the Postman.
  File `run.py` contain `whitelist`, which indicates which notification types you're interested in (or `None` to allow all supported types).
3. Execute `docker-compose up -d --force-recreate --build` and wait for notifications to arrive! After the character gets a notification in-game, `reconbot` may take up to 10 minutes to detect the notification.
4. If you receive no notification (but you believe you should) check `docker container ls` and use that id for `docker logs <id>`. This usually means that the refresh token is invalid, or ESI API is down.

`.env`:

- `WEBHOOK_URL` - discord webhook url from 2. step
- `SSO_APP_CLIENT_ID` - eve app client id from 1. step
- `SSO_APP_SECRET_KEY` - eve app secret from 1. step
- `CONTAINER_NAME` - name of the container which will be used for docker, does not really matter, but must not be empty
- `MAX_NOTIFICATION_AGE_IN_SECONDS` - the bot will get in game notifications not older that this
- `DEFAULT_PING_ROLE` - pings will use this handle for default-level pings. Can be empty string, then it will just write without pinging anyone.
- `ESCALATED_PING_ROLE` - same as above, but for escalated-level pings. Currently escalted level pings are: `OrbitalReinforced`, `OrbitalAttacked`, `StructureUnderAttack`, `StructureLostShields`, `StructureLostArmor`, `StructureWentLowPower`, `TowerAlertMsg`. Use `@everyone` or `@here` for pinging everyone in channel.
- `ADDITIONAL_INFO` - any text that, will be added to escalated level pings.

`characters.yaml`:

- `character_name` - self explanatory
- `character_id` - use zkillboard or similar service to grab id of your character
- `refresh_token` - token from postman from 1. step

# Other notes

Reconbot by default will try to evenly spread out checking API keys over the cache expiry window (which is 10 minutes for ESI), meaning that with 2 API keys in rotation an API key will be checked every ~5 minutes (with 10 keys - every minute), which can be useful to detect alliance or corporation-wide notifications more frequently than only once every 10 minutes.

## Supported notifications

As of writing this tool there is little documentation about the types of notifications available and their contents. The following list has been assembled from working experience, is not fully complete and may be subject to change as CCP changes internals:

- AllWarDeclaredMsg
- DeclareWar
- AllWarInvalidatedMsg
- AllyJoinedWarAggressorMsg
- CorpWarDeclaredMsg
- EntosisCaptureStarted
- SovCommandNodeEventStarted
- SovStructureDestroyed
- SovStructureReinforced
- StructureUnderAttack
- OwnershipTransferred
- OrbitalReinforced
- OrbitalAttacked
- StructureOnline
- StructureDestroyed
- StructureFuelAlert
- StructureWentLowPower
- StructureWentHighPower
- StructureFuelAlert
- StructureAnchoring
- StructureUnanchoring
- StructureServicesOffline
- StructureLostShields
- StructureLostArmor
- TowerAlertMsg
- TowerResourceAlertMsg
- StationServiceEnabled
- StationServiceDisabled
- OrbitalReinforced
- OrbitalAttacked
- SovAllClaimAquiredMsg
- SovStationEnteredFreeport
- AllAnchoringMsg
- InfrastructureHubBillAboutToExpire
- SovAllClaimLostMsg
- SovStructureSelfDestructRequested
- SovStructureSelfDestructFinished
- StationConquerMsg
- MoonminingExtractionStarted
- MoonminingExtractionCancelled
- MoonminingExtractionFinished
- MoonminingLaserFired
- MoonminingAutomaticFracture
- CorpAllBillMsg
- BillPaidCorpAllMsg
- CharAppAcceptMsg
- CorpAppNewMsg
- CharAppWithdrawMsg
- CharLeftCorpMsg
- CorpNewCEOMsg
- CorpVoteMsg
- CorpVoteCEORevokedMsg
- CorpTaxChangeMsg
- CorpDividendMsg
- BountyClaimMsg
- KillReportVictim
- KillReportFinalBlow
- AllianceCapitalChanged

Do you have sample contents of currently unsupported notification types? Consider sharing them by creating an issue, or submit a Pull Request. Any help would be appreciated!
