import math
import random
from dataclasses import dataclass
from typing import Dict, Tuple

import discord
from discord import app_commands
from discord.ext import commands


LINE_ORDER = ("inf", "cav", "arc")
LINE_LABELS = {"inf": "Infantry", "cav": "Cavalry", "arc": "Archers"}


def _ceil_int(value: float) -> int:
    return int(math.ceil(max(value, 0.0)))


def parse_line_triplet(raw: str) -> Dict[str, int]:
    """Parse inf,cav,arc values from a compact user string."""
    parts = [p.strip().replace(",", "") for p in raw.split("/")]
    if len(parts) != 3:
        parts = [p.strip().replace(",", "") for p in raw.split(",")]
    if len(parts) != 3:
        raise ValueError("Use format: inf,cav,arc (or inf/cav/arc).")

    out: Dict[str, int] = {}
    for idx, key in enumerate(LINE_ORDER):
        if not parts[idx].isdigit():
            raise ValueError("Line values must be whole numbers.")
        value = int(parts[idx])
        if value < 0:
            raise ValueError("Line values cannot be negative.")
        out[key] = value
    return out


def parse_line_bonus_map(raw: str) -> Dict[str, Dict[str, float]]:
    """
    Parse per-line bonus map.

    Format:
    inf:atk=12,def=8,hp=5,let=10;cav:atk=5;arc:def=4,hp=7
    """
    out = {"inf": {}, "cav": {}, "arc": {}}
    text = (raw or "").strip()
    if not text:
        return out

    for segment in [seg.strip() for seg in text.split(";") if seg.strip()]:
        if ":" not in segment:
            raise ValueError("Each line bonus segment must use line:stat=value format.")
        line_name, stats_blob = segment.split(":", 1)
        line_key = line_name.strip().lower()
        if line_key not in out:
            raise ValueError("Line must be one of inf, cav, arc.")

        for kv in [p.strip() for p in stats_blob.split(",") if p.strip()]:
            if "=" not in kv:
                raise ValueError("Line bonus stats must use key=value pairs.")
            key, val = kv.split("=", 1)
            stat_key = key.strip().lower()
            if stat_key in ("atk", "attack"):
                stat_key = "attack"
            elif stat_key in ("def", "defense"):
                stat_key = "defense"
            elif stat_key in ("hp", "health"):
                stat_key = "health"
            elif stat_key in ("let", "lethality"):
                stat_key = "lethality"
            else:
                raise ValueError("Allowed stats are atk, def, hp, let.")
            out[line_key][stat_key] = float(val.strip())
    return out


def parse_turn_events(raw: str) -> Dict[int, Dict[str, float]]:
    """
    Parse scheduled turn events.

    Format:
    2:a_skill=1.15,d_skill=1.05;4:a_add=10,d_add=5;6:a_special=7.5,d_special=10
    """
    out: Dict[int, Dict[str, float]] = {}
    text = (raw or "").strip()
    if not text:
        return out

    for segment in [seg.strip() for seg in text.split(";") if seg.strip()]:
        if ":" not in segment:
            raise ValueError("Each event must be turn:key=value list.")
        turn_blob, payload = segment.split(":", 1)
        turn = int(turn_blob.strip())
        if turn < 1:
            raise ValueError("Turn numbers must be >= 1.")
        out.setdefault(turn, {})

        for kv in [p.strip() for p in payload.split(",") if p.strip()]:
            if "=" not in kv:
                raise ValueError("Event payload must use key=value pairs.")
            key, val = kv.split("=", 1)
            event_key = key.strip().lower()
            if event_key not in {"a_skill", "d_skill", "a_add", "d_add", "a_special", "d_special"}:
                raise ValueError("Allowed event keys: a_skill,d_skill,a_add,d_add,a_special,d_special")
            out[turn][event_key] = float(val.strip())
    return out


def parse_kv_numbers(raw: str) -> Dict[str, float]:
    out: Dict[str, float] = {}
    text = (raw or "").strip()
    if not text:
        return out
    for kv in [p.strip() for p in text.split(",") if p.strip()]:
        if "=" not in kv:
            raise ValueError("Expected key=value pairs separated by commas.")
        key, val = kv.split("=", 1)
        out[key.strip().lower()] = float(val.strip())
    return out


def scale_anchor_map(
    anchors: Dict[str, Dict[str, int]],
    atk_scale: float,
    def_scale: float,
    hp_scale: float,
    let_scale: float,
) -> Dict[str, Dict[str, int]]:
    return {
        line: {
            "attack": max(_ceil_int(stats["attack"] * atk_scale), 1),
            "defense": max(_ceil_int(stats["defense"] * def_scale), 1),
            "health": max(_ceil_int(stats["health"] * hp_scale), 1),
            "lethality": max(_ceil_int(stats["lethality"] * let_scale), 1),
        }
        for line, stats in anchors.items()
    }


def compute_skill_mod(
    damage_up_pct: float,
    opp_def_down_pct: float,
    opp_dmg_down_pct: float,
    defense_up_pct: float,
) -> float:
    # Percent inputs are converted to multiplicative factors before ratioing.
    numerator = (1.0 + damage_up_pct / 100.0) * (1.0 + opp_def_down_pct / 100.0)
    denominator = (1.0 + opp_dmg_down_pct / 100.0) * (1.0 + defense_up_pct / 100.0)
    if denominator <= 0:
        return 1.0
    return max(numerator / denominator, 0.0)


def optimize_deployment(alpha: float, beta: float, gamma: float) -> Dict[str, float]:
    denom = (alpha * alpha) + (beta * beta) + (gamma * gamma)
    if denom <= 0:
        raise ValueError("At least one of alpha, beta, gamma must be greater than 0.")
    return {
        "inf": (alpha * alpha) / denom,
        "cav": (beta * beta) / denom,
        "arc": (gamma * gamma) / denom,
    }


def modified_time_seconds(base_seconds: int, additive_bonus_pct: float, chief_office_active: bool) -> int:
    if base_seconds <= 0:
        raise ValueError("Base time must be greater than 0.")
    additive_factor = 1.0 + additive_bonus_pct / 100.0
    if additive_factor <= 0:
        additive_factor = 0.01
    remaining = base_seconds / additive_factor
    if chief_office_active:
        remaining *= 0.8
    return _ceil_int(remaining)


def format_duration(seconds: int) -> str:
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{sec}s")
    return " ".join(parts)


@dataclass
class SideConfig:
    tier: int
    tg_level: int
    additive_pct: float
    special_pct: float
    attack_bonus_pct: float
    defense_bonus_pct: float
    health_bonus_pct: float
    lethality_bonus_pct: float
    skill_mod: float


