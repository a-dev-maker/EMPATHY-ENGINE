

__version__ = "1.2.0"
__author__  = "the guy who made it lol"
__license__ = "MIT"


import argparse
import json
import os
import sys
import textwrap
from dataclasses import dataclass, asdict
from typing import Optional

try:
    from rich.console import Console
    _RICH = True
except ImportError:
    _RICH = False



class C:
    RESET="\033[0m"; BOLD="\033[1m"; DIM="\033[2m"; ITALIC="\033[3m"
    RED="\033[91m"; GREEN="\033[92m"; YELLOW="\033[93m"
    BLUE="\033[94m"; MAGENTA="\033[95m"; CYAN="\033[96m"
    WHITE="\033[97m"; GRAY="\033[90m"



@dataclass
class Neurotransmitter:
    name: str
    baseline: float   # 0.0–2.0; 1.0 = healthy
    role: str
    game_effect: str

@dataclass
class PhysiologyProfile:
    condition_name: str
    neurotransmitters: list
    systems_affected: list
    primary_symptoms: list
    timeline_pattern: str   # episodic | chronic | fluctuating | developmental
    medication_targets: list

@dataclass
class GameMechanic:
    name: str
    description: str
    mapped_from: str
    implementation_hint: str
    intensity: float = 1.0

@dataclass
class TimelineLayer:
    name: str
    description: str
    events: list
    braid_mechanic: str

@dataclass
class MetaConsole:
    label: str
    variables: list
    description: str
    inception_note: str

@dataclass
class StaminaSystem:
    """"
    -------------------------------------------------------
    max_stamina       float  0–1   absolute ceiling (1.0 = healthy)
    regen_rate        float  /s    how fast stamina fills when resting
    drain_rate        float  /s    passive drain even at rest
    regen_cap         float  0–1   fraction of max reachable without sleep
    serotonin_weight  float        how strongly serotonin drives regen
    formula           str          human-readable formula shown in console
    rest_threshold    float  0–1   stamina below this triggers forced-rest warning
    overshoot_penalty bool         mania/excess NT: stamina decays if above cap
    """
    max_stamina:      float
    regen_rate:       float
    drain_rate:       float
    regen_cap:        float
    serotonin_weight: float
    formula:          str
    rest_threshold:   float = 0.25
    overshoot_penalty: bool = False


@dataclass
class GeneratedGame:
    condition: str
    genre: str
    title: str
    tagline: str
    core_loop: str
    mechanics: list
    timeline: TimelineLayer
    meta_console: MetaConsole
    learning_objectives: list
    design_notes: str
    pseudocode: str
    stamina: "StaminaSystem | None" = None



# CONDITION LIBRARY


class ConditionLibrary:
    REGISTRY: dict = {}

    @classmethod
    def register(cls, name, profile):
        cls.REGISTRY[name.lower()] = profile

    @classmethod
    def get(cls, name) -> Optional[PhysiologyProfile]:
        return cls.REGISTRY.get(name.lower())

    @classmethod
    def all_names(cls) -> list:
        return sorted(cls.REGISTRY.keys())


def _init_conditions():
    ConditionLibrary.register("depression", PhysiologyProfile(
        "Major Depressive Disorder",
        [Neurotransmitter("Serotonin",0.40,"mood/reward","energy bar drains 2x faster"),
         Neurotransmitter("Dopamine",0.35,"motivation/pleasure","reward events muted; 50% XP"),
         Neurotransmitter("Norepinephrine",0.45,"arousal/attention","movement x0.6, jump -40%")],
        ["limbic","prefrontal_cortex","HPA_axis","circadian"],
        ["persistent low mood","anhedonia","fatigue","psychomotor retardation",
         "concentration difficulty","sleep disruption"],
        "episodic",
        ["SSRI -> serotonin reuptake","SNRI -> serotonin+NE","bupropion -> dopamine"],
    ))
    ConditionLibrary.register("adhd", PhysiologyProfile(
        "Attention-Deficit/Hyperactivity Disorder",
        [Neurotransmitter("Dopamine",0.55,"salience/reward","distractors emit 2x dopamine vs task objects"),
         Neurotransmitter("Norepinephrine",0.50,"executive function","task queue re-shuffles every 30s")],
        ["prefrontal_cortex","basal_ganglia","cerebellum","default_mode_network"],
        ["inattention","impulsivity","hyperactivity","time blindness",
         "working memory deficits","emotional dysregulation"],
        "developmental",
        ["stimulants -> dopamine/NE reuptake inhibition","atomoxetine -> NE selective"],
    ))
    ConditionLibrary.register("autism", PhysiologyProfile(
        "Autism Spectrum Condition",
        [Neurotransmitter("GABA",0.60,"inhibition/filtering","all audio channels play simultaneously"),
         Neurotransmitter("Glutamate",1.40,"excitation","sensory inputs amplified x2"),
         Neurotransmitter("Serotonin",0.70,"social/routine","routine breaks trigger penalty")],
        ["sensory_cortex","social_brain_network","mirror_neuron_system","interoception"],
        ["sensory hypersensitivity","social communication differences",
         "need for predictability","special interests","masking fatigue"],
        "developmental",
        ["no approved core treatment; SSRIs/risperidone for specific symptoms"],
    ))
    ConditionLibrary.register("anxiety", PhysiologyProfile(
        "Generalised Anxiety Disorder",
        [Neurotransmitter("GABA",0.45,"inhibition","threat-detection fires every 0.5s"),
         Neurotransmitter("Cortisol",1.70,"stress response","stamina never reaches 100% in safe zones"),
         Neurotransmitter("Norepinephrine",1.60,"fight-or-flight","false-positive alerts spawn constantly")],
        ["amygdala","HPA_axis","locus_coeruleus","prefrontal_cortex"],
        ["excessive worry","restlessness","fatigue","concentration difficulty",
         "muscle tension","sleep disturbance"],
        "chronic",
        ["SSRIs","SNRIs","buspirone -> 5-HT1A","benzodiazepines -> GABA-A"],
    ))
    ConditionLibrary.register("chronic_pain", PhysiologyProfile(
        "Chronic Pain Syndrome",
        [Neurotransmitter("Substance P",1.80,"pain amplification","damage events deal 3x HP loss"),
         Neurotransmitter("Endorphins",0.30,"pain suppression","natural healing throttled to 5%"),
         Neurotransmitter("Serotonin",0.50,"descending inhibition","no pain-gating; all hits register")],
        ["spinal_cord","thalamus","anterior_cingulate","prefrontal_cortex"],
        ["allodynia","hyperalgesia","fatigue","sleep disruption","cognitive fog"],
        "chronic",
        ["SNRIs -> descending inhibition","gabapentinoids -> central sensitisation"],
    ))
    ConditionLibrary.register("ptsd", PhysiologyProfile(
        "Post-Traumatic Stress Disorder",
        [Neurotransmitter("Cortisol",0.30,"HPA dysregulation","threat response fires without enemies"),
         Neurotransmitter("Norepinephrine",1.80,"hyperarousal","ambient sounds trigger combat alert"),
         Neurotransmitter("Serotonin",0.45,"mood/memory","certain zones locked behind trauma triggers")],
        ["amygdala","hippocampus","prefrontal_cortex","HPA_axis"],
        ["flashbacks","nightmares","avoidance","hyperarousal","emotional numbing"],
        "episodic",
        ["SSRIs (sertraline)","prazosin -> nightmares","EMDR (therapy)"],
    ))
    ConditionLibrary.register("schizophrenia", PhysiologyProfile(
        "Schizophrenia",
        [Neurotransmitter("Dopamine_mesolimbic",1.90,"salience attribution","random objects gain significance halos"),
         Neurotransmitter("Dopamine_mesocortical",0.40,"cognition","working memory slots reduced to 2"),
         Neurotransmitter("Glutamate_NMDA",0.50,"reality testing","NPC speech sometimes replaced by internal voice")],
        ["mesolimbic_pathway","mesocortical_pathway","thalamus","hippocampus"],
        ["hallucinations","delusions","disorganised thought","flat affect","avolition"],
        "episodic",
        ["antipsychotics -> D2 antagonism","clozapine -> multi-receptor"],
    ))
    ConditionLibrary.register("bipolar", PhysiologyProfile(
        "Bipolar I Disorder",
        [Neurotransmitter("Dopamine",1.9,"mania drive","speed x3, infinite energy during mania"),
         Neurotransmitter("Serotonin",0.3,"mood","colour swings oversaturated to greyscale"),
         Neurotransmitter("Glutamate",1.5,"mania excitation","skill tree unlocks too fast then re-locks")],
        ["limbic","prefrontal_cortex","circadian_clock","HPA_axis"],
        ["manic episodes","depressive episodes","impulsivity","grandiosity"],
        "episodic",
        ["lithium -> mood stabilisation","valproate","atypical antipsychotics"],
    ))

_init_conditions()





GENRES = {
    "platformer": dict(description="Side-scrolling jump-and-run",
        core_mechanic="movement, traversal, momentum",
        strength="physical sensation - weight, energy, speed",
        weakness="social/cognitive symptoms harder to show",
        best_engines=["pygame","arcade","pyglet","pygame_zero"]),
    "puzzle": dict(description="Solve logic/spatial/pattern problems",
        core_mechanic="cognition, working memory, attention",
        strength="executive function deficits, attention, cognitive load",
        weakness="emotional or somatic symptoms less natural",
        best_engines=["pygame","arcade","kivy","cocos2d"]),
    "social_sim": dict(description="Navigate conversations and relationships",
        core_mechanic="dialogue choices, relationship meters, energy",
        strength="social cognition, masking, communication differences",
        weakness="physical/somatic symptoms less immediate",
        best_engines=["ursina","panda3d","cocos2d","kivy"]),
    "survival": dict(description="Manage resources in a hostile environment",
        core_mechanic="resource depletion, risk management, scarcity",
        strength="fatigue, pain, resource-constrained cognition",
        weakness="subtle cognitive symptoms hard to convey",
        best_engines=["panda3d","ursina","pygame","arcade"]),
    "narrative": dict(description="Branching story / visual novel",
        core_mechanic="choices, inner monologue, memory",
        strength="rich inner experience, stigma exploration",
        weakness="less visceral; relies on empathy leap",
        best_engines=["cocos2d","kivy","pyglet","pygame_zero"]),
    "stealth": dict(description="Avoid detection, manage visibility",
        core_mechanic="hypervigilance, masking, threat assessment",
        strength="anxiety, PTSD hyperarousal, social masking",
        weakness="physical/energy symptoms less natural",
        best_engines=["pygame","arcade","pyglet"]),
    "rts": dict(description="Real-time strategy / base building",
        core_mechanic="multitasking, prioritisation, planning",
        strength="executive dysfunction, cognitive fatigue",
        weakness="emotional/somatic symptoms less visible",
        best_engines=["pygame","arcade","cocos2d"]),
    "rhythm": dict(description="Timing, pattern, musical interaction",
        core_mechanic="timing perception, sensory processing",
        strength="sensory processing differences, time blindness",
        weakness="limited narrative space",
        best_engines=["pyglet","pygame","arcade"]),
}



ENGINES = {
    "pygame": dict(
        label="Pygame", install="pip install pygame",
        url="https://www.pygame.org",
        description="Most popular 2D library. Built on SDL. Great for learning and simple 2D.",
        best_for=["platformer","puzzle","narrative","rhythm","rts","stealth"],
        import_snippet="import pygame\npygame.init()",
    ),
    "arcade": dict(
        label="Arcade", install="pip install arcade",
        url="https://api.arcade.academy",
        description="Modern OOP 2D library. Better performance and cleaner syntax than Pygame.",
        best_for=["platformer","puzzle","survival","stealth","rts"],
        import_snippet="import arcade",
    ),
    "pyglet": dict(
        label="Pyglet", install="pip install pyglet",
        url="https://pyglet.org",
        description="OpenGL-based. Excellent for 2D games and multimedia. Strong sprite handling.",
        best_for=["platformer","rhythm","narrative","stealth"],
        import_snippet="import pyglet\nfrom pyglet import shapes, sprite",
    ),
    "pygame_zero": dict(
        label="Pygame Zero", install="pip install pgzero",
        url="https://pygame-zero.readthedocs.io",
        description="Built on Pygame. Removes boilerplate. Ideal for beginners and education.",
        best_for=["platformer","puzzle","narrative"],
        import_snippet="# No import needed\n# Run with: pgzrun your_game.py",
    ),
    "panda3d": dict(
        label="Panda3D", install="pip install panda3d",
        url="https://www.panda3d.org",
        description="Robust 3D framework. Originally by Disney. For complex 3D projects.",
        best_for=["survival","social_sim","narrative"],
        import_snippet="from direct.showbase.ShowBase import ShowBase\nfrom panda3d.core import *",
    ),
    "ursina": dict(
        label="Ursina", install="pip install ursina",
        url="https://www.ursinaengine.org",
        description="User-friendly 3D engine on Panda3D. Designed for fast game creation.",
        best_for=["social_sim","survival","narrative"],
        import_snippet="from ursina import *\napp = Ursina()",
    ),
    "cocos2d": dict(
        label="Cocos2d", install="pip install cocos2d",
        url="http://python.cocos2d.org",
        description="2D games, interactive GUI, cross-platform. Layer and scene system.",
        best_for=["platformer","social_sim","narrative","rts"],
        import_snippet="import cocos\nfrom cocos.director import director",
    ),
    "kivy": dict(
        label="Kivy", install="pip install kivy",
        url="https://kivy.org",
        description="Multi-touch framework. Mobile-friendly 2D games and apps.",
        best_for=["social_sim","puzzle","narrative"],
        import_snippet="from kivy.app import App\nfrom kivy.uix.widget import Widget",
    ),
    "pyopengl": dict(
        label="PyOpenGL", install="pip install PyOpenGL PyOpenGL_accelerate",
        url="https://pyopengl.sourceforge.net",
        description="Low-level 3D rendering. Often combined with Pygame/Pyglet.",
        best_for=["platformer","survival"],
        import_snippet="from OpenGL.GL import *\nfrom OpenGL.GLUT import *",
    ),
}




