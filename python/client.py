import threading
import time
import random
import requests

# Update with the LB HTTP listener IP
lb_base = "http://129.158.200.78"

def call_api(endpoint, sleep_time_range, total_duration):
    end_time = time.time() + total_duration
    while time.time() < end_time:
        start_time = time.time()
        try:
            response = requests.get(endpoint)
            elapsed_time_ms = (time.time() - start_time) * 1000
            print(f"Called {endpoint}, Status Code: {response.status_code}, Time: {elapsed_time_ms:.2f} ms")
        except requests.exceptions.RequestException as e:
            print(f"Error calling {endpoint}: {e}")
        sleep_time = random.uniform(*sleep_time_range)
        time.sleep(sleep_time)

def start_threads(endpoints, num_threads, sleep_time_range, total_duration):
    threads = []
    for _ in range(num_threads):
        for endpoint in endpoints:
            thread = threading.Thread(target=call_api, args=(endpoint, sleep_time_range, total_duration))
            threads.append(thread)
            thread.start()
    
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    endpoints = [
        lb_base+"/path1/",
      #  lb_base+"/path2/",
      #  lb_base+"/echo1",
      #  lb_base+"/echo2",
        lb_base+"/burn_cpu",
    ]
    num_threads = 30
    sleep_time_range = (1, 5)  # Sleep between 1 to 5 seconds
    total_duration = 60*60  # Run for 60 minutes

    start_threads(endpoints, num_threads, sleep_time_range, total_duration)