class CombatEngine:
    """
    Accuracy-focused combat model using known reverse-engineered rules.

    Notes:
    - Base troop stats are reconstructed from anchors + 7% tier scaling.
    - Turn damage is resolved simultaneously.
    - Final casualties and timers round up.
    - Damage floor is enforced when attack <= defense.
    """

    BASE_ANCHOR_T9 = {
        "inf": {"attack": 13, "defense": 14, "health": 14, "lethality": 13},
        "cav": {"attack": 14, "defense": 13, "health": 13, "lethality": 14},
        "arc": {"attack": 15, "defense": 12, "health": 12, "lethality": 15},
    }

    @staticmethod
    def _tier_scaled_stat(anchor_t9: int, tier: int) -> int:
        scaled = anchor_t9 * (1.07 ** (tier - 9))
        return max(_ceil_int(scaled), 1)

    @classmethod
    def base_stats(
        cls,
        line: str,
        tier: int,
        anchors: Dict[str, Dict[str, int]] | None = None,
    ) -> Dict[str, int]:
        if tier < 1 or tier > 12:
            raise ValueError("Tier must be between 1 and 12.")
        source = anchors if anchors is not None else cls.BASE_ANCHOR_T9
        anchor = source[line]
        return {
            "attack": cls._tier_scaled_stat(anchor["attack"], tier),
            "defense": cls._tier_scaled_stat(anchor["defense"], tier),
            "health": cls._tier_scaled_stat(anchor["health"], tier),
            "lethality": cls._tier_scaled_stat(anchor["lethality"], tier),
        }

    @staticmethod
    def tg_flat_bonus(tg_level: int) -> Dict[str, int]:
        if tg_level <= 0:
            return {"attack": 0, "defense": 0, "health": 0, "lethality": 0}

        # Exact from provided data at TG1/TG2; extended conservatively for TG3+.
        bonus = {"attack": 1, "defense": 1, "health": 1, "lethality": 1}
        if tg_level >= 2:
            bonus["attack"] += 2
            bonus["defense"] += 1
            bonus["health"] += 1
            bonus["lethality"] += 1
        if tg_level > 2:
            extra = tg_level - 2
            bonus["attack"] += 2 * extra
            bonus["defense"] += 1 * extra
            bonus["health"] += 1 * extra
            bonus["lethality"] += 1 * extra
        return bonus

    @staticmethod
    def _global_multiplier(additive_pct: float, special_pct: float) -> float:
        # Implemented as requested: special buff participates multiplicatively and then adds again.
        return ((1.0 + additive_pct / 100.0) * (1.0 + special_pct / 100.0)) + (special_pct / 100.0)

    @classmethod
    def effective_stats(
        cls,
        line: str,
        cfg: SideConfig,
        anchors: Dict[str, Dict[str, int]] | None = None,
        line_bonus: Dict[str, float] | None = None,
        additive_shift_pct: float = 0.0,
        special_shift_pct: float = 0.0,
    ) -> Dict[str, float]:
        base = cls.base_stats(line, cfg.tier, anchors=anchors)
        tg = cls.tg_flat_bonus(cfg.tg_level)
        global_mult = cls._global_multiplier(cfg.additive_pct + additive_shift_pct, cfg.special_pct + special_shift_pct)

        bonus = line_bonus or {}
        atk_bonus = cfg.attack_bonus_pct + bonus.get("attack", 0.0)
        def_bonus = cfg.defense_bonus_pct + bonus.get("defense", 0.0)
        hp_bonus = cfg.health_bonus_pct + bonus.get("health", 0.0)
        let_bonus = cfg.lethality_bonus_pct + bonus.get("lethality", 0.0)

        attack = (base["attack"] + tg["attack"]) * global_mult * (1.0 + atk_bonus / 100.0)
        defense = (base["defense"] + tg["defense"]) * global_mult * (1.0 + def_bonus / 100.0)
        health = (base["health"] + tg["health"]) * global_mult * (1.0 + hp_bonus / 100.0)
        lethality = (base["lethality"] + tg["lethality"]) * global_mult * (1.0 + let_bonus / 100.0)

        return {
            "attack": max(attack, 0.0),
            "defense": max(defense, 0.0),
            "health": max(health, 0.0),
            "lethality": max(lethality, 0.0),
        }

    @staticmethod
    def matchup_multipliers(attacker_line: str, defender_line: str) -> Tuple[float, float]:
        attack_mult = 1.0
        defense_mult = 1.0

        if attacker_line == "inf" and defender_line == "cav":
            attack_mult *= 1.10
        if attacker_line == "cav" and defender_line == "arc":
            attack_mult *= 1.10
        if attacker_line == "arc" and defender_line == "inf":
            attack_mult *= 1.10

        if defender_line == "inf" and attacker_line == "cav":
            defense_mult *= 1.10

        # Archer expected double-strike contribution.
        if attacker_line == "arc":
            attack_mult *= 1.10

        return attack_mult, defense_mult

    @staticmethod
    def _frontmost_alive(lines: Dict[str, int]) -> str | None:
        for key in LINE_ORDER:
            if lines.get(key, 0) > 0:
                return key
        return None

    @classmethod
    def _line_attack_kills(
        cls,
        attackers: int,
        atk_stats: Dict[str, float],
        def_stats: Dict[str, float],
        atk_line: str,
        def_line: str,
        skill_mod: float,
    ) -> float:
        if attackers <= 0:
            return 0.0

        atk_mult, def_mult = cls.matchup_multipliers(atk_line, def_line)
        effective_attack = atk_stats["attack"] * atk_mult
        effective_defense = def_stats["defense"] * def_mult

        # Hard floor: if attack cannot break defense, baseline damage is zero.
        offensive_term = max(effective_attack - effective_defense, 0.0)
        if offensive_term <= 0:
            return 0.0

        denom = max(def_stats["defense"] * def_stats["health"], 1e-9)
        kills = math.sqrt(attackers) * ((offensive_term * atk_stats["lethality"]) / denom) * max(skill_mod, 0.0)
        return max(kills, 0.0)

    @classmethod
    def _compute_turn_damage(
        cls,
        atk_lines: Dict[str, int],
        def_lines: Dict[str, int],
        atk_cfg: SideConfig,
        def_cfg: SideConfig,
        anchors: Dict[str, Dict[str, int]] | None = None,
        atk_line_bonuses: Dict[str, Dict[str, float]] | None = None,
        def_line_bonuses: Dict[str, Dict[str, float]] | None = None,
        atk_skill_turn_mult: float = 1.0,
        atk_add_shift_pct: float = 0.0,
        def_add_shift_pct: float = 0.0,
        atk_special_shift_pct: float = 0.0,
        def_special_shift_pct: float = 0.0,
    ) -> Dict[str, float]:
        damage_by_line = {"inf": 0.0, "cav": 0.0, "arc": 0.0}
        atk_line_bonuses = atk_line_bonuses or {}
        def_line_bonuses = def_line_bonuses or {}

        for atk_line in LINE_ORDER:
            attackers = atk_lines.get(atk_line, 0)
            if attackers <= 0:
                continue

            primary_target = cls._frontmost_alive(def_lines)
            if primary_target is None:
                break

            atk_stats = cls.effective_stats(
                atk_line,
                atk_cfg,
                anchors=anchors,
                line_bonus=atk_line_bonuses.get(atk_line),
                additive_shift_pct=atk_add_shift_pct,
                special_shift_pct=atk_special_shift_pct,
            )
            primary_def_stats = cls.effective_stats(
                primary_target,
                def_cfg,
                anchors=anchors,
                line_bonus=def_line_bonuses.get(primary_target),
                additive_shift_pct=def_add_shift_pct,
                special_shift_pct=def_special_shift_pct,
            )

            # Cavalry can bypass infantry to archers with expected-value split.
            if atk_line == "cav" and primary_target == "inf" and def_lines.get("arc", 0) > 0:
                base_kills = cls._line_attack_kills(
                    attackers,
                    atk_stats,
                    primary_def_stats,
                    atk_line,
                    primary_target,
                    atk_cfg.skill_mod * atk_skill_turn_mult,
                )
                damage_by_line["inf"] += base_kills * 0.8

                arc_def_stats = cls.effective_stats(
                    "arc",
                    def_cfg,
                    anchors=anchors,
                    line_bonus=def_line_bonuses.get("arc"),
                    additive_shift_pct=def_add_shift_pct,
                    special_shift_pct=def_special_shift_pct,
                )
                bypass_kills = cls._line_attack_kills(
                    attackers,
                    atk_stats,
                    arc_def_stats,
                    atk_line,
                    "arc",
                    atk_cfg.skill_mod * atk_skill_turn_mult,
                )
                damage_by_line["arc"] += bypass_kills * 0.2
                continue

            kills = cls._line_attack_kills(
                attackers,
                atk_stats,
                primary_def_stats,
                atk_line,
                primary_target,
                atk_cfg.skill_mod * atk_skill_turn_mult,
            )
            damage_by_line[primary_target] += kills

        return damage_by_line

    @classmethod
    def simulate(
        cls,
        attacker_lines: Dict[str, int],
        defender_lines: Dict[str, int],
        attacker_cfg: SideConfig,
        defender_cfg: SideConfig,
        turns: int,
        anchors: Dict[str, Dict[str, int]] | None = None,
    ) -> Dict[str, object]:
        if turns < 1 or turns > 60:
            raise ValueError("Turns must be between 1 and 60.")

        atk_state = dict(attacker_lines)
        def_state = dict(defender_lines)
        turn_log = []

        for turn in range(1, turns + 1):
            if sum(atk_state.values()) <= 0 or sum(def_state.values()) <= 0:
                break

            atk_damage = cls._compute_turn_damage(
                atk_state,
                def_state,
                attacker_cfg,
                defender_cfg,
                anchors=anchors,
            )
            def_damage = cls._compute_turn_damage(
                def_state,
                atk_state,
                defender_cfg,
                attacker_cfg,
                anchors=anchors,
            )

            # Simultaneous casualty application with upward rounding.
            atk_losses = {k: min(atk_state[k], _ceil_int(def_damage.get(k, 0.0))) for k in LINE_ORDER}
            def_losses = {k: min(def_state[k], _ceil_int(atk_damage.get(k, 0.0))) for k in LINE_ORDER}

            for k in LINE_ORDER:
                atk_state[k] -= atk_losses[k]
                def_state[k] -= def_losses[k]

            turn_log.append({
                "turn": turn,
                "attacker_losses": atk_losses,
                "defender_losses": def_losses,
                "attacker_remaining": dict(atk_state),
                "defender_remaining": dict(def_state),
            })

        atk_total_start = sum(attacker_lines.values())
        def_total_start = sum(defender_lines.values())
        atk_total_end = sum(atk_state.values())
        def_total_end = sum(def_state.values())

        if atk_total_end > def_total_end:
            winner = "Attacker"
        elif def_total_end > atk_total_end:
            winner = "Defender"
        else:
            winner = "Draw"

        return {
            "winner": winner,
            "attacker_start": atk_total_start,
            "defender_start": def_total_start,
            "attacker_end": atk_total_end,
            "defender_end": def_total_end,
            "attacker_remaining": atk_state,
            "defender_remaining": def_state,
            "turns_played": len(turn_log),
            "turn_log": turn_log,
        }

    @classmethod
    def simulate_advanced(
        cls,
        attacker_lines: Dict[str, int],
        defender_lines: Dict[str, int],
        attacker_cfg: SideConfig,
        defender_cfg: SideConfig,
        turns: int,
        attacker_line_bonuses: Dict[str, Dict[str, float]] | None = None,
        defender_line_bonuses: Dict[str, Dict[str, float]] | None = None,
        turn_events: Dict[int, Dict[str, float]] | None = None,
        anchors: Dict[str, Dict[str, int]] | None = None,
    ) -> Dict[str, object]:
        if turns < 1 or turns > 60:
            raise ValueError("Turns must be between 1 and 60.")

        atk_state = dict(attacker_lines)
        def_state = dict(defender_lines)
        turn_log = []
        turn_events = turn_events or {}

        for turn in range(1, turns + 1):
            if sum(atk_state.values()) <= 0 or sum(def_state.values()) <= 0:
                break

            event = turn_events.get(turn, {})
            a_skill = event.get("a_skill", 1.0)
            d_skill = event.get("d_skill", 1.0)
            a_add = event.get("a_add", 0.0)
            d_add = event.get("d_add", 0.0)
            a_special = event.get("a_special", 0.0)
            d_special = event.get("d_special", 0.0)

            atk_damage = cls._compute_turn_damage(
                atk_state,
                def_state,
                attacker_cfg,
                defender_cfg,
                anchors=anchors,
                atk_line_bonuses=attacker_line_bonuses,
                def_line_bonuses=defender_line_bonuses,
                atk_skill_turn_mult=a_skill,
                atk_add_shift_pct=a_add,
                def_add_shift_pct=d_add,
                atk_special_shift_pct=a_special,
                def_special_shift_pct=d_special,
            )
            def_damage = cls._compute_turn_damage(
                def_state,
                atk_state,
                defender_cfg,
                attacker_cfg,
                anchors=anchors,
                atk_line_bonuses=defender_line_bonuses,
                def_line_bonuses=attacker_line_bonuses,
                atk_skill_turn_mult=d_skill,
                atk_add_shift_pct=d_add,
                def_add_shift_pct=a_add,
                atk_special_shift_pct=d_special,
                def_special_shift_pct=a_special,
            )

            atk_losses = {k: min(atk_state[k], _ceil_int(def_damage.get(k, 0.0))) for k in LINE_ORDER}
            def_losses = {k: min(def_state[k], _ceil_int(atk_damage.get(k, 0.0))) for k in LINE_ORDER}

            for k in LINE_ORDER:
                atk_state[k] -= atk_losses[k]
                def_state[k] -= def_losses[k]

            turn_log.append(
                {
                    "turn": turn,
                    "event": event,
                    "attacker_losses": atk_losses,
                    "defender_losses": def_losses,
                    "attacker_remaining": dict(atk_state),
                    "defender_remaining": dict(def_state),
                }
            )

        atk_total_start = sum(attacker_lines.values())
        def_total_start = sum(defender_lines.values())
        atk_total_end = sum(atk_state.values())
        def_total_end = sum(def_state.values())

        winner = "Draw"
        if atk_total_end > def_total_end:
            winner = "Attacker"
        elif def_total_end > atk_total_end:
            winner = "Defender"

        return {
            "winner": winner,
            "attacker_start": atk_total_start,
            "defender_start": def_total_start,
            "attacker_end": atk_total_end,
            "defender_end": def_total_end,
            "attacker_remaining": atk_state,
            "defender_remaining": def_state,
            "turns_played": len(turn_log),
            "turn_log": turn_log,
        }


