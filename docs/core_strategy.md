# Copenhagen Re-Commerce Matrix — Strategic Core

## 1. Circular Potential Index (CPI) Formula
La formula proprietaria per valutare il potenziale di un quartiere/zona per la moda circolare e il re-commerce:

$$CPI = (S \times 0.40) + (D \times 0.35) + (G \times 0.25)$$

### Definizione delle Variabili (Normalizzate 0 - 100):
- **S (Supply / Scarti Tessili - Peso 40%):** Volume di rifiuti tessili (*textilaffald*) e presenza di punti di smistamento (*sorteringspunkter*) da Open Data DK. Rappresenta la facilità e l'economicità di approvvigionamento di materia prima a costo zero.
- **D (Demand / Demografia - Peso 35%):** Percentuale di popolazione 18-35 anni (Gen Z / Universitari) e livello di reddito medio da Københavns Kommune Statistikbank. Rappresenta il bacino d'utenza etico e propenso all'acquisto.
- **G (Market Gap / Vuoto di Mercato - Peso 25%):** Misura inversamente proporzionale alla densità dei competitor (negozi vintage/second-hand) rilevati tramite OpenStreetMap Overpass API nel raggio di 2 km. Valore 100 = Oceano Blu incontestato.

## 2. Strategia di Posizionamento
- **Oceano Blu:** A differenza dei sistemi GIS tradizionali (es. CARTO) focalizzati solo sul footfall pedonale e su affitti di centro città, il CPI scova quartieri ad alto potenziale di approvvigionamento e presenza Gen Z, abbattendo i costi fisici per le micro-imprese.
- **Canale Telegram (Zero-UI):** Interfaccia istantanea e asincrona per eliminare l'attrito d'uso rispetto ai software di Location Intelligence complessi.