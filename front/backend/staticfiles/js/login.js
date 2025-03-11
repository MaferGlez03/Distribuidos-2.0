document.getElementById('btn').addEventListener('click', function () {
    // Obtener los valores de los inputs
    const username = document.getElementById('exampleInputUsername').value;
    const password = document.getElementById('exampleInputPassword').value;
    const rememberMe = document.getElementById('customCheck').checked; // Verificar si está marcado el checkbox

    // Crear el objeto con los datos
    const data = {
        username: username,
        password: password,
    };

    // Enviar los datos al endpoint
    fetch('http://127.0.0.1:5000/log_in/', {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en el registro');
            }
            return response.json();
        })
        .then(data => {
            // if(rememberMe) {
            //     // Si "Remember Me" está marcado, guarda en localStorage
            //     localStorage.setItem('authToken', data.token);
            //     localStorage.setItem('userData', JSON.stringify(data.user));
            // } else {
            //     // Si "Remember Me" no está marcado, guarda en sessionStorage
            //     sessionStorage.setItem('authToken', data.token);
            //     sessionStorage.setItem('userData', JSON.stringify(data.user));
            // }
            sessionStorage.setItem('authToken', data.token);
            sessionStorage.setItem('userData', JSON.stringify(data.user));
            
            // Redirigir al usuario
            window.location.href = '/';
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
});
