#!/usr/bin/env python3
"""
批量生成像素画小鸟素材
每种鸟 6 种状态 × 4 帧 = 24 帧
"""

from PIL import Image
import os

BASE = os.path.join(os.path.dirname(__file__), 'assets', 'bird')

def new_frame():
    return Image.new('RGBA', (32, 32), (0, 0, 0, 0))

def put(img, x, y, color):
    if 0 <= x < 32 and 0 <= y < 32:
        img.putpixel((x, y), color + (255,))

def fill_ellipse(img, cx, cy, rx, ry, color):
    for dx in range(-rx, rx+1):
        for dy in range(-ry, ry+1):
            if (dx*dx)/(rx*rx+0.01) + (dy*dy)/(ry*ry+0.01) <= 1:
                put(img, cx+dx, cy+dy, color)

def fill_rect(img, x1, y1, x2, y2, color):
    for x in range(x1, x2+1):
        for y in range(y1, y2+1):
            put(img, x, y, color)

# ---- 鸟类定义 ----

BIRDS = {
    'canary': {
        'name': '金丝雀',
        'colors': {
            'body': (255, 217, 61), 'body_d': (240, 184, 0),
            'belly': (255, 245, 204), 'wing': (255, 204, 68),
            'wing_d': (232, 160, 0), 'head': (255, 224, 102),
            'eye': (61, 46, 31), 'beak': (255, 140, 0),
            'feet': (255, 140, 0), 'cheek': (255, 130, 130),
            'heart': (255, 107, 138), 'zzz': (139, 164, 216),
            'crumb': (196, 138, 78),
        }
    },
    'robin': {
        'name': '知更鸟',
        'colors': {
            'body': (139, 90, 43), 'body_d': (120, 70, 30),
            'belly': (220, 80, 50), 'wing': (100, 65, 30),
            'wing_d': (80, 50, 20), 'head': (80, 55, 30),
            'eye': (30, 20, 10), 'beak': (255, 200, 50),
            'feet': (100, 70, 40), 'cheek': (255, 130, 130),
            'heart': (255, 107, 138), 'zzz': (139, 164, 216),
            'crumb': (160, 100, 50),
        }
    },
    'bluejay': {
        'name': '蓝鸦',
        'colors': {
            'body': (70, 130, 210), 'body_d': (50, 100, 180),
            'belly': (220, 230, 245), 'wing': (50, 100, 180),
            'wing_d': (30, 70, 140), 'head': (80, 140, 220),
            'eye': (20, 20, 20), 'beak': (60, 60, 60),
            'feet': (80, 80, 80), 'cheek': (255, 200, 200),
            'heart': (255, 107, 138), 'zzz': (139, 164, 216),
            'crumb': (100, 100, 100),
        }
    },
    'sparrow': {
        'name': '麻雀',
        'colors': {
            'body': (160, 120, 70), 'body_d': (130, 95, 50),
            'belly': (220, 200, 170), 'wing': (130, 95, 50),
            'wing_d': (100, 70, 35), 'head': (140, 100, 55),
            'eye': (20, 15, 10), 'beak': (180, 140, 60),
            'feet': (140, 110, 60), 'cheek': (200, 160, 130),
            'heart': (255, 107, 138), 'zzz': (139, 164, 216),
            'crumb': (120, 85, 40),
        }
    },
    'cardinal': {
        'name': '红雀',
        'colors': {
            'body': (210, 50, 50), 'body_d': (180, 30, 30),
            'belly': (230, 80, 70), 'wing': (180, 30, 30),
            'wing_d': (140, 20, 20), 'head': (220, 60, 50),
            'eye': (20, 10, 10), 'beak': (255, 160, 40),
            'feet': (120, 80, 50), 'cheek': (255, 150, 150),
            'heart': (255, 107, 138), 'zzz': (180, 200, 230),
            'crumb': (180, 100, 50),
        }
    },
    'penguin': {
        'name': '企鹅',
        'colors': {
            'body': (40, 40, 50), 'body_d': (25, 25, 35),
            'belly': (230, 230, 240), 'wing': (50, 50, 60),
            'wing_d': (30, 30, 40), 'head': (35, 35, 45),
            'eye': (255, 255, 255), 'beak': (255, 160, 40),
            'feet': (255, 160, 40), 'cheek': (255, 180, 180),
            'heart': (255, 107, 138), 'zzz': (150, 180, 220),
            'crumb': (100, 100, 110),
        }
    },
    'owl': {
        'name': '猫头鹰',
        'colors': {
            'body': (140, 100, 60), 'body_d': (110, 75, 40),
            'belly': (200, 170, 130), 'wing': (110, 75, 40),
            'wing_d': (80, 55, 25), 'head': (150, 110, 65),
            'eye': (255, 200, 50), 'beak': (100, 80, 50),
            'feet': (100, 80, 50), 'cheek': (200, 150, 120),
            'heart': (255, 107, 138), 'zzz': (139, 164, 216),
            'crumb': (120, 85, 45),
        }
    },
    'flamingo': {
        'name': '火烈鸟',
        'colors': {
            'body': (255, 140, 160), 'body_d': (230, 110, 130),
            'belly': (255, 180, 195), 'wing': (230, 110, 130),
            'wing_d': (200, 80, 100), 'head': (255, 150, 170),
            'eye': (30, 20, 20), 'beak': (60, 60, 60),
            'feet': (255, 140, 100), 'cheek': (255, 180, 180),
            'heart': (255, 80, 120), 'zzz': (180, 200, 230),
            'crumb': (200, 120, 100),
        }
    },
}

