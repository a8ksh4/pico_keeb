# Keymap Keys

Keymap entries use [QMK](https://docs.qmk.fm/keycodes_basic) key names and
functions, so a QMK keymap mostly reads the same here. The `KC_` prefix is
optional: `A` and `KC_A` are the same key. Everything below is parsed by
`parse_key()` in `keymap_utils.py`.

The keymap file has two parts:

- `_KEYMAP`: one tuple of entries per layer, in the physical order given by `_LAYOUT`.
- `_CHORDS`: one list per layer (same order as `_KEYMAP`) of `(output, (keys...))`.

## Entry types

| Type | Example | What it does |
|---|---|---|
| Basic key | `'A'`, `'ENT'`, `'LSFT'` | Sends the key while held. |
| Single character | `'*'`, `'?'`, `' '` | Shortcut for the QMK name (`ASTR`, `QUES`, `SPC`). |
| Modified key | `'LSFT(8)'`, `'S(8)'`, `'C(S(A))'` | Sends the key with modifiers, here `*` and Ctrl+Shift+A. |
| Momentary layer | `'MO(1)'` | Layer 1 is active while held. |
| Default layer | `'DF(4)'` | Makes layer 4 the base layer until another `DF()`. |
| Layer tap | `'LT(1, MS_BTN1)'` | Tap: left click. Hold, or press another key: layer 1. |
| Mod tap | `'MT(LSFT, A)'` | Tap: A. Hold, or press another key: Shift. |
| Mouse key | `'MS_UP'`, `'MS_BTN1'` | Moves the pointer or presses a button while held. |
| Nothing | `''`, `'NO'` | Does nothing. |

Functions can be nested: `'LT(2, S(9))'` is `(` on tap and layer 2 on hold.
Inside a function, use names rather than characters that look like syntax:
`S(COMM)`, not `S(,)`.

## Chords

A chord sends its output when its keys are pressed together and released (or
held past `HOLD_TIME_MS`). The output can be any entry from the table above.
The keys are written exactly as they appear in that layer of `_KEYMAP`, and
can be on either side of the keyboard.

```python
_CHORDS = (
    # 0 - Base Layer
    [
        ('F', ('A', 'R')),
        ('SPC', ('E', 'Y', 'I', 'O')),
        ('LSFT', ('A', 'Y', 'I', 'O')),   # held: Shift
        ('DF(4)', ('E', 'R', 'I')),       # switch to the nav layer
    ],
    # 1 - Numbers Layer
    [
        ('SPC', ('5', '6', '7', '8')),
    ],
)
```

- Keys used in a layer's chords wait until they're released (or held past
  `HOLD_TIME_MS`) before sending, in case a chord is coming. Other keys send
  right away.
- The same output can appear in more than one chord.
- Mistakes stop the boot with an error that names the chord: a key that isn't
  in that layer, an unknown output, or two chords using the same keys.

## Key names

**Letters and numbers:** `A`–`Z`, `0`–`9`, `F1`–`F12`

**Editing and navigation:**
`ENT` `ESC` `BSPC` `TAB` `SPC` `DEL` `INS`
`HOME` `END` `PGUP` `PGDN` `UP` `DOWN` `LEFT` `RGHT`
`CAPS` `PSCR` `SCRL` `PAUS`

**Punctuation:**
`MINS` `EQL` `LBRC` `RBRC` `BSLS` `SCLN` `QUOT` `GRV` `COMM` `DOT` `SLSH`
`NUHS` (the non-US `#` key)

**Shifted punctuation:**

| Name | Char | Name | Char | Name | Char |
|---|---|---|---|---|---|
| `TILD` | `~` | `CIRC` | `^` | `PLUS` | `+` |
| `EXLM` | `!` | `AMPR` | `&` | `LCBR` | `{` |
| `AT` | `@` | `ASTR` | `*` | `RCBR` | `}` |
| `HASH` | `#` | `LPRN` | `(` | `PIPE` | `\|` |
| `DLR` | `$` | `RPRN` | `)` | `COLN` | `:` |
| `PERC` | `%` | `UNDS` | `_` | `DQUO` | `"` |
| `QUES` | `?` | `LABK` | `<` | `RABK` | `>` |

**Modifiers:** `LCTL` `LSFT` `LALT` `LGUI` `RCTL` `RSFT` `RALT` `RGUI`

**Modifier functions:** `LSFT()` `LCTL()` `LALT()` `LGUI()` `RSFT()` `RCTL()`
`RALT()` `RGUI()`, and the short forms `S()` `C()` `A()` `G()`

**Keypad:** `P0`–`P9` `PSLS` `PAST` `PMNS` `PPLS` `PENT` `NUM`

**Layers:** `MO(n)` `DF(n)` `LT(n, key)`

**Mod tap:** `MT(mod, key)`

**Mouse:** `MS_BTN1` (left), `MS_BTN2` (right), `MS_BTN3` (middle),
`MS_UP` `MS_DOWN` `MS_LEFT` `MS_RGHT`. Pointer speed is `MOUSE_KEY_SPEED` in
`main.py`. The wheel keys (`MS_WHLU`, `MS_WHLD`) aren't supported yet.

**Single characters:** `` ` `` `-` `=` `[` `]` `\` `;` `'` `,` `.` `/` and
space, plus their shifted versions `~ ! @ # $ % ^ & * ( ) _ + { } | : " < > ?`

The `usb.device.keyboard.KeyCode` names also work (`ENTER`, `ESCAPE`,
`LEFT_SHIFT`, ...). An unknown name prints a warning at boot and does nothing.

## Your own names

Add names for entries in `_MY_ALIASES` in the keymap file:

```python
_MY_ALIASES = {'NAV': 'DF(4)', 'BASE': 'DF(0)'}
```

Then use `'NAV'` anywhere in `_KEYMAP` or as a chord output.
