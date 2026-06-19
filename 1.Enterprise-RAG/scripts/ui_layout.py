
## main page ##
def ui_login(user_email, root_path):
    
    html_content = """
    <!DOCTYPE html>
    <html>

    <head>

        <title>Enterprise Search</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

        <style>

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {

                font-family: 'Inter', sans-serif;
                background: #f5f7fb;
                color: #111827;
                overflow: hidden;
            }

            /* TOP NAV */

            .topbar {
                position: relative;

                background: #5b89ae;
                color: white;
                padding: 18px 40px;

                box-shadow: 0 2px 4px rgba(0,0,0,0.1);

                display: flex;
                justify-content: center;
                align-items: center;
            }

            .topbar-title {
                font-size: 20px;
                font-weight: 600;
            }

            .user-section {
                position: absolute;
                right: 40px;

                display: flex;
                align-items: center;
                gap: 15px;

                font-size: 14px;
            }

            .username {
                max-width: 250px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .logout-link {
                color: white;
                text-decoration: none;
                font-weight: 600;
            }

            .logout-link:hover {
                text-decoration: underline;
            }

            /* MAIN AREA */

            .container {

                width: 100%;
                max-width: 1050px;
                margin: 40px auto;
                padding: 0 20px;
            }

            /* SEARCH BAR */

            .search-wrapper {

                display: flex;
                gap: 12px;
                margin-bottom: 28px;
                justify-content: center;                
            }

            .search-input {

                width: 700px;
                height: 46px;
                padding: 0 18px;
                border-radius: 14px;
                border: 1px solid #cbd5e1;
                background: white;
                font-size: 15px;
                outline: none;
            }

            .search-input:focus {

                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
            }

            .search-button {

                width: 95px;
                height: 42px;
                border: none;
                border-radius: 12px;
                background: #4f7ea8;
                color: white;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
            }

            .search-button:hover {

                background: #4f7ea8;
            }

            /* RESULT CARD */

            .results-container {

                margin-top: 24px;                
                height: calc(100vh - 220px);
                overflow-y: auto;
                padding-right: 6px;
            }

            .result-card {

                background: #f3f4f6;
                border-radius: 14px;
                border: 1px solid #e5e7eb;
                padding: 16px;
                box-shadow:
                    0 1px 2px rgba(0,0,0,0.04),
                    0 4px 10px rgba(0,0,0,0.04);
                width: 830px;     
                margin: 0 auto;   
                margin-bottom: 18px;   
                position: relative;
                overflow: visible;            
            }

            .result-content {

                font-size: 14px;
                line-height: 1.5;
                color: #1f2937;                
                text-align: justify;                
            }

            .citation-text {
                margin-top: 14px;
                font-size: 12px;
                color: #5b89ae;
                font-style: italic;
            }

            .copy-icon-button {

                margin-left: auto;
                position: absolute;
                right: -50px;
                bottom: 10px;
                border: none;
                background: #eef2f7;
                color: #6b7280;
                width: 30px;
                height: 30px;
                cursor: pointer;
                transition: all 0.2s ease;                
            }

            .copy-icon-button:hover {
                background: #dbe4ee;
                color: #374151;
            }

            .response-footer {
                display: flex;                
                align-items: center;
                margin-top: 10px;                
            }

            
            .loading {

                color: #6b7280;
            }

            .typing-indicator {
                display: flex;
                gap: 6px;
                padding: 12px 0;
            }

            .typing-indicator span {
                width: 8px;
                height: 8px;
                background: #5b89ae;
                border-radius: 50%;
                animation: bounce 1.4s infinite ease-in-out;
            }

            .typing-indicator span:nth-child(2) {
                animation-delay: 0.2s;
            }

            .typing-indicator span:nth-child(3) {
                animation-delay: 0.4s;
            }

            @keyframes bounce {
                0%, 80%, 100% {
                    transform: scale(0.6);
                    opacity: 0.5;
                }
                40% {
                    transform: scale(1);
                    opacity: 1;
                }
            }

            @media (max-width: 768px) {

                .search-wrapper {

                    flex-direction: column;
                }

                .search-button {

                    width: 100%;
                    height: 56px;
                }
            }

        </style>

    </head>

    <body>

        <div class="topbar">
            <div class="topbar-title">
                Enterprise Search
            </div>

            <div class="user-section">
                <span class="username">__USER_EMAIL__</span>
                <a href="__LOGOUT__" class="logout-link">Logout</a>
            </div>
        </div>

        <div class="container">

            <div class="search-wrapper">

                <input
                    type="text"
                    id="userInput"
                    class="search-input"                    
                    onkeypress="handleEnter(event)"
                >

                <button
                    class="search-button"
                    onclick="sendMessage()"
                >
                    Search
                </button>

            </div>

            <div id="resultsContainer" class="results-container"></div>

        </div>

        <script>

            async function sendMessage() {

                const inputBox = document.getElementById("userInput");

                const text = inputBox.value.trim();

                if (!text) return;

                const resultsContainer = document.getElementById("resultsContainer");

                const loadingId = "loading-" + Date.now();

                // ADD LOADING CARD

                resultsContainer.innerHTML += `

                    <div class="result-card" id="${loadingId}">

                        <div class="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>

                    </div>
                `;

                // AUTO SCROLL TO BOTTOM

                resultsContainer.scrollTop = resultsContainer.scrollHeight;

                try {

                    const response = await fetch("__USER_QUERY__", {

                        method: "POST",

                        headers: {
                            "Content-Type": "application/json"
                        },

                        body: JSON.stringify({
                            text: text
                        })
                    });

                    if (response.redirected) {

                        window.location.href = response.url;

                        return;
                    }

                    const data = await response.json();

                    // REPLACE LOADING CARD WITH ACTUAL RESPONSE

                    document.getElementById(loadingId).innerHTML = `

                        <div style="
                            font-size: 13px;
                            font-weight: 600;
                            color: #4f7ea8;
                            margin-bottom: 10px;
                        ">
                            Query: ${text}
                        </div>

                        <div class="result-content" >
                            ${data.answer}
                        </div>

                        <div class="response-footer" >

                            ${data.sources && data.sources.length > 0 ? `
                                <div class="citation-text">
                                    Citation: ${data.sources.join(", ")}
                                </div>
                            ` : ``}

                            <button
                                class="copy-icon-button"
                                onclick="copyResponse(this)"
                                title="Copy response"
                            >
                                ⧉
                            </button>

                        </div>
                    `;

                    // AUTO SCROLL AFTER RESPONSE

                    resultsContainer.scrollTop = resultsContainer.scrollHeight;
                }

                catch (error) {

                    document.getElementById(loadingId).innerHTML = `

                        <div class="result-content">
                            Oops! Server met with an issue, please try later.
                        </div>
                    `;
                }

                inputBox.value = "";
            }

            function handleEnter(event) {

                if (event.key === "Enter") {
                    sendMessage();
                }
            }

            function copyResponse(button) {

                const card = button.closest(".result-card");
                const responseText =
                    card.querySelector(".result-content").innerText;
                navigator.clipboard.writeText(responseText);
                button.innerText = "✓";
                setTimeout(() => {
                    button.innerText = "⧉";
                }, 1200);
            }

        </script>

    </body>

    </html>
    """

    #html_content = html_content.replace(
    #    "__USER_EMAIL__",
    #    user_email
    #)

    replacements = {
        "__USER_EMAIL__": user_email,
        "__USER_QUERY__": f"{root_path}/userquery",
        "__LOGOUT__": f"{root_path}/logout"
    }


    for key, value in replacements.items():
        html_content = html_content.replace(key, value)

    return html_content
