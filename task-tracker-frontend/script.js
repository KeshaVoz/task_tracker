const DEBOUNCE_TIME = 500;
const API_URL = "http://localhost:8080/api";
$(function() {
    function appendErrorToForm(error, element) {
        let errorDiv = $(`
            <div class="form-group mt-3">
                <div class="alert alert-danger mt-3"></div>
            </div>
        `);
        error.appendTo(errorDiv.find("div.alert"));
        errorDiv.insertAfter(element);
    }

    function removeErrorFromForm(error, element) {
        $(element).next().remove();
    }

    function formatTime(time) {
        return new Date(time).toLocaleString('en-GB');
    }

    function createTaskDiv() {
        return $(`
            <a type="button" class="list-group-item list-group-item-action" 
            data-bs-toggle="modal" data-bs-target="#task-modal">
            </a>
        `);
    }

    function jsonTaskToTaskDiv(task) {
        let div = createTaskDiv();
        div.text(task.title).attr("data-task-id", task.id);
        return div;
    }

    function toggleError(element, active, text = '') {
        element.attr('hidden', !active);
        if (active) {
            element.find('div.alert').text(text);
        }
    }

    function updateTaskModal(task) {
        $('#task-modal input[name="title"]').val(task.title);
        $('#task-modal textarea[name="text"]').val(task.text);
        $('#task-modal input[name="is-completed"]').prop("checked", task.isCompleted);
        $("#completed-at")
            .attr('hidden', !task.completedAt)
            .text(task.completedAt ? `Done at ${formatTime(task.completedAt)}` : '');
    }

    function updateNavbar(authenticated, userData = {}) {
        $("#login-button, #register-button").attr('hidden', authenticated);
        $("#user-email, #log-out-button").attr('hidden', !authenticated);

        if (authenticated && userData.email) {
            $("#email-text").text(userData.email);
        }
    }

    const tasks = {};

    function fetchTasks() {
        $.ajax({
            type: 'GET',
            url: `${API_URL}/task`,
            xhrFields: { withCredentials: true },
            success: function(data) {
                let doneTasks = $("#done-tasks").empty();
                let toDoTasks = $("#to-do-tasks").empty();

                data.forEach(task => {
                    let taskDiv = jsonTaskToTaskDiv(task);
                    tasks[task.id] = task;
                    if (task.isCompleted) {
                        doneTasks.append(taskDiv);
                    } else {
                        toDoTasks.append(taskDiv);
                    }
                });
            },
        });

        $('#tasks-container').attr('hidden', false);
    }

    $('#task-modal').on('show.bs.modal', function(e) {
        let task = tasks[$(e.relatedTarget).data('task-id')];

        updateTaskModal(task);

        $(e.currentTarget).find('button[name="delete"]').off('click').click(function() {
            $.ajax({
                type: 'DELETE',
                url: `${API_URL}/task`,
                xhrFields: { withCredentials: true },
                data: { id: task.id },
                success: function () { $(`#to-do-tasks a[data-task-id="${task.id}"]`).remove(); }
            });
        });

        $('#task-modal input[name="title"], #task-modal textarea[name="text"]').off('keyup').keyup(
            $.debounce(DEBOUNCE_TIME, function () {
                const field = $(this).attr('name');
                $.ajax({
                    type: 'PATCH',
                    url: `${API_URL}/task`,
                    xhrFields: { withCredentials: true },
                    data: { id: task.id, [field]: $(this).val() },
                    success: function(data) {
                        task[field] = data[field];
                        if (field === 'title') {
                            $(`#to-do-tasks a[data-task-id="${task.id}"]`).text(task.title);
                        }
                        toggleError($('#task-modal-error'), false);
                    },
                    error: function(xhr) {
                        toggleError($('#task-modal-error'), true, JSON.parse(xhr.responseText).message);
                    },
                });
            }));

        $('#task-modal input[name="is-completed"]').off('change').change(function () {
            $.ajax({
                type: 'PATCH',
                url: `${API_URL}/task`,
                xhrFields: { withCredentials: true },
                data: { id: task.id, isCompleted: $(this).prop('checked') },
                success: function(data) {
                    task.isCompleted = data.isCompleted;
                    task.completedAt = data.completedAt;
                    fetchTasks();
                },
            });
        });
    });

    function updateUserData() {
        $.ajax({
            type: 'GET',
            url: `${API_URL}/auth/user`,
            xhrFields: { withCredentials: true },
            success: function(data) {
                updateNavbar(true, data);
                fetchTasks();
            },
        });
    }

    let loginForm = $("#login-form");
    let registerForm = $("#register-form");

    function validateForm(form, rules, messages) {
        form.validate({
            rules: rules,
            messages: messages,
            errorPlacement: appendErrorToForm,
            success: removeErrorFromForm,
        });
    }

    function handleFormSubmit(form, route, modal, error) {
        form.submit(function(e) {
            e.preventDefault();
            $.ajax({
                type: 'POST',
                url: API_URL + route,
                xhrFields: { withCredentials: true },
                data: $(this).serialize(),
                success: function() {
                    modal.modal('hide');
                    toggleError(error, false);
                    updateUserData();
                },
                error: function(xhr) {
                    toggleError(error, true,
                        xhr.responseText ? JSON.parse(xhr.responseText).message : "Oops! Something went wrong...");
                }
            });
        });
    }

    validateForm(loginForm, {
        email: {
            required: true,
            email: true,
        },
        password: {
            required: true,
        },
    }, {
        email: "Please enter a valid email address",
        password: "Please provide a password",
    });
    handleFormSubmit(loginForm, "/auth/session", $('#login-modal'), $('#login-error'));

    validateForm(registerForm, {
        email: {
            required: true,
            email: true,
        },
        password: {
            required: true,
            minlength: 5,
        },
        confirmPassword: {
            required: true,
            equalTo: "#registerPassword",
        },
    }, {
        email: 'Please enter a valid email address',
        password: {
            required: 'Please provide a password',
            minlength: 'Your password must be at least 5 password long',
        },
        confirmPassword: {
            required: 'Please provide a password',
            equalTo: 'Please enter the same password as above',
        },
    });
    handleFormSubmit(registerForm, "/auth/user", $('#register-modal'), $('#register-error'));

    $("#log-out-button :button").click(function() {
        $.ajax({
            type: 'DELETE',
            url: `${API_URL}/auth/session`,
            xhrFields: {
                withCredentials: true,
            },
            success: function() {
                updateNavbar(false);
                $("#tasks-container").attr("hidden", true);
            }
        })
    });

    $("#create-task").submit(function (e) {
        e.preventDefault();
        $.ajax({
            type: 'POST',
            url: `${API_URL}/task`,
            data: $(this).serialize(),
            xhrFields: { withCredentials: true },
            success: fetchTasks,
        });
    });

    $('#theme-switcher').click(function () {
        $('html').attr('data-bs-theme', function (index, attr) {
            return (attr === 'light') ? 'dark' : 'light';
        });
    });

    updateUserData();
});
