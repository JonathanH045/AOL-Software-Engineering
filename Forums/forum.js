document.addEventListener('DOMContentLoaded', function() {
    const forumCards = document.querySelectorAll('.forum-card');
    
    forumCards.forEach(card => {
        card.addEventListener('click', function() {
            window.location.href = 'forumreplies.html';
        });
        
        card.style.cursor = 'pointer';
    });
});