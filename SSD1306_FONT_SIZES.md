# SSD1306 Font Size Options in MicroPython

The standard `ssd1306.text()` method uses a fixed 8×8 pixel font and doesn't support resizing directly. Here are the practical solutions:

## Method 1: Use Larger Spacing (Y-coordinates)
Simply increase the Y-spacing between lines to make text appear bigger by increasing whitespace.

```python
if OLED_AVAILABLE and display is not None:
    if menu == 10 and (menu_old != menu or volume_old != volume or squelch_old != squelch or ActiveFrequency_old != ActiveFrequency or StandbyFrequency_old != StandbyFrequency):
        display.fill(0)
        display.text(f"Vol:{volume:2d} Sq:{squelch:2d}", 0, 0, 1)      # Y=0
        display.text(f"Act:{ActiveFrequency[0]}.{ActiveFrequency[1]}", 0, 20, 1)   # Y=20 (larger gap)
        display.text(f"Stb:{StandbyFrequency[0]}.{StandbyFrequency[1]}", 0, 40, 1) # Y=40 (larger gap)
        display.show()
```

**Pros:** Simple, no extra dependencies  
**Cons:** Text still same pixel height, just more spaced

---

## Method 2: Draw Text Multiple Times (Pixel Doubling)
Manually draw text at overlapping positions to simulate larger font.

```python
def draw_large_text(display, text, x, y, scale=2, color=1):
    """Draw text with scale multiplier by redrawing at offset positions"""
    for i in range(scale):
        for j in range(scale):
            display.text(text, x + i, y + j, color)

# Usage:
if OLED_AVAILABLE and display is not None:
    if menu == 10 and (...):
        display.fill(0)
        draw_large_text(display, f"Vol:{volume:2d}", 0, 0, scale=2)    # 2x larger
        draw_large_text(display, f"Act:{ActiveFrequency[0]}.{ActiveFrequency[1]}", 0, 20, scale=2)
        draw_large_text(display, f"Stb:{StandbyFrequency[0]}.{StandbyFrequency[1]}", 0, 40, scale=2)
        display.show()
```

**Pros:** Simple scaling, no external fonts  
**Cons:** More CPU/memory, text becomes pixelated

---

## Method 3: Custom Large Font with FrameBuffer
Create a simple 2x scaled font using FrameBuffer for smoother scaling.

```python
import framebuf

def draw_scaled_text(display, text, x, y, scale=2, color=1):
    """Draw text with smooth scaling using FrameBuffer"""
    # Create buffer for text (8x8 per character for default font)
    width = len(text) * 8 * scale
    height = 8 * scale
    
    # Create a temporary framebuffer
    fbuf = framebuf.FrameBuffer(bytearray((width * height) // 8), width, height, framebuf.MONO_VLSB)
    
    # Draw text on temp buffer
    fbuf.text(text, 0, 0, 1)
    
    # Blit (paste) to main display at position
    display.blit(fbuf, x, y, -1)

# Usage:
if OLED_AVAILABLE and display is not None:
    if menu == 10 and (...):
        display.fill(0)
        draw_scaled_text(display, f"V:{volume}", 0, 0, scale=1)
        draw_scaled_text(display, f"A:{ActiveFrequency[0]}.{ActiveFrequency[1]}", 0, 20, scale=1)
        draw_scaled_text(display, f"S:{StandbyFrequency[0]}.{StandbyFrequency[1]}", 0, 40, scale=1)
        display.show()
```

**Pros:** Better control, relatively efficient  
**Cons:** More complex code

---

## Method 4: Use External Font Library (Recommended for Real Scalability)
Use `writer.py` or similar libraries for true scalable fonts.

```python
# First, upload writer.py and font files to Pico
# https://github.com/peterhinch/micropython-font-to-py

from writer import Writer
from machine import I2C, Pin
import ssd1306

# Initialize display
i2c = I2C(0, freq=400000, scl=Pin(9), sda=Pin(8))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

# Create writer with font
import ubuntu_mono_20  # or other font
w = Writer(display, ubuntu_mono_20)

# Draw text
w.set_clip(True, True, True)
w.printstring('Hello!')

display.show()
```

