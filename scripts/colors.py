white =        "\033[1;37m"
yellow =       "\033[1;33m"
green =        "\033[1;32m"
blue =         "\033[1;34m"
cyan =         "\033[1;36m"
red =          "\033[1;31m"
magenta =      "\033[1;35m"
black =        "\033[1;30m"
darkyellow =   "\033[33m"
darkblue =     "\033[34m"
darkmagenta =  "\033[35m"
darkblack =    "\033[30m"
darkred =      "\033[31m"
darkgreen =    "\033[32m"
clear =        "\033[0m"

FAIL =         "\033[91m"

BRIGHT    =    "\033[1m"
DIM       =    "\033[2m"
NORMAL    =    "\033[22m"
RESET_ALL =    "\033[0m"

BOLD =         "\033[1m"
FAINT =        "\033[2m"
ITALIC =       "\033[3m"
UNDERLINE =    "\033[4m"
BLINK =        "\033[5m"
NEGATIVE =     "\033[7m"
CROSSED =      "\033[9m"

import os
def clearTerminal():
    os.system('cls')