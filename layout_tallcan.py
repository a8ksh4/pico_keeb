'''This is a pico_keeb keyboard layout for the "tallcan" handheld 
computer.

p     i   i     p
i     n   n     i
n     d   d     n
k     e   e     k
y     x   x     y

a b c d   e f g h - furthest finger row
i j k l   m n o p - nearest finger row
  q r u   v s t   - thumbs buttons around joystick/wheel clickers
'''
    
LAYOUT = bytes((12, 13, 14, 15,    10,  9,  8,  7,
                17, 18, 19, 20,     5,  4,  3,  2,
                    21, 16,  1,     0, 11,  6)


KEYMAP = (
    # Base Layer
    ('S',   'T',   'R',   'A',      'A',   'R',   'T',   'S',
     'O',   'I',   'Y',   'E',      'E',   'Y',   'I',   'O',
          'TAB', 'ENTR',   '',      '',  'SHFT', 'CTRl',),
    # Numbers Layer
    ('4',  '3',  '2',  '1',   '1',   '2',  '3',  '4',
      '8',  '7', '6',  '5',    '5',  '6',  '7',  '8',
      )
    # Symbols Layer
    # Meta Layer
    # Navigation Layer

)