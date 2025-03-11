import {closeMenu} from './calendar.js';
import {closeMenu2} from './groups.js';

const chord_id = localStorage.getItem('chord_id') || sessionStorage.getItem('chord_id');
const userData = localStorage.getItem('user_id') || sessionStorage.getItem('user_id');
const username = localStorage.getItem('username') || sessionStorage.getItem('username');
const idActualUser = int(userData);

// Adicionar nuevo contacto
document.getElementById('btn_add_contact').addEventListener('click', function () {
    // Obtener los valores de los inputs
    const username = document.getElementById('exampleInputUsername').value;

    const contactData = {
        chord_id: chord_id,
        contact_name: username,
        owner_id: idActualUser
    }
    fetch('http://127.0.0.1:5000/contacts/', {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
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

// List Contacts
document.getElementById('list_contacts').addEventListener('click', function () {
    // Realizar la solicitud GET al endpoint de contactos
    // fetch('http://127.0.0.1:5000/api/contacts/', {
    fetch(`http://127.0.0.1:5000/contacts/${idActualUser}/${chord_id}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
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
            data1 = data.split('\n')
            // Aquí puedes manipular los datos para mostrarlos en la página
            const contactList = document.getElementById('contact-list'); // Asegúrate de tener un contenedor en tu HTML con este ID
            contactList.innerHTML = ''; // Limpiar cualquier contenido previo

            data1.forEach(contact => {
                const listItem = document.createElement('li');
                listItem.textContent = `${contact[0]}`; //name

                // Crear el ícono de basura
                const trashIcon = document.createElement('i');
                trashIcon.className = 'fas fa-trash-alt';
                trashIcon.style.paddingLeft = '5px'; // Espacio entre el nombre y el ícono
                trashIcon.addEventListener('click', function () {
                    console.log('Borro')
                    deleteGroupFunction(contact[1]) //id
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
    fetch(`http://127.0.0.1:5000/contacts/${contactId}/delete/${contactId}`, {
        method: 'DELETE', 
        headers: {
            'Content-Type': 'application/json',
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