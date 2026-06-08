#!/usr/bin/env python3
"""
Little Sunshine - 鸟类皮肤管理器
支持从 spritesheet 加载 PNG 帧，支持多种格式。
"""

import os
from pathlib import Path
from PyQt6.QtGui import QImage, QPixmap, QTransform

ASSETS_DIR = Path(__file__).parent / 'assets' / 'bird'


def load_frames_from_sheet(path, frame_w, frame_h, count=None):
    """从精灵图加载帧"""
    img = QImage(str(path))
    if img.isNull():
        return []
    cols = img.width() // frame_w
    rows = img.height() // frame_h
    frames = []
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if count and idx >= count:
                break
            x, y = c * frame_w, r * frame_w if False else r * frame_h
            frame = img.copy(x, y, frame_w, frame_h)
            if not frame.isNull():
                frames.append(frame)
            idx += 1
    return frames


def load_frames_from_dir(dirpath, prefix='', suffix='.png'):
    """从目录加载 PNG 帧，按文件名排序"""
    frames = []
    if not os.path.isdir(dirpath):
        return frames
    for f in sorted(os.listdir(dirpath)):
        if f.startswith(prefix) and f.endswith(suffix):
            img = QImage(os.path.join(dirpath, f))
            if not img.isNull():
                frames.append(img)
    return frames


def load_gif_frames(path):
    """从 GIF 加载帧"""
    img = QImage(str(path))
    if img.isNull():
        return []
    frames = []
    # PyQt6 的 QImageReader 不直接支持 GIF 多帧
    # 用临时 PIL 加载
    try:
        from PIL import Image as PILImage
        pil = PILImage.open(str(path))
        while True:
            pil_frame = pil.copy().convert('RGBA')
            data = pil_frame.tobytes()
            qimg = QImage(data, pil_frame.width, pil_frame.height,
                          QImage.Format.Format_RGBA8888)
            frames.append(qimg.copy())
            try:
                pil.seek(pil.tell() + 1)
            except EOFError:
                break
    except Exception:
        pass
    return frames


# ---- 皮肤定义 ----

class BirdSkin:
    """一个鸟皮肤，包含各状态的动画帧"""
    def __init__(self, name, display_name=None):
        self.name = name
        self.display_name = display_name or name
        # {state: [QImage, QImage, ...]}
        self.frames = {}
        self.frame_scale = 1.0  # 帧缩放比例

    def has_state(self, state):
        return state in self.frames and len(self.frames[state]) > 0

    def get_frame(self, state, index):
        frames = self.frames.get(state, [])
        if not frames:
            return None
        return frames[index % len(frames)]

    def get_pixmap(self, state, index, size=80):
        frame = self.get_frame(state, index)
        if frame is None:
            return None
        return QPixmap.fromImage(frame).scaled(
            int(size * self.frame_scale), int(size * self.frame_scale),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )


from PyQt6.QtCore import Qt




def _load_custom():
    """加载所有鸟类素材（逐帧 PNG 格式）"""
    skins = {}
    states = ['idle', 'walk', 'fly', 'eat', 'sleep', 'pet']

    # 扫描 assets/bird/ 下的所有子目录
    if not ASSETS_DIR.exists():
        return skins

    for bird_dir in sorted(ASSETS_DIR.iterdir()):
        if not bird_dir.is_dir():
            continue

        # 检查是否包含状态帧文件
        has_frames = any(list(bird_dir.glob(f'{s}_f*.png')) for s in states)
        if not has_frames:
            continue

        skin = BirdSkin(bird_dir.name, bird_dir.name)
        for state in states:
            frames = load_frames_from_dir(bird_dir, prefix=f'{state}_f')
            if frames:
                skin.frames[state] = frames

        if skin.frames:
            skins[bird_dir.name] = skin

    return skins


def load_all_skins():
    """加载所有可用皮肤"""
    skins = {}
    birds = _load_custom()
    skins.update(birds)
    return skins


if __name__ == '__main__':
    skins = load_all_skins()
    for name, skin in skins.items():
        states = list(skin.frames.keys())
        counts = {s: len(f) for s, f in skin.frames.items()}
        print(f"{name:30s} states={states}  counts={counts}")
