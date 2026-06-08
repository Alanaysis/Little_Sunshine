#!/usr/bin/env python3
"""
Little Sunshine - 桌面小鸟宠物 (PyQt6)
"""

import sys, json, math, random, os, time
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer, QPoint, QPointF, QRectF, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient, QLinearGradient,
    QPainterPath, QMouseEvent, QCursor, QFont, QRegion, QPolygonF, QPixmap
)
from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QLabel, QVBoxLayout, QHBoxLayout
from bird_skins import load_all_skins, BirdSkin

# ---- 常量 ----
S = 80
WIN_W, WIN_H = 400, 400
BIRD_X0, BIRD_Y0 = 160, 160

HUNGER_RATE = 0.005; ENERGY_SLEEP = 5.5; ENERGY_IDLE = 0.005; ENERGY_MOVE = 0.01
MOOD_DOWN = 0.02; MOOD_UP = 0.01; LOVE_DOWN = 0.001
HUNGER_PENALTY = 70; HUNGER_COMFORT = 30; ENERGY_LOW = 20; ENERGY_FLY = 30; HUNGER_WANDER = 60
EAT_MS = 2000; SLEEP_MS = 15000; SLEEP_TARGET = 80; PET_MS = 1500
WALK_MIN, WALK_MAX = 5000, 13000; BLINK_MIN, BLINK_MAX = 3000, 7000; BLINK_MS = 150
SAVE_MS = 5000; DT_CAP = 100; SPEED_WALK = 0.5; SPEED_FLY = 1.2
FEED_HUNGER = 30; FEED_MOOD = 10; PET_LOVE = 10; PET_MOOD = 15

STATE_EMOJI = {'idle': '😊', 'walk': '🚶', 'fly': '✈️', 'eat': '🍴', 'sleep': '😴', 'pet': '🥰'}
STATE_NAMES = {'idle': '发呆中', 'walk': '散步中', 'fly': '飞翔中', 'eat': '吃东西', 'sleep': '睡觉中', 'pet': '被摸摸'}

SAVE_FILE = Path.home() / '.little_sunshine.json'


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ---- 粒子系统 ----

class Particle:
    def __init__(self, x, y, vx, vy, life, size, color, kind='circle'):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.size = size
        self.color = color
        self.kind = kind
        self.rot = random.uniform(0, 6.28)
        self.rot_v = random.uniform(-0.1, 0.1)

    def update(self, dt):
        self.x += self.vx * dt * 0.06
        self.y += self.vy * dt * 0.06
        self.life -= dt
        self.rot += self.rot_v
        if self.kind == 'crumb':
            self.vy += dt * 0.003
        elif self.kind in ('heart', 'star'):
            self.vy -= dt * 0.001
            self.vx *= 0.99

    def draw(self, p):
        alpha = max(0, self.life / self.max_life)
        c = QColor(self.color)
        c.setAlphaF(alpha)
        p.save()
        p.translate(self.x, self.y)
        p.rotate(math.degrees(self.rot))
        p.setBrush(QBrush(c))
        p.setPen(Qt.PenStyle.NoPen)

        if self.kind == 'heart':
            path = QPainterPath()
            sz = self.size
            path.moveTo(0, sz * 0.3)
            path.cubicTo(0, 0, -sz, 0, -sz, sz * 0.3)
            path.cubicTo(-sz, sz * 0.8, 0, sz, 0, sz * 1.2)
            path.cubicTo(0, sz, sz, sz * 0.8, sz, sz * 0.3)
            path.cubicTo(sz, 0, 0, 0, 0, sz * 0.3)
            p.drawPath(path)
        elif self.kind == 'star':
            pts = []
            for i in range(5):
                a = i * 2.513 - 1.571
                pts.append(QPointF(math.cos(a) * self.size, math.sin(a) * self.size))
                a2 = a + 1.257
                pts.append(QPointF(math.cos(a2) * self.size * 0.4, math.sin(a2) * self.size * 0.4))
            p.drawPolygon(QPolygonF(pts))
        elif self.kind == 'sparkle':
            sz = self.size
            path = QPainterPath()
            path.moveTo(0, -sz); path.lineTo(sz * 0.3, -sz * 0.3)
            path.lineTo(sz, 0); path.lineTo(sz * 0.3, sz * 0.3)
            path.lineTo(0, sz); path.lineTo(-sz * 0.3, sz * 0.3)
            path.lineTo(-sz, 0); path.lineTo(-sz * 0.3, -sz * 0.3)
            path.closeSubpath()
            p.drawPath(path)
        else:
            p.drawEllipse(QPointF(0, 0), self.size, self.size)

        p.restore()

    @property
    def alive(self):
        return self.life > 0