# ---- 绘制函数 ----

def draw_base(img, C, ox=0, oy=0):
    fill_ellipse(img, 16+ox, 16+oy, 5, 6, C['body'])
    fill_ellipse(img, 16+ox, 17+oy, 4, 4, C['belly'])
    fill_ellipse(img, 16+ox, 10+oy, 3, 3, C['head'])
    fill_ellipse(img, 11+ox, 15+oy, 2, 3, C['wing'])
    put(img, 14+ox, 22+oy, C['feet'])
    put(img, 18+ox, 22+oy, C['feet'])

def draw_eyes(img, C, ox=0, oy=0, open=True):
    if open:
        put(img, 14+ox, 10+oy, C['eye'])
        put(img, 18+ox, 10+oy, C['eye'])
    else:
        for i in range(3):
            put(img, 13+i+ox, 10+oy, C['eye'])
            put(img, 17+i+ox, 10+oy, C['eye'])

def draw_beak(img, C, ox=0, oy=0, down=False):
    if down:
        put(img, 19+ox, 12+oy, C['beak'])
        put(img, 20+ox, 13+oy, C['beak'])
    else:
        put(img, 19+ox, 11+oy, C['beak'])
        put(img, 20+ox, 11+oy, C['beak'])

def gen_state(img_func, C, state, tick):
    f = new_frame()
    img_func(f, C, state, tick)
    return f

def idle_img(f, C, _, tick):
    dy = [0, -1, 0, 1][tick % 4]
    draw_base(f, C, oy=dy)
    draw_eyes(f, C, oy=dy)
    draw_beak(f, C, oy=dy)
    put(f, 14+dy, 12, C['cheek'])
    put(f, 18+dy, 12, C['cheek'])

def walk_img(f, C, _, tick):
    draw_base(f, C)
    draw_eyes(f, C)
    draw_beak(f, C)
    foot_l = 22 if tick % 2 == 0 else 23
    foot_r = 23 if tick % 2 == 0 else 22
    put(f, 14, foot_l, C['feet'])
    put(f, 18, foot_r, C['feet'])

def fly_img(f, C, _, tick):
    """飞行帧 — 翅膀大幅上下扇动"""
    # 身体随翅膀升降：翅上→身降，翅下→身升
    by = [17, 16, 15, 16][tick % 4]

    # 身体 + 肚皮
    fill_ellipse(f, 16, by, 5, 5, C['body'])
    fill_ellipse(f, 16, by + 1, 4, 3, C['belly'])
    # 头
    fill_ellipse(f, 16, by - 6, 3, 3, C['head'])

    # 翅膀（4帧：上、中上、下、中下）
    # 每帧画 3 段羽毛：内段(宽)→中段→外段(窄)
    wing_phases = [
        (-5, -3, -1),  # 翅膀上举
        (-2, -1, 0),   # 翅膀中上
        (1, 2, 3),     # 翅膀下压
        (-1, 0, 1),    # 翅膀中下
    ]
    wy = wing_phases[tick % 4]

    for side in (-1, 1):
        sx = 16 + side * 6  # 肩膀 x
        # 内段（靠近身体，较宽）
        for dy in range(-1, 2):
            fill_ellipse(f, sx + side * 1, by + wy[0] + dy, 2, 1, C['wing'])
        # 中段
        for dy in range(-1, 1):
            fill_ellipse(f, sx + side * 4, by + wy[1] + dy, 2, 1, C['wing_d'])
        # 外段（翼尖，窄）
        put(f, sx + side * 7, by + wy[2], C['wing_d'])
        put(f, sx + side * 7, by + wy[2] - 1, C['wing_d'])
        put(f, sx + side * 8, by + wy[2], C['wing_d'])

    # 眼睛
    draw_eyes(f, C, oy=by - 16)
    # 嘴巴
    draw_beak(f, C, oy=by - 16)
    # 脚
    put(f, 14, by + 6, C['feet'])
    put(f, 18, by + 6, C['feet'])

