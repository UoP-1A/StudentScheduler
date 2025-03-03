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
});


function customDayHeaderFormat(date) {
    const day = date.getDate();
    const suffix = (day % 10 === 1 && day !== 11) ? 'st' :
                   (day % 10 === 2 && day !== 12) ? 'nd' :
                   (day % 10 === 3 && day !== 13) ? 'rd' : 'th';
    return date.toLocaleDateString('en-UK', { weekday: 'long' }) + ' ' + day + suffix;
}