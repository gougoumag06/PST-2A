// ==========================================
// === RÉGLAGES DU JEU ======================
// ==========================================
const MODE_DEV_ACTIF = true; 

let updateInterval = null;
const btnStop = document.getElementById('btn-stop');

let isFetchingChrono = false;
let isFetchingEnigme = false;
let isFetchingQuizStatus = false;
let isFetchingMaboul = false;
let isChronoPenalized = false;

// === On mémorise la ligne pour la redirection et le polling ===
let currentLine = '1';

window.onload = function() {
    if (!MODE_DEV_ACTIF) {
        const style = document.createElement('style');
        style.innerHTML = '.bypass-btn { display: none !important; }';
        document.head.appendChild(style);
    }

    document.getElementById('status').innerHTML = 
        '<p class="status-message">⏳ Vérification de l\'état de la bombe...</p>';

    fetch('/bouton/getGameStatus')
    .then(response => response.json())
    .then(data => {
        const etat = data.etat;
        
        if (data.ligne_active) {
            currentLine = data.ligne_active;
        }

        if (etat.temps_depart !== null && !etat.chrono_arrete) {
            console.log("Reprise de la partie en cours !");
            document.getElementById('status').innerHTML = 
                '<div class="emoji-large">⏱️</div>' +
                '<p style="color: green; font-size: 20px;">Reprise du chronomètre...</p>';
            demarrerMiseAJourChrono(); 
        } 
        else if (etat.chrono_arrete && etat.dernier_temps !== null) {
            document.getElementById('status').innerHTML = 
                '<div class="emoji-large">✅</div>' +
                '<p style="color: blue; font-size: 32px; font-weight: bold;">Jeu terminé.</p>' +
                '<button onclick="quitterEtReset()" class="btn-stop" style="margin-top: 20px; background: #FFFF00; color: #000; border-color: #FFFF00; box-shadow: 4px 4px 0px #888800;">🔁 RETOUR INSCRIPTION</button>';
        } 
        else {
            allumerLedBouton();
        }
    })
    .catch(error => {
        console.error("Erreur de statut:", error);
        allumerLedBouton(); 
    });
};

function allumerLedBouton() {
    quizAlreadyStarted = false; 
    document.getElementById('status').innerHTML = '<p class="status-message">⏳ Initialisation du jeu...</p>';
    
    fetch('/bouton/lancerJeux', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
    .then(response => response.json())
    .then(data => {
        document.getElementById('status').innerHTML = 
            '<div class="emoji-large">💡</div>' +
            '<p class="status-message">Prêt ! Appuyez sur le gros bouton START pour démarrer.</p>';
        demarrerMiseAJourChrono();
    })
    .catch(error => {
        document.getElementById('status').innerHTML = '<p style="color: red;">❌ Erreur: ' + error + '</p>';
    });
}

function demarrerMiseAJourChrono() {
    updateInterval = setInterval(() => {
        
        if (!isFetchingChrono) {
            isFetchingChrono = true;
            fetch('/bouton/obtenirTempsActuel?line=' + currentLine)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'running') {
                    btnStop.disabled = false;
                    
                    if (!isChronoPenalized) {
                        document.getElementById('status').innerHTML = 
                            '<div class="emoji-large">⏱️</div>' +
                            '<p style="color: green; font-size: 20px;">Chronomètre: <span id="chrono">' + 
                            data.temps_formate + '</span> secondes</p>';
                    }
                    
                    verifierEnigme();       
                    verifierQuizActif();    
                    verifierMaboulActif();  
                    
                } else if (data.status === 'waiting') {
                    btnStop.disabled = true;
                    document.getElementById('status').innerHTML = 
                        '<div class="emoji-large">💡</div>' +
                        '<p class="status-message">En attente... Appuyez sur le bouton START.</p>';
                        
                } else if (data.status === 'stopped') {
                    clearInterval(updateInterval);
                    btnStop.disabled = true;
                    
                    document.getElementById('status').innerHTML = 
                        '<div class="emoji-large">✅</div>' +
                        '<p style="color: blue; font-size: 32px; font-weight: bold;">Temps final: ' + 
                        data.temps_formate + ' s</p>' +
                        '<button onclick="quitterEtReset()" class="btn-stop" style="margin-top: 20px; background: #FFFF00; color: #000; border-color: #FFFF00; box-shadow: 4px 4px 0px #888800;">🔁 RETOUR INSCRIPTION</button>';
                    
                    document.getElementById('enigme-container').style.display = 'none';
                    document.getElementById('quiz-survie-container').style.display = 'none';
                    document.getElementById('maboul-container').style.display = 'none'; 
                }
            })
            .catch(error => console.error('Erreur Chrono:', error))
            .finally(() => { isFetchingChrono = false; });
        }
    }, 250);
}