def eat_img(f, C, _, tick):
    head_off = [0, 1, 2, 1][tick % 4]
    fill_ellipse(f, 16, 16, 5, 5, C['body'])
    fill_ellipse(f, 16, 17, 4, 3, C['belly'])
    fill_ellipse(f, 18, 14+head_off, 3, 3, C['head'])
    put(f, 16, 14+head_off, C['eye'])
    put(f, 20, 14+head_off, C['eye'])
    put(f, 19, 18+head_off, C['beak'])
    fill_ellipse(f, 11, 15, 2, 3, C['wing'])
    put(f, 14, 22, C['feet'])
    put(f, 18, 22, C['feet'])
    if tick % 2 == 0:
        put(f, 20, 20, C['crumb'])

def sleep_img(f, C, _, tick):
    dy = [0, -1, 0, 0][tick % 4]
    draw_base(f, C, oy=dy)
    draw_eyes(f, C, open=False, oy=dy)
    draw_beak(f, C, oy=dy)
    z_z = tick % 3
    if z_z == 0: put(f, 24, 8+dy, C['zzz'])
    elif z_z == 1: put(f, 24, 7+dy, C['zzz']); put(f, 25, 6+dy, C['zzz'])
    else: put(f, 24, 6+dy, C['zzz']); put(f, 25, 5+dy, C['zzz']); put(f, 26, 4+dy, C['zzz'])

def pet_img(f, C, _, tick):
    dy = [0, -1, 0, 1][tick % 4]
    draw_base(f, C, oy=dy)
    put(f, 14, 12+dy, C['cheek'])
    put(f, 18, 12+dy, C['cheek'])
    for dx, ddy in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(0,1)]:
        put(f, 14+dx, 10+ddy+dy, C['heart'])
        put(f, 18+dx, 10+ddy+dy, C['heart'])
    for j in range(3): put(f, 15+j, 12+dy, C['beak'])
    draw_beak(f, C, oy=dy)
    if tick % 2 == 0:
        for dx, ddy in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(0,1)]:
            put(f, 24+dx, 4+ddy, C['heart'])

STATES = {
    'idle': idle_img, 'walk': walk_img, 'fly': fly_img,
    'eat': eat_img, 'sleep': sleep_img, 'pet': pet_img,
}

# ---- 主流程 ----

print("🎨 批量生成像素画小鸟素材...\n")

for bird_key, bird_def in BIRDS.items():
    bird_dir = os.path.join(BASE, bird_key)
    os.makedirs(bird_dir, exist_ok=True)
    C = bird_def['colors']

    for state, img_func in STATES.items():
        for i in range(4):
            f = gen_state(img_func, C, state, i)
            f.save(os.path.join(bird_dir, f'{state}_f{i}.png'))

    # 也生成总精灵图
    full = Image.new('RGBA', (32*4, 32*6), (0, 0, 0, 0))
    for row, (state, img_func) in enumerate(STATES.items()):
        for i in range(4):
            f = gen_state(img_func, C, state, i)
            full.paste(f, (i*32, row*32))
    full.save(os.path.join(bird_dir, 'all.png'))

    states_str = ', '.join(f'{s}×4' for s in STATES)
    print(f"  ✅ {bird_def['name']:6s} ({bird_key:10s}) → {states_str} = 24帧")

print(f"\n🎉 共 {len(BIRDS)} 种鸟 × 6状态 × 4帧 = {len(BIRDS)*24} 帧")
print(f"📁 输出目录: {BASE}/")
