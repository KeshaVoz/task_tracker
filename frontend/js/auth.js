

function getAccessToken() {
    const token = localStorage.getItem('access_token');
    console.log('getAccessToken: token =', token)
    return token;
}

function setAccessToken(token) {
    console.log('setAccessToken: token =', token);
    localStorage.setItem('access_token', token);
}


function login(email, password) {    
    $.ajax({
        url: '/api/auth/session',
        method: 'POST',
        data: { email, password },
        xhrFields: { withCredentials: true },
        success: function(response) {          
            if (response.access_token) {
                setAccessToken(response.access_token);
                console.log('After login, getAccessToken:', getAccessToken());
                setTimeout(() => {                    
                    const token = getAccessToken();
                    if (token) {
                        $.ajax({
                            url: '/api/auth/user',
                            method: 'GET',
                            headers: { 'Authorization': `Bearer ${token}` },
                            xhrFields: { withCredentials: true },
                            success: function(userResponse) {
                                window.location.href = '/tasks';
                            },
                            error: function(xhr) {
                                window.location.href = '/login';
                            }
                        });
                    } else {
                        alert('Token disappeared!');
                    }
                }, 500); 
            }
        },
        error: function(xhr) {
            alert(xhr.responseJSON?.message || 'Login failed');
        }
    });
}


function register(email, password) {
    $.ajax({
        url: '/api/auth/user',
        method: 'POST',
        data: { email, password },
        xhrFields: { withCredentials: true },
        success: function(response) {            
            if (response.access_token) {
                setAccessToken(response.access_token);                
                setTimeout(() => {                    
                    const token = getAccessToken();
                    if (token) {
                        window.location.href = '/tasks';
                    } else {
                        alert('Token disappeared!');
                    }
                }, 500);
            }
        },
        error: function(xhr) {
            alert(xhr.responseJSON?.detail?.message || 'Registration failed');
        }
    });
}


function logout() {
    $.ajax({
        url: '/api/auth/session',
        method: 'DELETE',
        xhrFields: { withCredentials: true },
        complete: function () {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        }
    });
}


async function getCurrentUser() {
    console.log('getCurrentUser start');    
    let token = getAccessToken();
    console.log('1. getCurrentUser: access_token =', token); 
    if (!token) {
        token = await tryRefreshToken();
        if (token) setAccessToken(token);
    }
    
    if (token) {
        console.log('2. getCurrentUser: sending /user request with token:', token.slice(0, 30) + '...');
        try {
            const response = await $.ajax({
                url: '/api/auth/user',
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}` },
                xhrFields: { withCredentials: true }
            });
            console.log('3. getCurrentUser: /user response =', response);
            return response;
        } catch (error) {
            console.log('4. getCurrentUser: /user error', error);
            localStorage.removeItem('access_token');
            throw error;
        }
    }
        throw new Error('Auth failed');
}

async function tryRefreshToken() {
    console.log('9. tryRefreshToken: BEFORE refresh, access_token =', getAccessToken());
    console.log('10. tryRefreshToken: document.cookie =', document.cookie);
    try {
        const response = await $.ajax({
            url: '/api/auth/session/refresh',
            method: 'POST',
            xhrFields: { withCredentials: true }
        });
        console.log('11. tryRefreshToken: refresh succeeded, new access_token =', response.access_token);
        return response.access_token;
    } catch (error) {
        console.log('12. tryRefreshToken: refresh error', error);
        localStorage.removeItem('access_token');
        return null;
    }
}


window.checkAuth = async function() {
    console.log('checkAuth start');
    const user = await getCurrentUser();
    console.log('checkAuth: returned user =', user); 
    return user;
};
window.login = login;
window.register = register;
window.logout = logout;

