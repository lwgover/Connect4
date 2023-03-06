#!/usr/bin/python3

"""
Connect Four

This program creates a "Connect Four" game (a la the classic 1974 Milton Bradley
game). If you are unfamiliar with the game, rules may be found at
https://en.wikipedia.org/wiki/Connect_Four.

By default, one player will be human and the other player will be a computer
player, whose AI is contained in the file "connect4player.py". This will have a
class called ComputerPlayer, that has two public methods. The __init__() method
will take self, an int that indicates the number of plies to look ahead, and an
int that is the value of the player's discs.  The pick_move() method will take
self, and a 2D int list of the board's current layout. This will be
column-major, with space 0,0 meaning the lower-left location. It will return an
int, indicating the column in which it wishes to play. (Note that if a column is
full, playing there is an invalid move.)

This is version 2.0, which includes a text-based mode. This isn't as fun, but 
will work if you can't get the graphics dependencies working.
"""

__author__ = "Adam A. Smith"
__license__ = "MIT"
__date__ = "September 2019"

import sys
import random
from functools import partial

################################################################################
# CONSTANTS
################################################################################

DEFAULT_PLAYER1_COLOR = "#FF0000"
DEFAULT_PLAYER2_COLOR = "#0000FF"
RACK_COLOR = "402010" #"#FFC080"
BACKGROUND_COLOR = "black"
SQUARE_SIZE = 100
FRAME_TIME = 25
GRAVITY = 20
DEFAULT_AI_LEVEL = 4
DEFAULT_AI_FILE = "connect4player"

# AUTOMATIC CONSTANTS--DON'T MESS WITH THESE
HALF_SQUARE = SQUARE_SIZE // 2

# ANSI ESCAPE SEQUENCES TO MAKE ASCII MODE IN COLOR--MAY NOT ALWAYS WORK
P1_ESCAPE = "\33[91m\33[1m"
P2_ESCAPE = "\33[34m\33[1m"
END_ESCAPE = "\33[0m"
BOARD_ESCAPE = "\33[90m"

################################################################################
# HUMAN PLAYER CLASS
################################################################################
class HumanPlayer:
    pass

################################################################################
# APPLICATION CLASS & GRAPHICS STUFF
################################################################################

# Does tkinter even exist on this computer? If not, don't do graphics.
do_graphics = True
try:
    import tkinter as tk
except ImportError:
    print("Warning: Could not find the tkinter module. Graphics disabled.", file=sys.stderr)
    do_graphics = False

try:        
    from PIL import Image, ImageDraw, ImageTk
except ImportError:
    print("Warning: Could not find the PIL module (or one of its components). Graphics disabled.", file=sys.stderr)
    do_graphics = False

