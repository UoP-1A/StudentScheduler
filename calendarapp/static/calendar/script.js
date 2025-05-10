let calendar;

document.addEventListener("DOMContentLoaded", function () {
  const calendarDiv = document.querySelector("#calendar");
  const closeBtn = document.querySelector('.close');
  const modal = document.querySelector("#event-modal");

  calendar = new FullCalendar.Calendar(calendarDiv, {
    initialView: "timeGridWeek",
    eventSources: [
      'get-calendar',
      '/study_sessions/sessions/',
    ],
    timeZone: 'local',
    eventTimeFormat: {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    },
    editable: true,
    eventDisplay: 'block',
    eventDidMount: function (info) {
      info.el.dataset.eventId = info.event.id;
      info.el.dataset.model = info.event.extendedProps.model;
    },
    eventClick: showEventDetails,
    nowIndicator: true,
    dayMaxEventRows: true,
    firstDay: 1,
    fixedWeekCount: false,
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay",
    },
    buttonText: {
      today: "Today",
      month: "Month",
      week: "Week",
      day: "Day",
    },
    views: {
      timeGridWeek: {
        allDaySlot: true,
      },
    },
    dayHeaderContent: function (arg) {
      return customDayHeaderFormat(arg.date);
    },
  });

  calendar.render();

  calendar.on("eventDrop", function (info) {
    updateEventOnServer(info.event);
  });

  calendar.on("eventResize", function (info) {
    updateEventOnServer(info.event);
  });

  closeBtn.onclick = function() {
    modal.style.display = 'none';
  }

  window.onclick = function(event) {
    if (event.target == modal) {
      modal.style.display = 'none';
    }
  }

});

function customDayHeaderFormat(date) {
  const day = date.getDate();
  const suffix =
    day % 10 === 1 && day !== 11
      ? "st"
      : day % 10 === 2 && day !== 12
      ? "nd"
      : day % 10 === 3 && day !== 13
      ? "rd"
      : "th";
  return (
    date.toLocaleDateString("en-UK", { weekday: "long" }) + " " + day + suffix
  );
}

function showEventDetails(info) {
  const modal = document.querySelector("#event-modal");
  const eventTitle = document.querySelector("#event-title");
  const eventStart = document.querySelector("#event-start");
  const eventEnd = document.querySelector("#event-end");
  const eventDescription = document.querySelector("#event-description");
  const eventModel = document.querySelector("#event-type"); // Add this line to your HTML modal

  const event = info.event;
  
  const formatForDisplay = (date) => {
    if (!date) return "N/A";
    return date.toLocaleString("en-UK", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    });
  };

  const start = formatForDisplay(event.start);
  const end = formatForDisplay(event.end);
  const description = event.extendedProps.description || "N/A";
  const model = event.extendedProps.model || "N/A";

  eventTitle.textContent = event.title;
  eventTitle.setAttribute("title", event.title);
  eventStart.textContent = start;
  eventEnd.textContent = end;
  eventDescription.textContent = description;
  eventDescription.setAttribute("title", description);
  
  // Display model information
  eventModel.textContent = model;
  eventModel.setAttribute("title", model);

  modal.style.display = "block";
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    } 
    return cookieValue;
  }
}

async function updateEventOnServer(event) {
  console.log("SENT");
  const csrftoken = getCookie("csrftoken");
  
  // Convert dates to local timezone before sending
  const formatDateForServer = (date) => {
    if (!date) return null;
    const localDate = new Date(date.getTime() - (date.getTimezoneOffset() * 60000));
    return localDate.toISOString().slice(0, 19); // Remove milliseconds and timezone info
  };

  const payload = {
    id: event.id,
    start: event.start ? formatDateForServer(event.start) : null,
    end: event.end ? formatDateForServer(event.end) : null,
    model: event.extendedProps.model 
  };

  try {
    const response = await fetch("/calendar/update-event/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Update failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();
    console.log("Event updated:", data);
  } catch (error) {
    console.error("Error:", error);
    event.revert(); // Make sure to revert the event on error
  }
}