HERO_DATABASE = [
    {"generation": 6, "name": "Triton", "rarity": "SSR", "archetype": "Infantry", "summary": "Invulnerability window + AoE burst; strong squad defense/skill scaling."},
    {"generation": 6, "name": "Yang", "rarity": "SSR", "archetype": "Archer", "summary": "Periodic extra strike and archer extra-damage proc."},
    {"generation": 6, "name": "Sophia", "rarity": "SSR", "archetype": "Cavalry", "summary": "AoE burst + confuse; chance to halve incoming squad damage."},
    {"generation": 5, "name": "Vivian", "rarity": "SSR", "archetype": "Archer", "summary": "Permanent enemy damage-taken amplification."},
    {"generation": 5, "name": "Thrud", "rarity": "SSR", "archetype": "Cavalry", "summary": "Cyclic damage up and damage reduction."},
    {"generation": 4, "name": "Alcar", "rarity": "SSR", "archetype": "Infantry", "summary": "Line damage plus enemy damage-taken debuff with expedition mitigation cycle."},
    {"generation": 3, "name": "Petra", "rarity": "SSR", "archetype": "Cavalry", "summary": "Enemy damage-taken boost, attack up, and damage taken down package."},
    {"generation": 2, "name": "Marlin", "rarity": "SSR", "archetype": "Archer", "summary": "Damage proc chance and enemy lethality suppression chance."},
    {"generation": 1, "name": "Helga", "rarity": "SSR", "archetype": "Infantry", "summary": "Damage-taken reduction proc and squad attack boost."},
    {"generation": 1, "name": "Amadeus", "rarity": "SSR", "archetype": "Infantry", "summary": "Conditional HP and lethality boosts up to 15%."},
    {"generation": 1, "name": "Yeonwoo", "rarity": "SR", "archetype": "Archer", "summary": "Expedition lethality boost and research utility passive."},
    {"generation": 1, "name": "Amane", "rarity": "SR", "archetype": "Archer", "summary": "Expedition attack boost and healing speed utility."},
    {"generation": 1, "name": "Chenko", "rarity": "SR", "archetype": "Cavalry", "summary": "Expedition lethality boost."},
    {"generation": 1, "name": "Howard", "rarity": "SR", "archetype": "Infantry", "summary": "Incoming troop damage reduction."},
    {"generation": 1, "name": "Saul", "rarity": "SR", "archetype": "Archer", "summary": "Construction utility passive."},
]

