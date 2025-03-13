import {manipulate} from './calendar.js';
import {selectUserEvent} from './groups.js';
import {selectGroupEvent} from './groups.js';

const userData = localStorage.getItem('user_id') || sessionStorage.getItem('user_id');
const username = localStorage.getItem('username') || sessionStorage.getItem('username').replace(/^["'](.*)["']$/, '$1');
const chord_id = parseInt(localStorage.getItem('chord_id') || sessionStorage.getItem('chord_id'), 10);
const idActualUser = parseInt(userData, 10);

// Variables globales
const overlay = document.getElementById('overlay');
let activeMenu = null; // Para rastrear qué menú está activo
let activeMenu2 = null;
const overlay2 = document.getElementById('overlay2');

// Crear evento
document.getElementById('btn_create_event').addEventListener('click', async function () {
    // Obtener los valores de los inputs
    const eventName = document.getElementById('EventName').value;
    const eventDateInit = document.getElementById('EventDateInit').value;
    // const eventTimeInit = document.getElementById('EventTimeInit').value;
    // const eventDateEnd = document.getElementById('EventDateEnd').value;
    // const eventTimeEnd = document.getElementById('EventTimeEnd').value;
    // const eventDescription = document.getElementById('EventDescription').value;
    const eventPrivacyCheck = document.getElementById('checkPrivacy').checked;
    const eventPrivacy = eventPrivacyCheck ? 'private' : 'public';
    const groupEvent = document.getElementById('EventGroup').value;
    const userEvent = document.getElementById('EventUser').value;
    // const participantsEvent = `${document.getElementById('EventParticipants').value}, ${user.id}`;

    // const numbers = participantsEvent
    // ? participantsEvent.split(',').map(num => parseFloat(num.trim())).filter(num => !isNaN(num)) 
    // : [];
    let rawData = {}
    let url = ''

    if (groupEvent){
        // data de evento grupal
        rawData = {
            title: eventName,
            start_time: `${eventDateInit}`,
            owner_id: idActualUser,
            group_id: groupEvent || userEvent,
            chord_id: chord_id
        };

        // url de evento grupal
        url = 'http://127.0.0.1:5000/create_group_event/'
    }
    else {
        // data de evento personal
        rawData = {
            title: eventName,
            start_time: `${eventDateInit}`,
            owner_id: idActualUser,
            privacy: eventPrivacy,
            chord_id: chord_id
        };

        // url de evento grupal
        url = 'http://127.0.0.1:5000/create_event/'
    }


    const dataF = Object.fromEntries(Object.entries(rawData).filter(([_, value]) => value !== null));
    console.log("userdata", idActualUser)

    try {
        // Enviar los datos al endpoint
        const response = await fetch(url, {
            method: 'POST', 
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dataF),
            
        });

        if (!response.ok) {
            throw new Error('Error en el registro');
        }

        const result = await response.json();

        // Llama a manipulate y espera a que se complete
        await manipulate();
        closeMenu();

    } catch (error) {
        console.error('Error:', error);
        alert(error.message);
    }
});

// Boton de Select Group en Create a new Event
document.getElementById('btn_select_group').addEventListener('click', function(){
    const idUserEvent = selectGroupEvent(); // Llamar a la función para abrir el menú flotante
})

// Boton de Select Contact en Create a new Event
document.getElementById('btn_select_contact').addEventListener('click', function(){
    const idUserEvent = selectUserEvent(idActualUser); // Llamar a la función para abrir el menú flotante
})

document.getElementById('alertsDropdown').addEventListener('click', function () {
    return fetch(`http://127.0.0.1:5000/list_events_pending/${chord_id}/${username}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
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
            let data1 = data.split('\n')
            if (data.length === 0) {
                data1 = data
            }
            const menuEvent = document.getElementById('EventsPending')
            menuEvent.innerHTML = ''

            const eventH6 = document.createElement('h6');
            eventH6.className = "dropdown-header"
            eventH6.textContent = "Events Pending"
            menuEvent.appendChild(eventH6)


            data1.forEach(singleEvent0 => {
                const singleEvent1 = singleEvent0.replace(/^\(/, "[").replace(/\)$/, "]");
                const singleEvent = JSON.parse(singleEvent1)
                const Aelement = document.createElement('a');
                Aelement.classList = ["dropdown-item d-flex align-items-center"];
                Aelement.id = "Aelement"
                Aelement.setAttribute('data-menu', "menu9")

                Aelement.addEventListener('click', function () {
                    
                    // viewEvent(event.id)
                    //     .then(eventDataFunc => {
                    //         const eventData = eventDataFunc

                    //         const eventTitle = document.getElementById('EventTitle');
                    //         eventTitle.textContent = eventData.title;

                    //         const descriptionEvent = document.getElementById('descriptionEvent');
                    //         descriptionEvent.textContent = eventData.description

                    //         const startTimeEvent = document.getElementById('startTimeEvent');
                    //         startTimeEvent.textContent = eventData.start_time

                    //         const endTimeEvent = document.getElementById('endTimeEvent');
                    //         endTimeEvent.textContent = eventData.end_time

                    //         const privacyEvent = document.getElementById('privacyEvent');
                    //         privacyEvent.textContent = eventData.privacy

                    //         const idEventText = document.getElementById('idEvent');
                    //         idEventText.textContent = eventData.id

                    //         const groupIdEvent = document.getElementById('groupIdEvent');
                    //         adminEvent.groupIdEvent = eventData.group

                    //         const participantIdsEvent = document.getElementById('participantIdsEvent');
                    //         participantIdsEvent.textContent = eventData.participants

                    //         const confirmedParticipantsEvent = document.getElementById('confirmedParticipantsEvent');
                    //         confirmedParticipantsEvent.textContent = eventData.accepted_by
                        
                    //         // Identifica el menú a abrir
                    //         const menuId = this.getAttribute('data-menu');
                    //         const menu = document.getElementById(menuId);

                    //         // Muestra el overlay y el menú flotante correspondiente
                    //         if (menu) {
                    //             overlay.style.display = 'flex';
                    //             menu.style.display = 'flex';
                    //             activeMenu = menu; // Guarda el menú activo
                    //         }

                    //         // Evento para cerrar menús
                    //         overlay.addEventListener('click', closeMenu);
                    //         document.querySelectorAll('.closeMenu').forEach(button => {
                    //             button.addEventListener('click', closeMenu);
                    //         });
                    //     })
                    //     .catch(error => {
                    //         console.error('Error al obtener el evento:', error.message);
                    //     });                    


                    const eventData = singleEvent

                    const eventTitle = document.getElementById('EventTitle');
                    eventTitle.textContent = eventData[1] // Name

                    const startTimeEvent = document.getElementById('startTimeEvent');
                    startTimeEvent.textContent = eventData[2] // Date

                    const privacyEvent = document.getElementById('privacyEvent');
                    privacyEvent.textContent = eventData[4] // Privacy

                    const idEventText = document.getElementById('idEvent');
                    idEventText.textContent = eventData[0] // ID

                    const groupIdEvent = document.getElementById('groupIdEvent');
                    adminEvent.groupIdEvent = eventData[5] // group_id
                
                    // Identifica el menú a abrir
                    const menuId = this.getAttribute('data-menu');
                    const menu = document.getElementById(menuId);

                    // Muestra el overlay y el menú flotante correspondiente
                    if (menu) {
                        overlay.style.display = 'flex';
                        menu.style.display = 'flex';
                        activeMenu = menu; // Guarda el menú activo
                    }

                    // Evento para cerrar menús
                    overlay.addEventListener('click', closeMenu);
                    document.querySelectorAll('.closeMenu').forEach(button => {
                        button.addEventListener('click', closeMenu);
                    });

                    // const eventData = event

                    // const eventTitle = document.getElementById('EventTitle');
                    // eventTitle.textContent = eventData.name;

                    // const startTimeEvent = document.getElementById('startTimeEvent');
                    // startTimeEvent.textContent = eventData.date

                    // const privacyEvent = document.getElementById('privacyEvent');
                    // privacyEvent.textContent = eventData.privacy

                    // const idEventText = document.getElementById('idEvent');
                    // idEventText.textContent = eventData.id

                    // const groupIdEvent = document.getElementById('groupIdEvent');
                    // adminEvent.groupIdEvent = eventData.group_id
                
                    // // Identifica el menú a abrir
                    // const menuId = this.getAttribute('data-menu');
                    // const menu = document.getElementById(menuId);

                    // // Muestra el overlay y el menú flotante correspondiente
                    // if (menu) {
                    //     overlay.style.display = 'flex';
                    //     menu.style.display = 'flex';
                    //     activeMenu = menu; // Guarda el menú activo
                    // }

                    // // Evento para cerrar menús
                    // overlay.addEventListener('click', closeMenu);
                    // document.querySelectorAll('.closeMenu').forEach(button => {
                    //     button.addEventListener('click', closeMenu);
                    // });
                });

                menuEvent.appendChild(Aelement)

                const divElement1 = document.createElement('div');
                divElement1.className = "mr-3"
                Aelement.appendChild(divElement1)

                const divElement2 = document.createElement('div');
                divElement2.classList = ["icon-circle bg-primary"]
                divElement1.appendChild(divElement2)

                const iElement = document.createElement('i');
                iElement.className = ["fas fa-file-alt text-white"]
                divElement2.appendChild(iElement)

                const divElement3 = document.createElement('div');
                Aelement.appendChild(divElement3)

                const divElement4 = document.createElement('div');
                divElement4.className = ["small text-gray-500"]
                divElement4.id = "DateInitEventPending"
                divElement4.textContent = `id ${singleEvent[0]} - date: ${formatToReadableDate(singleEvent[2])}`
                divElement3.appendChild(divElement4)

                const spanElement = document.createElement('span');
                spanElement.className = "font-weight-bold"
                spanElement.id = "TitleEventPending"
                spanElement.textContent = singleEvent[1]
                divElement3.appendChild(spanElement)

                
            });
            const CountEventsPending = document.getElementById('CountEventsPending')
            CountEventsPending.textContent = data.length
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert(error.message);
        });
});

function formatToReadableDate(dateStr) {
    // Intentar parsear la fecha con el constructor Date
    const date = new Date(dateStr);

    // Verificar si la fecha es válida
    if (isNaN(date)) {
        throw new Error('Fecha no válida');
    }

    // Obtener los componentes de la fecha
    const day = date.getDate().toString().padStart(2, '0'); // Día con dos dígitos
    const month = (date.getMonth() + 1).toString().padStart(2, '0'); // Mes con dos dígitos
    const year = date.getFullYear(); // Año

    // Formatear como DD/MM/YYYY
    return `${day}/${month}/${year}`;
}

function closeMenu() {
    if (activeMenu) {
        activeMenu.style.display = 'none';
        overlay.style.display = 'none';
        activeMenu = null; // Reinicia el menú activo
    }
}

// Confirm Event
document.getElementById('acceptBtn').addEventListener('click', function () {
    const idEventUrl =  document.getElementById('idEvent')
    // return fetch(`http://127.0.0.1:5000/api/events/${idEventUrl.textContent}/accept/`, {
    return fetch(`http://127.0.0.1:5000/confirm_event/${idEventUrl.textContent}/${chord_id}/${idActualUser}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: {},
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al aceptar evento: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log(data)
            manipulate()
            closeMenu()
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert(error.message);
        });
});