# ---- 状态面板 ----

class StatusPanel(QWidget):
    """自定义状态面板，替代 QMenu"""
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(200)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self.title = QLabel()
        self.title.setStyleSheet('font-size: 15px; font-weight: 800; color: #4A3728;')
        layout.addWidget(self.title)

        self.bars = {}
        for name, color in [('mood', '#FF9EC6'), ('hunger', '#FF9F43'), ('energy', '#7BC67E'), ('love', '#FF6B8A')]:
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel({'mood': '心情', 'hunger': '饥饿', 'energy': '精力', 'love': '亲密'}[name])
            lbl.setStyleSheet('font-size: 12px; font-weight: 700; color: #8B7355; min-width: 30px;')
            row.addWidget(lbl)

            bar_bg = QWidget()
            bar_bg.setFixedHeight(10)
            bar_bg.setStyleSheet('background: rgba(0,0,0,0.06); border-radius: 5px;')
            bar_fill = QWidget(bar_bg)
            bar_fill.setStyleSheet(f'background: {color}; border-radius: 5px;')
            bar_fill.setFixedHeight(10)
            row.addWidget(bar_bg, 1)

            val = QLabel('0%')
            val.setStyleSheet('font-size: 11px; font-weight: 700; color: #4A3728; min-width: 32px;')
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(val)

            layout.addLayout(row)
            self.bars[name] = (bar_bg, bar_fill, val)

    def update_data(self, state, d):
        self.title.setText(f'{STATE_EMOJI[state]} {d.name}')
        for name, (bg, fill, val) in self.bars.items():
            v = getattr(d, name)
            val.setText(f'{v:.0f}%')
            # 延迟设置宽度（需要先 show）
            QTimer.singleShot(0, lambda f=fill, bg_=bg, v_=v: f.setFixedWidth(max(1, int(bg_.width() * v_ / 100))))

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 卡片背景
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 16, 16)
        g = QLinearGradient(0, 0, self.width(), self.height())
        g.setColorAt(0, QColor(255, 248, 240, 245))
        g.setColorAt(1, QColor(255, 240, 224, 245))
        p.fillPath(path, QBrush(g))
        p.setPen(QPen(QColor(240, 224, 204), 1.5))
        p.drawPath(path)
        # 阴影
        p.setPen(Qt.PenStyle.NoPen)
        shadow = QColor(0, 0, 0, 15)
        p.setBrush(QBrush(shadow))
        p.drawRoundedRect(QRectF(2, 2, self.width() - 4, self.height() - 4), 14, 14)
        p.end()


# ---- 数据 ----

class BirdData:
    def __init__(self):
        self.name = '小阳光'
        self.mood = 80.0; self.hunger = 30.0; self.energy = 90.0; self.love = 50.0
        self.state = 'idle'; self.x = float(BIRD_X0); self.y = float(BIRD_Y0)
        self.last_saved = 0; self.follow_mouse = False

    def save(self):
        self.last_saved = time.time()
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump({'name': self.name, 'mood': self.mood, 'hunger': self.hunger,
                           'energy': self.energy, 'love': self.love, 'state': self.state,
                           'x': self.x, 'y': self.y, 'last_saved': self.last_saved,
                           'follow_mouse': self.follow_mouse}, f)
        except Exception: pass

    def load(self):
        try:
            if not SAVE_FILE.exists(): return
            with open(SAVE_FILE) as f: d = json.load(f)
            self.name = d.get('name', '小阳光')
            self.mood = float(d.get('mood', 80)); self.hunger = float(d.get('hunger', 30))
            self.energy = float(d.get('energy', 90)); self.love = float(d.get('love', 50))
            self.state = d.get('state', 'idle')
            self.x = float(d.get('x', BIRD_X0)); self.y = float(d.get('y', BIRD_Y0))
            self.last_saved = d.get('last_saved', 0); self.follow_mouse = d.get('follow_mouse', False)
            elapsed = time.time() - self.last_saved; hours = elapsed / 3600
            self.hunger = min(100, self.hunger + hours * 10)
            if self.hunger > 70: self.mood = max(0, self.mood - hours * 3)
            self.x = clamp(self.x, 0, WIN_W - S); self.y = clamp(self.y, 0, WIN_H - S)
        except Exception: pass


