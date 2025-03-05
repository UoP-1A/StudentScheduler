document.addEventListener('DOMContentLoaded', function() {
    var calendarDiv = document.querySelector('#calendar');
    
    var calendar = new FullCalendar.Calendar(calendarDiv, {
        initialView: 'timeGridWeek',
        events: "get-calendar",
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        },
        editable: true,
        eventDidMount: function(info) {
            info.el.dataset.eventId = info.event.id;
        },
        nowIndicator: true,
        dayMaxEventRows: true,
        firstDay: 1,
        fixedWeekCount: false,
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay',
        },
        buttonText: {
            today: 'Today',
            month: 'Month',
            week: 'Week',
            day: 'Day'
        },
        views: {
            timeGridWeek: {
                allDaySlot: true
            }
        },
        dayHeaderContent: function(arg) {
            return customDayHeaderFormat(arg.date);
        }
    });

    calendar.render();

    calendar.on('eventDrop', function(info) {
        updateEventOnServer(info.event);
    });

    calendar.on('eventResize', function(info) {
        updateEventOnServer(info.event);
    });
});


function customDayHeaderFormat(date) {
    const day = date.getDate();
    const suffix = (day % 10 === 1 && day !== 11) ? 'st' :
                   (day % 10 === 2 && day !== 12) ? 'nd' :
                   (day % 10 === 3 && day !== 13) ? 'rd' : 'th';
    return date.toLocaleDateString('en-UK', { weekday: 'long' }) + ' ' + day + suffix;
}

async function updateEventOnServer(event) {
    const csrftoken = getCookie('csrftoken');
    const payload = {
        id: event.id,
        start: event.start ? event.start.toISOString() : null,
        end: event.end ? event.end.toISOString() : null
    };

    try {
        const response = await fetch('/calendar/update-event/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error('Update failed');
        }

        const data = await response.json();
        console.log('Event updated:', data);
    } catch (error) {
        console.error('Error:', error);
        event.revert();
    }
}

function getCookie(name) {
    let value = `; ${document.cookie}`;
    let parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}