# if we got here, the infrastructure for graphics exists
if do_graphics:
    class App(tk.Tk):
        def __init__(self, players = None, player_colors = None, num_columns = 7, num_rows = 6):
            tk.Tk.__init__(self)
            self.title("Connect Four")
            self.configure(bg=BACKGROUND_COLOR)

            # parse the passed players to set the field holding the AIs
            if players == None or len(players) == 0: self.players = (None, HumanPlayer(), HumanPlayer())
            elif len(players) == 1: self.players = (None, HumanPlayer(), players[0])
            elif len(players) == 2: self.players = (None, players[0], players[1])
            elif len(players) == 3: self.players = players

            # parse the player color args, define the color strings we'll need
            if player_colors == None:
                player_color_tuples = (None, self._make_color_tuple(DEFAULT_PLAYER1_COLOR), self._make_color_tuple(DEFAULT_PLAYER2_COLOR))
            elif len(player_colors) == 2:
                player_color_tuples = (None, self._make_color_tuple(player_colors[0]), self._make_color_tuple(player_colors[1]))

            self.color_strs = (None, App._make_color_string(player_color_tuples[1]), App._make_color_string(player_color_tuples[2]))
            self.dark_strs = (None, App._make_color_string(App._darken(player_color_tuples[1])), App._make_color_string(App._darken(player_color_tuples[2])))
            self.light_strs = (None, App._make_color_string(App._lighten(player_color_tuples[1])), App._make_color_string(App._lighten(player_color_tuples[2])))

            # make the necessary images
            self.overlay_image = self._make_rack_image()
            self.disc1_image = self._make_disc_image(player_color_tuples[1])
            self.disc2_image = self._make_disc_image(player_color_tuples[2])
            self.wm_iconphoto(self, App._make_icon(player_color_tuples[1], player_color_tuples[2]))
            
            # other data structures
            #self.rack = [[0 for x in range(num_rows)] for y in range(num_columns)]
            self.rack = make_rack(num_columns, num_rows)

            # start forming up the screen--here's the top banner
            self.top_banner = tk.Label(self, bg=BACKGROUND_COLOR, font=("Arial", 20))
            self.top_banner.grid(column=1, row=1, columnspan=num_columns)

            # buttons
            self.buttons = []
            for i in range(num_columns):
                b = tk.Button(self, text=str(i+1), command=partial(self._drop_disc, i), highlightthickness=0)
                b.grid(column=(i+1), row=2, pady=10)
                self.buttons.append(b)

            self.canvas = tk.Canvas(width = num_columns*SQUARE_SIZE, height = num_rows*SQUARE_SIZE, bg=BACKGROUND_COLOR, highlightthickness=0)
            self.canvas.grid(column=1, row=3, columnspan=num_columns)

            self.discs = []
            # make the rack
            for r in range(num_rows):
                for c in range(num_columns):
                    self.canvas.create_image((c*SQUARE_SIZE+HALF_SQUARE,r*SQUARE_SIZE+HALF_SQUARE), image=self.overlay_image)

            # random player goes 1st
            self._set_player(random.randrange(1,3))
                    
        # actually make a play--modifies the rack, and starts up the animation
        def _drop_disc(self, location, player_num = None):

            if player_num == None: player_num = self.current_player

            # disable all the buttons while the disc is dropping
            for b in self.buttons: b.config(state=tk.DISABLED)
            
            # figure out where the thing drops to
            end_row = 0
            while self.rack[location][end_row] != 0: end_row += 1
            end_y = (len(self.rack[0]) - end_row) * SQUARE_SIZE - HALF_SQUARE
            self.rack[location][end_row] = player_num

            # create the new disc
            start = (location*SQUARE_SIZE + HALF_SQUARE, -HALF_SQUARE)
            if player_num == 1: image = self.disc1_image
            else: image = self.disc2_image
            new_disc = self.canvas.create_image((location*SQUARE_SIZE + HALF_SQUARE, -HALF_SQUARE), image=image)
            self.canvas.lower(new_disc)

            # start the dropping process
            self.after(1, self._continue_drop, new_disc, 0, end_y)

        # animate the disc as it continues to drop
        def _continue_drop(self, which_disc, speed, final_y):
            # gravity calcs
            speed += GRAVITY
            current_y = int(self.canvas.coords(which_disc)[1])

            # on end, get the token down, and start up final checks
            if current_y + speed >= final_y:
                self.canvas.move(which_disc, 0, final_y-current_y)
                self.after(FRAME_TIME, self._finish_turn, which_disc)

            # move the disc, and continue dropping
            else:
                self.canvas.move(which_disc, 0, speed)
                self.after(FRAME_TIME, self._continue_drop, which_disc, speed, final_y)

        # check for victory, swap player
        def _finish_turn(self, dropped_disc):
            column = int(self.canvas.coords(dropped_disc)[0] / SQUARE_SIZE)
            win_location = find_win(self.rack, column)
            if win_location:
                self._declare_victory(self.current_player, win_location)
            elif not exists_legal_move(self.rack):
                self.top_banner.config(text="Tie Game", fg="white")
            else: self._swap_player()
                
        # handle the UI aspect of the victory
        def _declare_victory(self, winner, win_location):
            self.top_banner.config(text="Player " +str(winner) + " wins!", fg=self.light_strs[self.current_player])
            num_rows = len(self.rack[0])
            coords = [(x[0]*SQUARE_SIZE+HALF_SQUARE, (num_rows-1-x[1])*SQUARE_SIZE+HALF_SQUARE) for x in win_location]
            self.canvas.create_line(coords[0][0], coords[0][1], coords[1][0], coords[1][1], fill=self.light_strs[winner], width=SQUARE_SIZE/10, capstyle=tk.ROUND)

        # set a button to the colors of the given player
        def _set_button_colors(self, button, player):
            button.config(fg = self.dark_strs[player], bg = self.color_strs[player],
                          activeforeground=self.color_strs[player], activebackground=self.light_strs[player],
                          highlightcolor="#ff0000", disabledforeground=self.color_strs[player])

        # switch players
        def _swap_player(self):
            if self.current_player == 1: self._set_player(2)
            else: self._set_player(1)

        # change to the specified player
        def _set_player(self, player_id):
            self.current_player = player_id

            # if the next player is human, set the banner & activate the appropriate buttons
            if type(self.players[player_id]) == HumanPlayer:
                self.top_banner.config(text="Player " +str(self.current_player), fg=self.color_strs[self.current_player])
                for b in range(len(self.buttons)):
                    self._set_button_colors(self.buttons[b], self.current_player)
                    if self.rack[b][-1] == 0: self.buttons[b].config(state=tk.NORMAL)

            # if it's an AI, disable buttons & start up its turn
            else:
                self.top_banner.config(text="Player " +str(self.current_player)+ " is thinking...", fg=self.color_strs[self.current_player])
                for b in self.buttons:
                    self._set_button_colors(b, self.current_player)
                    b.config(state=tk.DISABLED)

                self.after(50, self._do_computer_turn)

        # let the computer take a turn
        def _do_computer_turn(self):
            # pass the player a tuple (so it can't mess with the original rack)
            rack_tuple = tuple([tuple(column) for column in self.rack])
            move = self.players[self.current_player].pick_move(rack_tuple)

            # checks to make sure that the AI has made a valid move
            assert move >=0 and move < len(self.rack)
            assert self.rack[move][-1] == 0
            
            self.top_banner.config(text="Player " +str(self.current_player))
            self._drop_disc(move)
            
        # take in a color string or tuple, return a tuple
        @staticmethod
        def _make_color_tuple(color, alpha=255):
            if type(color) == str:
                full_int = int(color.lstrip("#"), 16)
                red = full_int // 65536
                green = (full_int // 256) % 256
                blue = full_int % 256
                return (red, green, blue, alpha)
            if type(color) == tuple or type(color) == list:
                if len(color) == 3: return (color[0], color[1], color[2], 255)
                elif len(color) == 4: return tuple(color)

        # return a darker version of the passed color tuple
        @staticmethod
        def _darken(color):
            return (color[0]//2, color[1]//2, color[2]//2, color[3])

        # return a lighter version of the passed color tuple
        @staticmethod
        def _lighten(color):
            return ((color[0]+255)//2, (color[1]+255)//2, (color[2]+255)//2, color[3])

        # given a color tuple, return a string in the form "#rrggbb"
        @staticmethod
        def _make_color_string(color_tuple):
            return "#" +hex(256*65536 + 65536 * color_tuple[0] + 256 * color_tuple[1] + color_tuple[2])[3:]

        # make an image for one square in the rack
        @staticmethod
        def _make_rack_image():
            # start by making something double-size, so we can shrink it and get anti-aliasing
            im = Image.new("RGBA", (2*SQUARE_SIZE,2*SQUARE_SIZE), App._make_color_tuple(RACK_COLOR)) #(255,255,0,255))
            draw = ImageDraw.Draw(im)
            edge = int(SQUARE_SIZE * 0.2)
            draw.ellipse((edge, edge, 2*SQUARE_SIZE-edge, 2*SQUARE_SIZE-edge), fill=(0,0,0,0))
            return ImageTk.PhotoImage(im.resize((SQUARE_SIZE, SQUARE_SIZE), resample=Image.BICUBIC))

        # make a disc out of the passed color
        @staticmethod
        def _make_disc_image(color):
            im = Image.new("RGBA", (2*SQUARE_SIZE,2*SQUARE_SIZE), (0,0,0,0))
            draw = ImageDraw.Draw(im)

            color = App._make_color_tuple(color)
            dark = (color[0]//2, color[1]//2, color[2]//2, color[3])
    
            draw.ellipse((0, 0, 2*SQUARE_SIZE, 2*SQUARE_SIZE), color, dark)
            draw.ellipse((50, 50, 2*SQUARE_SIZE-50, 2*SQUARE_SIZE-50), None, dark)
            return ImageTk.PhotoImage(im.resize((SQUARE_SIZE, SQUARE_SIZE), resample=Image.BICUBIC))

        # make an 64x64 image of a "4" on a disc
        @staticmethod
        def _make_icon(color1, color2):
            im = Image.new("RGBA", (100,100), (0,0,0,0))
            draw = ImageDraw.Draw(im)
            draw.ellipse((0, 0, 100, 100), color2)
            draw.line(((53,93),(69,14),(21,62),(78,60)), fill=color1, width=12)
            return ImageTk.PhotoImage(im.resize((64, 64), resample=Image.BICUBIC))
            
# error to print out if we couldn't load up graphics
#except ImportError:
#    print("Warning: Could not find the tkinter or PIL module. Graphics disabled.", file=sys.stderr)
#    do_graphics = False

################################################################################
# FUNCTIONS
################################################################################

def load_player(player_id, module_name = None, level = 1):
    """
    Load up a ComputerPlayer class from the given module. A module of None means 
    a human player.
    """
    class_name = "Player" +str(player_id)+ "Class"

    # if module_name is None, that means we have a human player
    if module_name == None:
        exec(class_name + " = HumanPlayer", globals())
        return HumanPlayer()

    # look for the file specified, see if we have a proper ComputerPlayer
    try:
        exec("from " +module_name+ " import ComputerPlayer as " +class_name, globals())
    except ImportError:
        print("Could not find ComputerPlayer in file \"" +module_name+ ".py\". Exiting.", file=sys.stderr)
        sys.exit(1)

    # make a local pointer to the ComputerPlayer class, and return a new instance
    exec("Player = " +class_name)
    return locals()["Player"](player_id, level)

def parse_command_line_args(args):
    """
    Search the command-line args for the various options (see the help function).
    """
    print(args)
    # print help message
    if "-h" in args or "--help" in args: print_help = True
    else: print_help = False

    # AI file
    if "-f" in args: ai_file = args[args.index("-f") + 1].rstrip(".py")
    else: ai_file = DEFAULT_AI_FILE
    
    # number of players
    if "-0" in args: players = (ai_file, ai_file)
    elif "-2" in args: players = (None, None)
    else: players = (None, ai_file)

    # level of players
    if "-l" in args:
        levels = args[args.index("-l") + 1].split(',')
        print(levels)
        if len(levels) == 1: levels = (int(levels[0]), int(levels[0]))
        else: levels = (int(levels[0]), int(levels[1]))
    else: levels = (DEFAULT_AI_LEVEL, DEFAULT_AI_LEVEL)
    print(levels)

    # colors
    if "-c" in args:
        color_string = args[args.index("-c") + 1]
        colors = color_string.split(',')
    else: colors = None
        
    # manually turn off the graphics
    if "-n" in args or "--nographics" in args: graphics_wanted = False
    else: graphics_wanted = True
    
    return (print_help, players, levels, colors, graphics_wanted)

def print_help(output = sys.stderr):
    """
    Print out a help screen for the user (probably to stderr).
    """
    
    print("Usage: python3 " +sys.argv[0]+ " <options>", file=output)
    print("Options include:", file=output)
    print("\t-0\t0-player (computer-v-computer)", file=output)
    print("\t-1\t1-player (human-v-computer)", file=output)
    print("\t-2\t2-player (human-v-human)", file=output)
    print("\t-c\tuse colors (RRGGBB,RRGGBB)", file=output)
    print("\t-f\tuse a non-standard AI file", file=output)
    print("\t-h\tprint this help", file=output)
    print("\t-l\tset AI level (#,#)", file=output)
    print("\t-n\tnon-graphics mode", file=output)

def play_game_in_ascii(player1, player2):
    """
    ASCII game. Boring. May not implement this.
    """
    rack = make_rack()
    players = (None, player1, player2)

    current_player = random.randrange(1,3)
    winning_quartet = None

    while not winning_quartet:
        current_player = 3 - current_player
        if current_player == 1: player_escape = P1_ESCAPE
        else: player_escape = P2_ESCAPE

        # print out rack state
        print(player_escape + "Player " + str(current_player) + ":" + END_ESCAPE)
        print_rack(rack)

        if not exists_legal_move(rack): break

        if type(players[current_player]) == HumanPlayer: move = do_human_turn(rack, players[current_player])
        else: move = do_computer_turn(rack, players[current_player])
        print()
        place_disc(rack, current_player, move)
        winning_quartet = find_win(rack, move)

    print_rack(rack)
    if winning_quartet:
        print(player_escape + "Player " + str(current_player)+ " wins!!!" +END_ESCAPE)
        
    else:
        print("It was a tie!")

def do_human_turn(rack, player):
    while True:
        print("Your move? ", end="")
        user_input = input()
        try:
            column = int(user_input) - 1 # -1 for 0/1 based counting
        except ValueError:
            column = -1

        if column >= 0 and column < len(rack) and rack[column][-1] == 0: return column
        else: print("INVALID")
    
        
def do_computer_turn(rack, player):
    # pass the player a tuple (so it can't mess with the original rack)
    rack_tuple = tuple([tuple(column) for column in rack])
    move = player.pick_move(rack_tuple)

    # checks to make sure that the AI has made a valid move
    assert move >=0 and move < len(rack)
    assert rack[move][-1] == 0

    return move
    
def place_disc(rack, player_number, column):
    # figure out where the thing drops to
    row = 0
    while rack[column][row] != 0: row += 1
    rack[column][row] = player_number
        
# return True if there exists at least 1 valid move
def exists_legal_move(rack):
    for c in range(len(rack)):
        if rack[c][-1] == 0: return True
    return False

def make_rack(num_columns = 7, num_rows = 6):
    """
    Create the basic rack object. (Just a list, really.)
    """
    rack = [[0 for x in range(num_rows)] for y in range(num_columns)]
    return rack

def print_rack(rack):
    # print numbers on top (doesn't work with 100 or more columns)
    if len(rack) >= 10:
        print("                  ", end="")
        for i in range(9, len(rack)): print(str((i+1)//10), end=" ")
        print()

    for i in range(len(rack)): print(str((i+1)%10), end=" ")
    print()

    # print the rack itself
    for r in range(len(rack[0])-1, -1, -1):
        for c in range(len(rack)):
            if rack[c][r] == 1: print(P1_ESCAPE + "X" + END_ESCAPE, end=" ")
            elif rack[c][r] == 2: print(P2_ESCAPE + "O" + END_ESCAPE, end=" ")
            else: print(BOARD_ESCAPE + "." + END_ESCAPE, end=" ")
        print()

def find_win(rack, column = None):
    # if no column explicitly given, do them all recursively
    if column == None:
        for c in range(len(rack)):
            win = find_win(c)
            if win: return win
        return None

    num_cols = len(rack)
    num_rows = len(rack[0])
    
    # figure out where the disc was dropped
    row = num_rows - 1
    while row > -1 and rack[column][row] == 0: row -= 1
    if row == -1: return None            

    player = rack[column][row]

    # check for vertical win
    if row >= 3:
        subrack = rack[column]
        if subrack[row] == subrack[row-1] and subrack[row] == subrack[row-2] and subrack[row] == subrack[row-3]:
            return ((column, row-3), (column, row))

    # check for horizontal win
    c = d = column
    while c > 0 and rack[c-1][row] == player: c -= 1
    while d < (num_cols-1) and rack[d+1][row] == player: d += 1
    if (d-c) >= 3: return ((c, row), (d, row))

    # check for forward-diagonal win
    c = d = column
    r = s = row
    while c > 0 and r > 0 and rack[c-1][r-1] == player: c -= 1; r -= 1
    while d < (num_cols-1) and s < (num_rows-1) and rack[d+1][s+1] == player: d += 1; s+=1
    if (d-c) >= 3: return ((c, r), (d, s))
    
    # check for backward-diagonal win
    c = d = column
    r = s = row
    while c > 0 and r < (num_rows-1) and rack[c-1][r+1] == player: c -= 1; r += 1
    while d < (num_cols-1) and s > 0 and rack[d+1][s-1] == player: d += 1; s-=1
    if (d-c) >= 3: return ((c, r), (d, s))

    # no win detected--return None
    return None
    

################################################################################
# MAIN(): PARSE COMMAND LINE & START PLAYING
################################################################################

if __name__ == "__main__":

    # look at the command line for what the user wants
    do_print_help, player_files, levels, colors, graphics_wanted = parse_command_line_args(sys.argv[1:])
    
    # help message for user, if -h or --help
    if do_print_help:
        print_help()
        sys.exit(1)

    # load up the player classes
    players = (load_player(1, player_files[0], levels[0]), load_player(2, player_files[1], levels[1]))

    # user can override graphics mode if desired
    if not graphics_wanted: do_graphics = False
    
    # hit it!
    if do_graphics:
        app = App(players, colors)
        app.mainloop()

    else:
        play_game_in_ascii(players[0], players[1])
        #print("Sorry--this game is not implemented yet in ASCII.", file=sys.stderr)

