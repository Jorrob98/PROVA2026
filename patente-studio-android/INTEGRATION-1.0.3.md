# Patente Studio Tablet 1.0.3 — contratto di integrazione Windows
Stato: specifica da implementare e verificare sul sorgente Windows esatto 0.8.8/0.8.9; non rappresenta funzionalità già operative.
## Invarianti
- Conservare identificativo protocollo, porta 18886, pairing QR, HTTPS con pin del certificato e ruolo capture. Nessun fallback HTTP o accettazione automatica di certificati diversi.
- Ogni pratica deve avere un ID opaco casuale, non derivato dal nominativo o da altri dati personali; ogni acquisizione ha un ID operazione indipendente. Il PC verifica autorizzazione, associazione tablet/pratica e versione della pratica.
- La richiesta di invio ripetuta con lo stesso ID e identico contenuto deve restituire la stessa ricevuta; un ID riutilizzato con contenuto diverso viene rifiutato. Il cambio pratica non può riassociare una bozza.
- Il PC restituisce conferma solo dopo salvataggio durevole di tutti i file richiesti, verifica dei relativi hash e registrazione atomica del risultato. Il tablet conserva una bozza cifrata locale finché la ricevuta corrisponde a pratica, operazione e contenuti; rimuove i temporanei dopo conferma. Nessuna cancellazione automatica della bozza in caso di timeout o risposta ambigua.
- Dopo perdita rete, riprovare con backoff e senza reinizializzare la WebView durante una pratica. Dopo riavvio, ripristinare solo le bozze relative alla stessa pratica; richiedere nuova autorizzazione quando necessaria.
- Cambio IP: scoperta LAN opzionale, senza fidarsi di risposte mDNS non autenticate; se il nuovo IP non è coperto dal certificato verificato, richiedere nuovo QR. Mai aggirare il pin.
- Notifiche: solo segnale generico di nuova pratica, senza nome o foto nella notifica. Nessun invio al cloud.
- Aggiornamenti: consentiti soltanto dalla home, mai durante una pratica; verificare package, versionCode, SHA-256 e firma identica. Non pubblicare un manifesto prima dell'APK firmato e verificato.
- Errori: registrare soltanto codice evento, ora e versione, senza token, nomi, IP, immagini o firme.
## Piano test integrato (non ancora eseguito)
10.000 operazioni effettive su istanza Windows di test con immagini e firme sintetiche, suddivise in 4.000 invii ordinari, 2.000 reinvii duplicati, 1.000 timeout prima/dopo commit, 1.000 associazioni errate, 1.000 riavvii/riconnessioni, 1.000 operazioni concorrenti. Conservare seed, log senza PII, esiti e contatori.
Criteri: zero associazioni errate accettate, zero duplicati persistiti, zero conferme prima del commit, zero perdite di bozze prima della ricevuta. Misurare latenza, memoria e spazio disco; riportare errori e condizioni del test.
Collaudo fisico separato con 6 PC e 4 tablet: QR, Wi-Fi disattivato/riattivato, cambio IP, spegnimento PC, chiusura app, riavvio tablet, fotocamera e orientamento, foto JPEG <=35 KB, firma, aggiornamento in-place, modalità dedicata.
