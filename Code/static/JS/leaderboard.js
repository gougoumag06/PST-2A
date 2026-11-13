/**
 * Rafraîchissement automatique du tableau des scores (Ajax/Fetch)
 * Toutes les 5000ms (5 secondes)
 */
setInterval(function() {
    fetch(window.location.href)
    .then(response => response.text())
    .then(html => {
        let parser = new DOMParser();
        let doc = parser.parseFromString(html, 'text/html');
        
        // Extraction du nouveau contenu du tableau
        let nouveauContenu = doc.getElementById('leaderboard-body').innerHTML;
        
        // Injection fluide dans le DOM actuel
        document.getElementById('leaderboard-body').innerHTML = nouveauContenu;
    })
    .catch(error => console.error('Erreur lors du rafraîchissement du leaderboard :', error));
}, 5000);