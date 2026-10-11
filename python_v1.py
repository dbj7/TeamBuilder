import csv, itertools


def carica(nomefile):
    with open(nomefile, newline='') as tabella:
        righe = list(csv.reader(tabella))
    nomi = righe[0][:-1]
    totale_persone = len(nomi)
    matrice_letta = [[0]*totale_persone for _ in range(totale_persone)]
    for i, r in enumerate(righe[1:totale_persone+1]):
        for j, v in enumerate(r[1:totale_persone+1]):
            if i != j and v.strip():          # diagonale 'x' e celle vuote assumo valgano 0
                matrice_letta[i][j] = int(v)
    return nomi, matrice_letta

def somma_punteggi(squadra, punteggi):
    return sum(punteggi[i][j] for i in squadra for j in squadra if i != j)

def migliore(nomi, M):
    totale_persone = len(nomi)
    dim_team = totale_persone // 2
    miglior_combinazione = (-1, None, None)
    for squadra_a in itertools.combinations(range(totale_persone), dim_team):
        if totale_persone % 2 == 0 and 0 not in squadra_a:  #con un numero pari di persone evito di creare squadre duplicate
            continue                                        #forzando la squadra_a ad avere la persona in 0               
        squadra_b = [i for i in range(totale_persone) if i not in squadra_a]
        punteggio = (somma_punteggi(squadra_a, M)/len(squadra_a) + somma_punteggi(squadra_b, M)/len(squadra_b)) / 2
        if punteggio > miglior_combinazione[0]:
            miglior_combinazione = (punteggio, squadra_a, squadra_b)
    return miglior_combinazione

nomi, tabella_letta = carica("tabella.csv")
punteggio_migliore, squadra_a, squadra_b = migliore(nomi, tabella_letta)

media_a = somma_punteggi(squadra_a, tabella_letta) / len(squadra_a)
media_b = somma_punteggi(squadra_b, tabella_letta) / len(squadra_b)

print("Squadra 1:", [nomi[i] for i in squadra_a], "- media:", round(media_a, 2))
print("Squadra 2:", [nomi[i] for i in squadra_b], "- media:", round(media_b, 2))
print("Valore medio:", round(punteggio_migliore, 2))