## end ##

## logout page
def ui_logout(root_path):
    
    html_content = """
    <!DOCTYPE html>
    <html>

    <head>

        <title>Enterprise Search - Logout</title>

        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

        <style>

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {

                font-family: 'Inter', sans-serif;
                background: #f5f7fb;
                color: #111827;
                min-height: 100vh;
            }

            /* TOP NAV */

            .topbar {

                position: relative;
                background: #5b89ae;
                color: white;
                padding: 18px 40px;

                box-shadow: 0 2px 4px rgba(0,0,0,0.1);

                display: flex;
                justify-content: center;
                align-items: center;
            }

            .topbar-title {

                font-size: 20px;
                font-weight: 600;
            }

            /* MAIN AREA */

            .container {

                width: 100%;
                max-width: 1050px;
                margin: 0 auto;
                padding: 0 20px;
            }

            /* LOGOUT CARD */

            .logout-card {

                width: 600px;

                margin: 120px auto;

                background: white;

                border: 1px solid #e5e7eb;
                border-radius: 14px;

                padding: 40px;

                text-align: center;

                box-shadow:
                    0 1px 2px rgba(0,0,0,0.04),
                    0 4px 10px rgba(0,0,0,0.04);
            }

            .logout-title {

                font-size: 24px;
                font-weight: 600;

                color: #111827;

                margin-bottom: 12px;
            }

            .logout-message {

                font-size: 15px;
                color: #6b7280;

                margin-bottom: 28px;
                line-height: 1.5;
            }

            .login-link {

                display: inline-block;

                background: #5b89ae;
                color: white;

                text-decoration: none;

                padding: 8px 24px;

                border-radius: 10px;

                font-size: 14px;
                font-weight: 600;

                transition: background 0.2s ease;
            }

            .login-link:hover {

                background: #4f7ea8;
            }

            @media (max-width: 768px) {

                .logout-card {

                    width: 100%;
                    margin-top: 80px;
                }
            }

        </style>

    </head>

    <body>

        <div class="topbar">

            <div class="topbar-title">
                Enterprise Search
            </div>

        </div>

        <div class="container">

            <div class="logout-card">

                <div class="logout-title">
                    ℹ️ Logged Out
                </div>

                <div class="logout-message">
                    You have been successfully signed out of Enterprise Search.
                </div>

                <a href="__LOGIN__" class="login-link">
                    Login Again
                </a>

            </div>

        </div>

    </body>

    </html>
    """

    html_content = html_content.replace("__LOGIN__", f"{root_path}/")

    return html_content
