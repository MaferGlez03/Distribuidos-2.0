const token = sessionStorage.getItem('authToken');
const userData = sessionStorage.getItem('userData');

console.log(userData)

// Convierte el string JSON a un objeto JavaScript
const userDataObject = JSON.parse(userData);
window.globalVariable = ""

let date = new Date();
let year = date.getFullYear();
let month = date.getMonth();

const day = document.querySelector(".calendar-dates");
const currdate = document.querySelector(".calendar-current-date");
const prenexIcons = document.querySelectorAll(".calendar-navigation");

// Array of month names
const months = [
    "January", "February", "March", "April", "May",
    "June", "July", "August", "September", "October",
    "November", "December"
];

// Function to generate the calendar
export const manipulate = async () => {
    return new Promise(async (resolve, reject) => {
        try {
            let dayone = new Date(year, month, 1).getDay(); // Posicion en la semana del primer dia del mes contando el 0
            let lastdate = new Date(year, month + 1, 0).getDate();// Cantidad de dias del mes actual
            let dayend = new Date(year, month, lastdate).getDay(); // Posicion en la semana del ultimo dia del mes contando el 0
            let monthlastdate = new Date(year, month, 0).getDate(); // Cantidad de dias del mes anterior
            let lit = "";
            
            // Agregar las fechas del mes anterior
            for (let i = dayone; i > 0; i--) {
                lit += `<li class="inactive">${monthlastdate - i + 1}</li>`;
            }

            // Agregar las fechas del mes actual
            let promises = [];
            for (let i = 1; i <= lastdate; i++) {
                let isToday = 
                    i === date.getDate()
                    && month === new Date().getMonth()
                    && year === new Date().getFullYear()
                    ? "active"
                    : "";

                let dayI = i < 10 ? `0${i}` : i;
                let listItem = `<li class="${isToday}" id="day-${year}-${month + 1}-${dayI}">${i}</li>`;
                lit += listItem;

                // Solicitar eventos para el día actual
                const dayString = `${year}-${month + 1}-${dayI}`;
                const fullDate = new Date(dayString)
                const noHours = fullDate.toISOString().split('T')[0]
                // const adjustDate = `${fixMonth(adjustDateByDays(dayString, 1))}`
                promises.push(
                    // dailyEvents(adjustDateByDays(dayString, 1), window.globalVariable).then(({ personalEvents, groupEvents }) => {
                    //     const dayElement = document.querySelector(`#day-${year}-${month + 1}-${dayI}`);
                    //     if (dayElement) {
                    //         let eventsHTML = "";
                    //         personalEvents.forEach(event => {
                    //             eventsHTML += `<p class="event-title">${event.title}</p>`;
                    //         });
                    //         groupEvents.forEach(event => {
                    //             eventsHTML += `<p class="event-title2">${event.title}</p>`;
                    //         });
                    //         dayElement.innerHTML += eventsHTML; // Añade los eventos sin reemplazar
                    //     }
                    // }).catch(error => {
                    //     console.error('Error:', error.message);
                    // })
                    // dailyEvents(adjustDateByDays(dayString, 1)).then((dayEvents) => {
                    dailyEvents(noHours).then((dayEvents) => {
                        const dayElement = document.querySelector(`#day-${dayString}`);
                        if (dayElement) {
                            let eventsHTML = "";
                            dayEvents.forEach(event => {
                                eventsHTML += `<p class="event-title">${event.name}</p>`;
                            });
                            dayElement.innerHTML += eventsHTML; // Añade los eventos sin reemplazar
                        }
                    }).catch(error => {
                        console.error('Error:', error.message);
                    })
                );
            }

            // Agregar las fechas del próximo mes
            for (let i = dayend; i < 6; i++) {
                lit += `<li class="inactive">${i - dayend + 1}</li>`;
            }

            currdate.innerText = `${months[month]} ${year}`;
            day.innerHTML = lit;

            // Esperar a que todas las promesas se resuelvan
            await Promise.all(promises);

            resolve();
        } catch (error) {
            console.error('Error en manipulate:', error);
            reject(error);
        }
    });
};



manipulate();

// Attach a click event listener to each icon
prenexIcons.forEach(icon => {

    // When an icon is clicked
    icon.addEventListener("click", () => {

        // Check if the icon is "calendar-prev"
        // or "calendar-next"
        month = icon.id === "calendar-prev" ? month - 1 : month + 1;

        // Check if the month is out of range
        if (month < 0 || month > 11) {

            // Set the date to the first day of the 
            // month with the new year
            date = new Date(year, month, new Date().getDate());

            // Set the year to the new year
            year = date.getFullYear();

            // Set the month to the new month
            month = date.getMonth();
        }

        else {

            // Set the date to the current date
            date = new Date();
        }

        // Call the manipulate function to 
        // update the calendar display
        manipulate();
    });
});

// Variables globales
const overlay = document.getElementById('overlay');
let activeMenu = null; // Para rastrear qué menú está activo

// Evento para abrir menús flotantes
document.querySelectorAll('.openMenu').forEach(button => {
    button.addEventListener('click', function (event) {
        event.preventDefault(); // Previene el comportamiento predeterminado del enlace

        // Identifica el menú a abrir
        const menuId = this.getAttribute('data-menu');
        const menu = document.getElementById(menuId);

        // Muestra el overlay y el menú flotante correspondiente
        if (menu) {
            overlay.style.display = 'flex';
            menu.style.display = 'flex';
            activeMenu = menu; // Guarda el menú activo
        }
    });
});

