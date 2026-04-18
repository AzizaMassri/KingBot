# KingBot Command Catalog

All listed commands are implemented as hybrid commands unless noted otherwise, so they can be used as both prefix commands and slash commands.
Prefix examples below use `!` for readability.

## Standard User Commands

**Alliance Merger**
- `!merger` aliases: `!projectmeteor` — elite-tier alliance roster merger tool.

**Arcade, Board Games, and Trivia**
- `!armada` aliases: `!battleship`
- `!armadaboard`
- `!diceduel`
- `!execution` aliases: `!hangman`
- `!heist` aliases: `!raid`
- `!knightsrow` aliases: `!kr` `!connect4`
- `!minigames` aliases: `!games`
- `!monarchsmysteries` aliases: `!trivia` `!mm`
- `!monopoly`
- `!monopoly list`
- `!race`
- `!roulette`
- `!swordsandshields` aliases: `!ss` `!tictactoe`

**Casino**
- `!casino` aliases: `!bet`
- `!coinflip` aliases: `!cf`
- `!blackjack` aliases: `!bj` `!21`
- `!roll`
- `!slots` aliases: `!slotmachine`

**Calculators**
- `!calculator` aliases: `!calc` `!calculators`
- `!buildingcalculator` aliases: `!building_calculator` `!bc` `!buildings`
- `!charmcalc` aliases: `!charm_calculator` `!cc` `!charms`
- `!governorcalc` aliases: `!governor_calculator` `!gc` `!gear`
- `!herocalc` aliases: `!hero_calculator` `!hc` `!herogear`
- `!shardcalc` aliases: `!shard_calculator` `!sc` `!shards`
- `!spincalc`
- `!troopcalculator` aliases: `!troop_calculator` `!tc` `!troops`

**Core Help and Utilities**
- `!bothelp` aliases: `!help`
- `!check_quota`

**Economy and Profiles**
- `!collect`
- `!economy` aliases: `!bank` `!bal`
- `!leaderboard`
- `!rank`
- `!setcolor`
- `!setimage` aliases: `!setbg` `!setbackground`

**Guides**
- `!guides` aliases: `!guide`
- `!guides events`
- `!guides viking`
- `!guides championship` aliases: `!guides champ`
- `!guides beartrap`
- `!guides oasis`
- `!guides drillcamp` aliases: `!guides drill`
- `!guides expedition` aliases: `!guides combat`
- `!guides playbook` aliases: `!guides definitive`
- `!guides whale`
- `!guides transfer`
- `!guides dailyops` aliases: `!guides daily`
- `!guides timeline`
- `!castle` aliases: `!kvk`
- `!facility` aliases: `!sanctuary` `!outpost` `!fortress`
- `!drillcamp` aliases: `!drill`
- `!expedition` aliases: `!combat`
- `!playbook` aliases: `!definitive`
- `!whale`
- `!transfer`
- `!dailyops` aliases: `!daily`

**Music and Translation**
- `!music` aliases: `!play`
- `!qtranslate` aliases: `!qt`
- `!translate`

**Simulator**
- `!sim`
- `!sim panel`
- `!sim combat`
- `!sim combat_adv`
- `!sim calibrate`
- `!sim skillmod`
- `!sim deploy`
- `!sim timer`
- `!sim vip`
- `!sim tg`
- `!sim heroes`

## Admin and Configuration Commands

**Admin Controls**
- `!control_panel` aliases: `!admin_suite` `!cpanel` — premium tier required.
- `!restart` aliases: `!reboot` — hidden maintenance command.
- `!reload` — hidden maintenance command.
- `!sync` — hidden maintenance command.
- `!toggle_command` aliases: `!toggle` — premium tier required.
- `!toggle_cog` aliases: `!togglecog` — premium tier required.
- `!toggle_invisible` aliases: `!invisible` — premium tier required, hidden maintenance command.

**Aliases and Logging**
- `!alias`
- `!aliases`
- `!setlogchannel`

**Armada Admin**
- `!armadastop`
- `!armadaset`
- `!armadaset extra`
- `!armadaset mention`
- `!armadaset imgboard`
- `!armadaset thread`

**Core Admin and Subscription**
- `!adminhelp` aliases: `!helpadmin`
- `!invite`
- `!set_tier`

**Economy and Leveling Admin**
- `!clearbucks`
- `!economy_admin` aliases: `!ecoconfig`
- `!givebucks` aliases: `!givemoney`
- `!takebucks` aliases: `!takemoney`
- `!givexp`
- `!leveling_admin` aliases: `!levelingconfig` `!setlevelupchannel`

**Keyword Management**
- `!keyword`
- `!keyword add`
- `!keyword remove`
- `!keyword list`

**Moderation**
- `!addrole`
- `!ban`
- `!forcename`
- `!kick`
- `!lock`
- `!mute`
- `!purge`
- `!removerole`
- `!unban`
- `!unlock`
- `!unmute`

**Monopoly Admin**
- `!monopolystop`
- `!monopoly delete`
- `!monopolyset`
- `!monopolyset auction`
- `!monopolyset bail`
- `!monopolyset darkmode`
- `!monopolyset doublego`
- `!monopolyset freeparking`
- `!monopolyset go`
- `!monopolyset hotellimit`
- `!monopolyset houselimit`
- `!monopolyset income`
- `!monopolyset luxury`
- `!monopolyset maxjailrolls`
- `!monopolyset mention`
- `!monopolyset minraise`
- `!monopolyset startingcash`
- `!monopolyset thread`
- `!monopolyset timeout`

**Music, Onboarding, Reaction Roles, Tickets, and Welcome**
- `!music_admin`
- `!onboarding_admin` — premium tier required.
- `!onboarding_add` — premium tier required.
- `!onboarding_remove` — premium tier required.
- `!onboarding_roles` — premium tier required.
- `!reactionroles` aliases: `!rr` `!build_roles` `!rrbuilder` — premium tier required.
- `!setonboardingchannel` — premium tier required.
- `!setup_tickets` aliases: `!tickets_admin` `!ticketconfig`
- `!welcome_admin` aliases: `!welcomeconfig` `!setwelcomechannel` `!setwelcome`

**Translation Admin**
- `!addtranschannel`
- `!removetranschannel`
- `!spawntranslator`
- `!toggle_auto_translator` aliases: `!toggleauto` `!autotoggle`
- `!transconfig`

## Simulator Notes

**Quick Settings Keys**: `a_` = attacker, `d_` = defender, `tier` = troop tier, `tg` = Truegold level, `turns` = number of turns, `add` = additive %, `special` = special %, `skill` = SkillMod multiplier

**Advanced Keys**: `atk` or `attack`, `def` or `defense`, `hp` or `health`, `let` or `lethality`

**Line Bonus Format**: `A|inf:atk=10;cav:atk=8||D|inf:def=12;arc:let=6`

**Turn Event Keys**: `a_skill` `d_skill` `a_add` `d_add` `a_special` `d_special`

**Turn Event Format**: `2:a_skill=1.2;4:d_skill=1.15;6:a_add=10,d_add=5`

**SkillMod Input Order**: `DamageUp,OppDefDown,OppDmgDown,DefenseUp`