function arreterJeu() {
    btnStop.disabled = true;
    quizAlreadyStarted = false;
    
    fetch('/bouton/resetJeu', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
    .then(response => response.json())
    .then(data => {
        if (updateInterval) {
            clearInterval(updateInterval);
            updateInterval = null;
        }
        
        document.getElementById('status').innerHTML = 
            '<div class="emoji-large">⏹️</div>' +
            '<p style="color: red; font-size: 24px; font-weight: bold;">Jeu arrêté manuellement</p>' +
            '<button onclick="quitterEtReset()" class="btn-stop" style="margin-top: 20px; background: #FFFF00; color: #000; border-color: #FFFF00; box-shadow: 4px 4px 0px #888800;">🔁 RETOUR INSCRIPTION</button>';
        
        document.getElementById('enigme-container').style.display = 'none';
        document.getElementById('quiz-survie-container').style.display = 'none';
        document.getElementById('maboul-container').style.display = 'none';
        
        fetch('/maboul/desactiver', { method: 'POST' }); 
    })
    .catch(error => { btnStop.disabled = false; });
}

function quitterEtReset() {
    fetch('/bouton/resetJeu', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
    .then(() => {
        window.location.href = '/player/login?line=' + currentLine;
    })
    .catch(err => {
        console.error("Erreur lors du reset:", err);
        window.location.href = '/player/login?line=' + currentLine;
    });
}

// ==========================================
// === LOGIQUE DU MASTERMIND (ÉTAPE 1) ======
// ==========================================
let mmSelectsFilled = false;
let isSubmittingMastermind = false;

function verifierEnigme() {
    if (isFetchingEnigme) return;
    isFetchingEnigme = true;

    fetch('/mastermind/obtenirEnigme?line=' + currentLine)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'active') {
            if(document.getElementById('maboul-container').style.display !== 'block') {
                document.getElementById('enigme-container').style.display = 'block';
            }
            if (!mmSelectsFilled) {
                const selects = document.querySelectorAll('.mm-select');
                selects.forEach(sel => {
                    data.colors.forEach(c => {
                        let opt = document.createElement('option');
                        opt.value = c;
                        opt.text = data.french_colors[c];
                        opt.style.backgroundColor = c;
                        opt.style.color = (['black', 'purple', 'blue', 'red'].includes(c)) ? 'white' : 'black';
                        sel.appendChild(opt);
                    });
                });
                mmSelectsFilled = true;
            }
            afficherHistorique(data.history);
        } else if (data.status === 'resolved') {
            document.getElementById('enigme-container').style.display = 'none';
        }
    })
    .catch(error => console.error(error))
    .finally(() => { isFetchingEnigme = false; });
}

function afficherHistorique(history) {
    const histDiv = document.getElementById('mm-history');
    histDiv.innerHTML = '';
    if (history && history.length > 0) {
        history.forEach((h, index) => {
            let html = `<div style="display:flex; justify-content:space-between; align-items: center; padding:8px; border-bottom:1px solid #eee;">
                <div style="display:flex; align-items:center;">
                    <span style="margin-right:15px; font-weight:bold;">Essai ${index + 1} :</span>`;
            h.guess.forEach(c => {
                html += `<div style="display:inline-block; width:25px; height:25px; border-radius:50%; background-color:${c}; margin-right:5px; border:1px solid #ccc;"></div>`;
            });
            html += `</div><div><span style="color:green; font-weight:bold;">${h.exact} bien placés</span> | <span style="color:orange; font-weight:bold;">${h.partial} mal placés</span></div></div>`;
            histDiv.innerHTML += html;
        });
        histDiv.scrollTop = histDiv.scrollHeight;
    }
}

const selects = document.querySelectorAll('.mm-select');

function updateSelectBackground(select) {
    const color = select.value;
    if (color) {
        select.style.backgroundColor = color;
        select.style.color = (['black', 'purple', 'blue', 'red'].includes(color)) ? 'white' : 'black';
    } else {
        select.style.backgroundColor = '';
        select.style.color = 'black';
    }
}