def _nt_dict(condition: str) -> str:
    profile = ConditionLibrary.get(condition)
    if not profile:
        return '{"serotonin": 0.5, "dopamine": 0.5}'
    pairs = []
    for nt in profile.neurotransmitters:
        key = nt.name.lower().replace(" ","_").replace("(","").replace(")","")
        val = nt.baseline if isinstance(nt.baseline, float) else 0.5
        pairs.append(f'    "{key}": {val}')
    return "{\n" + ",\n".join(pairs) + "\n}"




class EngineAdapterGenerator:

    @classmethod
    def generate(cls, game: GeneratedGame, engine_key: str) -> str:
        engine_key = engine_key.lower()
        if engine_key not in ENGINES:
            raise ValueError(f"Unknown engine '{engine_key}'. Available: {', '.join(ENGINES)}")
        method = getattr(cls, f"_adapter_{engine_key}", cls._adapter_generic)
        return method(game, ENGINES[engine_key])

    @staticmethod
    def _adapter_pygame(game, info):
        condition = game.condition.upper().replace("_", " ")
        nd        = _nt_dict(game.condition)
        # Build runtime mechanic table from real GameMechanic objects
        mechanic_rows = "\n".join(
            f'    "{m.name}": {{"intensity": {m.intensity}, "active": True}},'
            for m in game.mechanics
        )
        stamina_vals = ""
        if game.stamina:
            s = game.stamina
            stamina_vals = (
                f"MAX_STAMINA={s.max_stamina}, REGEN_RATE={s.regen_rate}, "
                f"DRAIN_RATE={s.drain_rate}, REGEN_CAP={s.regen_cap}, "
                f"OVERSHOOT={s.overshoot_penalty}"
            )
        return f'''"""{game.title} — Pygame scaffold.

Condition: {condition} | Genre: {game.genre.upper()} | Engine: Pygame
Generated by Mechanistic Empathy Engine v{__version__}
Install: {info['install']}
"""
__version__ = "{__version__}"

import pygame, sys, math, random
pygame.init()

SCREEN_W, SCREEN_H, FPS = 800, 600, 60
GRAVITY = 900


NT = {nd}

# ── Stamina system ({stamina_vals}) ─────────
MAX_STAMINA  = {game.stamina.max_stamina if game.stamina else 1.0}
REGEN_RATE   = {game.stamina.regen_rate  if game.stamina else 0.08}
DRAIN_RATE   = {game.stamina.drain_rate  if game.stamina else 0.01}
REGEN_CAP    = {game.stamina.regen_cap   if game.stamina else 1.0}
OVERSHOOT    = {game.stamina.overshoot_penalty if game.stamina else False}


MECHANICS = {{
{mechanic_rows}
}}

class MechanicRuntime:
    """
    def __init__(self, nt: dict, mechanics: dict):
        self.nt        = nt
        self.mechanics = mechanics
        # Internal state for mechanics that need it
        self._distractor_timer  = 0.0
        self._distractor_freeze = 0.0
        self._shuffle_timer     = 0.0
        self._false_alert_timer = 0.0
        self._false_alert_on    = False
        self._mood_timer        = 0.0
        self._mood_phase        = 0    0=mania 1=euthymia 2=depression 3=euthymia
        self._MOOD_PHASES       = [60, 30, 90, 30]

    def tick(self, gs: dict, dt: float) -> dict:
        """
        gs = game_state dict with keys:
          move_speed, jump_speed, energy, stamina, on_ground,
          color_sat, input_frozen, reward_mult, screen_flash
        Returns modified gs.
        """
        nt = self.nt

        
        serotonin      = nt.get("serotonin",      0.5)
        dopamine       = nt.get("dopamine",        0.5)
        norepinephrine = nt.get("norepinephrine",  0.5)
        cortisol       = nt.get("cortisol",        1.0)
        gaba           = nt.get("gaba",            1.0)

        
        gs["move_speed"]  = max(40,  int(220 * norepinephrine))
        gs["jump_speed"]  = max(200, int(480 * max(norepinephrine, 0.3)))
        gs["reward_mult"] = dopamine
        gs["color_sat"]   = min(1.0, serotonin + 0.15)

        
        gaba_gate   = 0.5 + 0.5 * min(gaba, 1.0)
        live_regen  = REGEN_RATE * (serotonin / 1.0) * gaba_gate * (1.0 / max(cortisol, 0.5))
        live_drain  = DRAIN_RATE
        cap         = REGEN_CAP * MAX_STAMINA if gs.get("is_resting") else gs["stamina"]
        if gs["stamina"] < cap:
            gs["stamina"] = min(cap, gs["stamina"] + live_regen * dt)
        else:
            gs["stamina"] = max(0.0, gs["stamina"] - live_drain * dt)
        if OVERSHOOT and dopamine > 1.5 and gs["stamina"] > MAX_STAMINA:
            gs["stamina"] -= (dopamine - 1.5) * 0.05 * dt
        gs["stamina"] = max(0.0, min(MAX_STAMINA, gs["stamina"]))

        
        if self.mechanics.get("Vital Energy Bar", {{}}).get("active"):
            drain = (0.8 / max(serotonin, 0.01)) * dt * 0.008
            gs["energy"] = max(0.0, gs["energy"] - drain)

        
        if self.mechanics.get("Colour Desaturation", {{}}).get("active"):
            gs["color_sat"] = gs["energy"]   # energy directly drives saturation

        
        if self.mechanics.get("Heavy Movement", {{}}).get("active"):
            gs["move_speed"]  = int(gs["move_speed"]  * 0.6)
            gs["jump_speed"]  = int(gs["jump_speed"]  * 0.6)

        
        if self.mechanics.get("Reward Blunting", {{}}).get("active"):
            gs["reward_mult"] *= 0.5

        
            self._distractor_timer += dt
            if self._distractor_freeze > 0:
                self._distractor_freeze -= dt
                gs["input_frozen"] = True
            else:
                gs["input_frozen"] = False
            if self._distractor_timer > 8.0:
                self._distractor_timer = 0.0
                gs["show_distractor"] = True
            else:
                gs["show_distractor"] = False

        
        if self.mechanics.get("Time Perception Warp", {{}}).get("active"):
            gs["clock_speed"] = 3.0   # displayed clock runs 3x real time

        
        if self.mechanics.get("False Positive Alerts", {{}}).get("active"):
            self._false_alert_timer += dt
            if self._false_alert_timer > 15.0:
                self._false_alert_timer = 0.0
                ne = nt.get("norepinephrine", 1.5)
                if random.random() < 0.25 * ne:
                    self._false_alert_on = True
            if self._false_alert_on:
                gs["show_alert"] = True
                gs["dread"]      = min(1.0, gs.get("dread", 0) + 0.05 * dt)
            else:
                gs["show_alert"] = False

        
        if self.mechanics.get("Mood Cycle", {{}}).get("active"):
            self._mood_timer += dt
            if self._mood_timer >= self._MOOD_PHASES[self._mood_phase]:
                self._mood_timer = 0.0
                self._mood_phase = (self._mood_phase + 1) % 4
            phase_name = ["mania","euthymia","depression","euthymia"][self._mood_phase]
            if phase_name == "mania":
                gs["move_speed"]  = int(gs["move_speed"]  * 3.0)
                gs["jump_speed"]  = int(gs["jump_speed"]  * 2.0)
                gs["energy"]      = 1.0
                gs["color_sat"]   = 2.0   # oversaturated
            elif phase_name == "depression":
                gs["move_speed"]  = int(gs["move_speed"]  * 0.4)
                gs["color_sat"]  *= 0.2
            gs["mood_phase"] = phase_name

        # ── Masking meter (autism) ────────────────────────────────────────────
        if self.mechanics.get("Masking Meter", {{}}).get("active"):
            # Masking drains passively; player action can drain faster
            gs["masking"] = max(0.0, gs.get("masking", 1.0) - 0.002 * dt)
            if gs["masking"] <= 0.0:
                gs["meltdown"] = True
                gs["input_frozen"] = True

        # ── PTSD flashback cooldown ───────────────────────────────────────────
        if self.mechanics.get("Flashback Intrusion", {{}}).get("active"):
            if gs.get("flashback_timer", 0) > 0:
                gs["flashback_timer"] -= dt
                gs["input_frozen"]    = True
                gs["screen_flash"]    = True
            else:
                gs["screen_flash"]    = False

        return gs

    def dismiss_alert(self):
        self._false_alert_on = False

    def distractor_clicked(self):
        self._distractor_freeze = 5.0   # 5s freeze on distractor click


# ── Sprites ───────────────────────────────────────────────────────────────────

class Platform(pygame.sprite.Sprite):
    """A solid platform the player can stand on."""
    def __init__(self, x, y, w, h=16, color=(70, 75, 95)):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(color)
        self.rect  = self.image.get_rect(topleft=(x, y))


class Player(pygame.sprite.Sprite):
    def __init__(self, platforms: pygame.sprite.Group):
        super().__init__()
        self.image    = pygame.Surface((28, 52), pygame.SRCALPHA)
        self._draw_player_shape((100, 180, 255))
        self.rect     = self.image.get_rect(midbottom=(SCREEN_W // 2, SCREEN_H - 60))
        self.vel_y    = 0.0
        self.on_ground = False
        self.platforms = platforms
        self._base_color = (100, 180, 255)

    def _draw_player_shape(self, color):
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, color, (0, 0, 28, 52), border_radius=6)

    def update(self, gs: dict, dt: float):
        keys = pygame.key.get_pressed()

        Input can be frozen by a mechanic (e.g. distractor, flashback, meltdown)
        if not gs.get("input_frozen", False):
            if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.rect.x -= gs["move_speed"] * dt
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.rect.x += gs["move_speed"] * dt
            if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
                self.vel_y = -gs["jump_speed"]

        Gravity
        self.vel_y += GRAVITY * dt
        self.rect.y += int(self.vel_y * dt)

        
        self.on_ground = False
        if self.vel_y >= 0:   # only check when falling
            hits = pygame.sprite.spritecollide(self, self.platforms, False)
            for plat in hits:
                # Only land if player was above the platform top last frame
                if self.rect.bottom - int(self.vel_y * dt) <= plat.rect.top + 4:
                    self.rect.bottom = plat.rect.top
                    self.vel_y       = 0
                    self.on_ground   = True

        
        self.rect.x = max(0, min(SCREEN_W - self.rect.width, self.rect.x))

        
        sat = min(1.0, max(0.0, gs.get("color_sat", 1.0)))
        r   = int(self._base_color[0] * sat + 80 * (1 - sat))
        g   = int(self._base_color[1] * sat + 80 * (1 - sat))
        b   = int(self._base_color[2] * sat + 80 * (1 - sat))
        self._draw_player_shape((r, g, b))

        
        gs["is_resting"] = self.on_ground and not (
            keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or
            keys[pygame.K_a]    or keys[pygame.K_d])

def build_level(condition: str) -> pygame.sprite.Group:
    """
    platforms = pygame.sprite.Group()

    platforms.add(Platform(0, SCREEN_H - 40, SCREEN_W, 40, color=(55, 60, 80)))

    layouts = {{
        "depression":    [(50,460,200),(320,390,180),(550,340,160),(150,280,200),(400,220,180)],
        "adhd":          [(30,500,80),(140,450,60),(240,480,70),(340,420,90),(460,460,55),
                          (560,390,75),(650,430,65),(100,350,80),(280,320,60),(500,300,70)],
        "autism":        [(i*130+20, 480-j*70, 110) for j in range(4) for i in range(6)
                          if (i+j)%2==0],
        "anxiety":       [(60,500,100),(350,430,80),(680,480,100),(180,350,70),
                          (500,320,90),(100,240,60),(620,200,80)],
        "chronic_pain":  [(0,500,160),(200,470,120),(400,430,100),(550,400,140),
                          (150,340,120),(450,300,100)],
        "ptsd":          [(50,520,150),(300,460,100),(600,500,120),(200,380,80),
                          (500,320,100),(350,260,80)],
        "schizophrenia": [(50,500,100),(200,460,80),(380,490,60),(520,440,90),
                          (150,380,70),(420,340,110),(600,380,60),(280,300,80)],
        "bipolar":       [(100,500,120),(350,460,100),(600,490,120),(200,380,80),
                          (500,340,100),(300,260,140)],
    }}
    for x, y, w in layouts.get(condition, layouts["depression"]):
        platforms.add(Platform(x, y, w))

    return platforms




def apply_saturation(surface: pygame.Surface, sat: float) -> pygame.Surface:
    if sat >= 1.0:
        return surface
    sat = max(0.0, sat)
    arr = pygame.surfarray.array3d(surface)
    grey = (arr[:,:,0]*0.299 + arr[:,:,1]*0.587 + arr[:,:,2]*0.114).astype("uint8")
    for ch in range(3):
        arr[:,:,ch] = (arr[:,:,ch] * sat + grey * (1 - sat)).astype("uint8")
    return pygame.surfarray.make_surface(arr)


def draw_bar(surf, x, y, w, h, val, maxv, fill_color, bg=(50,50,60), label=""):
    font = pygame.font.SysFont("monospace", 11)
    pygame.draw.rect(surf, bg, (x, y, w, h), border_radius=3)
    filled = int(w * max(0, min(val, maxv)) / maxv)
    if filled > 0:
        pygame.draw.rect(surf, fill_color, (x, y, filled, h), border_radius=3)
    if label:
        surf.blit(font.render(label, True, (190,190,190)), (x + w + 6, y - 1))


def draw_hud(surf, gs, stamina, font):
    energy = gs.get("energy", 1.0)
    draw_bar(surf, 10, 10, 180, 14, energy,  1.0,
             (int(255*(1-energy)), int(200*energy), 60), label="Energy")
    draw_bar(surf, 10, 30, 180, 14, stamina, MAX_STAMINA,
             (60, 160, 255), label="Stamina")

    hints = ["F1=console", "M=medication", "WASD/arrows=move", "Space=jump"]
    phase = gs.get("mood_phase", "")
    if phase:             hints.append("Mood:" + phase.upper())
    if gs.get("show_alert"):   hints.append("!! FALSE ALERT !!")
    if gs.get("meltdown"):     hints.append("MELTDOWN")
    if gs.get("input_frozen"): hints.append("FROZEN")

    x = 10
    for h in hints:
        color = (255,80,80) if h.startswith("!!") or h=="MELTDOWN" else (160,160,160)
        t = font.render(h, True, color)
        surf.blit(t, (x, SCREEN_H - 18))
        x += t.get_width() + 14


def draw_console(surf, nt, stamina, gs, font):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((12, 12, 28, 230))
    surf.blit(overlay, (0, 0))

    y = 18
    surf.blit(font.render("── META-CONSOLE  F1=close  M=medication ──",
                           True, (100,220,255)), (20, y)); y += 26
    for name, val in nt.items():
        bw = int(min(val, 2.0) * 90)
        pygame.draw.rect(surf, (40,40,70), (20, y, 180, 13))
        col = (80,200,120) if val <= 1.0 else (220,120,60)
        pygame.draw.rect(surf, col, (20, y, bw, 13))
        surf.blit(font.render(f"{{name:<22}} {{val:.3f}}", True, (200,200,200)),
                  (210, y - 1))
        y += 18

    y += 8
    surf.blit(font.render(f"STAMINA  {{stamina:.3f}} / {{MAX_STAMINA:.3f}}  "
                           f"regen={{REGEN_RATE:.4f}}/s  drain={{DRAIN_RATE:.4f}}/s",
                           True, (100,200,255)), (20, y)); y += 18
    surf.blit(font.render(f"regen_cap={{REGEN_CAP:.0%}}  overshoot={{OVERSHOOT}}",
                           True, (140,140,180)), (20, y)); y += 22
    surf.blit(font.render("NT levels drive all game parameters in real time.",
                           True, (90,90,110)), (20, y))


def draw_distractor(surf):
    t = pygame.time.get_ticks() / 400.0
    x = int(700 + 40 * math.sin(t))
    y = int(300 + 30 * math.cos(t * 1.3))
    pygame.draw.circle(surf, (255, 215, 0), (x, y), 18)
    pygame.draw.circle(surf, (255, 255, 150), (x, y), 10)
    f = pygame.font.SysFont("monospace", 10)
    surf.blit(f.render("SHINY", True, (80,60,0)), (x-18, y+20))


MEDICATION_PRESETS = dict(
    depression = dict(serotonin=0.3,  dopamine=0.2,  norepinephrine=0.2),
    adhd       = dict(dopamine=0.3,   norepinephrine=0.25),
    anxiety    = dict(gaba=0.4,       cortisol=-0.5),
    bipolar    = dict(dopamine=-0.5,  serotonin=0.3),
    chronic_pain=dict(substance_p=-0.4, serotonin=0.3, endorphins=0.2),
    ptsd       = dict(norepinephrine=-0.4, serotonin=0.3),
    schizophrenia=dict(dopamine_mesolimbic=-0.5, glutamate_nmda=0.2),
    autism     = dict(gaba=0.3, glutamate=-0.2),
)


def main():
    screen   = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("{game.title}")
    clock    = pygame.time.Clock()
    font     = pygame.font.SysFont("monospace", 12)
    big_font = pygame.font.SysFont("monospace", 22)

    nt       = dict(NT)
    platforms = build_level("{game.condition}")
    player   = Player(platforms)
    runtime  = MechanicRuntime(nt, MECHANICS)

    all_sprites = pygame.sprite.Group(player)
    all_sprites.add(platforms)

    stamina = MAX_STAMINA
    gs      = dict(move_speed=200, jump_speed=480, energy=1.0, stamina=stamina,
                   color_sat=1.0, input_frozen=False, reward_mult=1.0,
                   screen_flash=False, is_resting=False, dread=0.0,
                   masking=1.0, meltdown=False, mood_phase="", clock_speed=1.0)
    console = False

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    console = not console
                if event.key == pygame.K_m:
                    preset = MEDICATION_PRESETS.get("{game.condition}", {{}})
                    for k, v in preset.items():
                        if k in nt: nt[k] = max(0.0, min(2.0, nt[k] + v))
                if event.key == pygame.K_SPACE and gs.get("show_alert"):
                    runtime.dismiss_alert()
                if event.key == pygame.K_r and gs.get("meltdown"):
                    gs["meltdown"] = False   # reset meltdown

        # Run all mechanics — modifies gs in place
        gs["stamina"] = stamina
        gs = runtime.tick(gs, dt)
        stamina = gs["stamina"]

        player.update(gs, dt)

        
        sat  = gs.get("color_sat", 1.0)
        dread = gs.get("dread", 0.0)
        bg_r = int(20 + 60 * dread)
        bg_g = int(20 * sat)
        bg_b = int(35 * sat)
        world_surf = pygame.Surface((SCREEN_W, SCREEN_H))
        world_surf.fill((bg_r, bg_g, bg_b))

        
        platforms.draw(world_surf)
        # Draw player
        world_surf.blit(player.image, player.rect)

       
        if sat < 0.95:
            world_surf = apply_saturation(world_surf, sat)

        screen.blit(world_surf, (0, 0))

        
        if gs.get("screen_flash"):
            fl = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            fl.fill((255, 200, 100, 80))
            screen.blit(fl, (0, 0))

        if gs.get("show_distractor"):
            draw_distractor(screen)

        if gs.get("show_alert"):
            t = big_font.render("!! THREAT DETECTED !!", True, (255, 60, 60))
            screen.blit(t, (SCREEN_W//2 - t.get_width()//2, SCREEN_H//2 - 20))

        if gs.get("meltdown"):
            t = big_font.render("SENSORY OVERLOAD — press R to recover", True, (255,120,50))
            screen.blit(t, (SCREEN_W//2 - t.get_width()//2, SCREEN_H//2 - 20))

        if console:
            draw_console(screen, nt, stamina, gs, font)
        else:
            draw_hud(screen, gs, stamina, font)

        pygame.display.flip()


if __name__ == "__main__":
    main()
'''

    @staticmethod
    def _adapter_arcade(game, info):
        nd = _nt_dict(game.condition)
        return f'''"""{game.title} — Arcade scaffold.

Condition: {game.condition.upper().replace('_',' ')} | Genre: {game.genre.upper()} | Engine: Arcade
Generated by Mechanistic Empathy Engine v{__version__}
Install engine: {info['install']}
"""
__version__ = "{__version__}"

import arcade

SCREEN_W, SCREEN_H = 800, 600
TITLE = "{game.title}"
NT = {nd}


def nt_to_params(nt):
    return dict(
        move_speed  = 250 * nt.get("norepinephrine", 0.8),
        jump_speed  = 500 * max(nt.get("norepinephrine", 0.8), 0.3),
        energy_drain= 0.8 / max(nt.get("serotonin", 0.5), 0.01),
        saturation  = min(1.0, nt.get("serotonin", 0.5) + 0.1),
    )


class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_W, SCREEN_H, TITLE)
        arcade.set_background_color(arcade.color.DARK_MIDNIGHT_BLUE)

    def setup(self):
        self.player   = arcade.SpriteSolidColor(32, 64, arcade.color.LIGHT_BLUE)
        self.player.center_x, self.player.center_y = SCREEN_W//2, 100
        self.player.change_y = 0
        self.energy, self.console = 1.0, False
        self.nt = dict(NT)
        self.platform = arcade.SpriteSolidColor(SCREEN_W, 20, arcade.color.DIM_GRAY)
        self.platform.center_x, self.platform.center_y = SCREEN_W//2, 20
        self.all_sprites = arcade.SpriteList()
        self.all_sprites.extend([self.player, self.platform])

    def on_update(self, dt):
        p = nt_to_params(self.nt)
        self.player.change_y -= 900 * dt
        self.player.update()
        if self.player.bottom <= 30:
            self.player.bottom = 30; self.player.change_y = 0
        self.energy = max(0.0, self.energy - p["energy_drain"] * dt * 0.01)
        self.player.left  = max(0, self.player.left)
        self.player.right = min(SCREEN_W, self.player.right)

    def on_draw(self):
        self.clear()
        self.all_sprites.draw()
        arcade.draw_text(f"Vital Energy: {{self.energy:.0%}}  F1=Console  M=Medication",
                         10, SCREEN_H-25, arcade.color.WHITE, 13)
        arcade.draw_lrtb_rectangle_filled(10, 10+int(200*self.energy),
                                          SCREEN_H-30, SCREEN_H-46,
                                          (int(255*(1-self.energy)), int(200*self.energy), 60))
        if self.console:
            arcade.draw_lrtb_rectangle_filled(0, SCREEN_W, SCREEN_H, 0, (10,10,30,200))
            y = SCREEN_H-40
            arcade.draw_text("META-CONSOLE (F1 close)", 20, y, arcade.color.CYAN, 14); y-=24
            for name, val in self.nt.items():
                arcade.draw_lrtb_rectangle_filled(20, 20+int(val*100), y+12, y, (80,200,120))
                arcade.draw_text(f"{{name:<20}} {{val:.3f}}", 130, y, arcade.color.WHITE, 12)
                y -= 20

    def on_key_press(self, key, mod):
        if key == arcade.key.F1: self.console = not self.console
        if key == arcade.key.M:
            self.nt["serotonin"]      = min(2.0, self.nt.get("serotonin",0)+0.3)
            self.nt["dopamine"]       = min(2.0, self.nt.get("dopamine",0)+0.2)
            self.nt["norepinephrine"] = min(2.0, self.nt.get("norepinephrine",0)+0.2)
        p = nt_to_params(self.nt)
        if key == arcade.key.LEFT:  self.player.change_x = -p["move_speed"]
        if key == arcade.key.RIGHT: self.player.change_x =  p["move_speed"]
        if key == arcade.key.SPACE and self.player.bottom <= 32:
            self.player.change_y = p["jump_speed"]

    def on_key_release(self, key, mod):
        if key in (arcade.key.LEFT, arcade.key.RIGHT): self.player.change_x = 0


def main():
    w = GameWindow(); w.setup(); arcade.run()

if __name__ == "__main__":
    main()
'''

    @staticmethod
    def _adapter_pygame_zero(game, info):
        nd = _nt_dict(game.condition)
        return f'''"""{game.title} — Pygame Zero scaffold.

Run with: pgzrun {game.condition}_{game.genre}_pgzero.py
Install engine: {info['install']}
Generated by Mechanistic Empathy Engine v{__version__}
"""
__version__ = "{__version__}"

WIDTH, HEIGHT = 800, 600
TITLE = "{game.title}"

nt    = {nd}
state = dict(energy=1.0, x=400.0, y=500.0, vy=0.0, on_ground=True, console=False)


def params():
    return dict(
        speed = int(200 * nt.get("norepinephrine", 0.8)),
        drain = 0.8 / max(nt.get("serotonin", 0.5), 0.01),
    )

def update():
    p = params()
    if keyboard.left:  state["x"] -= p["speed"] * 0.016
    if keyboard.right: state["x"] += p["speed"] * 0.016
    if keyboard.space and state["on_ground"]:
        state["vy"] = -14; state["on_ground"] = False
    state["vy"] += 0.5; state["y"] += state["vy"]
    if state["y"] >= HEIGHT - 60:
        state["y"] = HEIGHT-60; state["vy"] = 0; state["on_ground"] = True
    state["energy"] = max(0.0, state["energy"] - p["drain"] * 0.0002)

def draw():
    screen.clear(); screen.fill((20,20,30))
    screen.draw.filled_rect(Rect(int(state["x"])-16, int(state["y"])-32, 32, 64), (100,180,255))
    screen.draw.filled_rect(Rect(0, HEIGHT-30, WIDTH, 30), (60,60,80))
    bw = int(200 * state["energy"])
    screen.draw.filled_rect(Rect(10,10,200,16), (60,60,60))
    screen.draw.filled_rect(Rect(10,10,bw,16),
                             (int(255*(1-state["energy"])), int(200*state["energy"]), 60))
    screen.draw.text("Vital Energy  F1=Console  M=Med", (10,28), color=(220,220,220), fontsize=13)
    if state["console"]:
        y = 55
        for k,v in nt.items():
            screen.draw.text(f"{{k}}: {{v:.3f}}", (20,y), color=(100,220,255), fontsize=12); y+=16

def on_key_down(key):
    if key == keys.F1: state["console"] = not state["console"]
    if key == keys.M:
        nt["serotonin"]  = min(2.0, nt.get("serotonin",0)+0.3)
        nt["dopamine"]   = min(2.0, nt.get("dopamine",0)+0.2)
'''

    @staticmethod
    def _adapter_pyglet(game, info):
        nd = _nt_dict(game.condition)
        return f'''"""{game.title} — Pyglet scaffold.

Condition: {game.condition.upper().replace('_',' ')} | Genre: {game.genre.upper()} | Engine: Pyglet
Install engine: {info['install']}
Generated by Mechanistic Empathy Engine v{__version__}
"""
__version__ = "{__version__}"

import pyglet
from pyglet.window import key as Key
from pyglet import shapes

window = pyglet.window.Window(800, 600, caption="{game.title}")
batch  = pyglet.graphics.Batch()
NT     = {nd}
state  = dict(x=400.0, y=80.0, vx=0.0, vy=0.0, energy=1.0, on_ground=True, console=False)
keys_held = set()
player_shape = shapes.Rectangle(384, 48, 32, 64, color=(100,180,255), batch=batch)
ground_shape = shapes.Rectangle(0, 0, 800, 30, color=(60,60,80), batch=batch)
nt = dict(NT)


def params():
    return dict(
        speed = 200 * nt.get("norepinephrine", 0.8),
        drain = 0.8 / max(nt.get("serotonin", 0.5), 0.01),
        jump  = 420 * nt.get("norepinephrine", 0.8),
    )

@window.event
def on_key_press(symbol, mod):
    keys_held.add(symbol)
    if symbol == Key.F1: state["console"] = not state["console"]
    if symbol == Key.M:
        nt["serotonin"]      = min(2.0, nt.get("serotonin",0)+0.3)
        nt["dopamine"]       = min(2.0, nt.get("dopamine",0)+0.2)
        nt["norepinephrine"] = min(2.0, nt.get("norepinephrine",0)+0.2)
    if symbol == Key.SPACE and state["on_ground"]:
        p = params(); state["vy"] = p["jump"]; state["on_ground"] = False

@window.event
def on_key_release(symbol, mod):
    keys_held.discard(symbol)

def update(dt):
    p = params()
    state["vx"] = (-p["speed"] if Key.LEFT in keys_held else
                    p["speed"] if Key.RIGHT in keys_held else 0)
    state["vy"] -= 900*dt; state["x"] += state["vx"]*dt; state["y"] += state["vy"]*dt
    if state["y"] <= 30: state["y"]=30; state["vy"]=0; state["on_ground"]=True
    state["x"] = max(0, min(768, state["x"]))
    state["energy"] = max(0.0, state["energy"] - p["drain"]*dt*0.01)
    player_shape.x, player_shape.y = int(state["x"]), int(state["y"])

@window.event
def on_draw():
    window.clear(); batch.draw()
    pyglet.text.Label(f"Energy:{{state['energy']:.0%}} F1=Console M=Med",
                      x=10, y=580, font_size=12, color=(220,220,220,255)).draw()
    if state["console"]:
        y = 550
        for k,v in nt.items():
            pyglet.text.Label(f"{{k}}: {{v:.3f}}", x=10, y=y,
                              font_size=11, color=(100,220,255,255)).draw()
            y -= 17

pyglet.clock.schedule_interval(update, 1/60.0)
pyglet.app.run()
'''

    @staticmethod
    def _adapter_ursina(game, info):
        nd = _nt_dict(game.condition)
        return f'''"""{game.title} — Ursina (3D) scaffold.

Condition: {game.condition.upper().replace('_',' ')} | Genre: {game.genre.upper()} | Engine: Ursina
Install engine: {info['install']}
Generated by Mechanistic Empathy Engine v{__version__}
"""
__version__ = "{__version__}"

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()
window.title = "{game.title}"
nt = {nd}

ground = Entity(model="plane", scale=(30,1,30), color=color.dark_gray, collider="box")
player = FirstPersonController(y=2)
energy_text = Text("Vital Energy: 100%", origin=(-0.85, 0.45), scale=1.5, color=color.white)
energy = [1.0]

def input(key):
    if key == "f1":
        for k,v in nt.items(): print(f"  {{k}}: {{v:.3f}}")
    if key == "m":
        nt["serotonin"]      = min(2.0, nt.get("serotonin",0)+0.3)
        nt["dopamine"]       = min(2.0, nt.get("dopamine",0)+0.2)
        nt["norepinephrine"] = min(2.0, nt.get("norepinephrine",0)+0.2)
        print("[Medication applied]")

def update():
    drain = 0.8 / max(nt.get("serotonin", 0.5), 0.01)
    energy[0] = max(0.0, energy[0] - drain * time.dt * 0.01)
    energy_text.text = f"Vital Energy: {{energy[0]:.0%}}"
    player.speed = 5 * nt.get("norepinephrine", 0.8)
    sat = nt.get("serotonin", 0.5)
    ground.color = color.hsv(200, sat*0.4, 0.3)

app.run()
'''

    @staticmethod
    def _adapter_panda3d(game, info):
        nd = _nt_dict(game.condition)
        return f'''"""{game.title} — Panda3D scaffold.

Condition: {game.condition.upper().replace('_',' ')} | Genre: {game.genre.upper()} | Engine: Panda3D
Install engine: {info['install']}
Generated by Mechanistic Empathy Engine v{__version__}
"""
__version__ = "{__version__}"

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import TextNode, Fog
import sys

class EmpathyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.setBackgroundColor(0.08, 0.08, 0.12, 1)
        self.nt = {nd}
        self.energy = 1.0

        # Ground
        from panda3d.core import CardMaker
        cm = CardMaker("ground"); cm.setFrame(-20,20,-20,20)
        self.ground = self.render.attachNewNode(cm.generate())
        self.ground.setP(-90); self.ground.setColor(0.2,0.2,0.3,1)

        # HUD text
        tn = TextNode("hud")
        tn.setText("Vital Energy: 100%  F1=Console  M=Medication")
        tn.setTextColor(0.9,0.9,0.9,1)
        self.hud = self.aspect2d.attachNewNode(tn)
        self.hud.setPos(-1.3,0,0.9); self.hud.setScale(0.055)

        self.accept("f1", self.toggle_console)
        self.accept("m",  self.apply_medication)
        self.accept("escape", sys.exit)
        self.taskMgr.add(self.update_task, "Update")

    def update_task(self, task):
        dt = globalClock.getDt()
        drain = 0.8 / max(self.nt.get("serotonin",0.5), 0.01)
        self.energy = max(0.0, self.energy - drain*dt*0.01)
        self.hud.node().setText(
            f"Energy: {{self.energy:.0%}}  serotonin={{self.nt.get('serotonin',0):.2f}}")
        fog = Fog("fog"); fog.setColor(0.05,0.05,0.08)
        fog.setLinearRange(10+30*self.nt.get("serotonin",0.5), 80)
        self.render.setFog(fog)
        return Task.cont

    def toggle_console(self):
        for k,v in self.nt.items(): print(f"  {{k}}: {{v:.3f}}")

    def apply_medication(self):
        self.nt["serotonin"]      = min(2.0, self.nt.get("serotonin",0)+0.3)
        self.nt["dopamine"]       = min(2.0, self.nt.get("dopamine",0)+0.2)
        self.nt["norepinephrine"] = min(2.0, self.nt.get("norepinephrine",0)+0.2)
        print("[Medication applied]")

EmpathyGame().run()
'''

    @staticmethod
    def _adapter_cocos2d(game, info):
        nd = _nt_dict(game.condition)
        return f'''"""{game.title} — Cocos2d scaffold.

Condition: {game.condition.upper().replace('_',' ')} | Genre: {game.genre.upper()} | Engine: Cocos2d
Install engine: {info['install']}
Generated by Mechanistic Empathy Engine v{__version__}
"""
__version__ = "{__version__}"

import cocos
from cocos.director import director
from cocos import layer, scene, text
from pyglet.window import key as Key

director.init(width=800, height=600, caption="{game.title}")
NT = {nd}

class GameLayer(layer.Layer):
    is_event_handler = True
    def __init__(self):
        super().__init__()
        self.nt, self.energy = dict(NT), 1.0
        self.lbl = text.Label("Energy: 100%  F1=Console  M=Medication",
                               font_size=12, color=(220,220,220,255))
        self.lbl.position = (10, 580); self.add(self.lbl)
        self.player = text.Label("♟", font_size=40, color=(100,180,255,255))
        self.player.position = (400, 60); self.add(self.player)
        self.schedule(self.update)

    def update(self, dt):
        drain = 0.8 / max(self.nt.get("serotonin",0.5), 0.01)
        self.energy = max(0.0, self.energy - drain*dt*0.01)
        self.lbl.element.text = f"Energy:{{self.energy:.0%}}  serotonin={{self.nt.get('serotonin',0):.2f}}"

    def on_key_press(self, symbol, mod):
        speed = 200 * self.nt.get("norepinephrine", 0.8)
        if symbol == Key.LEFT:  self.player.x = max(20, self.player.x - speed*0.016)
        if symbol == Key.RIGHT: self.player.x = min(780, self.player.x + speed*0.016)
        if symbol == Key.F1:
            for k,v in self.nt.items(): print(f"  {{k}}: {{v:.3f}}")
        if symbol == Key.M:
            self.nt["serotonin"] = min(2.0, self.nt.get("serotonin",0)+0.3)
            print("[Medication applied]")

director.run(scene.Scene(GameLayer()))
'''

    @staticmethod
    def _adapter_kivy(game, info):
        nd = _nt_dict(game.condition)
        return f'''"""{game.title} — Kivy scaffold.

Condition: {game.condition.upper().replace('_',' ')} | Genre: {game.genre.upper()} | Engine: Kivy
Install engine: {info['install']}
Generated by Mechanistic Empathy Engine v{__version__}
"""
__version__ = "{__version__}"

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock

NT = {nd}

class GameWidget(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.nt, self.energy, self.px = dict(NT), 1.0, 400
        self.hud = Label(text="Vital Energy: 100%", pos=(10,560), size=(300,30))
        self.add_widget(self.hud)
        Clock.schedule_interval(self.update, 1/60.0)

    def update(self, dt):
        drain = 0.8 / max(self.nt.get("serotonin",0.5), 0.01)
        self.energy = max(0.0, self.energy - drain*dt*0.01)
        self.hud.text = f"Energy: {{self.energy:.0%}}"
        self.canvas.clear()
        with self.canvas:
            Color(0.08,0.08,0.12); Rectangle(pos=(0,0), size=(800,600))
            Color(0.25,0.25,0.35); Rectangle(pos=(0,0), size=(800,30))
            r = 1.0-self.energy; g = self.energy*0.8
            Color(r,g,0.2); Rectangle(pos=(10,570), size=(int(200*self.energy),16))
            sat = self.nt.get("serotonin", 0.5)
            Color(sat*0.4, sat*0.7, 1.0); Rectangle(pos=(self.px-16, 30), size=(32,64))

    def on_touch_down(self, touch):
        if touch.x > 400: self.px = min(780, self.px+30)
        else: self.px = max(20, self.px-30)

class EmpathyApp(App):
    def build(self): return GameWidget()

if __name__ == "__main__": EmpathyApp().run()
'''

    @staticmethod
    def _adapter_pyopengl(game, info):
        nd = _nt_dict(game.condition)
        return f'''"""{game.title} — PyOpenGL scaffold.

Condition: {game.condition.upper().replace('_',' ')} | Genre: {game.genre.upper()} | Engine: PyOpenGL
Install engine: {info['install']}
Generated by Mechanistic Empathy Engine v{__version__}
"""
__version__ = "{__version__}"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

NT = {nd}
nt = dict(NT)
energy = [1.0]


def init():
    glClearColor(0.08,0.08,0.12,1.0)
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    gluOrtho2D(0,800,0,600)


def rect(x,y,w,h,r,g,b,a=1.0):
    glColor4f(r,g,b,a); glBegin(GL_QUADS)
    glVertex2f(x,y); glVertex2f(x+w,y); glVertex2f(x+w,y+h); glVertex2f(x,y+h)
    glEnd()


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    sat = nt.get("serotonin", 0.5)
    rect(0,0,800,600, 0.08*sat,0.08*sat,0.12+sat*0.1)   # desaturating bg
    rect(0,0,800,30,  0.25,0.25,0.35)                    # ground
    r,g = 1-nt.get("serotonin",0.5), nt.get("dopamine",0.5)*0.8
    rect(384,48,32,64, r*0.4,g,sat*0.8+0.2)              # player
    rect(10,570,int(200*energy[0]),16, 1-energy[0],energy[0]*0.8,0.2)  # energy bar
    glutSwapBuffers()


def timer_cb(v):
    drain = 0.8 / max(nt.get("serotonin",0.5), 0.01)
    energy[0] = max(0.0, energy[0] - drain*0.016*0.01)
    glutPostRedisplay(); glutTimerFunc(16, timer_cb, 0)


def keyboard(key, x, y):
    if key == b"m":
        nt["serotonin"] = min(2.0, nt.get("serotonin",0)+0.3)
        nt["dopamine"]  = min(2.0, nt.get("dopamine",0)+0.2)
        print("[Medication applied] NT levels raised; observe colour shift.")
    if key == b"\\x1b": import sys; sys.exit(0)


glutInit(); glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGB)
glutInitWindowSize(800,600); glutCreateWindow(b"{game.title}")
init()
glutDisplayFunc(display); glutKeyboardFunc(keyboard)
glutTimerFunc(16, timer_cb, 0); glutMainLoop()
'''

    @staticmethod
    def _adapter_generic(game, info):
        return f'''"""{game.title} — {info['label']} scaffold.

Condition: {game.condition.upper().replace('_',' ')} | Genre: {game.genre.upper()} | Engine: {info['label']}
Install engine: {info['install']}
Generated by Mechanistic Empathy Engine v{__version__}
"""
__version__ = "{__version__}"

{info['import_snippet']}

NT = {_nt_dict(game.condition)}

def nt_to_params(nt):
    return dict(
        move_speed  = 200 * nt.get("norepinephrine", 0.8),
        energy_drain= 0.8 / max(nt.get("serotonin", 0.5), 0.01),
        reward_mult = nt.get("dopamine", 0.5),
    )

# TODO: Implement game loop, applying nt_to_params(NT) each frame.
# See the *_pseudocode.py file for the full engine-agnostic implementation.
'''


