document.addEventListener('DOMContentLoaded', (event) => {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.add('dark-mode'); // Start in dark mode
    }
});

function toggleTheme() {
    const body = document.body;
    const toggleButton = document.getElementById('theme-toggle');

    body.classList.toggle('dark-mode');

    if (body.classList.contains('dark-mode')) {
        toggleButton.textContent = 'Switch to Light Mode';
        localStorage.setItem('darkMode', 'true');
    } else {
        toggleButton.textContent = 'Switch to Dark Mode';
        localStorage.setItem('darkMode', 'false');
    }
}

function clearChat() {
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML = ''; // Clear all messages
}

function checkEnter(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault(); // Prevent the default action (new line)
        sendMessage();
    }
}

function sendMessage(replyTo = null) {
    const userInput = document.getElementById('user-input').value;
    const username = document.getElementById('username').value; // Assuming you have a username input field
    const email = document.getElementById('email').value; // Assuming you have an email input field
    const chatBox = document.getElementById('chat-box');

    if (userInput.trim() === "" || !username || !email) {
        return; // Prevent sending empty messages or missing user details
    }

    const timestamp = new Date().toLocaleTimeString();

    // Create the user message element
    const userMessage = document.createElement('div');
    userMessage.classList.add('message', 'user-message');
    const userMessageContent = document.createElement('pre');
    userMessageContent.classList.add('message-content');
    userMessageContent.textContent = `${userInput}\n\n${timestamp}`;

    // Add reply button
    const replyButton = document.createElement('button');
    replyButton.textContent = 'Reply';
    replyButton.classList.add('reply-button');
    replyButton.onclick = () => replyToMessage(userMessage);

    userMessage.appendChild(userMessageContent);
    userMessage.appendChild(replyButton);

    if (replyTo) {
        let repliesContainer = replyTo.querySelector('.replies');
        if (!repliesContainer) {
            repliesContainer = document.createElement('div');
            repliesContainer.classList.add('replies');
            replyTo.appendChild(repliesContainer);
        }
        repliesContainer.appendChild(userMessage);
    } else {
        chatBox.appendChild(userMessage);
    }

    // Scroll to the bottom of the chat box
    chatBox.scrollTop = chatBox.scrollHeight;

    // Clear the input field
    document.getElementById('user-input').value = '';
    adjustTextareaHeight(); // Reset the textarea height

    // Send the message to the backend
    fetch('/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: userInput, username: username, email: email })
    })
    .then(response => response.json())
    .then(data => {
        // Add a delay before displaying the bot message
        setTimeout(() => {
            // Create the bot message element
            const botMessage = document.createElement('div');
            botMessage.classList.add('message', 'bot-message');
            const botMessageContent = document.createElement('pre');
            botMessageContent.classList.add('message-content');
            botMessageContent.textContent = `${data.result}\n\n${timestamp}`;

            // Add reply button
            const replyButton = document.createElement('button');
            replyButton.textContent = 'Reply';
            replyButton.classList.add('reply-button');
            replyButton.onclick = () => replyToMessage(botMessage);

            botMessage.appendChild(botMessageContent);
            botMessage.appendChild(replyButton);

            chatBox.appendChild(botMessage);

            // Scroll to the bottom of the chat box
            chatBox.scrollTop = chatBox.scrollHeight;
        }, 1000); // Delay before displaying the bot message (1 second)
    })
    .catch(error => {
        console.error('Error:', error);

        // Display error message
        const errorMessage = document.createElement('div');
        errorMessage.classList.add('message', 'bot-message', 'error');
        const errorContent = document.createElement('pre');
        errorContent.classList.add('message-content');
        errorContent.textContent = 'An error occurred. Please try again.';

        const replyButton = document.createElement('button');
        replyButton.textContent = 'Reply';
        replyButton.classList.add('reply-button');
        replyButton.onclick = () => replyToMessage(errorMessage);

        errorMessage.appendChild(errorContent);
        errorMessage.appendChild(replyButton);
        chatBox.appendChild(errorMessage);
        chatBox.scrollTop = chatBox.scrollHeight;
    });
}


function replyToMessage(messageElement) {
    document.getElementById('user-input').focus();
    sendMessage(messageElement);
}

function adjustTextareaHeight() {
    const textarea = document.getElementById('user-input');
    textarea.style.height = 'auto'; // Reset height
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'; // Set new height with a max limit
}

document.getElementById('user-input').addEventListener('input', adjustTextareaHeight);

function searchMessages() {
    const searchBar = document.getElementById('search-bar');
    const filter = searchBar.value.toLowerCase();
    const messages = document.getElementsByClassName('message');

    for (let i = 0; i < messages.length; i++) {
        const messageContent = messages[i].querySelector('.message-content').textContent;
        if (messageContent.toLowerCase().includes(filter)) {
            messages[i].style.display = '';
        } else {
            messages[i].style.display = 'none';
        }
    }
}
document.addEventListener('DOMContentLoaded', () => {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }

    document.getElementById('auth-form').addEventListener('submit', handleAuthSubmit);
});

function handleAuthSubmit(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const formTitle = document.getElementById('form-title').textContent;

    const url = formTitle === 'Register' ? '/register' : '/login';
    const method = formTitle === 'Register' ? 'POST' : 'POST';

    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (formTitle === 'Register') {
                alert('Registration successful!');
            } else {
                localStorage.setItem('userId', data.user_id);
                document.getElementById('auth-container').style.display = 'none';
                document.getElementById('chat-container').style.display = 'block';
            }
        } else {
            alert(data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    });
}

function toggleAuthForm() {
    const formTitle = document.getElementById('form-title');
    const authToggle = document.getElementById('auth-toggle');

    if (formTitle.textContent === 'Register') {
        formTitle.textContent = 'Log In';
        authToggle.innerHTML = 'Don\'t have an account? <a href="#" onclick="toggleAuthForm()">Register</a>';
        document.getElementById('auth-submit').textContent = 'Log In';
        document.getElementById('username').style.display = 'none'; // Hide username for login
    } else {
        formTitle.textContent = 'Register';
        authToggle.innerHTML = 'Already have an account? <a href="#" onclick="toggleAuthForm()">Log in</a>';
        document.getElementById('auth-submit').textContent = 'Register';
        document.getElementById('username').style.display = 'block'; // Show username for registration
    }
}