selects.forEach(s => s.addEventListener('change', function() {
    updateSelectBackground(this);
    if (Array.from(selects).every(s => s.value !== "")) {
        setTimeout(() => verifierReponseMastermind(), 200);
    }
}));

function verifierReponseMastermind() {
    if (isSubmittingMastermind) return; 
    const guess = Array.from(selects).map(s => s.value);
    if (guess.includes("")) return;
    isSubmittingMastermind = true; 

    fetch('/bouton/verifierReponseMastermind', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guess: guess })
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'correct') {
            document.getElementById('mm-result').innerHTML = `<span style="color:green; font-size:20px;">✅ ${data.message} - Appuyez sur le Bouton 1</span>`;
            setTimeout(() => { document.getElementById('enigme-container').style.display = 'none'; }, 3000);
        } else if(data.status === 'incorrect') {
            document.getElementById('mm-result').innerHTML = `<span style="color:orange;">Essai incorrect !</span>`;
            afficherHistorique(data.history);
            selects.forEach(s => { s.value = ''; updateSelectBackground(s); });
        }
        setTimeout(() => { isSubmittingMastermind = false; }, 200);
    })
    .catch(error => { 
        console.error(error);
        isSubmittingMastermind = false; 
    });
}

// ==========================================
// === LOGIQUE DU QUIZ SURVIE (ÉTAPE 2) =====
// ==========================================
let quizQuestions = [];
let quizCurrentIndex = 0;
let quizScore = 0; 
let quizAlreadyStarted = false; 
let quizVerrouille = false;

function verifierQuizActif() {
    if (isFetchingQuizStatus || quizAlreadyStarted) return;
    isFetchingQuizStatus = true;

    fetch('/bouton/verifierQuiz?line=' + currentLine)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'active' && !quizAlreadyStarted) {
            quizAlreadyStarted = true;
            activerQuizSurvie();
        }
    })
    .catch(e => console.error(e))
    .finally(() => { isFetchingQuizStatus = false; });
}

function activerQuizSurvie() {
    document.getElementById('quiz-survie-container').style.display = 'block';
    fetchQuizQuestions();
}

function fetchQuizQuestions() {
    fetch('/quiz/api/questions')
    .then(response => response.json())
    .then(data => {
        quizQuestions = data;
        resetQuiz();
    })
    .catch(err => console.error("Erreur chargement quiz:", err));
}

function resetQuiz() {
    quizCurrentIndex = 0;
    quizScore = 0; 
    quizVerrouille = false; 
    document.getElementById('quiz-error-msg').innerText = ""; 
    showQuizQuestion(); 
}

function afficherMessageInfo(message, couleur = "red") {
    const msgDiv = document.getElementById('quiz-error-msg');
    msgDiv.innerText = message;
    msgDiv.style.color = couleur;
    msgDiv.style.fontWeight = "bold";
    setTimeout(() => {
        if (msgDiv.innerText === message) msgDiv.innerText = "";
    }, 1500);
}

function showQuizQuestion() {
    if (quizCurrentIndex >= quizQuestions.length) {
        evaluerFinQuiz();
        return;
    }
    
    const q = quizQuestions[quizCurrentIndex];
    document.getElementById('quiz-question-text').innerText = q.question;
    document.getElementById('quiz-q-num').innerText = quizCurrentIndex + 1;
    
    const choicesDiv = document.getElementById('quiz-choices');
    choicesDiv.innerHTML = '';
    
    const quizColors = [
        { bg: '#e74c3c', hover: '#c0392b', keyLabel: 'R', key: 'r' }, 
        { bg: '#3498db', hover: '#2980b9', keyLabel: 'B', key: 'b' }, 
        { bg: '#2ecc71', hover: '#27ae60', keyLabel: 'G', key: 'g' }, 
        { bg: '#f1c40f', hover: '#f39c12', keyLabel: 'Y', key: 'y' }, 
        { bg: '#9b59b6', hover: '#8e44ad', keyLabel: 'P', key: 'p' }, 
        { bg: '#100e0e', hover: '#000000', keyLabel: 'K', key: 'k' }  
    ];

    q.choix.forEach((choix, index) => {
        const btn = document.createElement('button');
        const colorDef = quizColors[index % quizColors.length];

        btn.className = 'quiz-choice-btn';
        btn.style.backgroundColor = colorDef.bg;
        btn.innerHTML = choix;        
        btn.onmouseover = () => btn.style.backgroundColor = colorDef.hover;
        btn.onmouseout = () => btn.style.backgroundColor = colorDef.bg;
        
        btn.onclick = () => checkQuizAnswer(choix, q.bonne_reponse);
        choicesDiv.appendChild(btn);
    });
}