# ══════════════════════════════════════════════════════════════════════════════
# MECHANIC GENERATORS
# ══════════════════════════════════════════════════════════════════════════════

class StaminaSystemGenerator:
    """
    Derives a biologically-grounded regenerative stamina system from a
    condition's neurotransmitter profile.

    Design rules
    ────────────
    Serotonin is the primary driver of stamina regeneration because:
      • It regulates sleep quality (raphe → hypothalamus)
      • It modulates cortisol suppression (HPA axis feedback)
      • It underpins motivational renewal (reward salience at rest)

    Supporting NTs modify the formula:
      • Norepinephrine (high) → faster drain, reduced regen cap
      • Dopamine (high)       → regen overshoots cap (mania)
      • Cortisol (high)       → hard ceiling on recoverable stamina
      • GABA (low)            → rest feels shallow; regen rate halved
    """

    # Healthy reference values (NT level = 1.0 for all)
    _BASE_REGEN  = 0.08   # stamina/s at full serotonin
    _BASE_DRAIN  = 0.01   # stamina/s passive drain at rest (healthy)
    _BASE_CAP    = 1.00   # fraction of max_stamina recoverable without sleep

    @classmethod
    def generate(cls, condition: str) -> StaminaSystem:
        profile = ConditionLibrary.get(condition)
        if not profile:
            return cls._default()

        # Pull relevant NT baselines (default to 1.0 if absent)
        nt_map = {nt.name.lower().replace(" ","_"): nt.baseline
                  for nt in profile.neurotransmitters
                  if isinstance(nt.baseline, float)}

        serotonin      = nt_map.get("serotonin",      1.0)
        norepinephrine = nt_map.get("norepinephrine",  1.0)
        dopamine       = nt_map.get("dopamine",        1.0)
        cortisol       = nt_map.get("cortisol",        1.0)
        gaba           = nt_map.get("gaba",            1.0)
        substance_p    = nt_map.get("substance_p",     1.0)

        # ── max_stamina ───────────────────────────────────────────────────────
        # Chronic pain / high substance P reduces maximum capacity
        max_stamina = round(max(0.3, min(1.0,
            1.0
            - 0.15 * (1.0 - serotonin)        # low 5-HT lowers ceiling
            - 0.10 * max(0, cortisol - 1.0)   # excess cortisol erodes max
            - 0.20 * max(0, substance_p - 1.0) # pain burden
        )), 3)

        # ── regen_rate ────────────────────────────────────────────────────────
        # Serotonin is the primary multiplier; GABA gates whether rest "lands"
        serotonin_weight = round(serotonin / 1.0, 3)
        gaba_gate        = 0.5 + 0.5 * min(gaba, 1.0)   # 0.5–1.0
        regen_rate = round(max(0.002,
            cls._BASE_REGEN
            * serotonin_weight
            * gaba_gate
            * (1.0 / max(cortisol, 0.5))       # cortisol suppresses regen
        ), 4)

        # ── drain_rate ────────────────────────────────────────────────────────
        # High norepinephrine or substance P accelerates depletion
        drain_rate = round(min(0.20,
            cls._BASE_DRAIN
            + 0.015 * max(0, norepinephrine - 1.0)   # hyperarousal burns stamina
            + 0.020 * max(0, substance_p - 1.0)       # pain burns stamina
            + 0.005 * max(0, cortisol - 1.0)          # chronic stress drains
        ), 4)

        # ── regen_cap ─────────────────────────────────────────────────────────
        # How far stamina can recover without a proper sleep checkpoint
        # Anxiety/high cortisol: can never fully rest in a "safe" zone
        regen_cap = round(max(0.30, min(1.0,
            cls._BASE_CAP
            - 0.30 * max(0, cortisol - 1.0)
            - 0.15 * (1.0 - gaba)
            - 0.10 * (1.0 - serotonin)
        )), 3)

        # ── overshoot_penalty (mania) ─────────────────────────────────────────
        # Excess dopamine: stamina feels infinite but crashes past the ceiling
        overshoot = (dopamine > 1.5)

        # ── rest_threshold ────────────────────────────────────────────────────
        rest_threshold = round(max(0.10, 0.25 * (1.0 - serotonin * 0.5)), 3)

        # ── human-readable formula ────────────────────────────────────────────
        formula = (
            f"stamina += ({regen_rate:.4f} * serotonin_ratio - {drain_rate:.4f}) * dt\n"
            f"  where serotonin_ratio = NT['serotonin'] / 1.0  (healthy baseline)\n"
            f"  regen blocked above cap={regen_cap:.2f} unless sleep checkpoint reached\n"
            f"  max_stamina={max_stamina:.2f}  rest_threshold={rest_threshold:.2f}"
        )
        if overshoot:
            formula += "\n  MANIA: stamina decays if > max_stamina (overshoot penalty active)"

        return StaminaSystem(
            max_stamina      = max_stamina,
            regen_rate       = regen_rate,
            drain_rate       = drain_rate,
            regen_cap        = regen_cap,
            serotonin_weight = serotonin_weight,
            formula          = formula,
            rest_threshold   = rest_threshold,
            overshoot_penalty= overshoot,
        )

    @classmethod
    def _default(cls) -> StaminaSystem:
        return StaminaSystem(
            max_stamina=1.0, regen_rate=0.08, drain_rate=0.01,
            regen_cap=1.0,   serotonin_weight=1.0,
            formula="stamina += (0.08 * serotonin_ratio - 0.01) * dt",
            rest_threshold=0.25, overshoot_penalty=False,
        )

    @staticmethod
    def tick(stamina: float, nt: dict, sys: StaminaSystem, dt: float,
             is_resting: bool = False, is_sleeping: bool = False) -> float:
        """
        Advance the stamina value by one game tick.

        Call this every frame from your game loop::

            stamina = StaminaSystemGenerator.tick(stamina, NT, game.stamina, dt,
                                                  is_resting=player.is_idle)

        Parameters
        ----------
        stamina     Current stamina (0.0–max_stamina).
        nt          Live NT dict, e.g. {"serotonin": 0.4, ...}.
        sys         StaminaSystem instance from generate_game().stamina.
        dt          Delta time in seconds.
        is_resting  True when player is idle / in safe zone.
        is_sleeping True when player has reached a sleep checkpoint.
        """
        serotonin_ratio = nt.get("serotonin", sys.serotonin_weight) / 1.0
        cortisol        = nt.get("cortisol", 1.0)
        gaba            = nt.get("gaba", 1.0)

        # Recompute live regen (NT levels can change via meta-console / meds)
        gaba_gate   = 0.5 + 0.5 * min(gaba, 1.0)
        live_regen  = sys.regen_rate * serotonin_ratio * gaba_gate * (1.0 / max(cortisol, 0.5))
        live_drain  = sys.drain_rate

        if is_sleeping:
            cap = sys.max_stamina        # sleep = full recovery possible
        elif is_resting:
            cap = sys.regen_cap * sys.max_stamina   # rest = partial recovery
        else:
            cap = stamina                # active = no regen, just drain

        if stamina < cap:
            stamina += live_regen * dt
            stamina  = min(stamina, cap)
        else:
            stamina -= live_drain * dt

        # Mania overshoot: excess dopamine lets stamina spike past max then crash
        if sys.overshoot_penalty:
            dopamine = nt.get("dopamine", 1.0)
            if dopamine > 1.5 and stamina > sys.max_stamina:
                stamina -= (dopamine - 1.5) * 0.05 * dt

        return max(0.0, min(sys.max_stamina, stamina))


