# Copenhagen Re-Commerce Matrix — Strategic Core

## 1. Circular Potential Index (CPI) Formula
La formula proprietaria per valutare il potenziale di un quartiere/zona per la moda circolare e il re-commerce:

$$	ext{CPI} = (w_1 \cdot 	ext{Supply}) + (w_2 \cdot 	ext{Demographics}) + (w_3 \cdot 	ext{Market Gap})$$

### Definizione delle Variabili (Scala 0 - 10):
Il CPI è calcolato con pesi che dipendono dal profilo di business selezionato (`cpi_engine.py`, `BUSINESS_PROFILES`):

| Business profile | Supply ($w_1$) | Demographics ($w_2$) | Market Gap ($w_3$) | Sum |
|---|---:|---:|---:|---:|
| Vintage Premium | 0.20 | 0.40 | 0.40 | 1.00 |
| Kilo Sale | 0.50 | 0.30 | 0.20 | 1.00 |
| Upcycling | 0.40 | 0.20 | 0.40 | 1.00 |
| Curated Vintage | 0.33 | 0.33 | 0.34 | 1.00 |

- **Supply:** textile waste density and recoverable material volume.
- **Demographics:** share of the 18-35 target resident base and disposable income (DKK). Derived from `population_gen_z` and `avg_income_dkk` via min-max normalisation (see `D-016` in `DECISIONS.md`).
- **Market Gap:** resident population versus existing second-hand stores and collection bins.

## 2. Strategia di Posizionamento
- **Oceano Blu:** A differenza dei sistemi GIS tradizionali (es. CARTO) focalizzati solo sul footfall pedonale e su affitti di centro città, il CPI scova quartieri ad alto potenziale di approvvigionamento e presenza Gen Z, abbattendo i costi fisici per le micro-imprese.
- **Canale Telegram (Zero-UI):** Interfaccia istantanea e asincrona per eliminare l'attrito d'uso rispetto ai software di Location Intelligence complessi.
