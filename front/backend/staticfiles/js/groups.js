import {closeMenu} from './calendar.js';
import {adjustDateByDays} from './calendar.js';
import {manipulate} from './calendar.js';

console.log("sessionStorage", sessionStorage)
console.log("localStorage", localStorage)

const userData = localStorage.getItem('user_id') || sessionStorage.getItem('user_id');
const username = localStorage.getItem('username') || sessionStorage.getItem('username');
const chord_id = parseInt(localStorage.getItem('chord_id') || sessionStorage.getItem('chord_id'), 10);
const idActualUser = parseInt(userData, 10);

window.globalVariable = '';

// Variables globales
const overlay2 = document.getElementById('overlay2');
const overlay3 = document.getElementById('overlay3');
let activeMenu2 = null; // Para rastrear qué menú está activo en la 2da capa
let activeMenu3 = null; // Para rastrear qué menú está activo en la 3ra capa

// Create Group
document.getElementById('btn_create_group').addEventListener('click', function () {
    // Obtener los valores de los inputs
    const GroupName = document.getElementById('GroupName').value;
    // const GroupDescription = document.getElementById('GroupDescription').value;
    const is_hierarchical = document.getElementById('is_hierarchical').checked; // Verificar si está marcado el checkbox
    var data = 0
    
    if(is_hierarchical) {
        data = {
            name: GroupName,
            chord_id: chord_id,
            user_id: idActualUser
        };
    } else {
        data = {
            name: GroupName,
            chord_id: chord_id,
            user_id: idActualUser
        };
    }

    // Enviar los datos al endpoint
    // fetch('http://127.0.0.1:8000/api/groups/', {
    fetch('http://127.0.0.1:5000/create_group/', {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al crear el grupo: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Redirigir al usuario
            closeMenu()
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
});

// List Groups
document.getElementById('list_groups').addEventListener('click', function () {
    // Realizar la solicitud GET al endpoint de grupos
    // fetch('http://127.0.0.1:8000/api/groups/', {
    fetch(`http://127.0.0.1:5000/list_groups/${chord_id}/${username}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json', // Token para autenticación
        },
    })
        .then(response => {
            if (!response.ok) {
                // Manejar errores si la respuesta no es exitosa
                return response.json().then(err => {
                    throw new Error(`Error al obtener grupos: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            let data1 = data.split('\n')
            if (data.length === 0) {
                data1 = data
            }
            // Mostrar los contactos en la consola o en la UI
            console.log('Grupos obtenidos:', data);

            // Aquí puedes manipular los datos para mostrarlos en la página
            const groupList = document.getElementById('group-list'); // Asegúrate de tener un contenedor en tu HTML con este ID
            groupList.innerHTML = ''; // Limpiar cualquier contenido previo

            data1.forEach(group0 => {
                const group1 = group0.replace(/^\(/, "[").replace(/\)$/, "]");
                const group = JSON.parse(group1)
                const Item = document.createElement('li');
                
                // Nombre del grupo
                const nameItem = document.createElement('h5');
                nameItem.textContent = `${group[1]}`;

                // Crear el ícono de info
                const infoCircle = document.createElement('i');
                infoCircle.id = 'info_circle'
                infoCircle.setAttribute('data-menu', 'menu7'); // Asociar el ID del grupo
                infoCircle.className = 'fas fa-info-circle openMenu';
                infoCircle.style.paddingLeft = '5px'; // Espacio entre el nombre y el ícono

                // // Agregar un evento de clic al ícono
                // infoCircle.addEventListener('click', function () {
                //     openGroupInfoMenu(group); // Llamar a la función para abrir el menú flotante
                // });
                
                infoCircle.addEventListener('click', function () {
                    fetch(`http://127.0.0.1:5000/list_members/${group[0]}/${chord_id}`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    })
                        .then(response => {
                            if (!response.ok) {
                                // Manejar errores si la respuesta no es exitosa
                                return response.json().then(err => {
                                    throw new Error(`Error al obtener grupos: ${err.detail || err}`);
                                });
                            }
                            return response.json();
                        })
                        .then(data => {
                            openGroupInfoMenu(group, data); // Llamar a la función para abrir el menú flotante
                        })
                        .catch(error => {
                            // Manejar errores
                            console.error('Error:', error.message);
                            alert(error.message);
                        });
                });

                // Crear divider
                const divider = document.createElement('hr')
                divider.className = 'sidebar-divider'

                // Agregar elementos a la lista
                Item.appendChild(nameItem)
                nameItem.appendChild(infoCircle);

                // Agregar el elemento de lista al contenedor
                groupList.appendChild(Item);
                groupList.appendChild(divider);
            });
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert(error.message);
        });
});


