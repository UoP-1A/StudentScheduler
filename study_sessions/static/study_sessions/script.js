document.addEventListener('DOMContentLoaded', function() {

    function formSubmit() {
        const button = document.querySelector('.submit_session');
        button.addEventListener('click', function() {
            console.log('button clicked');
        });
    }
    formSubmit();

    function fetchSessions(){
        fetch('/study_sessions/sessions')
            .then(response => response.json())
            .then(data => {
                console.log(data);
            })
            .catch(error => console.error('Error:', error));
    }
    fetchSessions();
    
});