## end ##

def ui_access_denied(reason, root_path):
   
    html_content = """
    <!DOCTYPE html>
    <html>

    <head>

        <title>Enterprise Search - Access Denied</title>

        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

        <style>

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Inter', sans-serif;
                background: #f5f7fb;
                color: #111827;
                min-height: 100vh;
            }

            /* TOP NAV */

            .topbar {
                position: relative;
                background: #5b89ae;
                color: white;
                padding: 18px 40px;

                box-shadow: 0 2px 4px rgba(0,0,0,0.1);

                display: flex;
                justify-content: center;
                align-items: center;
            }

            .topbar-title {
                font-size: 20px;
                font-weight: 600;
            }

            /* MAIN AREA */

            .container {
                width: 100%;
                max-width: 1050px;
                margin: 0 auto;
                padding: 0 20px;
            }

            /* ERROR CARD */

            .error-card {
                width: 700px;
                margin: 120px auto;

                background: white;

                border: 1px solid #e5e7eb;
                border-radius: 14px;

                padding: 40px;

                text-align: center;

                box-shadow:
                    0 1px 2px rgba(0,0,0,0.04),
                    0 4px 10px rgba(0,0,0,0.04);
            }

            .error-title {
                font-size: 24px;
                font-weight: 600;
                color: #b91c1c;
                margin-bottom: 16px;
            }

            .error-message {
                font-size: 15px;
                line-height: 1.6;
                color: #374151;
                margin-bottom: 16px;
            }

            .redirect-message {
                font-size: 14px;
                color: #6b7280;
                margin-bottom: 28px;
            }

            .logout-link {
                display: inline-block;

                background: #5b89ae;
                color: white;

                text-decoration: none;

                padding: 8px 24px;
                border-radius: 10px;

                font-size: 14px;
                font-weight: 600;

                transition: background 0.2s ease;
            }

            .logout-link:hover {
                background: #4f7ea8;
            }

            @media (max-width: 768px) {
                .error-card {
                    width: 100%;
                    margin-top: 80px;
                }
            }

        </style>

    </head>

    <body>

        <div class="topbar">
            <div class="topbar-title">
                Enterprise Search
            </div>
        </div>

        <div class="container">

            <div class="error-card">

                <div class="error-title">
                    Oops! Something went wrong
                </div>

                <div class="error-message">
                    __REASON__ : Your session is invalid or has expired.
                </div>

                <div class="redirect-message">
                    You will be securely logged out in
                    <span id="countdown">5</span>
                    seconds...
                </div>

                <a href="__LOGOUT__" class="logout-link">
                    Logout Now
                </a>

            </div>

        </div>

        <script>

            let seconds = 5;

            const countdown = document.getElementById("countdown");

            const timer = setInterval(() => {

                seconds--;

                countdown.textContent = seconds;

                if (seconds <= 0) {

                    clearInterval(timer);

                    window.location.href = "__LOGOUT__";
                }

            }, 1000);

        </script>

    </body>

    </html>
    """

    html_content = html_content.replace("__REASON__",reason)
    html_content = html_content.replace("__LOGOUT__",f"{root_path}/logout")
    
    return html_content

## end ##