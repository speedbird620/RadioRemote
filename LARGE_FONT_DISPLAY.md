# SSD1306 Large Character Display for Raspberry Pi Pico MicroPython

## Overview

Updated the KTR2 display code to use **large bitmap characters** for improved readability on the SSD1306 OLED display. This follows the approach from Hackster's "Big Characters on SSD1306" project, adapted for MicroPython.

## Implementation Details

### 1. **Bitmap Font Data** (Lines 175-193)
```python
LARGE_FONT_DATA = {
    '0': [0x7E, 0x81, 0x81, 0x81, 0x7E],  # 5x7 pixel bitmap
    '1': [0x00, 0x41, 0xFF, 0x01, 0x00],
    # ... more digits and characters
}
```

- Each character is defined as a 5×7 pixel bitmap
- Stores 5 bytes per character (5 columns, each byte = 7 pixels)
- Supports digits 0-9, decimal point, colon, and space
- Easy to extend with more characters (A-Z, symbols, etc.)

### 2. **Character Drawing Function** (Lines 195-218)
```python
def draw_large_char(display, char, x, y, scale=2):
```

**Features:**
- Takes bitmap data and scales it by pixel multiplication
- `scale=1`: 5×7 pixels per character
- `scale=2`: 10×14 pixels per character (recommended)
- `scale=3`: 15×21 pixels per character
- Uses `display.pixel()` to draw individual pixels
- Boundary checking to prevent overflow

**How it works:**
1. Gets bitmap data for the character
2. For each column (5 bits wide)
3. For each row (7 bits tall)
4. If bit is set, draw scaled pixel(s)

### 3. **Text Drawing Function** (Lines 220-227)
```python
def draw_large_text(display, text, x, y, scale=2):
```

- Draws multiple characters with proper spacing
- Each character is 5×scale pixels wide
- Adds 1×scale pixel spacing between characters
- Called from display update code

## Display Updates

### Menu 10 - Active Frequency Display
```
V:XX S:XX
[Large Frequency Display]
```
- Small text: Volume and Squelch at top
- Large text: Active frequency (e.g., "118.550")

### Menu 20 - MHz Selection
```
MHz SELECT
[Large MHz Number]
```
- Header indicates selection mode
- Large MHz value (e.g., "123")

### Menu 30 - kHz Coarse Selection (±10)
```
kHz SELECT (x10)
[Large kHz Tens]xx
MHz:123
```
- Shows tens digit large
- Indicates "xx" for ones/hundredths

### Menu 40 - kHz Fine Selection (±1)
```
kHz SELECT (x1)
[Large kHz Value]
```
- Full kHz value displayed large
- Most precise frequency display

## Character Set

| Character | Support | Bitmap |
|-----------|---------|--------|
| 0-9 | ✅ Full | 5×7 pixel bitmaps |
| . (decimal) | ✅ Yes | Dot only |
| : (colon) | ✅ Yes | For time display |
| Space | ✅ Yes | Empty 5×7 |
| A-Z | ❌ Not included | Can be added |
| a-z | ❌ Not included | Can be added |

## Display Characteristics

| Property | Value |
|----------|-------|
| **Display Size** | 128×64 pixels |
| **I2C Address** | 0x3C |
| **GPIO Pins** | GPIO8 (SDA), GPIO9 (SCL) |
| **I2C Frequency** | 400 kHz |
| **Text Size (scale=2)** | 10×14 pixels per character |
| **Chars per line** | ~12 characters max |

## Usage Examples

### Draw single large character
```python
draw_large_char(display, '5', 0, 0, scale=2)
```

### Draw large text string
```python
draw_large_text(display, "118.55", 0, 12, scale=2)
```

### Different scales
```python
draw_large_text(display, "123", 0, 0, scale=1)  # 5×7 px chars
draw_large_text(display, "456", 0, 0, scale=2)  # 10×14 px chars
draw_large_text(display, "789", 0, 0, scale=3)  # 15×21 px chars
```

## Extending the Font

### Adding a New Character
```python
LARGE_FONT_DATA['A'] = [0x7E, 0x11, 0x11, 0x11, 0x7E]  # Example bitmap
```

### Understanding Bitmap Format
Each byte represents one column (7 bits = 7 pixels vertical):
```
Byte: 0x7E = 0111 1110 (binary)
       ▓▓▓▓▓░░  <- bit 7 (top)
       ▓▓▓▓▓░░  <- bit 6
       ░░░░░░░  <- bit 5
       ░░░░░░░  <- bit 4
       ░░░░░░░  <- bit 3
       ░░░░░░░  <- bit 2
       ░░░░░░░  <- bit 1
```

## Performance Considerations

| Scale | Chars/Update | CPU Time | Recommended Use |
|-------|-------------|----------|-----------------|
| 1 | High (~30) | Very Low | Small indicators |
| 2 | Medium (~12) | Low | Primary display |
| 3 | Low (~6) | Medium | Focus numbers |

## Benefits of Bitmap Font Approach

✅ **Advantages:**
- No external font files needed
- Works on minimal hardware
- Fully customizable fonts
- Efficient for embedded systems
- Easy to understand code

❌ **Limitations:**
- Only characters you define are available
- Manual bitmap creation needed for new fonts
- Less stylistic variety vs. TrueType fonts

## Code Structure Preserved

✅ **No changes to:**
- UART communication (serialData)
- Frequency arrays (HexArray, DecArray)
- Button input handling
- Message parsing logic
- Menu navigation system
- State tracking variables

✅ **Only updated:**
- Display initialization (added ssd1306 module)
- Display output (from print to SSD1306)
- Added large font bitmap data
- Added character/text drawing functions

## Related Resources

- **Original Project:** https://github.com/jdmorise/AVR_SSD1306_bigchar_demo
- **Font Generator:** https://github.com/jdmorise/TTF2BMH
- **Font Library:** https://github.com/jdmorise/AVR_BMH-fonts
- **MicroPython SSD1306:** https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html

## Future Enhancements

Possible additions:
1. Add A-Z characters for menu labels
2. Create multiple font sizes in LARGE_FONT_DATA
3. Add custom symbols (°, ±, etc.)
4. Implement variable-width fonts
5. Add animation support (scrolling, blinking)