class MechanicGenerator:
    @classmethod
    def generate(cls, condition, genre):
        base     = cls._nt_mechanics(condition)
        specific = getattr(cls, f"_{condition}_{genre}", lambda: cls._generic(condition, genre))()
        return base + specific

    @staticmethod
    def _nt_mechanics(condition):
        p = ConditionLibrary.get(condition)
        if not p: return []
        out = []
        for nt in p.neurotransmitters:
            bl = nt.baseline if isinstance(nt.baseline, float) else 0.5
            d  = "depleted" if bl < 0.8 else "excess"
            out.append(GameMechanic(
                f"{nt.name} Meter",
                f"Visible gauge ({d}). {nt.game_effect}.",
                f"NT: {nt.name} ({nt.role})",
                f"Float 0-2. Start {bl:.2f}. Update each tick.",
                abs(bl-1.0),
            ))

        # ── Regenerative Stamina (serotonin-driven) ───────────────────────────
        stamina_sys = StaminaSystemGenerator.generate(condition)
        intensity   = round(1.0 - stamina_sys.regen_rate / 0.08, 2)  # 0=healthy, 1=severest
        out.append(GameMechanic(
            name="Regenerative Stamina",
            description=(
                f"Stamina regenerates at {stamina_sys.regen_rate:.4f}/s (serotonin-scaled). "
                f"Cap without sleep: {stamina_sys.regen_cap:.0%} of max={stamina_sys.max_stamina:.2f}. "
                f"Drain: {stamina_sys.drain_rate:.4f}/s. "
                + ("Mania overshoot active — excess stamina decays. " if stamina_sys.overshoot_penalty else "")
                + f"Rest threshold: {stamina_sys.rest_threshold:.0%}."
            ),
            mapped_from=(
                "Serotonin → regen rate (raphe nuclei → HPA axis → sleep quality). "
                "Cortisol → regen cap. GABA → regen gate. Substance P → drain rate."
            ),
            implementation_hint=(
                f"Each frame: stamina = StaminaSystemGenerator.tick(stamina, NT, game.stamina, dt, is_resting). "
                f"Formula: {stamina_sys.formula.split(chr(10))[0]}"
            ),
            intensity=max(0.0, min(1.0, intensity)),
        ))
        return out

    @staticmethod
    def _generic(condition, genre):
        p = ConditionLibrary.get(condition)
        if not p: return []
        return [GameMechanic("Symptom Overlay",
            f"Core {genre} loop disrupted by: {'; '.join(p.primary_symptoms[:3])}.",
            "Primary symptom cluster", "Apply modifier to core loop every N frames.", 0.7)]

    # ── depression ────────────────────────────────────────────────────────────
    @staticmethod
    def _depression_platformer(): return [
        GameMechanic("Vital Energy Bar","Drains 0.8u/s regardless of action. Cannot pause.","Chronic fatigue","HUD bar. On zero: speed x0.3, jump disabled.",0.9),
        GameMechanic("Colour Desaturation","Saturation = energy/max. At zero -> greyscale.","Anhedonia","Post-process shader: saturation lerp(0,1,energy).",0.8),
        GameMechanic("Heavy Movement","Jump -40%, speed x0.6, input latency +200ms.","Psychomotor retardation","velocity *= 0.6; input_queue delay 200ms.",0.85),
        GameMechanic("Reward Blunting","Items give 50% XP; SFX at 40% volume.","Anhedonia","On pickup: score*0.5, sfx_vol*0.4, particles/2.",0.75),
        GameMechanic("Sleep Checkpoint","Must reach bed to save. 30% insomnia chance.","Sleep disruption","SavePoint: random()<0.3 -> insomnia QTE.",0.6),
    ]
    @staticmethod
    def _depression_narrative(): return [
        GameMechanic("Inner Monologue","Second text stream overlays dialogue at 40% opacity.","Cognitive distortions","Render second font layer over NPC speech.",0.9),
        GameMechanic("Decision Paralysis","Choices expire in 4s; default = say nothing.","Avolition","Timer per choice node; on expire -> null branch.",0.8),
        GameMechanic("Memory Fog","Past scenes shown at half resolution.","Concentration difficulty","old_scenes.set_sharpness(0.5).",0.65),
    ]
    @staticmethod
    def _depression_survival(): return [
        GameMechanic("Resource Inertia","Gathering actions take 2x longer.","Fatigue and motivation deficit","action_time_multiplier = 2.0.",0.8),
        GameMechanic("Hope Meter","Secondary bar that affects all action speeds.","Future orientation impairment","hope_level drives max_energy cap.",0.7),
    ]

    # ── adhd ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _adhd_puzzle(): return [
        GameMechanic("Shuffling Priority Queue","Task list re-orders randomly every 30s.","Time blindness","tasks.shuffle() on timer.",0.9),
        GameMechanic("Distractor Spawner","Shiny objects at edges; clicking pauses progress 5s.","Salience dysregulation","Spawn Distractor every 8s at random edge.",0.85),
        GameMechanic("Time Perception Warp","On-screen clock runs 3x real time.","Time blindness","game_clock_speed=3.0; display game time.",0.8),
        GameMechanic("Focus Token Economy","5 tokens; sustained tasks cost 1; regen 1/120s.","Limited executive resources","FocusToken counter; deduct on multi-step ops.",0.75),
        GameMechanic("Medication Mode","Item: clock->1x, distractors paused 45s, queue locked.","Stimulant normalises executive function","PowerUp 45s duration.",0.9),
    ]
    @staticmethod
    def _adhd_platformer(): return [
        GameMechanic("Hyperfocus Zone","Random 20s window: one platform type magnetically draws player.","Hyperfocus","Pick random tile_type; apply attraction force.",0.7),
        GameMechanic("Impulsivity Jump","10% chance: second unintended jump fires after 100ms.","Impulse control deficit","random()<0.1 -> queue second jump.",0.65),
    ]
    @staticmethod
    def _adhd_rts(): return [
        GameMechanic("Unit Insubordination","10% chance each order is ignored.","Impaired executive output","random()<0.1 -> unit ignores command.",0.8),
        GameMechanic("Resource Scatter","Dropped resources randomly move to adjacent cell.","Working memory / tracking deficit","On drop: 30% chance teleport to adjacent cell.",0.7),
    ]

    # ── autism ────────────────────────────────────────────────────────────────
    @staticmethod
    def _autism_social_sim(): return [
        GameMechanic("Simultaneous Audio","All NPCs speak at once at equal volume.","Auditory filtering deficit","Play all NPC tracks simultaneously.",0.95),
        GameMechanic("Eye Contact Spike","Eye contact -> screen brightness +300% for 0.5s.","Eye contact aversion","brightness_tween(300%, 0.5s) on EyeContact.",0.85),
        GameMechanic("Masking Meter","Second bar. NT-appropriate choices drain it. Zero -> meltdown.","Masking fatigue","Second bar; deduct on NT-script choices.",0.9),
        GameMechanic("Literal Language","Sarcasm shows literal first; decode token needed.","Pragmatic language differences","Tag [figurative] lines; show literal; button=decode.",0.75),
        GameMechanic("Routine Break Penalty","Schedule change -> disruption overlay + 3s control loss.","Need for predictability","DisruptionEvent on schedule_change; breathing QTE.",0.8),
    ]
    @staticmethod
    def _autism_survival(): return [
        GameMechanic("Sensory Overload Meter","Each stimulus adds to Overload bar. Max -> shutdown 10s.","Sensory hypersensitivity","Overload += intensity; on max: input disabled.",0.95),
        GameMechanic("Special Interest Yield","One resource type gives 3x yield.","Special interests as strength","tag SpecialInterest; yield_multiplier=3.",0.6),
    ]

    # ── anxiety ───────────────────────────────────────────────────────────────
    @staticmethod
    def _anxiety_stealth(): return [
        GameMechanic("False Positive Alerts","Ambient objects trigger threat alarm 25% chance/15s.","Amygdala hyperactivity","Every 15s: 25% FalseAlarm. Dispels after 3s.",0.9),
        GameMechanic("No Full Rest","Safe zone restores stamina to 70% max only.","Chronic cortisol elevation","safe_zone_regen_cap = 0.7 * max_stamina.",0.85),
        GameMechanic("Worry Spiral","Idle >5s -> thought-bubble overlays screen edge.","Ruminative worry","Idle timer -> WorryOverlay sprites. Movement clears.",0.8),
        GameMechanic("Avoidance Trap","Shortcuts avoid hard zones but give no XP.","Avoidance maintains anxiety","AvoidancePath dead-ends; skill gate needs XP.",0.75),
    ]

    # ── ptsd ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _ptsd_narrative(): return [
        GameMechanic("Flashback Intrusion","Trigger stimuli -> past-scene overlay 3-8s, input disabled.","Re-experiencing","Tag TriggerStimuli; overlay PastScene@80% opacity.",0.95),
        GameMechanic("Avoidance Map Lock","Trauma zones greyed; dread meter spikes on approach.","Avoidance","ZoneFlag=avoided; dread+=5/frame; therapy unlocks.",0.85),
        GameMechanic("Hypervigilance HUD","Phantom movement indicators at random edges every 5-20s.","Hyperarousal","Spawn phantom MovementIndicators randomly.",0.8),
        GameMechanic("Emotional Numbing","NPC expressions at 50% opacity; choices descriptive-only.","Emotional numbing","NPC emotion sprites alpha=0.5.",0.7),
    ]

    # ── schizophrenia ─────────────────────────────────────────────────────────
    @staticmethod
    def _schizophrenia_narrative(): return [
        GameMechanic("Salience Scrambler","Random objects glow with significance every 20s.","Aberrant salience","SignificanceHalo on random_object every 20s.",0.95),
        GameMechanic("Internal Voice Sub","5% of NPC lines replaced by internal voice.","Auditory hallucinations","random()<0.05 -> swap to InternalVoice; no indicator.",0.9),
        GameMechanic("WM Limit","Active goals capped at 2; oldest auto-clears.","Working memory impairment","goals[] max=2; FIFO eviction.",0.8),
        GameMechanic("Antipsychotic Toggle","Med: halluc rate /10, halos clear, WM->4, speed-20%.","D2 blockade reduces positive symptoms","MedPowerup 120s.",0.85),
    ]

    # ── bipolar ───────────────────────────────────────────────────────────────
    @staticmethod
    def _bipolar_platformer(): return [
        GameMechanic("Mood Cycle","MANIA(60s speed x3)->EUTHYMIA(30s)->DEPRESSION(90s drain)->repeat.","Bipolar cycling","MoodState machine; player cannot choose phase.",0.95),
        GameMechanic("Mania Overspend","Auto-purchase every 5s during mania until funds <10.","Mania impulsivity","auto_purchase_loop() on MANIA entry.",0.85),
        GameMechanic("Grandiosity Platform","During mania, unreachable platforms look solid but lack collision.","Grandiosity","MANIA: render platforms solid; collision absent.",0.8),
        GameMechanic("Lithium Stabiliser","Med: mania->x1.3, depression->x0.7, phase length x2.","Lithium reduces amplitude","While medicated: phase multipliers applied.",0.9),
    ]

    # ── chronic pain ──────────────────────────────────────────────────────────
    @staticmethod
    def _chronic_pain_survival(): return [
        GameMechanic("Allodynia","Rain/cloth/wind deal 10% HP damage.","Allodynia","DamageTag on Weather/TextureContact events.",0.9),
        GameMechanic("Throttled Healing","Rest heals 5% normal; items cost 3x.","Blunted endorphins","heal_rate*=0.05; item_cost*=3.",0.85),
        GameMechanic("Pacing Resource","Overexertion today -> max HP -30% tomorrow.","Post-exertional malaise","Track daily_exertion; tomorrow_maxhp*=0.7 if exceeded.",0.8),
        GameMechanic("Cognitive Fog","During high pain, 30% of crafting steps hidden.","Pain consumes cognition","pain_level>0.7: recipe_steps.hide_random(0.3).",0.7),
    ]


