document.addEventListener('DOMContentLoaded', () => {
        const elements = document.querySelectorAll('.stat-card, .custom-card');
        elements.forEach((el, index) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(15px)';
            el.style.transition = '0.4s ease-out';
            setTimeout(() => {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, index * 80);
        });
    });
