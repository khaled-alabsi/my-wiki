Sie können den terminalbasierten Coding-Agenten Pi (pi.dev) auf zwei Arten mit LM Studio verbinden: entweder über die manuelle Bearbeitung der Konfigurationsdatei oder vollautomatisch über eine offizielle Erweiterung. [1, 2] 
Bevor Sie beginnen, stellen Sie sicher, dass Ihr lokaler Server in LM Studio aktiv ist. Öffnen Sie LM Studio, wechseln Sie in den Reiter Local Server (Entwickler-Tab) und klicken Sie auf Start Server. Der Server läuft standardmäßig unter http://localhost:1234. [1, 3] 
------------------------------
## Methode 1: Automatisch via Pi-Erweiterung (Empfohlen)
Pi unterstützt Pakete aus der Community, die installierte Modelle aus LM Studio automatisch erkennen und hinzufügen. [1, 4] 

   1. Pi-Paket installieren: Öffnen Sie Ihr Terminal und führen Sie den Installationsbefehl für das LM Studio-Plugin aus:
   
   pi install pi-lmstudio
   
   (Alternativ können Sie auch das Community-Paket pi install @monroewilliams/pi-local oder pi install pi-setup-custom-providers nutzen).
   2. Modell auswählen: Starten Sie Pi in Ihrem Projektverzeichnis mit dem Befehl pi. Nutzen Sie anschließend den Befehl /model im Pi-Terminal.
   3. Wählen Sie das gewünschte Modell aus der Liste aus. Diese tragen nun das Präfix lmstudio/. [1, 5, 6, 7, 8] 

------------------------------
## Methode 2: Manuell über die models.json [9, 10] 
Falls Sie keine zusätzlichen Erweiterungen installieren möchten, können Sie LM Studio als benutzerdefinierten OpenAI-kompatiblen Provider eintragen. [2, 11] 

   1. Konfigurationsdatei öffnen: Öffnen oder erstellen Sie die Datei ~/.pi/agent/models.json auf Ihrem System.
   2. Konfiguration einfügen: Fügen Sie den folgenden JSON-Block ein. Ersetzen Sie "ihr-modell-id" durch die exakte Model ID, die in Ihrem LM Studio Server-Tab angezeigt wird: [2, 3, 11, 12] 


{
  "providers": {
    "lmstudio": {
      "baseUrl": "http://localhost:1234/v1",
      "api": "openai-completions",
      "apiKey": "lm-studio",
      "models": [
        {
          "id": "gemma-4-12b-it-qat",
          "name": "LM Studio Local",
          "contextWindow": 32000,
          "compat": {
            "supportsDeveloperRole": false,
            "supportsReasoningEffort": false
          }
        }
      ]
    }
  }
}


   1. Anpassung für lokale Modelle: Viele Open-Source-Modelle unterstützen bestimmte OpenAI-Rollen (wie developer) nicht nativ. Sollte das Modell Fehler ausgeben, fügen Sie die Kompatibilitäts-Flags "compat" in das JSON-Objekt Ihres Modells ein:
   
   "compat": {
     "supportsDeveloperRole": false,
     "supportsReasoningEffort": false
   }
   
   2. Aktivieren: Starten Sie pi im Terminal und tippen Sie /model, um Ihr manuell hinzugefügtes Modell auszuwählen. [1, 2, 12] 

