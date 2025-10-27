import random

def init_guild_deck():
    deck = [
        {"id":"g_w1","heroes":[{"type":"warrior","spawn_mark":"sword"}]},
        {"id":"g_a1","heroes":[{"type":"archer","spawn_mark":"eye"}]},
        {"id":"g_m1","heroes":[{"type":"mage","spawn_mark":"prison"}]},
        {"id":"g_r1","heroes":[{"type":"rogue","spawn_mark":"trap_room"}]},
    ]
    random.shuffle(deck)
    return deck

def draw(deck, n=1):
    drawn = []
    for _ in range(min(n, len(deck))):
        drawn.append(deck.pop(0))
    return drawn