function checkQuizAnswer(selected, correct) {
    if (quizVerrouille) return;
    quizVerrouille = true; 

    if (selected === correct) {
        quizScore++;
        afficherMessageInfo('✅ Bonne réponse !', '#2ecc71');
    } else {
        afficherMessageInfo('❌ Mauvaise réponse !', '#e74c3c');
    }

    setTimeout(() => {
        quizCurrentIndex++;
        quizVerrouille = false;
        showQuizQuestion();
    }, 500);
}

function evaluerFinQuiz() {
    quizVerrouille = true;
    if (quizScore >= 4) {
        validerVictoireQuiz(`🏆 SURVIE RÉUSSIE (${quizScore}/${quizQuestions.length}) !<br>Appuyez sur le Bouton 2`);
    } else {
        document.getElementById('quiz-error-msg').innerText = "";
        document.getElementById('quiz-survie-container').innerHTML = `<h2 style='color:#e74c3c; text-align:center;'>💀 ÉCHEC (${quizScore}/${quizQuestions.length}) !<br>Préparation d'un nouveau quiz...</h2>`;
        
        setTimeout(() => {
            const boutonBypass = MODE_DEV_ACTIF ? `<button onclick="bypassQuiz()" class="bypass-btn">⏩ BYPASS DEVS</button>` : '';

            document.getElementById('quiz-survie-container').innerHTML = `
                <h2 style="color: #00CCFF;">🚀 SURVIVAL MISSION</h2>
                <h3 id="quiz-question-text" style="font-size: 0.8em; line-height: 1.6; min-height: 60px;">Chargement...</h3>
                <div id="quiz-choices" style="display: flex; flex-direction: column; gap: 10px;"></div>
                <div style="margin-top: 20px; font-size: 0.6em; color: #888;">QUESTION <span id="quiz-q-num">1</span> / 5</div>
                <div id="quiz-error-msg" style="color: #FF0055; font-size: 0.6em; min-height: 24px; margin-top: 15px;"></div>
                ${boutonBypass}
            `;
            fetchQuizQuestions(); 
        }, 2000);
    }
}

function bypassQuiz() {
    if (!quizAlreadyStarted || quizVerrouille) return; 
    quizVerrouille = true;
    validerVictoireQuiz("🛠️ BYPASS ACTIVÉ !<br>Appuyez sur le Bouton 2");
}