// List Group Details
function openGroupInfoMenu(group, members) {
    // menu7 abierto
    const menu = document.getElementById('menu7');
    menu.innerHTML = ''; // Limpiar cualquier contenido previo
    if (members.length === 0) {
        let members1 = members
    }
    else{
        let members1 = members.split('\n')
    } 
    // Nombre del grupo
    const nameItem = document.createElement('h5');
    nameItem.textContent = `${group[1]}`;

    hierarchical.appendChild(checkbox);

    // Miembros
    const membersList = document.createElement('ul');
    membersList.className = 'get-list'
    // membersList.textContent = 'Members:'
    members1.forEach(member0 => {
        const member1 = member0.replace(/^\(/, "[").replace(/\)$/, "]");
        const member = JSON.parse(member1)
        const memberList = document.createElement('li');
        memberList.textContent = `Member: ${username}`;
        membersList.appendChild(memberList)

        // Icono agenda miembro
        const agendaIconMember = document.createElement('i');
        agendaIconMember.className = 'fas fa-calendar-alt';
        agendaIconMember.style.paddingLeft = '10px';
        agendaIconMember.style.paddingRight = '10px';
        agendaIconMember.addEventListener('click', function () {
            const date = agendaGroup();
            window.globalVariable = date;
            manipulate();
            window.globalVariable = "";
            closeMenu2();
            closeMenu();
        })

        // Icono borrar miembro
        const deleteMember = document.createElement('i');
        deleteMember.className = 'fas fa-trash-alt';
        deleteMember.style.paddingLeft = '10px'; // Espacio entre el nombre y el ícono
        deleteMember.addEventListener('click', function () {
            console.log('group id: ', group[0])
            deleteMemberFunction(group[0], member[0]); // Llamar a la función para abrir el menú flotante
        });
        memberList.appendChild(agendaIconMember)
        memberList.appendChild(deleteMember)
    })

    // Icono borrar grupo
    const trashIcon = document.createElement('i');
    trashIcon.className = 'fas fa-trash-alt';
    trashIcon.style.paddingLeft = '10px'; // Espacio entre el nombre y el ícono
    trashIcon.addEventListener('click', function () {
        deleteGroupFunction(group[0])
    })

    // Icono agenda grupo
    const agendaIcon = document.createElement('i');
    agendaIcon.className = 'fas fa-calendar-alt';
    agendaIcon.style.paddingLeft = '10px';
    agendaIcon.style.paddingRight = '10px';
    agendaIcon.addEventListener('click', function () {
        const date = agendaGroup(group[0]);
        window.globalVariable = date;
        manipulate();
        window.globalVariable = "";
        closeMenu2();
        closeMenu();
    })

    // Div para los iconos inferiores
    const divIcons = document.createElement('div')
    divIcons.style.marginBottom = '15px';
    divIcons.style.marginTop = '15px';
    divIcons.style.width = '90%';
    divIcons.style.display = 'flex';
    divIcons.style.justifyContent = 'space-between';


    // Icono y texto adicionar miembro
    const addMember = document.createElement('i')
    addMember.textContent = 'Add Member'
    addMember.className = 'fas fa-plus';
    addMember.id = 'icon'

    // Icono de abandonar grupo
    const leaveGroup = document.createElement('i')
    leaveGroup.className = 'fas fa-sign-out-alt';
    leaveGroup.id = 'icon'

    // Agregar un evento de clic al icono de addMember
    addMember.addEventListener('click', function () {
        addMemberFunction(idActualUser, group); // Llamar a la función para abrir el menú flotante
        closeMenu2();
        closeMenu();
    });

    // Agregar un evento de clic al icono de abandonar grupo
    leaveGroup.addEventListener('click', function () {
        leaveGroupFunction(group[0]); // Llamar a la función para abrir el menú flotante
    });
    
    const closeBtn = document.createElement('button')
    closeBtn.className = 'closeMenu2'
    closeBtn.textContent = 'Close'

    menu.appendChild(nameItem)
    nameItem.appendChild(agendaIcon)
    nameItem.appendChild(trashIcon)
    // menu.appendChild(admin)
    // menu.appendChild(description)
    menu.appendChild(hierarchical)
    menu.appendChild(membersList)
    divIcons.appendChild(addMember)
    divIcons.appendChild(leaveGroup)
    menu.appendChild(divIcons)
    menu.appendChild(closeBtn)

    activeMenu2 = document.getElementById('menu6');

    // Muestra el overlay y el menú flotante correspondiente
    if (menu) {
        overlay2.style.display = 'flex';
        menu.style.display = 'flex';
        activeMenu2 = menu; // Guarda el menú activo
    }

    // Evento para cerrar menús
    overlay2.addEventListener('click', closeMenu2);
    document.querySelectorAll('.closeMenu2').forEach(button => {
        button.addEventListener('click', closeMenu2);
    });
}