# ══════════════════════════════════════════════════════════════════════════════
# TIMELINE + CONSOLE
# ══════════════════════════════════════════════════════════════════════════════

class TimelineGenerator:
    _T = {
        "episodic": TimelineLayer("Episode Map",
            "Horizontal timeline of episodes, remissions, and medication trials. Scrub to witness past states.",
            ["First episode onset","Diagnosis","Medication trial","Therapy milestones","Relapse/recovery","Present"],
            "Scrubbing replays environmental changes. Future hidden behind fog-of-war."),
        "chronic": TimelineLayer("Persistence Ribbon",
            "Continuous ribbon — intensity fluctuates but never reaches zero.",
            ["Onset","Flare peaks","Relative troughs","Intervention markers","Present"],
            "Zoom out to see years. Cannot rewind — condition is always present."),
        "developmental": TimelineLayer("Growth Arc",
            "Early childhood to present. Traits were always there; diagnosis is a label, not a change.",
            ["Early childhood traits","School differences noted","Referral","Diagnosis","Accommodations","Present"],
            "Inhabit different age-selves by scrubbing. World changes; the player's core doesn't."),
        "fluctuating": TimelineLayer("Wave Form",
            "Sinusoidal intensity. Preview upcoming peaks but cannot stop them.",
            ["Predictable peaks","Predictable troughs","Trigger events","Intervention effects"],
            "Preview 30s ahead. No rewind. Preparation is the agency, not prevention."),
    }
    @classmethod
    def generate(cls, condition):
        p = ConditionLibrary.get(condition)
        return cls._T.get(p.timeline_pattern if p else "episodic", cls._T["episodic"])


