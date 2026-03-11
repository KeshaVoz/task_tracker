
$(document).ready(async function() {
    console.log('Tasks page loaded');
    
    try {
        console.log('Checking auth with window.checkAuth...');
        const user = await window.checkAuth();
        console.log('Auth OK, user:', user);
        $('#currentUser').text(user.email || 'User');
        initTasks();
    } catch (error) {
        console.log('Auth failed:', error);
        window.location.href = '/login';
    }
});

function initTasks() {
    $('#addTaskBtn').click(addTask);
    $('#newTaskTitle').on('keypress', function(e) {
        if (e.which === 13) addTask();
    });
    
    $('#logoutBtn').click(function() {
        window.logout();  
    });
    
    loadTasks();
}


async function apiRequest(options) {
    console.log(' apiRequest URL:', options.url);           
    console.log(' apiRequest METHOD:', options.method);
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login';
        throw new Error('No token');
    }

    return new Promise((resolve, reject) => {
        $.ajax({
            url: options.url,
            method: options.method || 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                ...(options.headers || {})  
            },
            data: options.data,
            xhrFields: { withCredentials: true },
            success: function(response) {
                console.log(`${options.method || 'GET'} ${options.url} success:`, response);
                resolve(response);
            },
            error: function(xhr, status, error) {
                console.log('API error details:', {
                    status: xhr.status,
                    statusText: xhr.statusText,
                    responseText: xhr.responseText?.substring(0, 200)
                });
                console.log(`❌ ${options.method} ${options.url} FAILED [${xhr.status}]:`, xhr.responseText);
                
                if (xhr.status === 401) {
                    localStorage.removeItem('access_token');
                    window.location.href = '/login';
                }
                reject({
                    status: xhr.status,
                    message: xhr.responseJSON?.detail || xhr.responseText || 'Unknown error'
                });
            }
        });
    });
}


async function loadTasks() {
    $('#loading').show();
    
    try {
        const response = await apiRequest({ url: '/api/tasks/all_tasks' });
        renderTasks(response.tasks || []);
    } catch (error) {
        console.error('Load tasks failed:', error);
        $('#tasksList').html(`
            <div class="empty-state">
                Error loading tasks: ${error.message || 'Unknown error'}
                <br><a href="/tasks">Try again</a>
            </div>
        `);
    } finally {
        $('#loading').hide();
        $('#mainContent').removeClass('hidden');
    }
}

function renderTasks(tasks) {
    console.log('Rendering', tasks.length, 'tasks');
    const pendingTasks = tasks.filter(task => !task.is_completed);
    const completedTasks = tasks.filter(task => task.is_completed);

    let html = '';

    html += `<h3>Pending Tasks (${pendingTasks.length})</h3>`;
    if (pendingTasks.length > 0) {
        html += pendingTasks.map(task => taskHtml(task, true)).join('');
    } else {
        html += '<div class="task empty-task">No pending tasks </div>';
    }


    html += '<hr style="margin: 40px 0;">';


    html += `<h3>Completed Tasks (${completedTasks.length})</h3>`;
    if (completedTasks.length > 0) {
        html += completedTasks.map(task => taskHtml(task, false)).join('');
    } else {
        html += '<div class="task empty-task">No completed tasks</div>';
    }

    $('#tasksList').html(html);
    $('#emptyState').toggleClass('hidden', tasks.length > 0);
}

function taskHtml(task, editable = false) {
    const isCompleted = task.is_completed;
    const date = new Date(task.updated_at).toLocaleDateString('en-US');
    
    return `
        <div class="task ${isCompleted ? 'completed' : ''}" data-task-id="${task.id}">
            <div style="flex: 1;">
                <div class="task-title" style="font-size: 1.3em; margin-bottom: 8px;">${task.title}</div>
                <div class="task-description" style="color: #7f8c8d; margin-bottom: 12px;">
                    ${task.description || 'No description'}
                </div>
                <div style="color: #95a5a6; font-size: 0.9em;">${date}</div>
            </div>
            <div class="task-actions">
                ${editable ? `
                    <button class="task-edit" data-task-id="${task.id}" title="Edit">
                        ✏️
                    </button>` : ''
                }
                <button class="task-toggle ${isCompleted ? 'completed-toggle' : ''}" 
                        data-task-id="${task.id}" 
                        title="${isCompleted ? 'Mark incomplete' : 'Mark complete'}">
                    ${isCompleted ? '↶' : '✓'}
                </button>
                <button class="task-delete" data-task-id="${task.id}" title="Delete">🗑️</button>
            </div>
        </div>
    `;
}


async function addTask() {
    const title = $('#newTaskTitle').val().trim();
    const description = $('#newTaskDescription').val().trim();
    
    if (!title) return;

    console.log('➕ addTask отправляем:', { title, description });  // ← ДОБАВЬТЕ
    console.log('➕ addTask URL будет:', '/api/tasks');
    try {
        await apiRequest({
            url: '/api/tasks',
            method: 'POST',
            data: JSON.stringify({ title, description }),  
            headers: { 'Content-Type': 'application/json' }
        });
        
        $('#newTaskTitle, #newTaskDescription').val('');
        loadTasks();
    } catch (error) {
        console.error('Add task error:', error);
    }
}


$(document).on('click', '.task-edit', async function(e) {
    e.stopPropagation();
    const taskId = $(this).data('task-id');
    const $task = $(`[data-task-id="${taskId}"]`);
    
    if ($task.hasClass('editing')) return;
    
    $task.addClass('task-editing editing');
    $(this).replaceWith(`
        <button class="task-save" data-task-id="${taskId}" title="Save">✅</button>
    `);
    
    const title = $task.find('.task-title').text();
    const description = $task.find('.task-description').text() === 'No description' ? '' : $task.find('.task-description').text();
    
    $task.find('.task-title').html(`<input class="task-edit-input" value="${title}" autofocus>`);
    $task.find('.task-description').html(`
        <textarea class="task-edit-textarea task-edit-input">${description}</textarea>
    `);
});


$(document).on('click', '.task-save', async function(e) {
    e.stopPropagation();
    const taskId = $(this).data('task-id');
    const $task = $(`[data-task-id="${taskId}"]`);
    
    const newTitle = $task.find('.task-edit-input').eq(0).val().trim();
    const newDescription = $task.find('.task-edit-input').eq(1).val().trim();
    
    if (!newTitle) return;
    
    try {
        await apiRequest({
            url: `/api/tasks/${taskId}`,
            method: 'PATCH',
            data: JSON.stringify({                    
                title: newTitle,
                description: newDescription || ''       
            }),
            headers: { 'Content-Type': 'application/json' }
        });
        loadTasks();
    } catch (error) {
        console.error('Save error:', error);
        loadTasks();
    }
});


$(document).on('click', '.task-toggle', async function(e) {
    e.stopPropagation();
    const taskId = $(this).data('task-id');
    
    try {
        await apiRequest({
            url: `/api/tasks/${taskId}/toggle`,
            method: 'PATCH'
  
        });
        loadTasks();
    } catch (error) {
        console.error('Toggle error:', error);
    }
});


$(document).on('click', '.task-delete', async function(e) {
    e.stopPropagation();
    const taskId = $(this).data('task-id');
    
    if (!confirm('Delete task permanently?')) return;
    
    try {
        await apiRequest({
            url: `/api/tasks/${taskId}`,
            method: 'DELETE'
        });
        loadTasks();
    } catch (error) {
        console.error('Delete error:', error);
    }
});
