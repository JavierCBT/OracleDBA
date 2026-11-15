from PIL import Image, ImageDraw, ImageFont
import os

def create_pwa_icon(size, out_path):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background rounded rect
    corner_radius = int(size * 0.22)
    draw.rounded_rectangle([0, 0, size, size], radius=corner_radius, fill=(15, 23, 42, 255))
    
    # Outer circle accent
    margin = int(size * 0.1)
    draw.ellipse([margin, margin, size - margin, size - margin], outline=(56, 189, 248, 120), width=int(size * 0.015))
    
    # Database cylinders
    cx = size // 2
    cw = int(size * 0.55)
    left = cx - cw // 2
    right = cx + cw // 2
    
    # Bottom disk
    y3 = int(size * 0.6)
    draw.ellipse([left, y3, right, y3 + int(size * 0.14)], fill=(2, 132, 199, 255))
    draw.rectangle([left, y3 + int(size * 0.07), right, y3 + int(size * 0.14)], fill=(2, 132, 199, 255))
    
    # Middle disk
    y2 = int(size * 0.46)
    draw.ellipse([left, y2, right, y2 + int(size * 0.14)], fill=(3, 105, 161, 255))
    draw.rectangle([left, y2 + int(size * 0.07), right, y2 + int(size * 0.14)], fill=(3, 105, 161, 255))
    
    # Top disk
    y1 = int(size * 0.32)
    draw.ellipse([left, y1, right, y1 + int(size * 0.14)], fill=(14, 165, 233, 255))
    draw.rectangle([left, y1 + int(size * 0.07), right, y1 + int(size * 0.14)], fill=(14, 165, 233, 255))
    draw.ellipse([left, y1, right, y1 + int(size * 0.14)], fill=(125, 211, 252, 255))
    
    # Green checkmark badge
    badge_r = int(size * 0.1)
    bx = int(size * 0.76)
    by = int(size * 0.32)
    draw.ellipse([bx - badge_r, by - badge_r, bx + badge_r, by + badge_r], fill=(16, 185, 129, 255), outline=(15, 23, 42, 255), width=int(size * 0.02))
    
    # Checkmark lines
    stroke = max(2, int(size * 0.025))
    p1 = (bx - int(badge_r * 0.4), by)
    p2 = (bx - int(badge_r * 0.1), by + int(badge_r * 0.35))
    p3 = (bx + int(badge_r * 0.5), by - int(badge_r * 0.35))
    draw.line([p1, p2, p3], fill=(255, 255, 255, 255), width=stroke, joint='curve')
    
    # Text badge at bottom: '19c'
    tb_w = int(size * 0.4)
    tb_h = int(size * 0.1)
    tb_x = cx - tb_w // 2
    tb_y = int(size * 0.78)
    draw.rounded_rectangle([tb_x, tb_y, tb_x + tb_w, tb_y + tb_h], radius=int(tb_h * 0.4), fill=(2, 132, 199, 255))
    
    img.save(out_path, 'PNG')
    print(f"Created {out_path} ({size}x{size})")

os.makedirs('assets/icons', exist_ok=True)
create_pwa_icon(192, 'assets/icons/icon-192.png')
create_pwa_icon(512, 'assets/icons/icon-512.png')