class MetaConsoleGenerator:
    @staticmethod
    def generate(condition):
        p = ConditionLibrary.get(condition)
        if not p: return MetaConsole("Debug Console",[],""," ")
        nt_names = [nt.name for nt in p.neurotransmitters]
        variables = nt_names + p.medication_targets[:2] + ["sleep_quality","stress_level","social_support"]
        return MetaConsole(
            label=f"{p.condition_name} — Biological Console",
            variables=variables,
            description="Developer-style console overlaid on the game. Inspect and adjust any biological variable in real time. The invisible made visible.",
            inception_note=(
                f"Adjusting '{nt_names[0]}' here directly changes the '{p.primary_symptoms[0]}' mechanic. "
                f"Medication targets ({', '.join(p.medication_targets[:2])}) are pre-wired as presets. "
                f"Students see the biology -> experience pipeline made explicit."
            ),
        )


# ══════════════════════════════════════════════════════════════════════════════
# PSEUDOCODE + LEARNING OBJECTIVES
# ══════════════════════════════════════════════════════════════════════════════

def _make_pseudocode(game):
    p = ConditionLibrary.get(game.condition)
    nt_block = ""
    if p:
        for nt in p.neurotransmitters:
            val = nt.baseline if isinstance(nt.baseline, float) else 0.5
            nt_block += f"            '{nt.name.lower()}': {val},\n"
    mhints = "\n".join(f"        # {m.name}: {m.implementation_hint}" for m in game.mechanics[:5])

    s = game.stamina
    stamina_block = ""
    if s:
        stamina_block = f"""
    # ── Regenerative Stamina (serotonin-driven) ─────────────────────────────
    # StaminaSystem parameters derived from {game.condition} NT profile:
    #   max_stamina      = {s.max_stamina}   (reduced by low serotonin / high substance P)
    #   regen_rate       = {s.regen_rate}/s  (serotonin × GABA gate × cortisol inverse)
    #   drain_rate       = {s.drain_rate}/s  (NE + substance P + cortisol burden)
    #   regen_cap        = {s.regen_cap}     (fraction recoverable without sleep checkpoint)
    #   serotonin_weight = {s.serotonin_weight}
    #   overshoot_penalty= {s.overshoot_penalty}  (mania: excess stamina decays)
    #   rest_threshold   = {s.rest_threshold}  (below this: forced-rest warning fires)
    #
    # Formula:
    #   {s.formula.replace(chr(10), chr(10)+'    #   ')}
    self.stamina = StaminaSystemGenerator.tick(
        self.stamina, self.neurotransmitters, STAMINA_SYS, dt,
        is_resting  = self.player.is_idle,
        is_sleeping = self.player.at_sleep_checkpoint,
    )
    if self.stamina < {s.rest_threshold}:
        RENDERER.show_warning("Low stamina — find rest")
"""

    return f"""# {'─'*60}
# {game.title}
# MechanisticEngine v{__version__}  |  Condition: {game.condition}  |  Genre: {game.genre}
# {'─'*60}

from mechanistic_empathy_engine import StaminaSystemGenerator, ConditionLibrary

# Stamina system — generated from NT profile, not hardcoded
_profile    = ConditionLibrary.get("{game.condition}")
STAMINA_SYS = StaminaSystemGenerator.generate("{game.condition}")

class GameState:
    def __init__(self):
        self.neurotransmitters = {{
{nt_block}        }}
        self.stamina           = STAMINA_SYS.max_stamina   # start full
        self.timeline_position = 0.0   # 0 = earliest, 1.0 = present
        self.console_open      = False

    def update(self, dt: float):
        self._apply_nt_effects(dt)
        self._tick_stamina(dt)
        self._update_timeline()
        if self.console_open:
            self._render_meta_console()

    def _apply_nt_effects(self, dt):
        \"\"\"
        Mechanic hooks:
{mhints}
        \"\"\"
        for nt_name, level in self.neurotransmitters.items():
            game_variable = NT_TO_MECHANIC_MAP[nt_name]
            game_variable.value = transform(level)

    def _tick_stamina(self, dt):
        \"\"\"Regenerative stamina — rate/cap fully driven by live NT levels.\"\"\"{stamina_block}

    def _update_timeline(self):
        \"\"\"Braid-style scrubbing replays historical NT levels.\"\"\"
        historical = TIMELINE[self.timeline_position]
        self.neurotransmitters = historical.neurotransmitters
        RENDERER.apply_era_palette(historical.visual_profile)

    def _render_meta_console(self):
        \"\"\"Inception layer — raw biology as editable variables.\"\"\"
        CONSOLE_UI.render(self.neurotransmitters)
        for var, val in CONSOLE_UI.poll_edits().items():
            self.neurotransmitters[var] = clamp(val, 0.0, 2.0)
        # Stamina responds live as NT values are adjusted:
        # e.g. raising serotonin in console immediately increases regen_rate

    def apply_medication_preset(self, med_name: str):
        delta = MEDICATION_PRESETS[med_name]
        for nt, d in delta.items():
            self.neurotransmitters[nt] = clamp(
                self.neurotransmitters.get(nt, 0.5) + d, 0.0, 2.0)
        # Stamina regen will update automatically next tick

if __name__ == "__main__":
    state = GameState()
    clock = GameClock(fps=60)
    while True:
        dt = clock.tick()
        handle_input(state)
        state.update(dt)
        RENDERER.draw(state)
        RENDERER.draw_stamina_bar(state.stamina, STAMINA_SYS.max_stamina,
                                  state.stamina < STAMINA_SYS.rest_threshold)
"""


_OBJ = [
    "Understand the neurobiological basis of {c} and how it affects daily function.",
    "Experience {s} as a first-person mechanic, not an abstract clinical description.",
    "Observe how neurotransmitter levels map to symptoms via the meta-console.",
    "Explore how pharmacological interventions ({m}) alter the biology->experience pipeline.",
    "Develop compassion for people with {c} by inhabiting their perceptual world.",
    "Distinguish between 'won't' and 'can't' in the context of {s}.",
    "Understand the {p} timeline pattern — how the condition evolves, cycles, or persists.",
]

def _objectives(condition):
    p = ConditionLibrary.get(condition)
    if not p: return ["Build empathy through gameplay."]
    return [t.format(c=p.condition_name,
                     s=p.primary_symptoms[i % len(p.primary_symptoms)],
                     m=p.medication_targets[0],p=p.timeline_pattern)
            for i,t in enumerate(_OBJ)]


# ══════════════════════════════════════════════════════════════════════════════
# THE ENGINE  — public API
# ══════════════════════════════════════════════════════════════════════════════

