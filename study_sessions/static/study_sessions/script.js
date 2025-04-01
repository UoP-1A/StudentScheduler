document.addEventListener('DOMContentLoaded', function() {
    const create_session_template = document.querySelector('#create_session_template');
    const recurring_session_template = document.querySelector('#recurring_session_template');

    // opens create form on page load
    function createForm() {
        console.log('createForm called');
        const form = create_session_template.content.cloneNode(true);
        const container = document.querySelector('.container');
        container.appendChild(form);
    }
    createForm();

    const is_recurring_checkbox = document.querySelector('#id_is_recurring');

    let is_recurring = false;

    is_recurring_checkbox.addEventListener('click', function() {
        is_recurring = !is_recurring;
        console.log('checkbox is ', is_recurring);
    });

    // was supposed to open recurring session form when checkbox is checked
    // but since form reloads the page, change of plans
    // ill do a thing where the for msubmit will redirect u to a new page
    // and the new page will have the recurring session form
    // the new page will be like /create/recurring or something like that
    // u know what i mean?
    const submitButton = document.querySelector('.submit_session');
    submitButton.addEventListener('click', function() {
        console.log('submit button clicked');
    });
    
    // opens the recurring session form 
    function recurringForm() {
        removeChildren();
        const form = recurring_session_template.content.cloneNode(true);
        const container = document.querySelector('.container');
        container.appendChild(form);
    }


    function removeChildren() {
        const container = document.querySelector('.container');
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }
    }



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