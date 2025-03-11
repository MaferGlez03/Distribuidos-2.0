import {closeMenu} from './calendar.js';
import {closeMenu2} from './groups.js';

const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
const userData = sessionStorage.getItem('userData');

// Convierte el string JSON a un objeto JavaScript
const userDataObject = JSON.parse(userData);

// Obtener el id de un usuario a partir de su username y su email
export function getUserId(username) {
    // Crear el objeto con los datos
    const data = {
        username: username
    };

    // Enviar los datos al endpoint
    return fetch('http://127.0.0.1:5000/contacts/get_user_id/', {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`,
        },
        body: JSON.stringify(data),
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al obtener el ID de usuario: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            const textInput = document.getElementById('EventUser')
            textInput.value = data['contact']
            closeMenu2();
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
            throw error;
        });
}

// Obtener el id de un grupo a partir de su name
export function getGroupId(name) {
    // Crear el objeto con los datos
    const data = {
        name: name
    };

    // Enviar los datos al endpoint
    return fetch('http://127.0.0.1:5000/get_group_id/', {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`,
        },
        body: JSON.stringify(data),
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al obtener el ID del grupo: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            const textInput = document.getElementById('EventGroup')
            textInput.value = data['group']
            closeMenu2();
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
            throw error;
        });
}

// Adicionar nuevo contacto
document.getElementById('btn_add_contact').addEventListener('click', function () {
    // Obtener los valores de los inputs
    const username = document.getElementById('exampleInputUsername').value;
    getUserId(username)
        .then(id => {
            const contactData = {
                user_id: id,
                contact_name: username,
                owner_id: userDataObject.id
            }
        
        
            // fetch('http://127.0.0.1:5000/api/contacts/', {
            fetch('http://127.0.0.1:5000/contacts/', {
                method: 'POST', 
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${token}`,
                },
                body: JSON.stringify(contactData),
            })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => {
                            throw new Error(`Error al crear el contacto: ${err.detail || err}`);
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
        })
        .catch(error => {
            console.error('Error al obtener el ID', error)
        })
});

// List Contacts
document.getElementById('list_contacts').addEventListener('click', function () {
    // Realizar la solicitud GET al endpoint de contactos
    // fetch('http://127.0.0.1:5000/api/contacts/', {
    fetch(`http://127.0.0.1:5000/contacts/${userDataObject.id}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`, // Token para autenticación
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
            // Mostrar los contactos en la consola o en la UI
            console.log('Contactos obtenidos:', data);

            // Aquí puedes manipular los datos para mostrarlos en la página
            const contactList = document.getElementById('contact-list'); // Asegúrate de tener un contenedor en tu HTML con este ID
            contactList.innerHTML = ''; // Limpiar cualquier contenido previo

            data['contacts'].forEach(contact => {
                const listItem = document.createElement('li');
                listItem.textContent = `${contact.contact_name}`;

                // Crear el ícono de basura
                const trashIcon = document.createElement('i');
                trashIcon.className = 'fas fa-trash-alt';
                trashIcon.style.paddingLeft = '5px'; // Espacio entre el nombre y el ícono
                trashIcon.addEventListener('click', function () {
                    console.log('Borro')
                    deleteGroupFunction(contact.id)
                })

                // Agregar el ícono al elemento de lista
                listItem.appendChild(trashIcon);

                // Agregar el elemento de lista al contenedor
                contactList.appendChild(listItem);
            });
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert(error.message);
        });
});

function deleteGroupFunction(contactId) {
    fetch(`http://127.0.0.1:5000/contacts/${contactId}/delete/`, {
        method: 'DELETE', 
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`,
        },
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al eliminar contacto: ${err.detail || err}`);
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
            closeMenu()
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
}