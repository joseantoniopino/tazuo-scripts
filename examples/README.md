# Examples - TazUO Script Testing & Learning

This folder contains **example scripts and tests** for learning TazUO API patterns. These files are **NOT production scripts** and should not be used in actual gameplay.

---

## 📁 Contents

### `gump_test.py` - Dynamic Gump Update Pattern Test

**Purpose:** Proof-of-concept to verify that TazUO gumps can be updated dynamically without recreation.

**What it tests:**
- ✅ Create gump ONCE with all controls
- ✅ Update control properties (`.Text`, `.Hue`) without recreating gump
- ✅ Verify no flicker during updates
- ✅ Confirm gump position is preserved when user moves it
- ✅ Test dynamic width changes for progress bars (`.SetWidth()`)

**Pattern discovered:**
```python
# CREATE ONCE (on init)
self.gump = API.CreateGump(acceptMouseInput=True, canMove=True)
self.label = API.CreateGumpLabel("Initial text", hue=0x3F)
self.gump.Add(self.label)
API.AddGump(self.gump)

# UPDATE DYNAMICALLY (in loop)
self.label.Text = "New text"  # ✅ Works - no recreation
self.label.Hue = 0x21         # ✅ Works - dynamic color change
```

**How to use:**
1. Open script in TazUO: Scripts → Load Script → `examples/gump_test.py`
2. Set `DEBUG = True` (line 19) for detailed logs
3. Run script - gump will appear and update every second
4. Move the gump - it should stay in place during updates
5. Script auto-stops after 30 cycles
6. Check logs: `logs/gump_test-YYYYMMDD.log`

**Key findings:**
- `CreateGump()` + `CreateGumpLabel()` + `gump.Add()` pattern works
- Controls have **read-only position properties** (use `SetPos()`, `SetX()`, `SetY()`)
- Controls have **writable properties** like `Text` and `Hue`
- `SetWidth()` and `SetHeight()` work for dynamic sizing (ColorBox, ItemPic)
- NO FLICKER when updating properties (unlike recreating gump)

---

## � Complete Gump API Reference

### Control Creation
- `API.CreateGump(acceptMouseInput, canMove, keepOpen)` - Create gump container
- `API.CreateGumpLabel(text, hue)` - Create text label
- `API.CreateGumpColorBox(opacity, color)` - Create colored rectangle
- `API.CreateGumpItemPic(graphic, width, height)` - Create item graphic
- `API.CreateGumpCheckbox(text, isChecked)` - Create checkbox control
- `API.AddGump(gump)` - Send gump to client (call ONCE)

### Control Positioning Methods
- `control.SetPos(x, y)` - Set position (X/Y are read-only properties!)
- `control.SetX(x)` - Set X position only
- `control.SetY(y)` - Set Y position only
- `control.SetRect(x, y, width, height)` - Set position and size
- `control.SetWidth(width)` - Set width (useful for progress bars)
- `control.SetHeight(height)` - Set height
- `control.GetX()` - Get X position (workaround for read-only property)
- `control.GetY()` - Get Y position (workaround for read-only property)

### Gump Positioning & Visibility
- `gump.SetInScreen()` - Ensure gump fully visible in screen boundaries
- `gump.CenterXInScreen()` - Center gump horizontally in full screen
- `gump.CenterYInScreen()` - Center gump vertically in full screen
- `gump.CenterXInViewPort()` - Center gump horizontally in viewport (game area)
- `gump.CenterYInViewPort()` - Center gump vertically in viewport (game area)

**Note:** ViewPort = game area (excludes UI bars), Screen = full window

### Control Properties
- `control.Text` - **WRITABLE** - Update text dynamically
- `control.Hue` - **WRITABLE** - Update color dynamically
- `control.X` - **READ-ONLY** - Use `SetPos()` or `SetX()` instead
- `control.Y` - **READ-ONLY** - Use `SetPos()` or `SetY()` instead

### Checkbox Control
- `checkbox.IsChecked` - **READ-ONLY** property (bool) - Get checkbox state
- `checkbox.GetIsChecked()` - Get checkbox state (method)
- `checkbox.SetIsChecked(bool)` - Set checkbox state
- `checkbox.GetText()` - Get checkbox label text

### NineSlice Gumps (Advanced)
- `nineSliceGump.GetHue()` / `SetHue(hue)` - Get/set gump hue
- `nineSliceGump.GetResizable()` / `SetResizable(bool)` - Get/set resizable state
- `nineSliceGump.GetBorderSize()` / `SetBorderSize(int)` - Get/set border size
- `modernNineSliceGump.SetResizeCallback(callback)` - Callback for resize events

### Hide/Show Techniques
- **Labels:** Set `Text = ""` to hide, set actual text to show
- **ColorBox:** Set `SetWidth(0)` to hide, restore width to show
- **ItemPic:** Set `SetWidth(0)` and `SetHeight(0)` to hide, restore to show

### Common Mistakes
- ❌ Assigning to `control.X` or `control.Y` directly (read-only - use `SetPos()`)
- ❌ Calling `gump.AddLabel()` - method doesn't exist (use `API.CreateGumpLabel()`)
- ❌ Recreating gump every update (causes flicker and position reset)
- ❌ Not storing control references (can't update without them)
- ❌ Confusing ViewPort vs Screen centering

---

## �🚫 .gitignore

This folder is **git-ignored** to keep the repository clean. Example scripts are for local testing only.

---

## 📚 Related Documentation

- **API Reference:** `docs/API.md`
- **Gump Controls:** `docs/PyControl.md`, `docs/PyBaseControl.md`
- **Project Instructions:** `.github/copilot-instructions.md`

---

## 💡 Creating New Examples

When creating test scripts:

1. **Use DEBUG flag pattern:**
   ```python
   DEBUG = False  # Set to True for logging
   ```

2. **Use ScriptLogger class:**
   ```python
   logger = ScriptLogger("my_test")
   logger.info("CONTEXT", "EVENT", "Message", {"details": "value"})
   ```

3. **Document what you're testing:**
   - Clear comments at top of file
   - Explanation of pattern being tested
   - How to interpret results

4. **Clean up resources:**
   ```python
   finally:
       if gump:
           gump.Dispose()
   ```

---

**Last Updated:** October 13, 2025  
**Examples Version:** 1.1 (Added complete API reference from PR merge findings)
