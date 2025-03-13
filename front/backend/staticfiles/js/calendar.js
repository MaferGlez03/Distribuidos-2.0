const userData = localStorage.getItem('user_id') || sessionStorage.getItem('user_id');
const username = localStorage.getItem('username') || sessionStorage.getItem('username').replace(/^["'](.*)["']$/, '$1');
const chord_id = parseInt(localStorage.getItem('chord_id') || sessionStorage.getItem('chord_id'), 10);
const idActualUser = parseInt(userData, 10);

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

// export const manipulate = async () => {
//     return new Promise(async (resolve, reject) => {
//         try {
//             let dayone = new Date(year, month, 1).getDay(); // Posicion en la semana del primer dia del mes contando el 0
//             let lastdate = new Date(year, month + 1, 0).getDate();// Cantidad de dias del mes actual
//             let dayend = new Date(year, month, lastdate).getDay(); // Posicion en la semana del ultimo dia del mes contando el 0
//             let monthlastdate = new Date(year, month, 0).getDate(); // Cantidad de dias del mes anterior
//             let lit = "";
            
//             // Agregar las fechas del mes anterior
//             for (let i = dayone; i > 0; i--) {
//                 lit += `<li class="inactive">${monthlastdate - i + 1}</li>`;
//             }

//             // Agregar las fechas del mes actual
//             let promises = [];
//             for (let i = 1; i <= lastdate; i++) {
//                 let isToday = 
//                     i === date.getDate()
//                     && month === new Date().getMonth()
//                     && year === new Date().getFullYear()
//                     ? "active"
//                     : "";

//                 let dayI = i < 10 ? `0${i}` : i;
//                 let listItem = `<li class="${isToday}" id="day-${year}-${month + 1}-${dayI}">${i}</li>`;
//                 lit += listItem;

//                 // Solicitar eventos para el día actual
//                 const dayString = `${year}-${month + 1}-${dayI}`;
//                 const fullDate = new Date(dayString)
//                 const noHours = fullDate.toISOString().split('T')[0]
//                 // const adjustDate = `${fixMonth(adjustDateByDays(dayString, 1))}`
//                 promises.push(

//                     getMonthlyEvents(noHours).then((dayEvents) => {
//                         const dayElement = document.querySelector(`#day-${dayString}`);
//                         if (dayElement) {
//                             let eventsHTML = "";
//                             dayEvents.forEach(event => {
//                                 eventsHTML += `<p class="event-title">${event[0]}</p>`;
//                             });
//                             dayElement.innerHTML += eventsHTML; // Añade los eventos sin reemplazar
//                         }
//                     }).catch(error => {
//                         console.error('Error:', error.message);
//                     })
//                 );
//             }

//             // Agregar las fechas del próximo mes
//             for (let i = dayend; i < 6; i++) {
//                 lit += `<li class="inactive">${i - dayend + 1}</li>`;
//             }

//             currdate.innerText = `${months[month]} ${year}`;
//             day.innerHTML = lit;

//             // Esperar a que todas las promesas se resuelvan
//             await Promise.all(promises);

//             resolve();
//         } catch (error) {
//             console.error('Error en manipulate:', error);
//             reject(error);
//         }
//     });
// };

export const manipulate = async () => {
    return new Promise(async (resolve, reject) => {
        try {
            let dayone = new Date(year, month, 1).getDay(); 
            let lastdate = new Date(year, month + 1, 0).getDate();
            let dayend = new Date(year, month, lastdate).getDay();
            let monthlastdate = new Date(year, month, 0).getDate(); 
            let lit = "";

            // Obtener eventos de todo el mes
            let eventsByDay = await getMonthlyEvents(year, month + 1);

            // Agregar las fechas del mes anterior
            for (let i = dayone; i > 0; i--) {
                lit += `<li class="inactive">${monthlastdate - i + 1}</li>`;
            }

            console.log("eventsByDay: ", eventsByDay)
            console.log("eventsByDay: ", typeof eventsByDay)
            // Agregar las fechas del mes actual con eventos
            for (let i = 1; i <= lastdate; i++) {
                let isToday =
                    i === date.getDate() &&
                    month === new Date().getMonth() &&
                    year === new Date().getFullYear()
                        ? "active"
                        : "";

                let dayI = i < 10 ? `0${i}` : i;
                let dayString = `${year}-${month + 1}-${dayI}`;
                let formatDayString = formatearFecha(dayString)
                console.log(dayString)
                console.log(typeof dayString)
                let dayDate = new Date(dayString)
                console.log(dayDate)
                console.log(typeof dayDate)
                console.log(eventsByDay[dayString])
                console.log(eventsByDay[dayDate])
                console.log(formatDayString)
                console.log(typeof formatDayString)
                console.log(eventsByDay[formatDayString])
                
                // Obtener eventos del día
                let eventsHTML = "";
                if (eventsByDay[formatDayString]) {
                    eventsByDay[formatDayString].forEach(event => {
                        eventsHTML += `<p class="event-title">${event}</p>`;
                    });
                }

                lit += `<li class="${isToday}" id="day-${formatDayString}">${i}${eventsHTML}</li>`;
            }

            // Agregar las fechas del próximo mes
            for (let i = dayend; i < 6; i++) {
                lit += `<li class="inactive">${i - dayend + 1}</li>`;
            }

            currdate.innerText = `${months[month]} ${year}`;
            day.innerHTML = lit;

            resolve();
        } catch (error) {
            console.error('Error en manipulate:', error);
            reject(error);
        }
    });
};

function formatearFecha(fecha) {
    // Dividir la fecha en partes (año, mes, día)
    const partes = fecha.split("-");
    let año = partes[0];
    let mes = partes[1];
    let día = partes[2];
  
    // Comprobar si el mes tiene una sola cifra
    if (mes.length === 1) {
      mes = "0" + mes; // Agregar un 0 al principio
    }
  
    // Unir las partes nuevamente
    const fechaFormateada = `${año}-${mes}-${día}`;
    return fechaFormateada;
  }




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
// export function dailyEvents(day, url) {
//     fetch(`http://127.0.0.1:5000/list_events/${chord_id}/${username}/`, {
//         method: 'GET',
//         headers: {
//             'Content-Type': 'application/json',
//         },
//     })
//         .then(response => {
//             if (!response.ok) {
//                 return response.json().then(err => {
//                     throw new Error(`Error al obtener eventos: ${err.detail || err}`);
//                 });
//             }
//             return response.json();
//         })
//         .then(data => {
//             let data1 = data ? data.split('|').map(item => item.trim()) : [];
//             const dayEvents = data1.filter(event0 => {
//                 const event2 = event0
//                     .replace(/^\(/, "[")  // Reemplaza paréntesis de apertura
//                     .replace(/\)$/, "]")  // Reemplaza paréntesis de cierre
//                     .replace(/(\d+),\s*([a-zA-Z0-9_]+)/, '$1, "$2"'); // Agrega comillas a los strings
        
//                 const event1 = JSON.parse(event2)

//                 const date = Date(event1[1])
//                 console.log("Dia en el calendario", day, "Dia del evento", date)
//                 return date == day
//             })
//             console.log("Eventos del dia", dayEvents)
//             return dayEvents
//         })
//         .catch(error => {
//             console.error('Error:', error.message);
//         });
// }
export async function getMonthlyEvents(year, month) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/list_events/${chord_id}/${username}/`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Error al obtener eventos: ${errorData.detail || errorData}`);
        }

        const data = await response.json();
        let eventsByDay = {};

        if (data) {
            data.split('|').forEach(eventRaw => {
                const regex = /\('([^']+)', datetime.datetime\((\d+), (\d+), (\d+), (\d+), (\d+)\)\)/;
                const match = eventRaw.match(regex);
                
                if (match) {
                    // Extraer los valores
                    const stringValue = match[1];
                    const year = parseInt(match[2], 10);
                    const month = parseInt(match[3], 10) - 1; // Los meses en JavaScript son 0-indexados
                    const day = parseInt(match[4], 10);
                    const hour = parseInt(match[5], 10);
                    const minute = parseInt(match[6], 10);
                
                    // Crear el objeto Date
                    const dateValue = new Date(year, month, day, hour, minute);
                
                    // Crear la lista
                    const eventData = [stringValue, dateValue];
                
                    console.log(eventData);

                const eventDate = new Date(eventData[1]).toISOString().split('T')[0];

                if (!eventsByDay[eventDate]) {
                    eventsByDay[eventDate] = [];
                }
                eventsByDay[eventDate].push(eventData[0]);
            }});
        }

        return eventsByDay;  
    } catch (error) {
        console.error('Error en getMonthlyEvents:', error.message);
        return {};
    }
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