export function closeMenu2() {
    if (activeMenu2) {
        activeMenu2.style.display = 'none';
        overlay2.style.display = 'none';
        activeMenu2 = null; // Reinicia el menú activo
    }
}

function closeMenu3() {
    if (activeMenu3) {
        activeMenu3.style.display = 'none';
        overlay3.style.display = 'none';
        activeMenu3 = null; // Reinicia el menú activo
    }
}

function searchId(created_by) {
    return created_by
}

function addMemberFunction(id, group) {
    // closeMenu()
    const menu = document.getElementById('menu8');

    fetch(`http://127.0.0.1:5000/contacts/${id}/${chord_id}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json', // Token para autenticación
        },
    })
        .then(response => {
            if (!response.ok) {
                // Manejar errores si la respuesta no es exitosa
                return response.json().then(err => {
                    throw new Error(`Error al obtener contactos: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            let data1 = data.split('\n')
            if (data.length === 0) {
                data1 = data
            }
            // Mostrar los contactos en la consola o en la UI
            console.log('Contactos obtenidos:', data);
            // Aquí puedes manipular los datos para mostrarlos en la página
            const contactList = document.getElementById('contact-list-member'); // Asegúrate de tener un contenedor en tu HTML con este ID
            contactList.innerHTML = ''; // Limpiar cualquier contenido previo

            data1.forEach(contact0 => {
                const listItem = document.createElement('li');
                const contact1 = contact0.replace(/^\(/, "[").replace(/\)$/, "]");
                const contact = JSON.parse(contact1)
                listItem.textContent = `${contact[0]}`;
                // Crear el ícono de basura
                const addMemberIcon = document.createElement('i');
                addMemberIcon.className = 'fas fa-plus';
                addMemberIcon.id = 'icon'
                addMemberIcon.style.marginBottom = '15px';
                addMemberIcon.style.marginLeft = '15px';

                addMemberIcon.addEventListener('click', function () {
                    addMemberEndpoint(group.id, contact)
                })

                // Agregar el ícono al elemento de lista
                listItem.appendChild(addMemberIcon);

                // Agregar el elemento de lista al contenedor
                contactList.appendChild(listItem);
            });
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert(error.message);
        });


    activeMenu3 = document.getElementById('menu7');

    // Muestra el overlay y el menú flotante correspondiente
    if (menu) {
        overlay3.style.display = 'flex';
        menu.style.display = 'flex';
        activeMenu3 = menu; // Guarda el menú activo
    }

    // Evento para cerrar menús
    overlay3.addEventListener('click', closeMenu3);
    document.querySelectorAll('.closeMenu3').forEach(button => {
        button.addEventListener('click', closeMenu3);
    });
}

function addMemberEndpoint(group_id, contact) {

    const memberData = {
        group_id: group_id,
        user_id: contact[1],
        role: 'member',
        chord_id: chord_id
    }
    // fetch('http://127.0.0.1:8000/api/groups/add-member/', {
    fetch('http://127.0.0.1:5000/add_member_to_group/', {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(memberData),
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al adicionar miembro: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Redirigir al usuario
            closeMenu3()
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });

}

