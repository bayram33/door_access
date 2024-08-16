from flask import Flask, jsonify
from zk import ZK, const
import requests
import schedule
import threading
import time

app = Flask(__name__)

zk = ZK(
    "192.168.1.220", port=4370, timeout=5, password=0, force_udp=False, ommit_ping=False
)

# URL of your API endpoint
API_URL = "http://localhost:5000/users"


def fetch_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            print("Fetched Data:", data)
        else:
            print("Failed to fetch data. Status code:", response.status_code)
    except Exception as e:
        print("Error fetching data:", e)


# Schedule the task to run every minute
schedule.every(1).minute.do(fetch_data)


@app.route("/", methods=["GET"])
def root():
    # Return HTML with a styled link and a loading spinner
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ZKTeco API</title>
        <style>
            a {
                text-decoration: none;
                color: blue;
                font-size: 18px;
                transition: all 0.3s ease;
            }
            a:hover {
                color: red;
                font-size: 22px;
                font-weight: bold;
            }

            /* Spinner style */
            .spinner {
                display: none;
                border: 4px solid rgba(0, 0, 0, 0.1);
                border-left-color: #4CAF50;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin-top: 20px;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <h1>Welcome to ZKTeco API</h1>
        <p>Use the link below to get the user list:</p>
        <a href="#" id="fetchUsersLink">http://127.0.0.1:5000/users</a>

        <div class="spinner" id="spinner"></div>

        <script>
            document.getElementById("fetchUsersLink").addEventListener("click", function(event) {
                event.preventDefault();  // Prevent default link behavior
                
                // Show the spinner
                document.getElementById("spinner").style.display = "block";

                // Redirect to /users immediately
                window.location.href = "/users";
            });
        </script>
    </body>
    </html>
    """


@app.route("/users", methods=["GET"])
def get_zkteco_users():
    try:
        conn = zk.connect()
        conn.disable_device()
        users = conn.get_users()
        records = conn.get_attendance()

        user_data = []
        for record in records[-1:-101:-1]:
            user_info = {
                "user_id": record.user_id,
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for user in users:
                if record.user_id == user.user_id:
                    user_info["name"] = user.name
                    break
            user_data.append(user_info)

        conn.enable_device()
        return jsonify(user_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.disconnect()


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)  # Wait a second before checking for pending tasks


if __name__ == "__main__":
    # Start the background thread for the scheduler
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()

    # Fetch data immediately when the server starts
    fetch_data()

    # Run the Flask app
    app.run(host="0.0.0.0", port=5000)
