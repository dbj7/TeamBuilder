import csv
import io
import itertools
import math

import pandas as pd
import streamlit as st

# ---------------- Funzioni ----------------
def carica(file_caricato):
    errori, avvisi = [], []

    try:
        testo = file_caricato.getvalue().decode("utf-8-sig")
    except UnicodeDecodeError:
        return None, None, ["Il file non è un testo valido (codifica UTF-8)."], []

    if not testo.strip():
        return None, None, ["Il file è vuoto."], []

    try:
        delimitatore = csv.Sniffer().sniff(testo.splitlines()[0], delimiters=",;\t").delimiter
    except csv.Error:
        delimitatore = ","
    righe = list(csv.reader(io.StringIO(testo, newline=""), delimiter=delimitatore))
    righe = [r for r in righe if any(c.strip() for c in r)]  # ignoro righe completamente vuote

    # Formato tabella
    nomi = [c.strip() for c in righe[0][1:-1]] 
    n = len(nomi)
    if n < 2:
        return None, None, ["Servono almeno 2 persone."], []
    if any(not x for x in nomi):
        errori.append("L'intestazione contiene nomi vuoti.")
    doppi = sorted({x for x in nomi if x and nomi.count(x) > 1})
    if doppi:
        errori.append(f"Nomi duplicati nell'intestazione: {', '.join(doppi)}.")

    # Valori
    dati = righe[1:]
    if len(dati) < n:
        errori.append(f"Attese {n} righe di dati (una per persona), trovate {len(dati)}.")
    elif len(dati) > n:
        avvisi.append(f"Trovate {len(dati)} righe di dati, ne uso solo {n}: le altre vengono ignorate.")

    # Matrice punteggi
    M = [[0] * n for _ in range(n)]
    for i, r in enumerate(dati[:n]):
        riga_file = i + 2
        if len(r) < n + 1:
            errori.append(f"Riga {riga_file}: trovate {len(r)} colonne, ne servono almeno {n + 1}.")
            continue
        if r[0].strip() != nomi[i]:
            errori.append(f"Riga {riga_file}: l'etichetta '{r[0].strip()}' non corrisponde al nome atteso '{nomi[i]}'.")
        errori_prima = len(errori)
        for j in range(n):
            v = r[j + 1].strip()
            cella = f"riga {riga_file} ({nomi[i]}) → colonna {nomi[j]}"
            if i == j:
                if v.lower() != "x":
                    avvisi.append(f"{cella}: la diagonale dovrebbe essere 'x', trovato '{v}' (ignorato).")
            elif v == "":
                avvisi.append(f"{cella}: cella vuota, assumo 0.")
            elif int(v) < 0:
                errori.append(f"{cella}: valore negativo")
            else:
                try:
                    M[i][j] = int(v)
                except ValueError:
                    errori.append(f"{cella}: '{v}' non è un numero intero.")

        # Controllo totale di riga
        if len(errori) == errori_prima and len(r) > n + 1 and r[n + 1].strip():
            try:
                if int(r[n + 1]) != sum(M[i]):
                    avvisi.append(f"Riga {riga_file} ({nomi[i]}): totale {r[n + 1].strip()} "
                                  f"diverso dalla somma dei valori ({sum(M[i])}).")
            except ValueError:
                pass

    if errori:
        return None, None, errori, avvisi
    return nomi, M, [], avvisi


def mostra_messaggi(messaggi, funzione, titolo, max_visibili=6):
    if not messaggi:
        return
    righe = "\n".join(f"- {m}" for m in messaggi[:max_visibili])
    if len(messaggi) > max_visibili:
        righe += f"\n- ... e altri {len(messaggi) - max_visibili}"
    funzione(f"**{titolo}**\n\n{righe}")


def somma_punteggi(squadra, punteggi):
    return sum(punteggi[i][j] for i in squadra for j in squadra if i != j)

# Calcolo combinazione migliore
def migliore(nomi, M):
    totale_persone = len(nomi)
    dim_team = totale_persone // 2
    miglior_combinazione = (-1, None, None)
    for squadra_a in itertools.combinations(range(totale_persone), dim_team):
        if totale_persone % 2 == 0 and 0 not in squadra_a:  # Evito squadre duplicate
            continue
        squadra_b = [i for i in range(totale_persone) if i not in squadra_a]
        punteggio = (somma_punteggi(squadra_a, M) / len(squadra_a)
                     + somma_punteggi(squadra_b, M) / len(squadra_b)) / 2
        if punteggio > miglior_combinazione[0]:
            miglior_combinazione = (punteggio, squadra_a, squadra_b)
    return miglior_combinazione



# ---------------- GUI ----------------
st.title("Divisione squadre ottimale")

st.markdown(
    "*Carica la tabella dei punteggi* (`.csv`) *strutturata nel modo"
    " seguente:*"
)

st.code(
    "Categoria, persona1, persona2, ..., Totale\n"
    "persona1, x, valore, ..., parziale1\n"
    "persona2, valore, x, ..., parziale2",
    language="text",
) 


st.markdown(
    '<p style="color: #555555; font-style: italic; font-size: 0.9em; margin-top:'
    ' -10px;">Il minimo numero di persone è 2, se sono presenti poù di 20 persone il calcolo richiederà più tempo.</p>',
    unsafe_allow_html=True,
)  

uploaded_file = st.file_uploader("Scegli un file CSV", type="csv")

if uploaded_file is not None:
    nomi, tabella_letta, errori, avvisi = carica(uploaded_file)

    if errori:
        mostra_messaggi(errori, st.error, "Il file non è nel formato atteso:")
        mostra_messaggi(avvisi, st.warning, "Altre segnalazioni:")
        st.info("Formato atteso: prima riga con i nomi + una colonna finale di totale; "
                "poi una riga per persona con etichetta, i valori, 'x' sulla diagonale e il totale.")
        st.stop()

    st.success("File caricato con successo!")
    mostra_messaggi(avvisi, st.warning, "Segnalazioni (il calcolo procede comunque):")

    st.subheader("Anteprima dei dati")
    st.dataframe(pd.DataFrame(tabella_letta, index=nomi, columns=nomi))

    n = len(nomi)
    col1, col2 = st.columns(2)
    col1.metric("Partecipanti", n)
    col2.metric("Combinazioni da provare", f"{math.comb(n, n // 2) // (2 if n % 2 == 0 else 1):,}")

    if n > 22:
        st.warning("Con tante persone il calcolo può richiedere molto tempo.")

    if st.button("Calcola squadre migliori"):
        with st.spinner("Calcolo in corso..."):
            punteggio_migliore, squadra_a, squadra_b = migliore(nomi, tabella_letta)

        media_a = somma_punteggi(squadra_a, tabella_letta) / len(squadra_a)
        media_b = somma_punteggi(squadra_b, tabella_letta) / len(squadra_b)

        st.subheader("Risultati")
        c1, c2, c3 = st.columns(3)
        c1.metric("Media squadra 1", round(media_a, 2))
        c2.metric("Media squadra 2", round(media_b, 2))
        c3.metric("Valore medio", round(punteggio_migliore, 2))

        t1, t2 = st.columns(2)
        with t1:
            st.markdown("**Squadra 1**")
            st.write([nomi[i] for i in squadra_a])
        with t2:
            st.markdown("**Squadra 2**")
            st.write([nomi[i] for i in squadra_b])
