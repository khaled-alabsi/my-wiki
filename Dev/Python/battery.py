from concurrent.futures import thread
import time
import subprocess
from datetime import datetime
import multiprocessing
import sys
import random

from numpy import power


def get_battery_percentage() -> int:
    result = subprocess.run(
        ["pmset", "-g", "batt"], capture_output=True, text=True
    )
    for line in result.stdout.split("\n"):
        if "%" in line:
            try:
                percent = int(line.split("\t")[-1].split("%")[0].strip())
                return percent
            except ValueError:
                continue
    return -1


def keep_screen_on() -> None:
    subprocess.Popen(
        ["caffeinate", "-dims"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("Screen will remain on.")


def log_battery_life(start_time: datetime) -> None:
    end_time = datetime.now()
    duration = end_time - start_time
    with open(f"battery_life_log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt", "w") as file:
        file.write(f"Battery lasted: {duration}\n")
        file.write(f"Start time: {start_time}\n")
        file.write(f"End time: {end_time}\n")
    print(f"Battery lasted: {duration}")


def cpu_stress_test(_) -> None:
    while True:
        powers = [2, 4, 7]
        weights = [1, 0.7, 0.15]
        power = random.choices(powers, weights=weights, k=1)[0]
        _ = [
            i**2 for i in range(10**power)
        ]  # Randomized load
        time.sleep(random.uniform(0.1, 4.0))  # Randomized sleep time


def simulate_usage() -> None:
    threads = 3
    start_time = datetime.now()
    print("Monitoring battery usage...")
    with multiprocessing.Pool(threads) as pool:
        pool.map_async(cpu_stress_test, range(threads))
        try:
            while get_battery_percentage() != 0:
                battery_level = get_battery_percentage()
                elapsed_time = datetime.now() - start_time
                print(
                    f"Battery at {battery_level}%, Time spent on battery: {elapsed_time}")
                time.sleep(random.uniform(20, 40))
        except KeyboardInterrupt:
            print("Interrupted by user, stopping stress test...")
        finally:
            print("Stopping stress test and logging data...")
            pool.terminate()
            log_battery_life(start_time)
            sys.exit(0)



if __name__ == "__main__":
    multiprocessing.set_start_method(
        "spawn", force=True
    )  # Ensures compatibility with macOS
    print(f"started_at_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
    keep_screen_on()
    simulate_usage()