function validerVictoireQuiz(message) {
    document.getElementById('quiz-error-msg').innerText = "";
    document.getElementById('quiz-survie-container').innerHTML = `<h2 style='color:#2ecc71; text-align:center;'>${message}</h2>`;
    fetch('/bouton/validerQuiz', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
    .then(() => {
        setTimeout(() => { document.getElementById('quiz-survie-container').style.display = 'none'; }, 3000);
    });
}

// ==========================================
// === LOGIQUE DU DR MABOUL (POLLING) =======
// ==========================================
let lastNbTouches = 0;
let lastMaboulPhase = ""; 

function verifierMaboulActif() {
    if (isFetchingMaboul) return;
    isFetchingMaboul = true;

    // ---> SÉCURITÉ ULTIME : Le JS dit clairement au serveur sur quelle ligne il est !
    fetch('/maboul/status?line=' + currentLine)
    .then(res => res.json())
    .then(data => {
        const maboulContainer = document.getElementById('maboul-container');
        
        if (data.phase === 'inactive') {
            if (maboulContainer.style.display !== 'none') maboulContainer.style.display = 'none';
            return;
        }
        
        if (document.getElementById('enigme-container').style.display !== 'none') document.getElementById('enigme-container').style.display = 'none';
        if (document.getElementById('quiz-survie-container').style.display !== 'none') document.getElementById('quiz-survie-container').style.display = 'none';
        if (maboulContainer.style.display !== 'block') maboulContainer.style.display = 'block';

        const maboulStatusBox = document.getElementById('maboul-status-box');
        const maboulInstruction = document.getElementById('maboul-instruction');
        const maboulAlert = document.getElementById('maboul-alert');

        if (data.phase === 'idle') {
            if (lastMaboulPhase !== 'idle') {
                maboulStatusBox.className = "maboul-box-inner status-attente";
                maboulInstruction.innerHTML = `👉 POSITIONNEZ L'ANNEAU SUR LE PLOT : <span style="color: #00FF55; font-weight:bold;">START</span>`;
                lastMaboulPhase = 'idle';
            }
        } 
        else if (data.phase === 'playing') {
            if (lastMaboulPhase !== 'playing') {
                maboulStatusBox.className = "maboul-box-inner status-en-cours";
                lastMaboulPhase = 'playing';
            }
            
            maboulInstruction.innerHTML = `⚡ FIL SOUS TENSION !<br>AVANCEZ JUSQU'AU PLOT : <span style="color: #FF0055; font-weight:bold;">END</span><br><br><span style="color:#00CCFF; font-size:1.2em;">Évitez de toucher le fil !</span>`;

            if (data.nb_touches > lastNbTouches) {
                console.log("💥 CHOC DETECTÉ ! AFFECTATION DE LA PÉNALITÉ...");
                
                maboulStatusBox.classList.add('flash-red');
                maboulAlert.innerHTML = `💥 AÏE ! PÉNALITÉ +5 SECONDES !<br><span style="font-size: 0.7em;">(Erreur n°${data.nb_touches})</span>`;
                
                isChronoPenalized = true;
                document.getElementById('status').innerHTML = 
                    '<div class="emoji-large" style="animation: none;">⚡</div>' +
                    '<p style="color: #FF0055; font-size: 32px; font-weight:bold; text-shadow: 2px 2px #000;">+5 SECONDES !</p>';
                
                setTimeout(() => {
                    maboulStatusBox.classList.remove('flash-red');
                    maboulAlert.innerHTML = "";
                }, 800);
                
                setTimeout(() => {
                    isChronoPenalized = false; 
                }, 1500);
            }
            lastNbTouches = data.nb_touches;
        } 
        else if (data.phase === 'finished') {
            if (lastMaboulPhase !== 'finished') {
                maboulStatusBox.classList.remove('flash-red');
                if (data.result === 'success') {
                    maboulStatusBox.className = "maboul-box-inner";
                    maboulStatusBox.style.borderColor = "#00FF55";
                    maboulInstruction.innerHTML = `🏆 OPÉRATION RÉUSSIE !<br>Appuyez sur le Bouton de Fin.`;
                } else {
                    maboulStatusBox.className = "maboul-box-inner";
                    maboulStatusBox.style.borderColor = "#FF0000";
                    maboulInstruction.innerHTML = `💀 ÉCHEC !`;
                }
                lastMaboulPhase = 'finished';
            }
        }
    })
    .catch(err => console.error("Erreur Maboul:", err))
    .finally(() => { isFetchingMaboul = false; });
}

// ==========================================
// === GESTIONNAIRE GLOBAL DU CLAVIER =======
// ==========================================
document.addEventListener('keydown', function(event) {
    if (event.ctrlKey || event.altKey || event.metaKey) return;
    const key = event.key.toLowerCase();

    if (document.getElementById('enigme-container').style.display === 'block') {
        const keyMapMastermind = {'k': 'black', 'r': 'red', 'b': 'blue', 'p': 'purple', 'y': 'yellow', 'g': 'green'};
        
        if (keyMapMastermind[key]) {
            for (let i = 0; i < selects.length; i++) {
                if (!selects[i].value) {
                    selects[i].value = keyMapMastermind[key];
                    updateSelectBackground(selects[i]);
                    break; 
                }
            }
            if (Array.from(selects).every(s => s.value !== "")) {
                setTimeout(() => verifierReponseMastermind(), 200);
            }
        } 
        else if (key === 'backspace') {
            for (let i = selects.length - 1; i >= 0; i--) {
                if (selects[i].value) {
                    selects[i].value = "";
                    updateSelectBackground(selects[i]);
                    break;
                }
            }
        }
        return; 
    }

    if (document.getElementById('quiz-survie-container').style.display === 'block') {
        const keyMapQuiz = { 'r': 0, 'b': 1, 'g': 2, 'y': 3, 'p': 4, 'k': 5 };
        const indexChoisi = keyMapQuiz[key];
        if (indexChoisi !== undefined) {
            const q = quizQuestions[quizCurrentIndex];
            if (q && q.choix && q.choix[indexChoisi]) {
                checkQuizAnswer(q.choix[indexChoisi], q.bonne_reponse);
            }
        }
    }
});