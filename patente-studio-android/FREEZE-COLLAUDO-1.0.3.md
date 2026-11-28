# Freeze di collaudo Patente Studio 1.0.3 / PC 0.8.9
Data: 28 novembre 2026.
Nessuna nuova funzionalità; soltanto correzioni di difetti riproducibili.
Android build: https://github.com/Jorrob98/PROVA2026/actions/runs/46132710010
Commit compilato: 8ad9b2db3f3155e4dd583484e9bc99979bc20c0b
APK candidato: PatenteStudio-Tablet-1.0.3-COLLAUDO-IP.apk
SHA-256: c20c841760225247cb77b507a47f216a06ff4567f8a9bef0c97fcf83950b12b4
Dimensione: 1845998 byte
Certificato SHA-256: 3f31e96ace4144ce33391c06444ecbb93c36084dcd0e1fd4c0ce7f2f223ad54b
PC isolato: PatenteStudio-PC-0.8.9-COLLAUDO-ISOLATO.exe
SHA-256: e7e3269c47bdbad96c74ebc0cab5a638ddd0a857a5dcf3f4d9ff0045e4b506a4
Sorgenti Android SHA-256: 132450d5f8b5af5662731fb5c30637183a9108764776ab019b1fa2ff4d24fdfd
Sorgenti Windows riconciliati SHA-256: aa4e59ae4e65915382ce659308e3845f603b7aa797296b4607f6b456e2e47a6c

## Controlli ripetuti
- go test ./... -count=1: PASS
- go vet ./...: PASS
- node tests/draft_protocol_test.js: PASS (bridge simulato)
- verify_ai_assets.py --manifest ai-hashes.json: PASS (integrità, non qualità fotografica)
- apksigner verify: PASS v2/v3
- tutte le 106 entry ZIP dell'APK firmato coincidono byte per byte con l'APK unsigned della build; il blocco firma e padding differiscono come previsto.
- archivio sorgente Android coincide byte per byte con l'artifact.
- feed main: 1.0.2, versionCode 3. Nessun aggiornamento 1.0.3 pubblico.

## Blocco rilascio
Prima di pubblicare: collaudo fisico con dati fittizi, confronto con 0.8.8 operativa, verifica foto/firma, riavvio e Wi-Fi, cambio IP, aggiornamento in-place da file, 8 ore effettive. Non dichiarare il collaudo completato in assenza dei risultati.
Il PC candidato non è firmato Authenticode e non deve sostituire l'EXE operativo.
Dopo esito positivo, pubblicare atomicamente APK verificato e indice; controllare su secondo tablet 1.0.2 il download e installazione dall'app. Se questo fallisce, interrompere distribuzione; non effettuare downgrade forzato. Ogni modifica post-freeze richiede nuovo hash, nuova build e nuovo codice versione se già installato.
