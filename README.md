# Jorrob Toolkit

Toolkit PWA modulare pensato per preparare il lavoro tecnico prima di passarlo a ChatGPT.

## Versione
0.2.0

## Cosa cambia rispetto all'MVP iniziale
- Workspace persistente in `localStorage`
- import/export dello stato progetto
- Project Scanner con riconoscimento framework, `package.json`, script, test, TODO/FIXME e possibili credenziali esposte
- Debug Pack con categorie e prossime verifiche
- PWA Doctor più severo su manifest, service worker, cache e incoerenze di versione
- ChatGPT Pack schema `jorrob-chatgpt-pack/v2`
- copia diretta del Markdown per ChatGPT
- registro moduli in `modules.json`, base per aggiungere nuove PWA/strumenti senza cambiare il contratto centrale

## Principio architetturale
ChatGPT resta il cervello creativo/tecnico. Ogni strumento specializzato produce un output standard che può essere riutilizzato dagli altri moduli o consegnato a ChatGPT.

## Moduli attuali
1. Project Workspace
2. Project Scanner
3. Debug / Test Pack
4. PWA Doctor
5. ChatGPT Pack

## Prossimi moduli
- Replica / Project Planner
- Visual Diff
- Test Runner via GitHub Actions
- OCR Bench / Image Bench
- Orchestrator

## Privacy
I file selezionati dallo Scanner vengono elaborati nel browser. Lo stato persistente contiene sintesi e metadati; i contenuti completi dei file non vengono salvati automaticamente.
