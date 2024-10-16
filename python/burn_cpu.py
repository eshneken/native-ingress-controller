from flask import Flask
import random
import time

app = Flask(__name__)

def burn_cpu_for_duration(duration_seconds):
    # Burn CPU for a given duration (in seconds)
    start_time = time.time()
    x = 0
    while time.time() - start_time < duration_seconds:
        x += 1  # Perform some calculation to keep CPU busy

@app.route('/burn_cpu', methods=['GET'])
def burn_cpu_endpoint():
    # Randomly choose a burn duration between 10 milliseconds and 2 seconds
    burn_duration = random.uniform(0.01, 2.0)  # duration in seconds
    burn_cpu_for_duration(burn_duration)
    # Return HTTP 200 OK response after burning CPU for the random duration
    return f"CPU Burned for {burn_duration:.3f} seconds", 200

if __name__ == '__main__':
    app.run(debug=True)
