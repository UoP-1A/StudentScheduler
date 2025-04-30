document.addEventListener("DOMContentLoaded", function () {
  const calendarDiv = document.querySelector("#calendar");
  const closeBtn = document.querySelector('.close');
  const modal = document.querySelector("#event-modal");

  const calendar = new FullCalendar.Calendar(calendarDiv, {
    initialView: "timeGridWeek",
    events: "get-calendar",
    eventTimeFormat: {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    },
    editable: true,
    eventDidMount: function (info) {
      info.el.dataset.eventId = info.event.id;
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
  const eventType = document.querySelector("#event-type");
  const eventStart = document.querySelector("#event-start");
  const eventEnd = document.querySelector("#event-end");
  const eventDescription = document.querySelector("#event-description");

  const event = info.event;

  const start = event.start ? event.start.toUTCString() : "N/A";
  const end = event.end ? event.end.toUTCString() : "N/A";
  const description = event.extendedProps.description || "N/A";

  eventTitle.textContent = event.title;
  eventTitle.setAttribute("title", event.title);
  eventType.textContent = String(event.extendedProps.type).charAt(0).toUpperCase() + String(event.extendedProps.type).slice(1);
  eventStart.textContent = start;
  eventEnd.textContent = end;
  eventDescription.textContent = description;
  eventDescription.setAttribute("title", description);

  modal.style.display = "block";
}

async function updateEventOnServer(event) {
  const csrftoken = getCookie("csrftoken");
  const payload = {
    id: event.id,
    start: event.start ? event.start.toISOString() : null,
    end: event.end ? event.end.toISOString() : null,
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
      throw new Error("Update failed");
    }

    const data = await response.json();
    console.log("Event updated:", data);
  } catch (error) {
    console.error("Error:", error);
    event.revert();
  }
}
