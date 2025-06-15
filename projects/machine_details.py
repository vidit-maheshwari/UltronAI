import platform


def get_machine_details():
    """
    Retrieves and returns system and hardware information.
    """
    details = {}

    # General System Information
    details['system'] = platform.system()
    details['release'] = platform.release()
    details['version'] = platform.version()

    # CPU Information
    details['cpu_count'] = platform.processor()

    # Memory Information
    # Note: platform module doesn't provide memory info
    # For full memory details, you might need to use psutil

    # Platform Specific Information
    details['platform'] = platform.platform()
    details['uname'] = platform.uname()

    return details


def print_machine_details():
    """
    Prints the machine details in a formatted manner.
    """
    details = get_machine_details()

    print("### Machine Details ###")
    print(f"System: {details['system']}")
    print(f"Release: {details['release']}")
    print(f"Version: {details['version']}")
    print(f"CPU: {details['cpu_count']}")
    print(f"Platform: {details['platform']}")
    print(f"Uname: {details['uname']}")


def main():
    print_machine_details()

if __name__ == '__main__':
    main()