# ---- 主窗口 ----

class BirdWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.d = BirdData(); self.d.load()

        # 状态机
        self.state = self.d.state; self.state_t = 0; self.anim_f = 0; self.anim_t = 0
        self.target_x = self.d.x; self.target_y = self.d.y; self.face_r = True
        self.blink_t = 0; self.blinking = False; self.next_blink = random.uniform(BLINK_MIN, BLINK_MAX)
        self.wander_t = 0; self.next_wander = random.uniform(WALK_MIN, WALK_MAX)
        self.save_t = 0

        # 拖拽
        self.dragging = False; self.drag_sx = 0; self.drag_sy = 0

        # 跟随鼠标
        self.follow_mouse = self.d.follow_mouse
        self.follow_cursor_pos = QPoint(0, 0)

        # 粒子
        self.particles = []

        # 皮肤系统
        self.all_skins = load_all_skins()
        # 默认使用第一个可用皮肤
        first_key = next(iter(self.all_skins), None)
        self.current_skin = self.all_skins.get(first_key)
        self.skin_name = first_key or ''

        # 状态面板
        self.status_panel = StatusPanel()
        self.status_visible = False

        # 窗口
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(WIN_W, WIN_H)
        cursor = QCursor.pos()
        self.move(cursor.x() - WIN_W // 2, cursor.y() - WIN_H // 2)
        self.setMouseTracking(True)
        self.update_input_mask()
        if self.follow_mouse:
            # 启动时鸟居中到屏幕
            screen = QApplication.primaryScreen().geometry()
            self.d.x = (screen.width() - S) / 2
            self.d.y = (screen.height() - S) / 2
            self._resize_for_follow()

        # 游戏循环
        self.last_time = time.time() * 1000
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

    # ---- 输入区域（X11 穿透） ----

    def update_input_mask(self):
        if os.environ.get('XDG_SESSION_TYPE') != 'x11': return
        try:
            cx, cy = int(self.d.x + S / 2), int(self.d.y + S / 2)
            r = int(S / 2 + 10)
            self.setMask(QRegion(cx - r, cy - r, r * 2, r * 2, QRegion.RegionType.Ellipse))
        except Exception: pass

    # ---- 窗口尺寸 ----

    def _resize_for_follow(self):
        if self.follow_mouse:
            # 记录鸟当前屏幕绝对坐标
            abs_x = self.x() + self.d.x
            abs_y = self.y() + self.d.y
            # 窗口铺满全屏
            screen = QApplication.primaryScreen().geometry()
            self.setFixedSize(screen.width(), screen.height())
            self.move(0, 0)
            # 鸟保持在原来的屏幕位置
            self.d.x = abs_x
            self.d.y = abs_y
            self.target_x = self.d.x; self.target_y = self.d.y
        else:
            # 记录鸟当前屏幕绝对坐标
            abs_x = self.x() + self.d.x
            abs_y = self.y() + self.d.y
            # 窗口缩回小尺寸，居中到鸟的位置
            self.setFixedSize(WIN_W, WIN_H)
            self.move(int(abs_x - WIN_W / 2), int(abs_y - WIN_H / 2))
            # 鸟在小窗口内居中
            self.d.x = (WIN_W - S) / 2
            self.d.y = (WIN_H - S) / 2
            self.target_x = self.d.x; self.target_y = self.d.y

    # ---- 游戏循环 ----

    def tick(self):
        now = time.time() * 1000
        dt = min(now - self.last_time, DT_CAP)
        self.last_time = now

        # 每帧读取光标位置（跟随模式）
        if self.follow_mouse and not self.dragging:
            self.follow_cursor_pos = self.mapFromGlobal(QCursor.pos())

        self.update_state(dt); self.update_decay(dt / 1000)
        self.update_particles(dt); self.spawn_effects(dt)

        self.save_t += dt
        if self.save_t >= SAVE_MS:
            self.save_t = 0; self.d.state = self.state; self.d.save()

        self.update_input_mask()
        self.update()

    def update_decay(self, dt):
        self.d.hunger = min(100, self.d.hunger + dt * HUNGER_RATE)
        if self.state == 'sleep': self.d.energy = min(100, self.d.energy + dt * ENERGY_SLEEP)
        elif self.state in ('walk', 'fly'): self.d.energy = max(0, self.d.energy - dt * ENERGY_MOVE)
        else: self.d.energy = min(100, self.d.energy + dt * ENERGY_IDLE)
        if self.d.hunger > HUNGER_PENALTY: self.d.mood = max(0, self.d.mood - dt * MOOD_DOWN)
        elif self.d.hunger < HUNGER_COMFORT and self.d.energy > 50: self.d.mood = min(100, self.d.mood + dt * MOOD_UP)
        self.d.love = max(0, self.d.love - dt * LOVE_DOWN)

    def set_state(self, s):
        self.state = s; self.state_t = 0; self.anim_f = 0; self.anim_t = 0
        if s == 'idle':
            self.wander_t = 0; self.next_wander = random.uniform(WALK_MIN, WALK_MAX)

    def update_state(self, dt):
        self.state_t += dt; self.anim_t += dt; self.wander_t += dt
        fr = {'walk': 200, 'fly': 150, 'eat': 100}.get(self.state, 500)
        if self.anim_t >= fr: self.anim_f += 1; self.anim_t = 0

        self.blink_t += dt
        if not self.blinking and self.blink_t > self.next_blink:
            self.blinking = True; self.blink_t = 0
        if self.blinking and self.blink_t > BLINK_MS:
            self.blinking = False; self.blink_t = 0
            self.next_blink = random.uniform(BLINK_MIN, BLINK_MAX)

        if self.dragging: return

        bx0, by0, bx1, by1 = 0, 0, self.width() - S, self.height() - S
        if self.state == 'idle':
            if self.follow_mouse:
                tx = clamp(self.follow_cursor_pos.x() - S / 2, bx0, bx1)
                ty = clamp(self.follow_cursor_pos.y() - S / 2, by0, by1)
                if math.hypot(tx - self.d.x, ty - self.d.y) > 3:
                    self.target_x = tx; self.target_y = ty
                    self.set_state('fly')
            else:
                if self.wander_t > self.next_wander:
                    self.wander_t = 0; self.next_wander = random.uniform(WALK_MIN, WALK_MAX)
                    if random.random() > 0.4:
                        self.target_x = clamp(self.target_x + random.uniform(-75, 75), bx0, bx1)
                        self.target_y = clamp(self.target_y + random.uniform(-40, 40), by0, by1)
                        self.set_state('walk')
                    elif self.d.energy > ENERGY_FLY and random.random() > 0.5:
                        self.target_x = clamp(self.target_x + random.uniform(-100, 100), bx0, bx1)
                        self.target_y = clamp(random.uniform(0, by1), by0, by1)
                        self.set_state('fly')
                if self.d.hunger > HUNGER_WANDER and self.wander_t > 2000:
                    self.wander_t = 0
                    self.target_x = clamp(self.target_x + random.uniform(-50, 50), bx0, bx1)
                    self.target_y = clamp(self.target_y + random.uniform(-30, 30), by0, by1)
                    self.set_state('walk')
                if self.d.energy < ENERGY_LOW and self.d.hunger < HUNGER_WANDER:
                    self.set_state('sleep')

        if self.state == 'walk':
            if self.follow_mouse:
                self.set_state('fly')
            dx, dy = self.target_x - self.d.x, self.target_y - self.d.y
            dist = math.hypot(dx, dy)
            if dist > 3:
                self.d.x += dx / dist * SPEED_WALK * dt; self.d.y += dy / dist * SPEED_WALK * dt
                self.face_r = dx > 0
            elif not self.follow_mouse:
                self.set_state('idle')

        if self.state == 'fly':
            if self.follow_mouse:
                tx = clamp(self.follow_cursor_pos.x() - S / 2, bx0, bx1)
                ty = clamp(self.follow_cursor_pos.y() - S / 2, by0, by1)
                self.target_x = tx; self.target_y = ty
            dx, dy = self.target_x - self.d.x, self.target_y - self.d.y
            dist = math.hypot(dx, dy)
            if dist > 1:
                # 到达减速：远处匀速，近处渐停
                if self.follow_mouse:
                    speed = min(SPEED_FLY * 0.4, dist * 0.015)
                else:
                    speed = SPEED_FLY
                self.d.x += dx / dist * speed * dt; self.d.y += dy / dist * speed * dt
                self.face_r = dx > 0
            elif not self.follow_mouse:
                self.set_state('idle')

        if self.state == 'eat' and self.state_t > EAT_MS:
            self.d.hunger = max(0, self.d.hunger - FEED_HUNGER)
            self.d.mood = min(100, self.d.mood + FEED_MOOD)
            self.set_state('idle')
        if self.state == 'sleep' and (self.d.energy >= SLEEP_TARGET or self.state_t > SLEEP_MS):
            self.set_state('idle')
        if self.state == 'pet' and self.state_t > PET_MS:
            self.set_state('idle')

    # ---- 粒子 ----

    def update_particles(self, dt):
        for p in self.particles: p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def spawn_effects(self, _dt):
        cx, cy = self.d.x + S / 2, self.d.y + S / 3
        # idle 星星
        if self.state == 'idle' and random.random() < 0.02:
            self.particles.append(Particle(
                cx + random.uniform(-30, 30), cy + random.uniform(-30, 30),
                random.uniform(-0.3, 0.3), random.uniform(-0.8, -0.3),
                random.uniform(800, 1400), random.uniform(2, 4),
                random.choice(['#FFE066', '#FFCC02', '#FFB84D']), 'sparkle'))
        # 吃东西碎屑
        if self.state == 'eat' and random.random() < 0.3:
            self.particles.append(Particle(
                cx + 8, cy + 5,
                random.uniform(-1, 1), random.uniform(-2, -0.5),
                random.uniform(400, 800), random.uniform(1.5, 3),
                random.choice(['#C68A4E', '#8B6914']), 'crumb'))
        # 睡觉 zzz
        if self.state == 'sleep' and random.random() < 0.04:
            self.particles.append(Particle(
                cx + 20, cy - 20, 0.3, -0.6,
                random.uniform(1500, 2500), 5, '#8BA4D8', 'circle'))
        # 饥饿星星
        if self.d.hunger > 70 and self.state == 'idle' and random.random() < 0.03:
            self.particles.append(Particle(
                cx + random.uniform(-10, 10), cy - 30,
                random.uniform(-0.3, 0.3), -0.6, 800, 3, '#FF9F43', 'star'))

    def spawn_burst(self, kind, count):
        cx, cy = self.d.x + S / 2, self.d.y + S / 3
        for _ in range(count):
            if kind == 'sparkle':
                self.particles.append(Particle(
                    cx + random.uniform(-15, 15), cy + random.uniform(-10, 10),
                    random.uniform(-1.5, 1.5), random.uniform(-2.5, -0.5),
                    random.uniform(400, 800), random.uniform(3, 5),
                    '#FFB84D', 'sparkle'))
            elif kind == 'heart':
                self.particles.append(Particle(
                    cx + random.uniform(-20, 20), cy + random.uniform(-10, 10),
                    random.uniform(-1, 1), random.uniform(-1.5, -0.5),
                    random.uniform(800, 1400), random.uniform(4, 6),
                    random.choice(['#FF6B8A', '#FF9EC6']), 'heart'))

    # ---- 绘制 ----

    def paintEvent(self, _event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = time.time()
        self.draw_glow(p, t); self.draw_shadow(p, t)
        for pt in self.particles: pt.draw(p)
        self.draw_bird(p, t); self.draw_hunger(p, t)
        p.end()

    def draw_glow(self, p, t):
        cx, cy = self.d.x + S / 2, self.d.y + S / 2
        if self.state == 'pet': color, r = QColor(255, 107, 138), 65
        elif self.state == 'sleep': color, r = QColor(139, 164, 216), 40
        elif self.state == 'eat': color, r = QColor(255, 184, 77), 55
        elif self.d.hunger > 60: color, r = QColor(255, 159, 67), 50
        else: color, r = QColor(255, 217, 61), 50
        pulse = 0.6 + math.sin(t * 2) * 0.15
        g = QRadialGradient(QPointF(cx, cy), r)
        c = QColor(color); c.setAlphaF(pulse * 0.25); g.setColorAt(0, c)
        c2 = QColor(color); c2.setAlphaF(pulse * 0.1); g.setColorAt(0.5, c2)
        c3 = QColor(color); c3.setAlphaF(0); g.setColorAt(1, c3)
        p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), r, r)

    def draw_shadow(self, p, t):
        x, y = self.d.x + S / 2, self.d.y + S * 0.45
        sc = 0.6 + math.sin(t * 3) * 0.1 if self.state == 'fly' else 0.85 if self.state == 'sleep' else 1.0
        g = QRadialGradient(QPointF(x, y), S * 0.35 * sc)
        g.setColorAt(0, QColor(80, 50, 20, 30)); g.setColorAt(1, QColor(80, 50, 20, 0))
        p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(x, y), S * 0.35 * sc, 6 * sc)

    def draw_bird(self, p, t):
        # 优先用精灵图渲染
        if self.current_skin and self.current_skin.has_state(self.state):
            pm = self.current_skin.get_pixmap(self.state, self.anim_f, size=S)
            if pm:
                p.save()
                bx = self.d.x + (S - pm.width()) / 2
                by = self.d.y + (S - pm.height()) / 2
                if not self.face_r:
                    p.translate(bx + pm.width(), 0)
                    p.scale(-1, 1)
                    bx = 0
                p.drawPixmap(int(bx), int(by), pm)
                p.restore()
                return

        # fallback: 代码绘制
        x, y, s = self.d.x, self.d.y, S
        p.save()
        p.translate(x + s / 2, y + s / 2)
        if not self.face_r: p.scale(-1, 1)

        bob = {'idle': math.sin(t * 2) * 2, 'fly': math.sin(t * 6) * 5, 'pet': math.sin(t * 4) * 1.5}.get(self.state, 0)
        p.translate(0, bob)

        # 身体
        g = QRadialGradient(QPointF(-5, -5), s * 0.45)
        g.setColorAt(0, QColor('#FFE066')); g.setColorAt(0.6, QColor('#FFD93D')); g.setColorAt(1, QColor('#F0B800'))
        p.setBrush(QBrush(g)); p.setPen(QPen(QColor('#E8B800'), 1.2))
        p.drawEllipse(QPointF(0, 0), s * 0.35, s * 0.4)

        # 肚皮
        p.setBrush(QBrush(QColor('#FFF5CC'))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(0, s * 0.05), s * 0.25, s * 0.3)

        # 翅膀（多段关节）
        if self.state == 'fly':
            ph = t * 12
            shoulder_a = math.sin(ph) * 0.5
            mid_a = math.sin(ph - 0.6) * 0.9
            tip_a = math.sin(ph - 1.2) * 1.2
        else:
            wa = {'idle': math.sin(t * 1.5) * 0.1}.get(self.state, math.sin(t * 4) * 0.3)
            shoulder_a = wa * 0.4; mid_a = wa * 0.7; tip_a = wa
        for side in (-1, 1):
            p.save()
            p.translate(side * s * 0.28, -s * 0.05)
            # 肩
            p.rotate(math.degrees(side * shoulder_a + side * 0.2))
            wg1 = QRadialGradient(QPointF(0, 0), s * 0.18)
            wg1.setColorAt(0, QColor('#FFCC44')); wg1.setColorAt(1, QColor('#FFB800'))
            p.setBrush(QBrush(wg1)); p.setPen(QPen(QColor('#E8A000'), 0.8))
            p.drawEllipse(QPointF(0, 0), s * 0.12, s * 0.18)
            # 中段（二级飞羽）
            p.translate(0, -s * 0.16)
            p.rotate(math.degrees(side * (mid_a - shoulder_a) + side * 0.3))
            wg2 = QRadialGradient(QPointF(0, 0), s * 0.22)
            wg2.setColorAt(0, QColor('#FFCC44')); wg2.setColorAt(1, QColor('#FFB000'))
            p.setBrush(QBrush(wg2)); p.setPen(QPen(QColor('#E8A000'), 0.8))
            p.drawEllipse(QPointF(0, 0), s * 0.10, s * 0.22)
            # 翼尖（初级飞羽）
            p.translate(0, -s * 0.20)
            p.rotate(math.degrees(side * (tip_a - mid_a)))
            wg3 = QRadialGradient(QPointF(0, 0), s * 0.16)
            wg3.setColorAt(0, QColor('#FFCC44')); wg3.setColorAt(1, QColor('#E8A000'))
            p.setBrush(QBrush(wg3)); p.setPen(QPen(QColor('#D49000'), 0.8))
            p.drawEllipse(QPointF(0, 0), s * 0.07, s * 0.16)
            # 羽尖
            p.translate(0, -s * 0.14)
            p.rotate(math.degrees(side * (tip_a - mid_a) * 0.5))
            p.setBrush(QBrush(QColor('#FFB800')))
            p.drawEllipse(QPointF(0, 0), s * 0.04, s * 0.10)
            p.restore()

        # 头
        hg = QRadialGradient(QPointF(-3, -s * 0.38), s * 0.25)
        hg.setColorAt(0, QColor('#FFE066')); hg.setColorAt(1, QColor('#FFD93D'))
        p.setBrush(QBrush(hg)); p.setPen(QPen(QColor('#E8B800'), 1.2))
        p.drawEllipse(QPointF(0, -s * 0.35), s * 0.22, s * 0.22)

        # 腮红
        if self.state == 'pet' or self.d.mood > 80:
            alpha = 90 if self.state == 'pet' else 40
            p.setBrush(QBrush(QColor(255, 130, 130, alpha))); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(-s * 0.15, -s * 0.28), 5, 3)
            p.drawEllipse(QPointF(s * 0.15, -s * 0.28), 5, 3)

        # 眼睛
        if self.state == 'sleep':
            p.setPen(QPen(QColor('#6B5B4A'), 2)); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(-s * 0.08 - 4, -s * 0.38 - 4, 8, 8))
            p.drawEllipse(QRectF(s * 0.08 - 4, -s * 0.38 - 4, 8, 8))
        elif self.blinking:
            p.setPen(QPen(QColor('#6B5B4A'), 1.8))
            p.drawLine(QPointF(-s * 0.1, -s * 0.38), QPointF(-s * 0.02, -s * 0.38))
            p.drawLine(QPointF(s * 0.02, -s * 0.38), QPointF(s * 0.1, -s * 0.38))
        elif self.state == 'pet':
            p.setBrush(QBrush(QColor('#FF6B8A'))); p.setPen(Qt.PenStyle.NoPen)
            self._heart(p, -s * 0.08, -s * 0.4, 7); self._heart(p, s * 0.08, -s * 0.4, 7)
        else:
            p.setBrush(QBrush(QColor('#3D2E1F'))); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(-s * 0.08, -s * 0.38), 3.5, 3.5)
            p.drawEllipse(QPointF(s * 0.08, -s * 0.38), 3.5, 3.5)
            p.setBrush(QBrush(QColor('white')))
            p.drawEllipse(QPointF(-s * 0.06, -s * 0.4), 1.8, 1.8)
            p.drawEllipse(QPointF(s * 0.1, -s * 0.4), 1.8, 1.8)

        # 嘴巴
        p.setBrush(QBrush(QColor('#FF8C00')))
        if self.state == 'eat' and self.anim_f % 2 == 0:
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(s * 0.12 - 5, -s * 0.3 - 6, 10, 12))
        elif self.state == 'pet':
            p.setPen(QPen(QColor('#6B5B4A'), 1.5)); p.setBrush(Qt.BrushStyle.NoBrush)
            path = QPainterPath(); path.arcMoveTo(QRectF(-6, -s * 0.28 - 6, 12, 12), 0)
            path.arcTo(QRectF(-6, -s * 0.28 - 6, 12, 12), 6, 170); p.drawPath(path)
        else:
            p.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.moveTo(s * 0.12, -s * 0.32); path.lineTo(s * 0.2, -s * 0.28)
            path.lineTo(s * 0.12, -s * 0.25); path.closeSubpath(); p.drawPath(path)

        # 脚
        lo = math.sin(t * 8) * 3 if self.state == 'walk' else 0
        p.setBrush(QBrush(QColor('#FF8C00'))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(-s * 0.1 + lo - 5, s * 0.35 - 3, 10, 6))
        p.drawEllipse(QRectF(s * 0.1 - lo - 5, s * 0.35 - 3, 10, 6))

        p.restore()

    def _heart(self, p, x, y, sz):
        path = QPainterPath()
        path.moveTo(x, y + sz / 4)
        path.cubicTo(x, y, x - sz / 2, y, x - sz / 2, y + sz / 4)
        path.cubicTo(x - sz / 2, y + sz / 2, x, y + sz * 0.75, x, y + sz)
        path.cubicTo(x, y + sz * 0.75, x + sz / 2, y + sz / 2, x + sz / 2, y + sz / 4)
        path.cubicTo(x + sz / 2, y, x, y, x, y + sz / 4)
        p.drawPath(path)

    def draw_hunger(self, p, t):
        if self.d.hunger <= 60: return
        f = QFont('sans-serif', 14); f.setBold(self.d.hunger > 80); p.setFont(f)
        p.setPen(QColor('#FF4444') if self.d.hunger > 80 else QColor('#FF6B6B'))
        p.drawText(QPointF(self.d.x + S * 0.6, self.d.y - 10 + math.sin(t * 3) * 3),
                   '🍖!!' if self.d.hunger > 80 else '🍖?')

    # ---- 鼠标 ----

    def hit_bird(self, pos):
        return math.hypot(pos.x() - self.d.x - S / 2, pos.y() - self.d.y - S / 2) < S / 2 + 10

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton and self.hit_bird(e.pos()):
            self.dragging = True
            self.drag_sx = e.globalPosition().x(); self.drag_sy = e.globalPosition().y()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            if self.state != 'fly': self.set_state('fly')
        elif e.button() == Qt.MouseButton.RightButton and self.hit_bird(e.pos()):
            self._show_menu(e.globalPosition().toPoint())

    def mouseMoveEvent(self, e: QMouseEvent):
        if self.dragging:
            gx, gy = e.globalPosition().x(), e.globalPosition().y()
            dx, dy = gx - self.drag_sx, gy - self.drag_sy
            self.drag_sx = gx; self.drag_sy = gy
            self.move(self.x() + int(dx), self.y() + int(dy))
        else:
            self.setCursor(Qt.CursorShape.OpenHandCursor if self.hit_bird(e.pos()) else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False; self.setCursor(Qt.CursorShape.ArrowCursor)
            QTimer.singleShot(500, lambda: self.set_state('idle') if self.state == 'fly' else None)

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton and self.hit_bird(e.pos()) and self.state != 'eat':
            self.set_state('eat'); self.spawn_burst('sparkle', 5)

    # ---- 菜单 ----

    def _show_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #FFF8F0, stop:1 #FFF0E0);
                border: 1.5px solid #F0E0CC; border-radius: 12px; padding: 6px;
                font-size: 13px; font-weight: 600; color: #4A3728;
            }
            QMenu::item { padding: 8px 24px; border-radius: 8px; }
            QMenu::item:selected { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #FFD49A, stop:1 #FFB84D); }
        """)
        feed = menu.addAction('🌽 喂食'); pet = menu.addAction('💕 摸摸头')
        follow_label = '🖱️ 取消跟随' if self.follow_mouse else '🖱️ 跟随鼠标'
        follow = menu.addAction(follow_label)
        menu.addSeparator(); status = menu.addAction('📊 查看状态')

        # 皮肤子菜单
        skin_menu = menu.addMenu('🎨 换皮肤')
        skin_menu.setStyleSheet(menu.styleSheet())
        for skin_key, skin_obj in sorted(self.all_skins.items()):
            label = f'  {skin_obj.display_name}'
            if skin_key == self.skin_name:
                label = f'✓ {skin_obj.display_name}'
            act = skin_menu.addAction(label)
            act.setData(skin_key)

        menu.addSeparator(); quit_a = menu.addAction('👋 再见')

        action = menu.exec(pos)
        if action == feed and self.state != 'eat':
            self.set_state('eat'); self.spawn_burst('sparkle', 5)
        elif action == pet and self.state != 'pet':
            self.set_state('pet')
            self.d.love = min(100, self.d.love + PET_LOVE); self.d.mood = min(100, self.d.mood + PET_MOOD)
            self.spawn_burst('heart', 6)
        elif action == follow:
            self.follow_mouse = not self.follow_mouse
            self.d.follow_mouse = self.follow_mouse
            self._resize_for_follow()
        elif action == status:
            self._toggle_status()
        elif action == quit_a:
            self.d.state = self.state; self.d.save(); QApplication.quit()
        elif action and action.data() and action.data() in self.all_skins:
            self.current_skin = self.all_skins[action.data()]
            self.skin_name = action.data()
            self.update()

    def _toggle_status(self):
        if self.status_visible:
            self.status_panel.hide(); self.status_visible = False
        else:
            self.status_panel.update_data(self.state, self.d)
            px = self.x() + S + 10; py = self.y()
            if px + 210 > self.x() + WIN_W: px = self.x() - 210
            self.status_panel.move(px, py); self.status_panel.show()
            self.status_visible = True


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = BirdWindow(); window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