// Delete Members
function deleteMemberFunction(groupId, memberId) {
    // fetch(`http://127.0.0.1:5000/api/groups/${groupId}/remove-member/${memberId}/`, {
    fetch(`http://127.0.0.1:5000/remove_member_from_group/${groupId}/${memberId}/${chord_id}/${username}/`, {
        method: 'DELETE', 
        headers: {
            'Content-Type': 'application/json',
        },
    })
        .then(response => {
            if(response.status == 403) {
                throw new Error(`No tiene permisos para eliminar miembros`)
            }
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al eliminar miembro del grupo ${err.detail || err}`);
                });
            }
            // Verificar si hay contenido en la respuesta antes de procesarla
            if (response.status !== 204) { // 204 significa No Content
                return response.json();
            }
            return null; // No hay contenido para procesar
        })
        .then(data => {
            // Redirigir al usuario
            if (data) {
                console.log('Respuesta del servidor:', data);
            }
            manipulate()
            closeMenu2()
            closeMenu()
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
}

function deleteGroupFunction(groupId) {
    // fetch(`http://127.0.0.1:5000/api/groups/${groupId}/delete/`, {
    fetch(`http://127.0.0.1:5000/delete_group/${groupId}/${chord_id}/`, {
        method: 'DELETE', 
        headers: {
            'Content-Type': 'application/json',
        },
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al eliminar grupo: ${err.detail || err}`);
                });
            }
            // Verificar si hay contenido en la respuesta antes de procesarla
            if (response.status !== 204) { // 204 significa No Content
                return response.json();
            }
            return null; // No hay contenido para procesar
        })
        .then(data => {
            // Redirigir al usuario
            if (data) {
                console.log('Respuesta del servidor:', data);
            }
            closeMenu2()
            closeMenu()
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
}

function leaveGroupFunction(groupId) {
    fetch(`http://127.0.0.1:5000/leave_group/${groupId}/${idActualUser}`, {
        method: 'DELETE', 
        headers: {
            'Content-Type': 'application/json',
        },
    })
        .then(response => {
            if (!response.ok) {
                console.log('response', response.json())
                return response.json().then(err => {
                    throw new Error(`Error al abandonar grupo: ${err.detail || err}`);
                });
            }
            // Verificar si hay contenido en la respuesta antes de procesarla
            if (response.status !== 204) { // 204 significa No Content
                return response.json();
            }
            return null; // No hay contenido para procesar
        })
        .then(data => {
            // Redirigir al usuario
            if (data) {
                console.log('Respuesta del servidor:', data);
            }
            closeMenu2()
            closeMenu()
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
}

export function selectUserEvent(id) {
    // closeMenu()
    const menu = document.getElementById('menu8');

    fetch(`http://127.0.0.1:5000/contacts/${id}/${chord_id}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json', // Token para autenticación
        },
    })
        .then(response => {
            if (!response.ok) {
                // Manejar errores si la respuesta no es exitosa
                return response.json().then(err => {
                    throw new Error(`Error al obtener contactos: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            let data1 = data.split('\n')
            if (data.length === 0) {
                data1 = data
            }
            // Mostrar los contactos en la consola o en la UI
            console.log('Contactos obtenidos:', data);
            // Aquí puedes manipular los datos para mostrarlos en la página
            const contactList = document.getElementById('contact-list-member'); // Asegúrate de tener un contenedor en tu HTML con este ID
            contactList.innerHTML = ''; // Limpiar cualquier contenido previo

            data1.forEach(contact0 => {
                const listItem = document.createElement('li');
                const contact1 = contact0.replace(/^\(/, "[").replace(/\)$/, "]");
                const contact = JSON.parse(contact1)
                listItem.textContent = `${contact[0]}`;

                // Crear el ícono de basura
                const addMemberIcon = document.createElement('i');
                addMemberIcon.className = 'fas fa-plus';
                addMemberIcon.id = 'icon'
                addMemberIcon.style.marginBottom = '15px';
                addMemberIcon.style.marginLeft = '15px';

                addMemberIcon.addEventListener('click', function () {
                    const returnValue = contact[1]
                    console.log("return Value", returnValue)
                    return returnValue['<value>']
                })

                // Agregar el ícono al elemento de lista
                listItem.appendChild(addMemberIcon);

                // Agregar el elemento de lista al contenedor
                contactList.appendChild(listItem);
            });
        })  
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert(error.message);
        });
    activeMenu2 = document.getElementById('menu7');

    // Muestra el overlay y el menú flotante correspondiente
    if (menu) {
        overlay2.style.display = 'flex';
        menu.style.display = 'flex';
        activeMenu2 = menu; // Guarda el menú activo
    }

    const closeMenuContacts = document.getElementById('closeMenuContacts')
    closeMenuContacts.addEventListener('click', function () {
        closeMenu2()
    })

    // Evento para cerrar menús
    overlay2.addEventListener('click', closeMenu2);
    document.querySelectorAll('.closeMenu2').forEach(button => {
        button.addEventListener('click', closeMenu2);
    });
}

export function selectGroupEvent() {
    // closeMenu()
    const menu = document.getElementById('menu6');

    fetch(`http://127.0.0.1:5000/list_groups/${chord_id}/${username}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json', // Token para autenticación
        },
    })
        .then(response => {
            if (!response.ok) {
                // Manejar errores si la respuesta no es exitosa
                return response.json().then(err => {
                    throw new Error(`Error al obtener grupos: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            let data1 = data.split('\n')
            if (data.length === 0) {
                data1 = data
            }
            // Mostrar los contactos en la consola o en la UI
            console.log('Grupos obtenidos:', data);
            // Aquí puedes manipular los datos para mostrarlos en la página
            const groupList = document.getElementById('group-list'); // Asegúrate de tener un contenedor en tu HTML con este ID
            groupList.innerHTML = ''; // Limpiar cualquier contenido previo

            data1.forEach(group0 => {
                const group1 = group0.replace(/^\(/, "[").replace(/\)$/, "]");
                const group = JSON.parse(group1)
                const listItem = document.createElement('li');
                listItem.textContent = `${group[1]}`;

                // Crear el ícono de basura
                const addGroupIcon = document.createElement('i');
                addGroupIcon.className = 'fas fa-plus';
                addGroupIcon.id = 'icon'
                addGroupIcon.style.marginBottom = '15px';
                addGroupIcon.style.marginLeft = '15px';

                addGroupIcon.addEventListener('click', function () {
                    const returnValue = group[0]
                    console.log("return Value", returnValue)
                    return returnValue['<value>']
                })

                // Agregar el ícono al elemento de lista
                listItem.appendChild(addGroupIcon);

                // Agregar el elemento de lista al contenedor
                groupList.appendChild(listItem);
            });
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert(error.message);
        });


    activeMenu2 = document.getElementById('menu7');

    // Muestra el overlay y el menú flotante correspondiente
    if (menu) {
        overlay2.style.display = 'flex';
        menu.style.display = 'flex';
        activeMenu2 = menu; // Guarda el menú activo
    }

    const closeMenuContacts = document.getElementById('closeMenuGroups')
    closeMenuContacts.addEventListener('click', function (event) {
        closeMenu2()
    })

    // Evento para cerrar menús
    overlay2.addEventListener('click', closeMenu2);
    document.querySelectorAll('.closeMenu2').forEach(button => {
        button.addEventListener('click', closeMenu2);
    });
}

function agendaGroup1(groupID) {
    
    fetch(`http://127.0.0.1:5000/api/groups/${groupID}/agendas`, {
        method: 'GET', 
        headers: {
            'Content-Type': 'application/json',
        },
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al consultar la agenda: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Redirigir al usuario
            closeMenu()
            closeMenu2()
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
}

function agendaMember1() {
    fetch(`http://127.0.0.1:5000/api/agendas`, {
        method: 'GET', 
        headers: {
            'Content-Type': 'application/json',
        },
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al consultar la agenda: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Redirigir al usuario
            closeMenu()
            closeMenu2()
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
}

function agendaGroup(groupID) {
    let date = new Date();
    let day = date.getDate();
    let year = date.getFullYear();
    let month = date.getMonth();
    const dayString = `${year}-${month + 1}-${day}`;
    const initDate = adjustDateByDays(dayString, -100000);
    const endDate = adjustDateByDays(dayString, 100000);

    const returnDate = groupID ? `?start_date=${initDate}&end_date=${endDate}&group_id=${groupID}` : `?start_date=${initDate}&end_date=${endDate}`;
    return returnDate;
}