VIP_THRESHOLDS = {
    1: 5,
    2: 16,
    3: 35,
    6: 570,
    7: 1400,
    8: 4200,
    10: 15000,
    13: 150000,
}

TG_STEP_COSTS = {
    1: 132,
    2: 158,
    3: 238,
    4: 280,
    5: 335,
}

TG5_RESOURCE_TOTAL = {
    "wood": 2_100_000_000,
    "bread": 2_100_000_000,
    "stone": 430_000_000,
    "iron": 108_000_000,
    "truegold": 5_715,
}


class Simulator(commands.Cog):
    """High-accuracy rally/combat simulator with clear assumptions and tooling."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _combat_result_embed(
        result: Dict[str, object],
        title: str,
        description: str,
        footer: str,
    ) -> discord.Embed:
        embed = discord.Embed(title=title, color=discord.Color.gold(), description=description)
        embed.add_field(
            name="Outcome",
            value=(
                f"Winner: **{result['winner']}**\n"
                f"Turns Played: **{result['turns_played']}**\n"
                f"Attacker Remaining: **{result['attacker_end']:,}** / {result['attacker_start']:,}\n"
                f"Defender Remaining: **{result['defender_end']:,}** / {result['defender_start']:,}"
            ),
            inline=False,
        )
        embed.add_field(
            name="Attacker Remaining Lines",
            value=(
                f"Inf: {result['attacker_remaining']['inf']:,}\n"
                f"Cav: {result['attacker_remaining']['cav']:,}\n"
                f"Arc: {result['attacker_remaining']['arc']:,}"
            ),
            inline=True,
        )
        embed.add_field(
            name="Defender Remaining Lines",
            value=(
                f"Inf: {result['defender_remaining']['inf']:,}\n"
                f"Cav: {result['defender_remaining']['cav']:,}\n"
                f"Arc: {result['defender_remaining']['arc']:,}"
            ),
            inline=True,
        )
        if result["turn_log"]:
            last_turn = result["turn_log"][-1]
            embed.add_field(
                name="Last Turn Losses",
                value=(
                    f"Attacker: inf {last_turn['attacker_losses']['inf']:,}, "
                    f"cav {last_turn['attacker_losses']['cav']:,}, arc {last_turn['attacker_losses']['arc']:,}\n"
                    f"Defender: inf {last_turn['defender_losses']['inf']:,}, "
                    f"cav {last_turn['defender_losses']['cav']:,}, arc {last_turn['defender_losses']['arc']:,}"
                ),
                inline=False,
            )
        embed.set_footer(text=footer)
        return embed

    @staticmethod
    def _build_side_config(
        tier: int,
        tg_level: int,
        additive: float,
        special: float,
        skill_mod: float,
    ) -> SideConfig:
        return SideConfig(
            tier=tier,
            tg_level=tg_level,
            additive_pct=additive,
            special_pct=special,
            attack_bonus_pct=0.0,
            defense_bonus_pct=0.0,
            health_bonus_pct=0.0,
            lethality_bonus_pct=0.0,
            skill_mod=max(skill_mod, 0.0),
        )

    @commands.hybrid_group(name="sim", invoke_without_command=True)
    async def sim(self, ctx: commands.Context):
        """KingShot simulator hub with combat, deployment, timer, and progression tools."""
        embed = discord.Embed(
            title="Simulator Hub",
            color=discord.Color.orange(),
            description=(
                "Accuracy-first simulator based on reverse-engineered rules with explicit assumptions.\n\n"
                "How to use quickly:\n"
                "1) Run /sim combat with inf,cav,arc troop lines and buffs.\n"
                "2) Run /sim skillmod to compute Rule-of-4 ratio.\n"
                "3) Run /sim deploy for optimal join fractions.\n"
                "4) Run /sim timer for additive speed math + Chief Office exception.\n"
                "5) Run /sim combat_adv for per-line buffs and turn schedules.\n"
                "6) Run /sim calibrate to fit hidden stat constants from battle outcomes.\n"
                "7) Run /sim panel for button-driven guided input."
            ),
        )
        embed.add_field(
            name="Combat Input Template",
            value=(
                "attacker_lines: inf,cav,arc\n"
                "defender_lines: inf,cav,arc\n"
                "Example attacker_lines: 250000,120000,90000\n"
                "Example defender_lines: 300000,100000,110000"
            ),
            inline=False,
        )
        embed.add_field(
            name="Advanced Templates",
            value=(
                "attacker_line_bonuses: inf:atk=10,def=5;cav:atk=8;arc:hp=12\n"
                "defender_line_bonuses: inf:def=12,hp=10;arc:let=7\n"
                "turn_events: 2:a_skill=1.2;4:d_skill=1.15;6:a_add=10,d_add=5"
            ),
            inline=False,
        )
        embed.add_field(
            name="Model Notes",
            value=(
                "Reconstructed T1-T12 bases use 7% tier scaling with known anchor points. "
                "Simultaneous turns, front-line targeting, cavalry bypass expectation, damage floor, "
                "and upward rounding are all enforced."
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @sim.command(name="panel")
    async def sim_panel(self, ctx: commands.Context):
        """Open an interactive simulator panel with guided modals."""
        embed = discord.Embed(
            title="Interactive Simulator Panel",
            color=discord.Color.blurple(),
            description=(
                "Use the buttons below to run the simulator without memorizing command syntax.\n"
                "Each modal explains expected input format directly in placeholders."
            ),
        )
        embed.add_field(
            name="Quick Start",
            value=(
                "1) Click Quick Combat for normal simulation.\n"
                "2) Click Advanced Combat to add line buffs and turn schedules.\n"
                "3) Click SkillMod Helper if you need Rule-of-4 ratio first."
            ),
            inline=False,
        )
        await ctx.send(embed=embed, view=SimulatorPanelView(self))

    @sim.command(name="combat")
    @app_commands.describe(
        attacker_lines="Required: inf,cav,arc (example: 250000,120000,90000)",
        defender_lines="Required: inf,cav,arc (example: 300000,100000,110000)",
        attacker_tier="Attacker troop tier (1-12)",
        defender_tier="Defender troop tier (1-12)",
        turns="Turn count (1-60)",
        attacker_additive="Attacker additive bonus percent",
        attacker_special="Attacker special multiplicative percent",
        defender_additive="Defender additive bonus percent",
        defender_special="Defender special multiplicative percent",
        attacker_skillmod="Attacker total SkillMod factor (use /sim skillmod)",
        defender_skillmod="Defender total SkillMod factor (use /sim skillmod)",
    )
    async def sim_combat(
        self,
        ctx: commands.Context,
        attacker_lines: str | None = None,
        defender_lines: str | None = None,
        attacker_tier: app_commands.Range[int, 1, 12] = 10,
        defender_tier: app_commands.Range[int, 1, 12] = 10,
        turns: app_commands.Range[int, 1, 60] = 10,
        attacker_additive: float = 0.0,
        attacker_special: float = 0.0,
        defender_additive: float = 0.0,
        defender_special: float = 0.0,
        attacker_skillmod: float = 1.0,
        defender_skillmod: float = 1.0,
        attacker_tg: app_commands.Range[int, 0, 5] = 0,
        defender_tg: app_commands.Range[int, 0, 5] = 0,
    ):
        """Run an accuracy-focused march simulation with explained assumptions."""
        if not attacker_lines or not defender_lines:
            embed = discord.Embed(
                title="Combat Input Needed",
                color=discord.Color.blurple(),
                description=(
                    "Required inputs:\n"
                    "1) attacker_lines as inf,cav,arc\n"
                    "2) defender_lines as inf,cav,arc\n\n"
                    "Exact prefix example:\n"
                    "!sim combat 250000,120000,90000 300000,100000,110000\n\n"
                    "Slash example:\n"
                    "/sim combat attacker_lines:250000,120000,90000 defender_lines:300000,100000,110000"
                ),
            )
            embed.add_field(
                name="Need guided input?",
                value="Use the panel buttons below to open modals and fill fields step by step.",
                inline=False,
            )
            return await ctx.send(embed=embed, view=SimulatorPanelView(self))

        try:
            atk = parse_line_triplet(attacker_lines)
            deff = parse_line_triplet(defender_lines)
        except ValueError as exc:
            return await ctx.send(
                "Invalid troop line format.\n"
                f"Reason: {exc}\n"
                "Expected: inf,cav,arc using whole numbers only.\n"
                "Example: 250000,120000,90000"
            )

        if sum(atk.values()) <= 0 or sum(deff.values()) <= 0:
            return await ctx.send("Both sides must have at least one troop.")

        attacker_cfg = self._build_side_config(attacker_tier, attacker_tg, attacker_additive, attacker_special, attacker_skillmod)
        defender_cfg = self._build_side_config(defender_tier, defender_tg, defender_additive, defender_special, defender_skillmod)

        result = CombatEngine.simulate(atk, deff, attacker_cfg, defender_cfg, turns=turns)
        embed = self._combat_result_embed(
            result,
            title="Combat Simulation",
            description=(
                "Model explanation above results:\n"
                "- Simultaneous turn resolution (both sides deal damage each turn).\n"
                "- Frontline targeting order: Infantry -> Cavalry -> Archers.\n"
                "- Cavalry bypass modeled as 20% expected split to enemy archers when eligible.\n"
                "- Damage floor at 0 when effective attack does not exceed effective defense.\n"
                "- Final casualty counts rounded up."
            ),
            footer="Use /sim skillmod to compute each side's Rule-of-4 modifier before running combat.",
        )
        await ctx.send(embed=embed)

    @sim.command(name="combat_adv")
    @app_commands.describe(
        attacker_lines="Required: inf,cav,arc (example: 250000,120000,90000)",
        defender_lines="Required: inf,cav,arc (example: 300000,100000,110000)",
        attacker_line_bonuses="Optional: inf:atk=10,def=5;cav:atk=8;arc:hp=12",
        defender_line_bonuses="Optional: inf:def=12,hp=10;arc:let=7",
        turn_events="Optional: 2:a_skill=1.2;4:d_skill=1.15;6:a_add=10,d_add=5",
    )
    async def sim_combat_adv(
        self,
        ctx: commands.Context,
        attacker_lines: str | None = None,
        defender_lines: str | None = None,
        attacker_tier: app_commands.Range[int, 1, 12] = 10,
        defender_tier: app_commands.Range[int, 1, 12] = 10,
        turns: app_commands.Range[int, 1, 60] = 10,
        attacker_additive: float = 0.0,
        attacker_special: float = 0.0,
        defender_additive: float = 0.0,
        defender_special: float = 0.0,
        attacker_skillmod: float = 1.0,
        defender_skillmod: float = 1.0,
        attacker_tg: app_commands.Range[int, 0, 5] = 0,
        defender_tg: app_commands.Range[int, 0, 5] = 0,
        attacker_line_bonuses: str = "",
        defender_line_bonuses: str = "",
        turn_events: str = "",
    ):
        """Advanced combat with per-line buffs and per-turn proc schedule support."""
        if not attacker_lines or not defender_lines:
            embed = discord.Embed(
                title="Advanced Input Needed",
                color=discord.Color.blurple(),
                description=(
                    "Required inputs:\n"
                    "1) attacker_lines as inf,cav,arc\n"
                    "2) defender_lines as inf,cav,arc\n\n"
                    "Optional advanced fields:\n"
                    "attacker_line_bonuses example: inf:atk=10,def=5;cav:atk=8;arc:hp=12\n"
                    "defender_line_bonuses example: inf:def=12,hp=10;arc:let=7\n"
                    "turn_events example: 2:a_skill=1.2;4:d_skill=1.15;6:a_add=10,d_add=5"
                ),
            )
            return await ctx.send(embed=embed, view=SimulatorPanelView(self))

        try:
            atk = parse_line_triplet(attacker_lines)
            deff = parse_line_triplet(defender_lines)
            atk_line_bonus_map = parse_line_bonus_map(attacker_line_bonuses)
            def_line_bonus_map = parse_line_bonus_map(defender_line_bonuses)
            events = parse_turn_events(turn_events)
        except ValueError as exc:
            return await ctx.send(
                "Invalid advanced input.\n"
                f"Reason: {exc}\n"
                "Line bonus format: inf:atk=10,def=5;cav:atk=8;arc:hp=12\n"
                "Turn event format: 2:a_skill=1.2;4:d_skill=1.15;6:a_add=10,d_add=5"
            )

        if sum(atk.values()) <= 0 or sum(deff.values()) <= 0:
            return await ctx.send("Both sides must have at least one troop.")

        attacker_cfg = self._build_side_config(attacker_tier, attacker_tg, attacker_additive, attacker_special, attacker_skillmod)
        defender_cfg = self._build_side_config(defender_tier, defender_tg, defender_additive, defender_special, defender_skillmod)

        result = CombatEngine.simulate_advanced(
            atk,
            deff,
            attacker_cfg,
            defender_cfg,
            turns=turns,
            attacker_line_bonuses=atk_line_bonus_map,
            defender_line_bonuses=def_line_bonus_map,
            turn_events=events,
        )

        embed = self._combat_result_embed(
            result,
            title="Advanced Combat Simulation",
            description=(
                "This mode adds:\n"
                "- Per-line stat bonuses (attack/defense/health/lethality).\n"
                "- Turn-scheduled hero proc effects via skill, additive, and special shifts.\n"
                "- Same simultaneous casualty and targeting core as base mode."
            ),
            footer="Tip: use sparse schedules only where effects begin; keep static buffs in base additive/special fields.",
        )
        if events:
            event_preview = []
            for turn in sorted(events.keys())[:5]:
                payload = ", ".join(f"{k}={v:g}" for k, v in events[turn].items())
                event_preview.append(f"T{turn}: {payload}")
            embed.add_field(name="Event Preview", value="\n".join(event_preview), inline=False)
        await ctx.send(embed=embed)

    @sim.command(name="calibrate")
    @app_commands.describe(
        attacker_lines="Attacker lines in inf,cav,arc format",
        defender_lines="Defender lines in inf,cav,arc format",
        observed_attacker_remaining="Observed attacker remaining troops",
        observed_defender_remaining="Observed defender remaining troops",
        samples="Search samples (higher = slower but tighter)",
    )
    async def sim_calibrate(
        self,
        ctx: commands.Context,
        attacker_lines: str,
        defender_lines: str,
        observed_attacker_remaining: int,
        observed_defender_remaining: int,
        attacker_tier: app_commands.Range[int, 1, 12] = 10,
        defender_tier: app_commands.Range[int, 1, 12] = 10,
        turns: app_commands.Range[int, 1, 60] = 10,
        attacker_additive: float = 0.0,
        attacker_special: float = 0.0,
        defender_additive: float = 0.0,
        defender_special: float = 0.0,
        attacker_skillmod: float = 1.0,
        defender_skillmod: float = 1.0,
        samples: app_commands.Range[int, 100, 3000] = 700,
    ):
        """Fit hidden base constants by searching anchor scale combinations against observed outcomes."""
        try:
            atk = parse_line_triplet(attacker_lines)
            deff = parse_line_triplet(defender_lines)
        except ValueError as exc:
            return await ctx.send(f"Invalid troop line format: {exc}")

        if observed_attacker_remaining < 0 or observed_defender_remaining < 0:
            return await ctx.send("Observed remaining values must be non-negative.")

        attacker_cfg = self._build_side_config(attacker_tier, 0, attacker_additive, attacker_special, attacker_skillmod)
        defender_cfg = self._build_side_config(defender_tier, 0, defender_additive, defender_special, defender_skillmod)

        await ctx.defer()

        candidates = [(1.0, 1.0, 1.0, 1.0)]
        for _ in range(samples - 1):
            candidates.append(
                (
                    random.uniform(0.75, 1.35),
                    random.uniform(0.75, 1.35),
                    random.uniform(0.75, 1.35),
                    random.uniform(0.75, 1.35),
                )
            )

        best = None
        best_result = None
        best_error = float("inf")

        for atk_s, def_s, hp_s, let_s in candidates:
            anchors = scale_anchor_map(CombatEngine.BASE_ANCHOR_T9, atk_s, def_s, hp_s, let_s)
            sim = CombatEngine.simulate(atk, deff, attacker_cfg, defender_cfg, turns=turns, anchors=anchors)
            error = abs(sim["attacker_end"] - observed_attacker_remaining) + abs(sim["defender_end"] - observed_defender_remaining)
            if error < best_error:
                best_error = error
                best = (atk_s, def_s, hp_s, let_s)
                best_result = sim

        assert best is not None
        embed = discord.Embed(
            title="Calibration Result",
            color=discord.Color.dark_teal(),
            description=(
                "This tool fits hidden base constants by minimizing remaining-troop error against your observed battle outcome.\n"
                "Use the resulting scale factors in future tuning sessions to improve parity."
            ),
        )
        embed.add_field(
            name="Best Scales",
            value=(
                f"Attack Scale: **{best[0]:.4f}**\n"
                f"Defense Scale: **{best[1]:.4f}**\n"
                f"Health Scale: **{best[2]:.4f}**\n"
                f"Lethality Scale: **{best[3]:.4f}**"
            ),
            inline=False,
        )
        embed.add_field(
            name="Fit Quality",
            value=(
                f"Absolute Error: **{best_error:,}**\n"
                f"Observed A/D Remaining: {observed_attacker_remaining:,} / {observed_defender_remaining:,}\n"
                f"Sim A/D Remaining: {best_result['attacker_end']:,} / {best_result['defender_end']:,}"
            ),
            inline=False,
        )
        embed.set_footer(text="Run calibration across multiple battle reports and average scales for a stable profile.")
        await ctx.send(embed=embed)

    @sim.command(name="skillmod")
    @app_commands.describe(
        damage_up_pct="DamageUp percent",
        opp_def_down_pct="Opponent DefenseDown percent",
        opp_dmg_down_pct="Opponent DamageDown percent",
        defense_up_pct="DefenseUp percent",
    )
    async def sim_skillmod(
        self,
        ctx: commands.Context,
        damage_up_pct: float,
        opp_def_down_pct: float,
        opp_dmg_down_pct: float,
        defense_up_pct: float,
    ):
        """Compute the Rule-of-4 SkillMod ratio from percent inputs."""
        skill_mod = compute_skill_mod(damage_up_pct, opp_def_down_pct, opp_dmg_down_pct, defense_up_pct)
        embed = discord.Embed(
            title="Rule-of-4 SkillMod",
            color=discord.Color.blue(),
            description=(
                "Formula:\n"
                "SkillMod = (DamageUp x OppDefenseDown) / (OppDamageDown x DefenseUp)\n"
                "Percent values are converted to multiplicative factors first."
            ),
        )
        embed.add_field(name="Computed SkillMod", value=f"**{skill_mod:.4f}x**", inline=False)
        embed.add_field(
            name="Plug into Combat",
            value="Use this number as attacker_skillmod or defender_skillmod in /sim combat.",
            inline=False,
        )
        await ctx.send(embed=embed)

    @sim.command(name="deploy")
    @app_commands.describe(
        alpha="Leader modified Infantry factor",
        beta="Leader modified Cavalry factor",
        gamma="Leader modified Archer factor",
        total_troops="Optional total troops to convert fractions into headcount",
    )
    async def sim_deploy(
        self,
        ctx: commands.Context,
        alpha: float,
        beta: float,
        gamma: float,
        total_troops: int = 0,
    ):
        """Return optimal inf/cav/arc rally join fractions from alpha/beta/gamma."""
        try:
            fracs = optimize_deployment(alpha, beta, gamma)
        except ValueError as exc:
            return await ctx.send(str(exc))

        embed = discord.Embed(
            title="Optimal Fractional Deployment",
            color=discord.Color.green(),
            description=(
                "Computed via squared-factor allocation:\n"
                "f_inf = alpha^2 / (alpha^2 + beta^2 + gamma^2), and similarly for cav/arc."
            ),
        )

        embed.add_field(
            name="Fractions",
            value=(
                f"Infantry: **{fracs['inf']:.4f}**\n"
                f"Cavalry: **{fracs['cav']:.4f}**\n"
                f"Archers: **{fracs['arc']:.4f}**"
            ),
            inline=False,
        )

        if total_troops > 0:
            inf_n = _ceil_int(total_troops * fracs["inf"])
            cav_n = _ceil_int(total_troops * fracs["cav"])
            arc_n = max(total_troops - inf_n - cav_n, 0)
            embed.add_field(
                name=f"Suggested Split for {total_troops:,}",
                value=f"Inf {inf_n:,} | Cav {cav_n:,} | Arc {arc_n:,}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @sim.command(name="timer")
    @app_commands.describe(
        base_seconds="Base duration in seconds",
        additive_bonus_pct="Total additive speed bonus percent",
        chief_office="Apply Chief Office 20% multiplicative reduction",
    )
    async def sim_timer(
        self,
        ctx: commands.Context,
        base_seconds: app_commands.Range[int, 1, 10_000_000],
        additive_bonus_pct: float,
        chief_office: bool = False,
    ):
        """Calculate modified completion times with additive rule + Chief Office exception."""
        try:
            mod = modified_time_seconds(base_seconds, additive_bonus_pct, chief_office)
        except ValueError as exc:
            return await ctx.send(str(exc))

        embed = discord.Embed(
            title="Time Reduction Calculator",
            color=discord.Color.teal(),
            description=(
                "Formula:\n"
                "Modified Time = Base / (1 + sum bonuses)\n"
                "Chief Office exception applies an additional x0.8 afterward when enabled."
            ),
        )
        embed.add_field(name="Base", value=f"{base_seconds:,}s ({format_duration(base_seconds)})", inline=False)
        embed.add_field(name="Modified", value=f"{mod:,}s ({format_duration(mod)})", inline=False)
        embed.add_field(
            name="Effective Reduction",
            value=f"{(1 - (mod / base_seconds)) * 100:.2f}%",
            inline=False,
        )
        await ctx.send(embed=embed)

    @sim.command(name="vip")
    async def sim_vip(self, ctx: commands.Context):
        """Show known VIP cumulative cost milestones."""
        lines = [f"VIP {lvl}: ${cost:,}" for lvl, cost in sorted(VIP_THRESHOLDS.items())]
        embed = discord.Embed(
            title="VIP Milestones",
            color=discord.Color.purple(),
            description="Known cumulative spend thresholds used for progression modeling.",
        )
        embed.add_field(name="Thresholds", value="\n".join(lines), inline=False)
        embed.add_field(
            name="Notable Gates",
            value=(
                "VIP 6: extra march queue\n"
                "VIP 7: daily orange shard\n"
                "VIP 8: mythic shards/books\n"
                "VIP 10: +50% offspring stats"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @sim.command(name="tg")
    @app_commands.describe(
        target_level="Target TG level (1-5)",
        current_level="Current TG level (0-5)",
    )
    async def sim_tg(
        self,
        ctx: commands.Context,
        target_level: app_commands.Range[int, 1, 5],
        current_level: app_commands.Range[int, 0, 5] = 0,
    ):
        """Estimate Truegold step costs and projected stat deltas."""
        if target_level <= current_level:
            return await ctx.send("Target TG level must be greater than current TG level.")

        tg_needed = sum(TG_STEP_COSTS[level] for level in range(current_level + 1, target_level + 1))
        projected = CombatEngine.tg_flat_bonus(target_level)

        embed = discord.Embed(
            title="Truegold Progression",
            color=discord.Color.green(),
            description=(
                "Cost and stat projection tool using known TG step costs and simulator assumptions.\n"
                "TG1/TG2 stat effects are data-backed; TG3+ extends the same increment pattern for planning."
            ),
        )
        embed.add_field(
            name="Step Costs",
            value=(
                f"Current TG: {current_level}\n"
                f"Target TG: {target_level}\n"
                f"Estimated Truegold Needed: **{tg_needed:,}**"
            ),
            inline=False,
        )
        embed.add_field(
            name="Projected Flat Stat Bonus At Target",
            value=(
                f"Attack: +{projected['attack']}\n"
                f"Defense: +{projected['defense']}\n"
                f"Health: +{projected['health']}\n"
                f"Lethality: +{projected['lethality']}"
            ),
            inline=False,
        )
        embed.add_field(
            name="Reference Total To Reach TG5",
            value=(
                f"Truegold: {TG5_RESOURCE_TOTAL['truegold']:,}\n"
                f"Wood: {TG5_RESOURCE_TOTAL['wood']:,}\n"
                f"Bread: {TG5_RESOURCE_TOTAL['bread']:,}\n"
                f"Stone: {TG5_RESOURCE_TOTAL['stone']:,}\n"
                f"Iron: {TG5_RESOURCE_TOTAL['iron']:,}"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @sim.command(name="heroes")
    @app_commands.describe(generation="Optional generation filter")
    async def sim_heroes(self, ctx: commands.Context, generation: int = 0):
        """Show the reverse-engineered hero dataset used by the simulator."""
        rows = HERO_DATABASE
        if generation > 0:
            rows = [h for h in HERO_DATABASE if h["generation"] == generation]
            if not rows:
                return await ctx.send("No heroes found for that generation.")

        embed = discord.Embed(
            title="Hero Database Snapshot",
            color=discord.Color.dark_gold(),
            description="Skill summaries used for skill-mod and scenario setup decisions.",
        )

        for hero in rows[:20]:
            embed.add_field(
                name=f"Gen {hero['generation']} | {hero['name']} ({hero['rarity']} {hero['archetype']})",
                value=hero["summary"],
                inline=False,
            )

        if len(rows) > 20:
            embed.set_footer(text=f"Showing first 20 of {len(rows)} heroes.")
        await ctx.send(embed=embed)


class SkillModModal(discord.ui.Modal, title="SkillMod Helper"):
    values = discord.ui.TextInput(
        label="DamageUp,OppDefDown,OppDmgDown,DefenseUp",
        placeholder="Example: 25,15,10,8",
        required=True,
        max_length=120,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            parts = [p.strip() for p in str(self.values.value).split(",")]
            if len(parts) != 4:
                raise ValueError("Provide exactly 4 values.")
            d_up, od_down, odmg_down, def_up = [float(x) for x in parts]
            skill_mod = compute_skill_mod(d_up, od_down, odmg_down, def_up)
        except ValueError as exc:
            return await interaction.response.send_message(f"Invalid input: {exc}", ephemeral=True)

        embed = discord.Embed(
            title="Rule-of-4 SkillMod",
            color=discord.Color.blue(),
            description="Computed from your modal input. Use this value in combat runs.",
        )
        embed.add_field(name="SkillMod", value=f"**{skill_mod:.4f}x**", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class QuickCombatModal(discord.ui.Modal, title="Quick Combat Simulation"):
    attacker_lines = discord.ui.TextInput(
        label="Attacker lines (inf,cav,arc)",
        placeholder="Example: 250000,120000,90000",
        required=True,
        max_length=120,
    )
    defender_lines = discord.ui.TextInput(
        label="Defender lines (inf,cav,arc)",
        placeholder="Example: 300000,100000,110000",
        required=True,
        max_length=120,
    )
    settings = discord.ui.TextInput(
        label="Settings",
        placeholder="a_tier=10,d_tier=10,turns=10,a_add=0,a_skill=1,d_add=0,d_skill=1",
        required=False,
        max_length=400,
        style=discord.TextStyle.paragraph,
    )

    def __init__(self, cog: Simulator):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            atk = parse_line_triplet(str(self.attacker_lines.value))
            deff = parse_line_triplet(str(self.defender_lines.value))
            cfg = parse_kv_numbers(str(self.settings.value))

            attacker_cfg = self.cog._build_side_config(
                int(cfg.get("a_tier", 10)),
                int(cfg.get("a_tg", 0)),
                float(cfg.get("a_add", 0.0)),
                float(cfg.get("a_special", 0.0)),
                float(cfg.get("a_skill", 1.0)),
            )
            defender_cfg = self.cog._build_side_config(
                int(cfg.get("d_tier", 10)),
                int(cfg.get("d_tg", 0)),
                float(cfg.get("d_add", 0.0)),
                float(cfg.get("d_special", 0.0)),
                float(cfg.get("d_skill", 1.0)),
            )
            turns = int(cfg.get("turns", 10))

            result = CombatEngine.simulate(atk, deff, attacker_cfg, defender_cfg, turns=turns)
            embed = self.cog._combat_result_embed(
                result,
                title="Combat Simulation (Panel)",
                description="Quick panel run with the same core assumptions as /sim combat.",
                footer="Tip: use Advanced Combat for line buffs and scheduled turn effects.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as exc:
            await interaction.response.send_message(f"Could not run simulation: {exc}", ephemeral=True)


class AdvancedCombatModal(discord.ui.Modal, title="Advanced Combat Simulation"):
    attacker_lines = discord.ui.TextInput(
        label="Attacker lines (inf,cav,arc)",
        placeholder="Example: 250000,120000,90000",
        required=True,
        max_length=120,
    )
    defender_lines = discord.ui.TextInput(
        label="Defender lines (inf,cav,arc)",
        placeholder="Example: 300000,100000,110000",
        required=True,
        max_length=120,
    )
    settings = discord.ui.TextInput(
        label="Base settings",
        placeholder="a_tier=10,d_tier=10,turns=10,a_add=0,a_skill=1,d_add=0,d_skill=1",
        required=False,
        max_length=350,
    )
    line_bonuses = discord.ui.TextInput(
        label="Line bonuses",
        placeholder="A|inf:atk=10;cav:atk=8||D|inf:def=12;arc:let=6",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph,
    )
    turn_events = discord.ui.TextInput(
        label="Turn events",
        placeholder="2:a_skill=1.2;4:d_skill=1.15;6:a_add=10,d_add=5",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph,
    )

    def __init__(self, cog: Simulator):
        super().__init__()
        self.cog = cog

    @staticmethod
    def _split_bonus_blob(raw: str) -> Tuple[str, str]:
        text = (raw or "").strip()
        if not text:
            return "", ""
        if "||" not in text:
            raise ValueError("Line bonuses must separate sides using ||")
        left, right = text.split("||", 1)
        left = left.strip()
        right = right.strip()
        if left.upper().startswith("A|"):
            left = left[2:].strip()
        if right.upper().startswith("D|"):
            right = right[2:].strip()
        return left, right

    async def on_submit(self, interaction: discord.Interaction):
        try:
            atk = parse_line_triplet(str(self.attacker_lines.value))
            deff = parse_line_triplet(str(self.defender_lines.value))
            cfg = parse_kv_numbers(str(self.settings.value))
            atk_bonus_blob, def_bonus_blob = self._split_bonus_blob(str(self.line_bonuses.value))
            atk_bonuses = parse_line_bonus_map(atk_bonus_blob)
            def_bonuses = parse_line_bonus_map(def_bonus_blob)
            events = parse_turn_events(str(self.turn_events.value))

            attacker_cfg = self.cog._build_side_config(
                int(cfg.get("a_tier", 10)),
                int(cfg.get("a_tg", 0)),
                float(cfg.get("a_add", 0.0)),
                float(cfg.get("a_special", 0.0)),
                float(cfg.get("a_skill", 1.0)),
            )
            defender_cfg = self.cog._build_side_config(
                int(cfg.get("d_tier", 10)),
                int(cfg.get("d_tg", 0)),
                float(cfg.get("d_add", 0.0)),
                float(cfg.get("d_special", 0.0)),
                float(cfg.get("d_skill", 1.0)),
            )
            turns = int(cfg.get("turns", 10))

            result = CombatEngine.simulate_advanced(
                atk,
                deff,
                attacker_cfg,
                defender_cfg,
                turns,
                attacker_line_bonuses=atk_bonuses,
                defender_line_bonuses=def_bonuses,
                turn_events=events,
            )
            embed = self.cog._combat_result_embed(
                result,
                title="Advanced Combat (Panel)",
                description="Panel-run advanced mode with per-line buffs and turn-scheduled effects.",
                footer="Keep schedules concise and only define turns where behavior changes.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as exc:
            await interaction.response.send_message(f"Could not run advanced simulation: {exc}", ephemeral=True)


class SimulatorPanelView(discord.ui.View):
    def __init__(self, cog: Simulator):
        super().__init__(timeout=900)
        self.cog = cog

    @discord.ui.button(label="Quick Combat", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def quick_combat(self, interaction: discord.Interaction, _: discord.ui.Button):
        try:
            await interaction.response.send_modal(QuickCombatModal(self.cog))
        except Exception as e:
            if interaction.response.is_done():
                await interaction.followup.send(f"Could not open Quick Combat modal: {e}", ephemeral=True)
            else:
                await interaction.response.send_message(f"Could not open Quick Combat modal: {e}", ephemeral=True)

    @discord.ui.button(label="Advanced Combat", style=discord.ButtonStyle.danger, emoji="🧠")
    async def advanced_combat(self, interaction: discord.Interaction, _: discord.ui.Button):
        try:
            await interaction.response.send_modal(AdvancedCombatModal(self.cog))
        except Exception as e:
            if interaction.response.is_done():
                await interaction.followup.send(f"Could not open Advanced Combat modal: {e}", ephemeral=True)
            else:
                await interaction.response.send_message(f"Could not open Advanced Combat modal: {e}", ephemeral=True)

    @discord.ui.button(label="SkillMod Helper", style=discord.ButtonStyle.secondary, emoji="📐")
    async def skillmod(self, interaction: discord.Interaction, _: discord.ui.Button):
        try:
            await interaction.response.send_modal(SkillModModal())
        except Exception as e:
            if interaction.response.is_done():
                await interaction.followup.send(f"Could not open SkillMod modal: {e}", ephemeral=True)
            else:
                await interaction.response.send_message(f"Could not open SkillMod modal: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Simulator(bot))
