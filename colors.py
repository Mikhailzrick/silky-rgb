
from .utilities import mix, Numeric, Color
from copy import copy

SMOOTH = 0.15

def color_255ize(c:Color):
    return [round(x*255)/255 for x in c]

class Palette():
    def __init__(self, bg:Color, fg:Color|None=None) -> None:
        self.bg = color_255ize(bg)
        self._bg = color_255ize(bg)
        if fg is None:
            self.fg = color_255ize(bg)
            self._fg = color_255ize(bg)
        else:
            self.fg = color_255ize(fg)
            self._fg = color_255ize(fg)

    def __eq__(self, p2) -> bool:
        return \
            round(self.fg[0]*255) == round(p2.fg[0]*255) and \
            round(self.fg[1]*255) == round(p2.fg[1]*255) and \
            round(self.fg[2]*255) == round(p2.fg[2]*255) and \
            round(self.bg[0]*255) == round(p2.bg[0]*255) and \
            round(self.bg[1]*255) == round(p2.bg[1]*255) and \
            round(self.bg[2]*255) == round(p2.bg[2]*255)

    def swap(self):
        return Palette(copy(self.fg), copy(self.bg))

    def paintdrop(self, p2:'Palette'):
        if self != p2:
            self._bg = mix(self._bg, 1-SMOOTH, p2.bg, SMOOTH)
            self._fg = mix(self._fg, 1-SMOOTH, p2.fg, SMOOTH)
            self.bg = [a for a in self._bg]
            self.fg = [a for a in self._fg]
            return False
        else:
            self.bg = [a for a in p2.bg]
            self.fg = [a for a in p2.fg]
        return True
    
    def __str__(self) -> str:
        return f"P( {str(self.bg)} {str(self.fg)} )"

GREEN = Palette([0,1,0])
RED = Palette([1,0,0])
BLUE = Palette([0,0,1])
AMBER = Palette([1,0.8,0])
WHITE = Palette([1,1,1])
BLACK = Palette([0,0,0])

COLORS = {
    # Original Set
    'Cyan': [0.0, 0.7843, 0.7843],
    'Aqua': [0.1, 0.6, 0.92],
    'Magenta': [1.0, 0.0, 0.7059],
    'Green': [0.0, 1.0, 0.0],
    'Blue': [0.0, 0.1961, 1.0],
    'PBlue': [0.0, 0.0, 1.0],
    'Violet': [0.2941, 0.0, 1.0],
    'Yellow': [1.0, 0.7843, 0.0],
    'Gold': [1.0, 0.75, 0.0],
    'Silver': [0.8, 0.8, 0.9],
    'Red': [1.0, 0.0196, 0.0],
    'PRed': [1.0, 0.0, 0.0],
    'Pink': [1.0, 0.4, 0.6],
    'White': [1.0, 1.0, 1.0],
    'Black': [0.0, 0.0, 0.0],

    # Second Set
    'Electric Blue': [0.0, 0.7, 1.0],
    'Sky Blue': [0.5294, 0.8078, 0.9216],
    'Mint': [0.4, 0.8784, 0.7],
    'Deep Green': [0.0, 0.70, 0.50], # really low brightness
    'Deep Purple': [0.5412, 0.0, 0.8863],
    'Hot Pink': [1.0, 0.4118, 0.7059],
    'Amethyst': [0.6, 0.5, 0.7],
    'Fuchsia': [1.0, 0.0, 1.0],
    'Lime Green': [0.30, 0.8039, 0.0],
    'Spring Green': [0.0, 1.0, 0.498],
    'Tangerine': [1.0, 0.5098, 0.0],
    'Scarlet': [1.0, 0.1373, 0.0],
    'Goldenrod': [0.8549, 0.6471, 0.1255],
    'Warm White': [1.0, 0.9608, 0.902],
    'Ice White': [0.902, 0.9804, 1.0],
    'Knulli Light Green': [0.43, 1.0, 0.0],
    'Knulli Golden Moss': [0.60, 0.85, 0.0],

    'Off': [0.0, 0.0, 0.0]
}

PALETTES = {
    # Red Coded
    'Sunset': ['Hot Pink', 'Tangerine'],
    'Flame': ['Red', 'Tangerine'],
    'Medal': ['Silver', 'Gold'],

    # Blue Coded
    'The Deep': ['Blue', 'Deep Green'],
    'Mint': ['Electric Blue', 'Spring Green'],
    'Gender Reveal Party': ['Aqua', 'Pink'],

    #'Synthwave': ['Hot Pink', 'Electric Blue'],
    #'Fuchsia Flash': ['Fuchsia', 'Electric Blue'], #probably redundant
    #'Scarlet Surge': ['Scarlet', 'Aqua'],

    # Green Coded
    'Knulli': ['Knulli Light Green', 'Knulli Golden Moss'],
    'Knulli Silver': ['Knulli Light Green', 'Silver'],
    'Spring Meadow': ['Spring Green', 'Yellow'],
    'Forrest': ['Lime Green', 'Deep Green'],
    
    # Fun & Sweet
    #'Cotton Candy': ['Pink', 'Sky Blue'],
    #'Bubblegum': ['Pink', 'Aqua'], # there are a few like this
    
    # Vibrant
    'Orchid': ['Magenta', 'Violet'],
    'Cyberpunk': ['Fuchsia', 'Cyan'],
    'Toxic': ['Fuchsia', 'Green'],
    'Royal': ['Violet', 'Gold'],

    # Haze
    #'Mint': ['Silver', 'Mint'],v
    #'Arctic': ['White', 'Cyan'],
    #'Blue Haze': ['Sky Blue', 'PBlue'], #cool dark palette
    #'Purple Haze': ['Amethyst', 'Deep Purple'], # small diff
    #'Fuchsia Haze': ['Amethyst', 'Fuchsia'], # small diff
}

def get_palette(S:str) -> list[Color]:
    colors_ = S.split("-")
    if(len(colors_) == 1):
        c1 = colors_[0]
        ret = [COLORS[c1], COLORS[c1]]
        return ret
    if(len(colors_) == 2):
        c1 = colors_[0]
        c2 = colors_[1]
        ret = [COLORS[c1], COLORS[c2]]
        return ret
    return [[0,0,0], [0,0,0]]