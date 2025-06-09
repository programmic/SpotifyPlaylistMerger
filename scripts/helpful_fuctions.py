import colors as colors

clear = "\033c"

def readFile(pName, pNr):
    """readFile liest die Datei pName mit Nummer pNr in eine
    Liste ein, die zurückgegeben wird.
    """
    dateiname = pName + str(pNr) + ".txt"
    with open(dateiname, "r", encoding = "utf-8") as data:
        ausgabe = data.read().split("\n")
    # ausgabe.reverse()
    return ausgabe

def lenformat(pInput, pDesiredLength, character=" ", place="back"):
    if place == "back":
        return str(str(pInput) + str(character * int(int(pDesiredLength) - len(str(pInput)))))
    elif place == "front":
        return str(character * int(int(pDesiredLength) - len(str(pInput)))) + str(str(pInput))
    

def clearTerminal():
    print("\033c", end="")  # Clears Python Console Output

def makeMatrix(pX, pY, pZ=1):
    """
    Easy way to quickly generate empty matrix
    Args:
        pX (int): matrix x dimension
        pY (int): matrix y dimension

    Returns:
    2-Dimensional, empty data matrix
    """
    ret = []
    for i in range (pY):
        ret.append([])
        for j in range( pX ):
            ret[i].append([])
            if pZ > 1:
                for n in range(pZ):
                    ret[i][j].append([])  
    return ret


def abschnitt(pBeschriftung):
    laenge = int(25/2) - int(len(pBeschriftung)/2) - 1
    print()
    print("-"*25)
    print("\n")
    print("-"*25)
    print("-"*laenge,pBeschriftung,"-"*laenge)
    print("-"*25)
    print("\n")
    print("-"*25)
    print()