class MechanisticEngine:
    """
    Mechanistic Empathy Engine — public API.

    Quick start::

        engine = MechanisticEngine()
        game   = engine.generate_game("depression", "platformer")
        engine.export_game(game, "./output", engine_target="pygame")

    Register a custom condition::

        engine.define_condition("fibromyalgia", PhysiologyProfile(
            condition_name="Fibromyalgia",
            neurotransmitters=[
                Neurotransmitter("Substance P", 1.6, "pain amplification", "ambient pain drains HP"),
                Neurotransmitter("Serotonin",   0.5, "pain modulation",    "healing 50% effective"),
            ],
            systems_affected=["central_sensitisation","autonomic_nervous_system"],
            primary_symptoms=["widespread pain","fatigue","cognitive fog","sleep disruption"],
            timeline_pattern="chronic",
            medication_targets=["duloxetine -> SNRI","pregabalin -> calcium channel"],
        ))
        game = engine.generate_game("fibromyalgia", "survival")
        engine.export_game(game, "./fibromyalgia_out", engine_target="arcade")
    """

    def __init__(self):
        self._custom: dict = {}

    def define_condition(self, name, physiology, additional_mechanics=None):
        """Register a new (or override an existing) condition."""
        ConditionLibrary.register(name, physiology)
        if additional_mechanics:
            self._custom[name.lower()] = additional_mechanics
        print(f"{C.GREEN}+ Condition '{name}' registered.{C.RESET}")

    def generate_game(self, condition: str, genre: str) -> GeneratedGame:
        """Generate a complete empathy game specification."""
        condition = condition.lower().replace(" ","_")
        genre     = genre.lower().replace(" ","_")
        p = ConditionLibrary.get(condition)
        if not p:
            raise ValueError(f"Unknown condition '{condition}'. "
                             f"Available: {', '.join(self.list_conditions())}.")
        if genre not in GENRES:
            raise ValueError(f"Unknown genre '{genre}'. "
                             f"Available: {', '.join(GENRES)}.")

        mechanics  = MechanicGenerator.generate(condition, genre)
        mechanics += self._custom.get(condition, [])
        timeline   = TimelineGenerator.generate(condition)
        console    = MetaConsoleGenerator.generate(condition)
        objs       = _objectives(condition)
        stamina_sys = StaminaSystemGenerator.generate(condition)

        cw = p.condition_name.split()[0]
        gw = GENRES[genre]["core_mechanic"].split(",")[0].strip().title()
        title   = f"{cw}: A {gw} of {p.condition_name}"
        tagline = f"What if you felt what they feel? A {genre} about living with {p.condition_name}."
        core    = (f"Standard {genre} loop ({GENRES[genre]['core_mechanic']}) "
                   f"modified by {len(p.primary_symptoms)} symptom mechanics. "
                   f"Timeline: {timeline.name}. Meta-console exposes {len(console.variables)} variables. "
                   f"Serotonin-driven stamina: regen={stamina_sys.regen_rate:.4f}/s, "
                   f"cap={stamina_sys.regen_cap:.0%}, max={stamina_sys.max_stamina:.2f}.")
        notes   = (f"Genre strength: '{GENRES[genre]['strength']}'. "
                   f"Limitation: '{GENRES[genre]['weakness']}'. "
                   f"Mitigate with narrative tooltips.")

        game = GeneratedGame(condition=condition, genre=genre, title=title, tagline=tagline,
                             core_loop=core, mechanics=mechanics, timeline=timeline,
                             meta_console=console, learning_objectives=objs,
                             design_notes=notes, pseudocode="", stamina=stamina_sys)
        game.pseudocode = _make_pseudocode(game)
        return game

    def export_game(self, game: GeneratedGame, directory=".", engine_target="pygame") -> dict:
        """
        Export game to directory. Creates:
          - spec JSON, pseudocode .py, engine scaffold .py
          - pyproject.toml  (Flit packaging — run 'flit build' to create .whl)
          - README.md
        """
        os.makedirs(directory, exist_ok=True)
        slug = f"{game.condition}_{game.genre}"
        paths = {}

        # JSON
        json_path = os.path.join(directory, f"{slug}_spec.json")
        with open(json_path,"w",encoding="utf-8") as f:
            json.dump({
                "title":game.title,"tagline":game.tagline,
                "condition":game.condition,"genre":game.genre,
                "core_loop":game.core_loop,
                "stamina_system": asdict(game.stamina) if game.stamina else None,
                "mechanics":[asdict(m) for m in game.mechanics],
                "timeline":asdict(game.timeline),
                "meta_console":asdict(game.meta_console),
                "learning_objectives":game.learning_objectives,
                "design_notes":game.design_notes,
            }, f, indent=2, ensure_ascii=False)
        paths["json"] = json_path

        # Pseudocode
        py_path = os.path.join(directory, f"{slug}_pseudocode.py")
        with open(py_path,"w",encoding="utf-8") as f:
            f.write(game.pseudocode)
        paths["pseudocode"] = py_path

        # Engine scaffold
        engine_key = engine_target.lower()
        eng = ENGINES.get(engine_key, ENGINES["pygame"])
        code = EngineAdapterGenerator.generate(game, engine_key)
        ep = os.path.join(directory, f"{slug}_{engine_key}.py")
        with open(ep,"w",encoding="utf-8") as f:
            f.write(code)
        paths["engine_scaffold"] = ep

        # ── Copy the engine module itself into the export directory ──────────────
        # Flit reads the MODULE FILE for __version__ and the module docstring.
        # The module file must:
        #   1. Be named exactly as [tool.flit.module] specifies (mechanistic_empathy_engine.py)
        #   2. Start with a triple-quoted module docstring (no shebang above it)
        #   3. Have __version__ = "x.y.z" at top level
        # The engine file already satisfies all three requirements.
        import shutil as _shutil
        engine_src = os.path.abspath(__file__)
        engine_dst = os.path.join(directory, "mechanistic_empathy_engine.py")
        if os.path.abspath(engine_src) != os.path.abspath(engine_dst):
            _shutil.copy2(engine_src, engine_dst)
        paths["engine_module"] = engine_dst

        # ── pyproject.toml (Flit-compatible) ──────────────────────────────────
        # Key rules obeyed here:
        #   * [tool.flit.module] = "mechanistic_empathy_engine"  ← the module Flit reads
        #   * version / description come from that module (dynamic)
        #   * The game launcher is a console_scripts entry point that imports
        #     from mechanistic_empathy_engine, so it doesn't need its own metadata.
        pkg       = f"empathy-{game.condition.replace('_','-')}-{game.genre.replace('_','-')}"
        cmd_name  = f"empathy-{game.condition.replace('_','-')}-{game.genre.replace('_','-')}"
        eng_deps  = eng['install'].replace('pip install ','').strip()
        # Strip any extras like "PyOpenGL_accelerate" into a list
        dep_list  = [d.strip() for d in eng_deps.split() if d.strip()]
        deps_toml = "\n".join(f'  "{d}",' for d in dep_list)

        toml = f"""\
# ─────────────────────────────────────────────────────────────────────────────
# pyproject.toml — Flit packaging for {game.title}
# Generated by Mechanistic Empathy Engine v{__version__}
#
# HOW TO USE:
#   pip install flit                      # install Flit once
#   flit build                            # creates dist/*.whl  and  dist/*.tar.gz
#   pip install dist/*.whl                # install locally
#   {cmd_name}                            # run the game
#   flit publish                          # upload to PyPI (needs credentials)
#
# WHAT FLIT READS:
#   Flit reads mechanistic_empathy_engine.py for the module docstring
#   (used as the long description) and for __version__.  Do NOT move or
#   rename that file, or Flit will error with "SyntaxError / no __version__".
# ─────────────────────────────────────────────────────────────────────────────

[build-system]
requires      = ["flit_core>=3.4,<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
# This tells Flit WHICH FILE to parse for docstring + __version__.
# It must match the filename exactly (without .py).
name = "mechanistic_empathy_engine"

[project]
name            = "{pkg}"
dynamic         = ["version", "description"]   # pulled from the module file
readme          = "README.md"
license         = {{text = "MIT"}}
requires-python = ">=3.10"
dependencies    = [
{deps_toml}
]

[project.urls]
Homepage   = "https://github.com/education-singularity/mechanistic-empathy-engine"
Tracker    = "https://github.com/education-singularity/mechanistic-empathy-engine/issues"

[project.scripts]
# The entry point calls mechanistic_empathy_engine.main() directly.
# This avoids any dependency on the scaffold file having its own metadata.
"{cmd_name}" = "mechanistic_empathy_engine:main"

[project.optional-dependencies]
dev = ["flit", "pytest", "mypy"]
"""
        tp = os.path.join(directory, "pyproject.toml")
        with open(tp,"w",encoding="utf-8") as f:
            f.write(toml)
        paths["pyproject"] = tp

        # README + troubleshooting guide
        mech_md = "\n".join(
            f"- **{m.name}** ({m.intensity:.0%}) — {m.description[:70]}…"
            for m in game.mechanics[:6])
        pkg       = f"empathy-{game.condition.replace('_','-')}-{game.genre.replace('_','-')}"
        cmd_name  = f"empathy-{game.condition.replace('_','-')}-{game.genre.replace('_','-')}"
        readme = f"""\
# {game.title}

> {game.tagline}

Generated by [Mechanistic Empathy Engine](https://github.com/education-singularity/mechanistic-empathy-engine) v{__version__}

---

## Quick Start — Just Run It

```bash
# Step 1: install the game engine
{eng['install']}

# Step 2: run the game directly (no packaging needed)
python {slug}_{engine_key}.py
```

**In-game controls**

| Key | Action |
|-----|--------|
| Arrow keys / WASD | Movement |
| `F1` | Toggle Meta-Console — live neurotransmitter editor |
| `M` | Apply medication preset (raises NT levels, observe mechanic change) |
| `Esc` | Quit |

---

## Package & Distribute with Flit

Flit lets you turn this into a proper pip-installable package.

```bash
# ── Prerequisites ─────────────────────────────────────────────────────────
pip install flit

# ── IMPORTANT: run ALL flit commands from THIS directory ──────────────────
cd path/to/this/folder

# ── Build wheel + sdist ───────────────────────────────────────────────────
flit build
#   Creates: dist/{pkg}-{__version__}-py3-none-any.whl
#            dist/{pkg}-{__version__}.tar.gz

# ── Install locally ───────────────────────────────────────────────────────
pip install dist/{pkg}-{__version__}-py3-none-any.whl

# ── Run via entry point ───────────────────────────────────────────────────
{cmd_name}

# ── Publish to PyPI (optional) ────────────────────────────────────────────
flit publish
```

### How Flit finds your metadata

Flit reads **`mechanistic_empathy_engine.py`** (not the scaffold file) for:
- The module docstring → used as the package description
- `__version__ = "..."` → used as the package version

Both are present and correct in that file. **Do not rename or move it.**

### Common Flit errors and fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `SyntaxError: invalid syntax` on `usage (cli):` | Flit tried to parse a file that starts with a shebang or plain comment instead of a module docstring | Make sure `pyproject.toml` points at `mechanistic_empathy_engine` (not the scaffold). Already fixed in this export. |
| `No __version__ found` | Module file missing `__version__ = "..."` at top level | The engine file has it on line 2. Don't delete it. |
| `Module mechanistic_empathy_engine not found` | You ran `flit build` from the wrong directory | `cd` into the folder that contains `mechanistic_empathy_engine.py` first. |
| `No module named 'flit'` | Flit not installed | `pip install flit` |
| `Dependency not found` | Game engine not installed | `{eng['install']}` |

---

## Condition: {game.condition.replace('_',' ').title()}

**{ConditionLibrary.get(game.condition).condition_name if ConditionLibrary.get(game.condition) else ''}**

## Core Mechanics

{mech_md}

## Timeline — {game.timeline.name}

{game.timeline.description}

## Meta-Console

{game.meta_console.description}

Variables: `{', '.join(game.meta_console.variables[:6])}`…

## Learning Objectives

{chr(10).join(f'{i+1}. {o}' for i,o in enumerate(game.learning_objectives))}

## Design Notes

{game.design_notes}

---
MIT License — Open Source — Extend freely.
"""
        rp = os.path.join(directory, "README.md")
        with open(rp,"w",encoding="utf-8") as f:
            f.write(readme)
        paths["readme"] = rp

        print(f"\n{C.GREEN}Exported {len(paths)} files -> {directory}/{C.RESET}")
        for role, path in paths.items():
            print(f"  {C.CYAN}{role:<18}{C.RESET} {path}")
        print()
        return paths

    @staticmethod
    def list_conditions(): return ConditionLibrary.all_names()
    @staticmethod
    def list_genres():     return sorted(GENRES.keys())
    @staticmethod
    def list_engines():    return sorted(ENGINES.keys())


# ══════════════════════════════════════════════════════════════════════════════
# TERMINAL RENDERER
# ══════════════════════════════════════════════════════════════════════════════