// Evento para cerrar menús
overlay.addEventListener('click', closeMenu);
document.querySelectorAll('.closeMenu').forEach(button => {
    button.addEventListener('click', closeMenu);
});

// Función para cerrar el menú flotante activo
export function closeMenu() {
    if (activeMenu) {
        activeMenu.style.display = 'none';
        overlay.style.display = 'none';
        activeMenu = null; // Reinicia el menú activo
    }
}

// Listar eventos
export function dailyEvents(day, url) {
    var urlFinal
    if (url) {
        if (url !== "") {
            // urlFinal = 'http://127.0.0.1:5000/api/events/${url}'
            urlFinal = `http://127.0.0.1:5000/list_events/${userDataObject.id}`
        }
    } else {
        // urlFinal = 'http://127.0.0.1:5000/api/events/'
        urlFinal = `http://127.0.0.1:5000/list_events/${userDataObject.id}`
    }
    return fetch(urlFinal, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`, // Token para autenticación
        },
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al obtener eventos: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            const dayEvents = data.events.filter(event => {
                console.log("Dia en el calendario", day, "Dia del evento", event.date)
                return event.date == day
            })
            // const targetDate = new Date(fixHourZone(`${day}T00:00:00Z`, -19)); // Forzar formato UTC
            // const targetDateEnd = new Date(fixHourZone(`${day}T00:00:00Z`, 5));

            // console.log("DATA", data);
            // console.log()
            
            // const groupEvents = data.events.filter(event => {
            //     console.log("EVENTO", event)
            //     // Object { date: "2025-02-15", group_id: null, id: 3, name: "asd", owner_id: 11, privacy: "public", status: "pending" }
            //     const start = new Date(fixHourZone(event.start_time, 5));
            //     const end = new Date(fixHourZone(event.end_time, 5));

            //     const initCalendarDay = dateToInt(targetDate);
            //     const endCalendarDay = dateToInt(targetDateEnd);
            //     const normalizedStart = dateToInt(start);
            //     const normalizedEnd = dateToInt(end);

            //     console.log("testing", start)
            //     console.log("testing", end)
            //     console.log("----------------------------")

            //     // Empieza y termina antes
            //     const case1 = (initCalendarDay >= normalizedStart && initCalendarDay >= normalizedEnd)

            //     // Empieza y termina despues
            //     const case2 = (endCalendarDay <= normalizedStart && endCalendarDay <= normalizedEnd)
                
            //     return !(case1 || case2)
            //     // const start = new Date(event.start_time);
            //     // const end = new Date(event.end_time);

            //     // const normalizedTarget = Date.UTC(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate());
            //     // const normalizedStart = Date.UTC(start.getFullYear(), start.getMonth(), start.getDate());
            //     // const normalizedEnd = Date.UTC(end.getFullYear(), end.getMonth(), end.getDate());

            //     // return normalizedTarget >= normalizedStart && normalizedTarget <= normalizedEnd;
            // });

            // const personalEvents = data.events.filter(event => {
            //     const start = new Date(fixHourZone(event.start_time, 5));
            //     const end = new Date(fixHourZone(event.end_time, 5));

            //     const initCalendarDay = dateToInt(targetDate);
            //     const endCalendarDay = dateToInt(targetDateEnd);
            //     const normalizedStart = dateToInt(start);
            //     const normalizedEnd = dateToInt(end);

            //     // Empieza y termina antes
            //     const case1 = (initCalendarDay >= normalizedStart && initCalendarDay >= normalizedEnd)

            //     // Empieza y termina despues
            //     const case2 = (endCalendarDay <= normalizedStart && endCalendarDay <= normalizedEnd)
                
            //     return !(case1 || case2)
            // });
            

            // return { personalEvents, groupEvents };
            console.log("Eventos del dia", dayEvents)
            return dayEvents
        })
        .catch(error => {
            console.error('Error:', error.message);
        });
}

export function adjustDateByDays(dateString, days) {
    const date = new Date(dateString);
    date.setDate(date.getDate() + days); // Sumar o restar días
    return date.toISOString().split('T')[0]; // Retornar solo la parte de la fecha
}

function fixMonth(EntryDate) {
    const dateString = `${EntryDate}`
    const datefix = dateString.split('-')
    const dayfix = datefix[2]
    let monthfix = datefix[1]
    const yearfix = datefix[0]
    if (datefix[1][0] == 0) {
        monthfix = datefix[1][1]
    }
    return `${yearfix}-${monthfix}-${dayfix}`
}

function fixHourZone(day, hours) {
    const date = new Date(day);
    date.setHours(date.getHours() + hours);
    return date;
}

document.getElementById('logoutBtn').addEventListener('click', function () {
    // Eliminar los datos del usuario del almacenamiento
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    sessionStorage.removeItem('authToken');
    sessionStorage.removeItem('userData');

})

function dateToInt(date) {
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const hours = date.getHours();
    const minutes = date.getMinutes();
    const seconds = date.getSeconds();
    const intDate = year * 10000000000 + month * 100000000 + day * 1000000 + hours * 10000 + minutes * 100 + seconds;
    return intDate;
}
