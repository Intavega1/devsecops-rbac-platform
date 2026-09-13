import time


def main():
    print("Excel Worker started")

    while True:
        print("Excel Worker waiting for jobs...")
        time.sleep(30)


if __name__ == "__main__":
    main()