class TerminalRenderer:
    W = 80

    @classmethod
    def render(cls, game: GeneratedGame):
        p = ConditionLibrary.get(game.condition)
        cls._header(game); cls._section("CORE LOOP", game.core_loop)
        cls._physiology(p); cls._stamina(game.stamina)
        cls._mechanics(game.mechanics)
        cls._timeline(game.timeline); cls._console(game.meta_console)
        cls._objectives(game.learning_objectives); cls._notes(game.design_notes)
        cls._pseudocode_preview(game.pseudocode)
        cls._engines_hint(game); cls._footer()

    @classmethod
    def _hr(cls, ch="─", col=C.GRAY): print(f"{col}{ch*cls.W}{C.RESET}")

    @classmethod
    def _stamina(cls, s: "StaminaSystem | None"):
        if not s: return
        print(f"{C.BOLD}{C.YELLOW}>> REGENERATIVE STAMINA SYSTEM  [serotonin-driven]{C.RESET}")

        # Visual bar helpers
        def bar(val, maxv=1.0, width=24, col=C.GREEN):
            filled = max(0, min(width, int(val / maxv * width)))
            return col + "█"*filled + C.GRAY + "░"*(width-filled) + C.RESET

        # Regen rate bar (0 → 0.08 is healthy reference)
        regen_pct = min(1.0, s.regen_rate / 0.08)
        drain_pct = min(1.0, s.drain_rate / 0.10)

        print(f"    {C.BOLD}max_stamina     {C.RESET} {bar(s.max_stamina)}  {s.max_stamina:.3f}")
        print(f"    {C.BOLD}regen_rate      {C.RESET} {bar(regen_pct, col=C.CYAN)}  {s.regen_rate:.4f}/s"
              f"  {C.DIM}(serotonin_weight={s.serotonin_weight:.3f}){C.RESET}")
        print(f"    {C.BOLD}drain_rate      {C.RESET} {bar(drain_pct, col=C.RED)}  {s.drain_rate:.4f}/s")
        print(f"    {C.BOLD}regen_cap       {C.RESET} {bar(s.regen_cap)}  {s.regen_cap:.0%}"
              f"  {C.DIM}(max recoverable without sleep){C.RESET}")
        print(f"    {C.BOLD}rest_threshold  {C.RESET} {bar(s.rest_threshold, col=C.YELLOW)}  {s.rest_threshold:.0%}"
              f"  {C.DIM}(below this: forced-rest warning){C.RESET}")
        if s.overshoot_penalty:
            print(f"    {C.MAGENTA}⚡ MANIA OVERSHOOT ACTIVE{C.RESET}"
                  f"  {C.DIM}stamina decays when above max (excess dopamine){C.RESET}")
        print()
        print(f"    {C.BOLD}Live formula:{C.RESET}")
        for ln in s.formula.split("\n"):
            print(f"      {C.DIM}{ln}{C.RESET}")
        print()
        print(f"    {C.BOLD}Usage in your game loop:{C.RESET}")
        print(f"      {C.GREEN}from mechanistic_empathy_engine import StaminaSystemGenerator{C.RESET}")
        print(f"      {C.GREEN}stamina = StaminaSystemGenerator.tick({C.RESET}")
        print(f"      {C.GREEN}    stamina, NT, game.stamina, dt,{C.RESET}")
        print(f"      {C.GREEN}    is_resting=player.is_idle,{C.RESET}")
        print(f"      {C.GREEN}    is_sleeping=player.at_sleep_checkpoint){C.RESET}")
        print()

    @classmethod
    def _header(cls, g):
        print(); cls._hr("═",C.CYAN)
        print(f"  {C.BOLD}{C.CYAN}{g.title}{C.RESET}")
        print(f"  {C.ITALIC}{C.GRAY}{g.tagline}{C.RESET}")
        print(f"  {C.YELLOW}Condition:{C.RESET} {g.condition.upper().replace('_',' ')}   "
              f"{C.YELLOW}Genre:{C.RESET} {g.genre.upper()}")
        cls._hr("═",C.CYAN); print()

    @classmethod
    def _section(cls, h, b):
        print(f"{C.BOLD}{C.YELLOW}>> {h}{C.RESET}")
        for ln in textwrap.wrap(b, cls.W-4): print(f"    {ln}")
        print()

    @classmethod
    def _physiology(cls, p):
        if not p: return
        print(f"{C.BOLD}{C.YELLOW}>> PHYSIOLOGY{C.RESET}")
        print(f"    {C.BOLD}Condition:{C.RESET} {p.condition_name}  |  Pattern: {p.timeline_pattern}")
        print(f"    {C.BOLD}Systems:{C.RESET}   {', '.join(p.systems_affected)}")
        print(); print(f"    {C.BOLD}Neurotransmitter Baselines:{C.RESET}")
        for nt in p.neurotransmitters:
            lvl = nt.baseline if isinstance(nt.baseline, float) else 0.5
            fl  = min(20, max(0, int(lvl*10)))
            bar = C.GREEN+"█"*fl+C.GRAY+"░"*(20-fl)+C.RESET
            lvs = f"{lvl:.2f}" if isinstance(nt.baseline, float) else str(nt.baseline)
            print(f"      {C.CYAN}{nt.name:<22}{C.RESET} {bar} {lvs}  {C.DIM}{nt.game_effect}{C.RESET}")
        print(); print(f"    {C.BOLD}Symptoms:{C.RESET}")
        for s in p.primary_symptoms: print(f"      {C.GRAY}*{C.RESET} {s}")
        print(); print(f"    {C.BOLD}Medication Targets:{C.RESET}")
        for m in p.medication_targets: print(f"      {C.MAGENTA}[M]{C.RESET} {m}")
        print()

    @classmethod
    def _mechanics(cls, mechanics):
        print(f"{C.BOLD}{C.YELLOW}>> GAME MECHANICS  ({len(mechanics)} total){C.RESET}")
        for i, m in enumerate(mechanics, 1):
            ib = int(m.intensity*10)
            bar= C.RED+"#"*ib+C.GRAY+"."*(10-ib)+C.RESET
            print(f"    {C.BOLD}{C.WHITE}{i:02d}. {m.name}{C.RESET}  [{bar}]")
            for ln in textwrap.wrap(m.description, cls.W-10): print(f"        {ln}")
            print(f"        {C.GRAY}From:{C.RESET} {C.ITALIC}{m.mapped_from}{C.RESET}")
            print(f"        {C.GRAY}Impl:{C.RESET} {C.DIM}{m.implementation_hint}{C.RESET}")
            print()

    @classmethod
    def _timeline(cls, tl):
        print(f"{C.BOLD}{C.YELLOW}>> TIMELINE LAYER  [{tl.name}]{C.RESET}")
        for ln in textwrap.wrap(tl.description, cls.W-4): print(f"    {ln}")
        print()
        for i,ev in enumerate(tl.events):
            c = "--" if i<len(tl.events)-1 else "  "
            print(f"    {C.CYAN}*{c}{C.RESET} {ev}")
        print(f"\n    {C.BOLD}Braid mechanic:{C.RESET} {tl.braid_mechanic}\n")

    @classmethod
    def _console(cls, con):
        print(f"{C.BOLD}{C.YELLOW}>> META-CONSOLE  [{con.label}]{C.RESET}")
        for ln in textwrap.wrap(con.description, cls.W-4): print(f"    {ln}")
        print(); print(f"    {C.BOLD}Variables:{C.RESET}")
        cols=3; v=con.variables
        for rs in range(0,len(v),cols):
            print("    "+"   ".join(f"{C.CYAN}{x:<24}{C.RESET}" for x in v[rs:rs+cols]))
        print(); print(f"    {C.BOLD}Inception note:{C.RESET}")
        for ln in textwrap.wrap(con.inception_note, cls.W-6): print(f"      {C.DIM}{ln}{C.RESET}")
        print()

    @classmethod
    def _objectives(cls, objs):
        print(f"{C.BOLD}{C.YELLOW}>> LEARNING OBJECTIVES{C.RESET}")
        for i,o in enumerate(objs,1):
            for j,ln in enumerate(textwrap.wrap(o, cls.W-8)):
                print(f"{'    '+str(i)+'. ' if j==0 else '       '}{ln}")
        print()

    @classmethod
    def _notes(cls, n):
        print(f"{C.BOLD}{C.YELLOW}>> DESIGN NOTES{C.RESET}")
        for ln in textwrap.wrap(n, cls.W-4): print(f"    {ln}")
        print()

    @classmethod
    def _pseudocode_preview(cls, code):
        print(f"{C.BOLD}{C.YELLOW}>> PSEUDOCODE (preview){C.RESET}")
        for ln in code.strip().split("\n")[:22]: print(f"  {C.GREEN}{ln}{C.RESET}")
        print(f"  {C.GRAY}  ... (full file in --export output){C.RESET}\n")

    @classmethod
    def _engines_hint(cls, game):
        print(f"{C.BOLD}{C.YELLOW}>> SUPPORTED GAME ENGINES{C.RESET}")
        best = GENRES.get(game.genre,{}).get("best_engines",[])
        for key, info in ENGINES.items():
            star = "* " if key in best else "  "
            print(f"  {C.CYAN}{star}{key:<14}{C.RESET} {info['label']:<14} "
                  f"{C.GRAY}{info['description'][:42]}{C.RESET}")
        print(f"\n  {C.DIM}(* = good match for '{game.genre}')  --engine KEY to export scaffold{C.RESET}\n")

    @classmethod
    def _footer(cls):
        cls._hr("═",C.CYAN)
        print(f"  {C.BOLD}MECHANISTIC EMPATHY ENGINE v{__version__}{C.RESET}  "
              f"{C.GRAY}|  MIT License  |  Open Source{C.RESET}")
        print(f"  {C.DIM}define_condition() . generate_game() . export_game(engine_target='...')  {C.RESET}")
        cls._hr("═",C.CYAN); print()


# ══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE MODE
# ══════════════════════════════════════════════════════════════════════════════

def interactive_mode(engine: MechanisticEngine):
    print(f"\n{C.BOLD}{C.CYAN}{'='*80}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  MECHANISTIC EMPATHY ENGINE v{__version__} -- Interactive{C.RESET}")
    print(f"{C.CYAN}{'='*80}{C.RESET}\n")

    conditions = engine.list_conditions()
    genres     = engine.list_genres()
    engines_   = engine.list_engines()

    print(f"{C.BOLD}Conditions:{C.RESET}")
    for i,c in enumerate(conditions,1):
        p=ConditionLibrary.get(c)
        print(f"  {C.CYAN}{i:2}. {c:<22}{C.RESET} {C.GRAY}{p.condition_name if p else ''}{C.RESET}")

    print(f"\n{C.BOLD}Genres:{C.RESET}")
    for i,g in enumerate(genres,1):
        print(f"  {C.YELLOW}{i:2}. {g:<16}{C.RESET} {C.GRAY}{GENRES[g]['core_mechanic']}{C.RESET}")

    print(f"\n{C.BOLD}Engines:{C.RESET}")
    for i,e in enumerate(engines_,1):
        print(f"  {C.MAGENTA}{i:2}. {e:<14}{C.RESET} {C.GRAY}{ENGINES[e]['label']:<12}  {ENGINES[e]['install']}{C.RESET}")
    print()

    def pick(prompt, options):
        while True:
            raw = input(f"{C.BOLD}{prompt}: {C.RESET}").strip()
            if raw.isdigit() and 1<=int(raw)<=len(options): return options[int(raw)-1]
            normed = raw.lower().replace(" ","_")
            if normed in options: return normed
            print(f"  {C.RED}Not found.{C.RESET}")

    condition  = pick("Condition (name or number)", conditions)
    genre      = pick("Genre (name or number)", genres)
    engine_key = pick("Engine (name or number)", engines_)

    print(f"\n{C.GRAY}Generating...{C.RESET}\n")
    game = engine.generate_game(condition, genre)
    TerminalRenderer.render(game)

    if input(f"{C.BOLD}Export? [y/N]: {C.RESET}").strip().lower() == "y":
        d = input(f"  Directory [{condition}_{genre}/]: ").strip() or f"{condition}_{genre}"
        engine.export_game(game, d, engine_target=engine_key)


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def build_parser():
    p = argparse.ArgumentParser(
        prog="mechanistic_empathy_engine",
        description="Generate empathy games from medical conditions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(f"""\
        Examples:
          python mechanistic_empathy_engine.py
          python mechanistic_empathy_engine.py -c depression -g platformer
          python mechanistic_empathy_engine.py -c adhd -g puzzle -e ./out --engine arcade
          python mechanistic_empathy_engine.py --list-conditions
          python mechanistic_empathy_engine.py --list-genres
          python mechanistic_empathy_engine.py --list-engines

        Conditions: {', '.join(ConditionLibrary.all_names())}
        Genres:     {', '.join(sorted(GENRES))}
        Engines:    {', '.join(sorted(ENGINES))}
        """))
    p.add_argument("--condition","-c")
    p.add_argument("--genre","-g")
    p.add_argument("--export","-e", metavar="DIR")
    p.add_argument("--engine","-E", metavar="ENGINE", default="pygame",
                   help="Game engine scaffold (default: pygame)")
    p.add_argument("--list-conditions", action="store_true")
    p.add_argument("--list-genres",     action="store_true")
    p.add_argument("--list-engines",    action="store_true")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main():
    parser = build_parser(); args = parser.parse_args()
    engine = MechanisticEngine()

    if args.list_conditions:
        print(f"\n{C.BOLD}Conditions ({len(engine.list_conditions())}){C.RESET}\n")
        for n in engine.list_conditions():
            p=ConditionLibrary.get(n)
            print(f"  {C.CYAN}{n:<22}{C.RESET} {p.condition_name if p else '':<44} "
                  f"{C.GRAY}[{p.timeline_pattern if p else ''}]{C.RESET}")
        print(); return

    if args.list_genres:
        print(f"\n{C.BOLD}Genres ({len(GENRES)}){C.RESET}\n")
        for n in sorted(GENRES):
            print(f"  {C.YELLOW}{n:<16}{C.RESET} {GENRES[n]['description']:<38} "
                  f"{C.GRAY}strength: {GENRES[n]['strength'][:35]}{C.RESET}")
        print(); return

    if args.list_engines:
        print(f"\n{C.BOLD}Engines ({len(ENGINES)}){C.RESET}\n")
        for n,info in sorted(ENGINES.items()):
            print(f"  {C.MAGENTA}{n:<14}{C.RESET} {info['label']:<12}  "
                  f"{C.GRAY}{info['install']:<32}  best for: {', '.join(info['best_for'])}{C.RESET}")
        print(); return

    if args.condition and args.genre:
        try:
            game = engine.generate_game(args.condition, args.genre)
            TerminalRenderer.render(game)
            if args.export:
                engine.export_game(game, args.export, engine_target=args.engine)
        except ValueError as e:
            print(f"\n{C.RED}Error: {e}{C.RESET}\n"); sys.exit(1)
        return

    interactive_mode(engine)


if __name__ == "__main__":

    main()
