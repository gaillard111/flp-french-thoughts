@echo off
REM ===========================================================================
REM bootstrap.bat — Démarrage automatique MTTV-FLP
REM ===========================================================================
REM  Ce script est conçu pour être exécuté par le Windows Task Scheduler
REM  au démarrage de la machine. Il lance l'orchestrateur MTTV-FLP qui
REM  démarre et supervise tous les services.
REM
REM  Installation :
REM    1. Ouvrir "Task Scheduler"
REM    2. Créer une tâche :
REM       - Déclencheur : "Au démarrage"
REM       - Action : démarrer ce script
REM       - Exécuter avec les plus hauts privilèges : OUI
REM       - Configurer pour : Windows 10/11
REM
REM  Signature : 0x4D545456
REM ===========================================================================

SETLOCAL

REM ─── Chemins ─────────────────────────────────────────────────────────────
SET PROJECT_DIR=%~dp0
SET PYTHON=python
SET ORCHESTRATOR=%PROJECT_DIR%zoo-code\mttv_orchestrator.py
SET LOG_FILE=%PROJECT_DIR%bootstrap.log

REM ─── Rediriger toute la sortie vers le log ───────────────────────────────
ECHO [%DATE% %TIME%] ==================================================== >> "%LOG_FILE%" 2>&1
ECHO [%DATE% %TIME%] MTTV-FLP BOOTSTRAP — Démarrage >> "%LOG_FILE%" 2>&1
ECHO [%DATE% %TIME%] Signature: 0x4D545456 >> "%LOG_FILE%" 2>&1
ECHO [%DATE% %TIME%] ==================================================== >> "%LOG_FILE%" 2>&1

REM ─── Vérifier que Python est accessible ─────────────────────────────────
WHERE %PYTHON% >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO [%DATE% %TIME%] ERREUR: Python introuvable dans le PATH >> "%LOG_FILE%" 2>&1
    EXIT /B 1
)

ECHO [%DATE% %TIME%] Python trouvé: >> "%LOG_FILE%" 2>&1
%PYTHON% --version >> "%LOG_FILE%" 2>&1

REM ─── Attendre que le réseau soit disponible (optionnel) ─────────────────
REM Ping d'un hôte fiable pour attendre la connexion réseau
ECHO [%DATE% %TIME%] Attente du réseau... >> "%LOG_FILE%" 2>&1
ping -n 1 8.8.8.8 >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    ECHO [%DATE% %TIME%] Réseau disponible >> "%LOG_FILE%" 2>&1
) ELSE (
    ECHO [%DATE% %TIME%] Avertissement: Réseau non disponible (les services continuent) >> "%LOG_FILE%" 2>&1
)

REM ─── Lancer l'orchestrateur en mode daemon (watchdog) ───────────────────
ECHO [%DATE% %TIME%] Démarrage de l'orchestrateur... >> "%LOG_FILE%" 2>&1

START "MTTV-Orchestrator" /MIN /B %PYTHON% "%ORCHESTRATOR%" daemon --interval 15 >> "%LOG_FILE%" 2>&1

REM Sauvegarder le PID de l'orchestrateur
SET ORCHESTRATOR_PID=%ERRORLEVEL%
ECHO [%DATE% %TIME%] Orchestrateur démarré (PID: regarder le fichier PID) >> "%LOG_FILE%" 2>&1

REM ─── Vérification initiale après 10 secondes ────────────────────────────
ECHO [%DATE% %TIME%] Attente 10s pour le démarrage des services... >> "%LOG_FILE%" 2>&1
ping -n 11 localhost >nul

ECHO [%DATE% %TIME%] Vérification des services... >> "%LOG_FILE%" 2>&1
%PYTHON% "%ORCHESTRATOR%" status --json >> "%LOG_FILE%" 2>&1

ECHO [%DATE% %TIME%] ==================================================== >> "%LOG_FILE%" 2>&1
ECHO [%DATE% %TIME%] BOOTSTRAP TERMINÉ >> "%LOG_FILE%" 2>&1
ECHO [%DATE% %TIME%] ==================================================== >> "%LOG_FILE%" 2>&1

ENDLOCAL
EXIT /B 0
