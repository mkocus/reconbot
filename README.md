Reconbot for Eve Online [![tests](https://github.com/mkocus/reconbot/actions/workflows/tests.yml/badge.svg)](https://github.com/mkocus/reconbot/actions/workflows/tests.yml)
=======================

Reconbot is a notification relay bot for an MMO game [Eve Online](http://secure.eveonline.com/signup/?invc=905e73a0-eb57-49ab-8fe5-9759c2ba5e99&action=buddy).
It fetches character notifications from the EVE API, filters irrelevant ones out and sends relevant ones to a Discord channel via a webhook.
Notifications like SOV changes, SOV/POS/POCO/Citadel attacks.

# About this fork

This is a maintained fork of [flakas/reconbot](https://github.com/flakas/reconbot), which is no longer developed. Version 2.0 (November 2026) brings it up to date:

**Security**
- ESI notification bodies are parsed with a safe YAML loader. The old code used `yaml.load()` from PyYAML 4.2b1, which builds arbitrary Python objects. Notification texts contain values controlled by other players (structure, corporation and character names), so a crafted YAML tag could run code on the host. Unknown tags are now loaded as plain data.
- `characters.yaml` is loaded with `yaml.safe_load()`.
- The ESI access token is sent in the `Authorization` header instead of the URL.
- All HTTP requests have timeouts, so a hanging ESI, SSO or Discord call can no longer stall the bot.

**Runtime**
- Python 3.6 on Debian 10 (both end-of-life) → Python 3.13 on Debian 13 (`python:3.13-slim-trixie`).
- Current libraries: PyYAML 6.0.3, requests 2.34.2, schedule 1.2.2, python-dotenv 1.2.4. The unused `discord.py` dependency was removed.
- Deprecated APIs (`datetime.utcnow()`, `utcfromtimestamp()`, `distutils`) replaced.
- The error handler no longer crashes on exceptions that carry no HTTP response.

**Container**
- Runs as an unprivileged user (UID 1000) with a read-only root filesystem, all Linux capabilities dropped and `no-new-privileges`.
- Secrets stay out of the image: `.env` is passed as environment variables and `characters.yaml` is mounted read-only at runtime.
- Docker Compose v2 (`docker compose`).

**Development**
- CircleCI (Python 3.5) replaced with GitHub Actions running `pytest` on Python 3.13.
- Tests for notification parsing, including YAML injection attempts.

## Upgrading from the old version

1. Pull the new code. Your existing `.env` and `characters.yaml` keep working.
2. Make `characters.yaml` readable by UID 1000, which the container runs as: `sudo chown 1000:1000 characters.yaml && sudo chmod 600 characters.yaml`.
3. Rebuild with Compose v2: `docker compose up -d --build`. If you still have the old `docker-compose` v1 (1.29), it may fail with `KeyError: 'ContainerConfig'` when recreating containers; install the Compose v2 plugin instead.

# Setup

Reconbot was intended to be used as a base for further customizations, or integration with other systems, but it can be run via `run.py` as well. Check it out for an example. In this version it can also be run in Docker container, using simple `docker compose` command. Requires Python 3.10+ (the Docker image uses Python 3.13).

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

## 2. Discord webhook

Reconbot posts to Discord through a webhook. Simply follow [this Discord guide](https://support.discordapp.com/hc/en-us/articles/228383668-Intro-to-Webhooks) to create a webhook for your channel.
You should now have a URL like this:
```
https://discordapp.com/api/webhooks/496014874437332490/5783au24jzyEFIaWnfTvJn0gFzh5REEEE3ee3e3eNKeFee3We2cIe_6e7e36ugUj5zEm
```

It is used by `DiscordWebhookNotifier`, see `run.py`.

## 3. Reconbot setup

This one uses Docker Compose v2, over raw python execution. `characters.yaml` is mounted into the container at runtime (it is not baked into the image); keep it readable by UID 1000, e.g. `chmod 600 characters.yaml` as that user.

1. Clone this repository
2. Copy `.env.example` to `.env` and modify it using your settings. More on that below. Do the same with `characters.yaml.example` -> `characters.yaml`. Take character ID from zkillboard, use refresh token from the Postman.
  File `run.py` contain `whitelist`, which indicates which notification types you're interested in (or `None` to allow all supported types).
3. Execute `docker compose up -d --force-recreate --build` and wait for notifications to arrive! After the character gets a notification in-game, `reconbot` may take up to 10 minutes to detect the notification.
4. If you receive no notification (but you believe you should) check `docker container ls` and use that id for `docker logs <id>`. This usually means that the refresh token is invalid, or ESI API is down.

`.env`:

- `WEBHOOK_URL` - discord webhook url from 2. step
- `SSO_APP_CLIENT_ID` - eve app client id from 1. step
- `SSO_APP_SECRET_KEY` - eve app secret from 1. step
- `CONTAINER_NAME` - name of the container which will be used for docker, does not really matter, but must not be empty
- `MAX_NOTIFICATION_AGE_IN_SECONDS` - the bot will get in game notifications not older that this
- `DEFAULT_PING_ROLE` - pings will use this handle for default-level pings. Can be empty string, then it will just write without pinging anyone.
- `ESCALATED_PING_ROLE` - same as above, but for escalated-level pings. Currently escalted level pings are: `OrbitalReinforced`, `OrbitalAttacked`, `StructureUnderAttack`, `StructureLostShields`, `StructureLostArmor`, `StructureWentLowPower`, `TowerAlertMsg`, `WarInvalid`, `WarDeclared`. Use `@everyone` or `@here` for pinging everyone in channel.
- `ADDITIONAL_INFO_TEXT` - any text that will be added to escalated level pings.

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

Development
-----------

```
pip install -r requirements-dev.txt
python -m pytest
```
