document.addEventListener('DOMContentLoaded', function() {

    const is_recurring_checkbox = document.querySelector('#id_is_recurring');

    let is_recurring = false;

    is_recurring_checkbox.addEventListener('click', function() {
        is_recurring = !is_recurring;
        console.log('checkbox is ', is_recurring);
    });

    const submitButton = document.querySelector('.submit_session');
    submitButton.addEventListener('click', function() {
        console.log('submit button clicked');
    });
    

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