**Pros:** True scalable fonts, professional appearance  
**Cons:** Requires external files, more memory

---

## Method 5: Smart Compression (Y-offset optimization)
Adjust your code to use the exact Y-offsets that fit on 64-pixel display.

```python
if OLED_AVAILABLE and display is not None:
    if menu == 10:
        display.fill(0)
        
        # Line 1: Y=0 (pixels 0-7)
        display.text(f"Vol:{volume:2d} Sq:{squelch:2d}", 0, 0, 1)
        
        # Line 2: Y=18 (pixels 18-25) - leaves gap
        display.text(f"Act:{ActiveFrequency[0]}.{ActiveFrequency[1]}", 0, 18, 1)
        
        # Line 3: Y=36 (pixels 36-43) - leaves gap
        display.text(f"Stb:{StandbyFrequency[0]}.{StandbyFrequency[1]}", 0, 36, 1)
        
        # Line 4 would be Y=54 (pixels 54-61) - barely fits
        
        display.show()
```

---

## Recommended Solution for Your Code

**Option A - Simple (No code changes needed):**
```python
display.text(f"Vol:{volume:2d} Sq:{squelch:2d}", 0, 0, 1)
display.text(f"Act:{ActiveFrequency[0]}.{ActiveFrequency[1]}", 0, 20, 1)
display.text(f"Stb:{StandbyFrequency[0]}.{StandbyFrequency[1]}", 0, 40, 1)
```
This gives the appearance of larger text through spacing.

---

**Option B - Pixel Doubling (Best balance):**
Add this helper function at top of file:

```python
def draw_large_text(display, text, x, y, scale=2, color=1):
    """Draw text scaled 2x by repeating"""
    for i in range(scale):
        for j in range(scale):
            display.text(text, x + i, y + j, color)
```

Then use:
```python
display.fill(0)
draw_large_text(display, f"V:{volume:2d}", 0, 0, scale=2)
draw_large_text(display, f"A:{ActiveFrequency[0]}.{ActiveFrequency[1]}", 0, 20, scale=2)
draw_large_text(display, f"S:{StandbyFrequency[0]}.{StandbyFrequency[1]}", 0, 40, scale=2)
display.show()
```

---

## Font Size Reference

| Method | Text Height | CPU Use | Code Complexity |
|--------|------------|---------|-----------------|
| Default (Y-offset) | 8 pixels | Very Low | None |
| 2× Pixel Double | 16 pixels | Low | Low |
| 3× Pixel Double | 24 pixels | Medium | Low |
| External Font Lib | Variable | Medium-High | High |

---

## Your Code With Option B Applied

```python
# Add this helper function near the top after imports
def draw_large_text(display, text, x, y, scale=2, color=1):
    """Draw text with scale multiplier"""
    if not (display and OLED_AVAILABLE):
        return
    try:
        for i in range(scale):
            for j in range(scale):
                display.text(text, x + i, y + j, color)
    except Exception as e:
        print(f"Error drawing text: {e}")

# Then in your display section:
if OLED_AVAILABLE and display is not None:
    if menu == 10 and (menu_old != menu or volume_old != volume or squelch_old != squelch or ActiveFrequency_old != ActiveFrequency or StandbyFrequency_old != StandbyFrequency):
        display.fill(0)
        draw_large_text(display, f"Vol:{volume:2d} Sq:{squelch:2d}", 0, 0, scale=2)
        draw_large_text(display, f"Act:{ActiveFrequency[0]}.{ActiveFrequency[1]}", 0, 20, scale=2)
        draw_large_text(display, f"Stb:{StandbyFrequency[0]}.{StandbyFrequency[1]}", 0, 40, scale=2)
        display.show()
```

This gives you **2× larger text** while keeping your code simple!

