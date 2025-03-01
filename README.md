# ThreatLinker - CVE & CAPEC Correlation Platform

ThreatLinker è una piattaforma di **correlazione tra vulnerabilità CVE e attacchi CAPEC**, progettata per analizzare e collegare automaticamente le vulnerabilità del **National Vulnerability Database (NVD)** ai pattern di attacco del **Common Attack Pattern Enumeration and Classification (CAPEC)**.

##  **A cosa serve ThreatLinker?**
- **Correlazione automatica tra CVE e CAPEC**  
  Analizza vulnerabilità **CVE** e le collega ai relativi **pattern di attacco CAPEC**.
  
- **Machine Learning e NLP per la sicurezza informatica**  
  Utilizza modelli avanzati come **SBERT** e **AttackBERT** per identificare relazioni tra vulnerabilità e tecniche di attacco.

- **Supporto per GPU NVIDIA**  
  Accelerazione tramite **CUDA** per elaborazioni più veloci su grandi dataset.

- **Aggiornamento automatico dei dati**  
  Scarica e importa automaticamente gli ultimi dataset CVE, CAPEC.

---
## **Prerequisiti**

Per eseguire correttamente il progetto, assicurati di avere i seguenti componenti installati sul tuo sistema operativo.

### 🔹 **Windows**
- **Windows 10/11 con WSL 2 abilitato**  
  (WSL 2 è richiesto per il supporto GPU nei container)
- **Una distribuzione Linux installata su WSL** (es. Ubuntu)
- **Docker Desktop con supporto per WSL 2**
- **Driver NVIDIA aggiornati**
- **NVIDIA Container Toolkit** (necessario per l'uso della GPU nei container)

### 🔹 **Linux**
- **Driver NVIDIA aggiornati**
- **Docker e Docker Compose installati**
- **NVIDIA Container Toolkit** (per l'accesso alla GPU nei container)

**Nota:**  
Se non hai una GPU NVIDIA, puoi comunque eseguire il progetto, ma senza accelerazione hardware per i modelli di Machine Learning.

---
## **Setup & Avvio**

Dopo aver completato l'installazione dei prerequisiti, segui questi passaggi per avviare ThreatLinker:

### 🔹 **1. Clona il repository**
```bash
git clone https://github.com/andreaciavotta/threatlinker-docker.git
cd threatlinker
```

### 🔹 **2. Costruisci le immagini Docker**
```bash
docker build -t cuda_installer -f backend/Dockerfile.cuda backend/
docker build -t base -f backend/Dockerfile.base backend/
docker-compose build --no-cache
```

### 🔹 **3. Avvia l'applicazione**
```bash
docker compose up -d
```

Durante l'avvio Django deve scaricare tutte le CVE dal 1999 all'anno corrente per cui potrebbe volerci un pò di tempo prima di essere operativo.
