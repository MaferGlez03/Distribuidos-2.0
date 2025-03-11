document.getElementById('btn').addEventListener('click', function () {
    // Obtener los valores de los inputs
    const username = document.getElementById('exampleInputUsername').value;
    const email = document.getElementById('exampleInputEmail').value;
    const password = document.getElementById('exampleInputPassword').value;
    const repeatPassword = document.getElementById('exampleRepeatPassword').value;
    const rememberMe = document.getElementById('customCheck').checked; // Verificar si está marcado el checkbox

    // Validar que las contraseñas coincidan
    if (password !== repeatPassword) {
        alert('Las contraseñas no coinciden');
        return;
    }

    // Crear el objeto con los datos
    const data = {
        username: username,
        email: email,
        password: password,
    };

    // Enviar los datos al endpoint
    fetch('http://127.0.0.1:5000/sign_up/', {
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
            console.log(data.message)

            // Redirigir al usuario o realizar otra acción
            window.location.href = '/';
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
});

