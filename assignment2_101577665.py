"""
Author: <Kalid Ali>
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

# TODO: Import the required modules (Step ii)
# socket, threading, sqlite3, os, platform, datetime
import socket, threading, sqlite3, os, platform, datetime


# TODO: Print Python version and OS name (Step iii)
print(f"Python Version: {platform.python_version()}")
print(f"Operating System: {os.name}")

# TODO: Create the common_ports dictionary (Step iv)
# Maps port numbers to their standard network service names
common_ports = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
    443: "HTTPS", 3306: "MySQL", 3389: "RDP", 8080: "HTTP-Alt"
}

# TODO: Create the NetworkTool parent class (Step v)

class NetworkTool:
    def __init__(self, target):
        self.__target = target  # Private property

    # Q3: What is the benefit of using @property and @target.setter?
    # TODO: Your 2-4 sentence answer here... (Part 2, Q3)
    #   Using @property and a setter gives us control over how the target value is accessed and changed.
    #   Instead of letting anything directly modify it, we can validate it first (like preventing empty values).
    #   It also keeps the variable private while still letting us use it like a normal attribute.

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if value.strip() != "":
            self.__target = value
        else:
            print("Error: Target cannot be empty")

    def __del__(self):
        print("NetworkTool instance destroyed")



# Q1: How does PortScanner reuse code from NetworkTool?
# TODO: Your 2-4 sentence answer here... (Part 2, Q1)
#   PortScanner builds on NetworkTool instead of starting from scratch. It reuses the target handling,
#   including the getter/setter logic, by calling super().__init__(target). For example, when we access
#   self.target in PortScanner, we’re actually using the property defined in NetworkTool, so we don’t
#   have to rewrite validation or storage logic again.

# TODO: Create the PortScanner child class that inherits from NetworkTool (Step vi)
class PortScanner(NetworkTool):
    def __init__(self, target):
        # Step vi: Call parent constructor and initialize local properties
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()

# - scan_port(self, port):
    def scan_port(self, port):
#     Q4: What would happen without try-except here?
#     TODO: Your 2-4 sentence answer here... (Part 2, Q4)
#       Without the try-except block, any network issue (like a timeout or unreachable host) would crash the whole program.
#       That means even one bad port would stop the entire scan.
#       With exception handling, errors are caught and printed, and the scanner just keeps going with the rest of the ports.
        try:
            # Create a TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            # connect_ex returns 0 if the connection is successful (port is open)
            result = sock.connect_ex((self.target, port))

            status = "Open" if result == 0 else "Closed"
            service_name = common_ports.get(port, "Unknown")

            # Use lock to safely update the shared results list from different threads
            with self.lock:
                self.scan_results.append((port, status, service_name))
        except socket.error as e:
            print(f"Error scanning port {port}: {e}")
        finally:
            sock.close()

#
# - get_open_ports(self):
#     - Use list comprehension to return only "Open" results
    def get_open_ports(self):
        return [res for res in self.scan_results if res[1] == "Open"]
#
#     Q2: Why do we use threading instead of scanning one port at a time?
#     TODO: Your 2-4 sentence answer here... (Part 2, Q2)
#       Threading lets the scanner check a bunch of ports at the same time instead of waiting on each one.
#       Since each port can take up to 1 second to respond, scanning 1024 ports one-by-one would take a really long time.
#       With threads, everything runs in parallel, so the scan finishes much faster and feels more efficient.

    def scan_range(self, start_port, end_port):
        threads = []
        # Create and start threads
        for port in range(start_port, end_port + 1):
            t = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(t)
            t.start()

        # Join threads in a separate loop
        for t in threads:
            t.join()

# TODO: Create save_results(target, results) function (Step vii)
# - Connect to scan_history.db
# - CREATE TABLE IF NOT EXISTS scans (id, target, port, status, service, scan_date)
# - INSERT each result with datetime.datetime.now()
# - Commit, close
# - Wrap in try-except for sqlite3.Error
def save_results(target, results):
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            port INTEGER,
            status TEXT,
            service TEXT,
            scan_date TEXT
        )""")

        for port, status, service in results:
            cursor.execute("""INSERT INTO scans (target, port, status, service, scan_date) 
                              VALUES (?, ?, ?, ?, ?)""",
                           (target, port, status, service, str(datetime.datetime.now())))

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

# TODO: Create load_past_scans() function (Step viii)
# - Connect to scan_history.db
# - SELECT all from scans
# - Print each row in readable format
# - Handle missing table/db: print "No past scans found."
# - Close connection

def load_past_scans():
    try:
        if not os.path.exists("scan_history.db"):
            print("No past scans found.")
            return

        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()
        cursor.execute("SELECT scan_date, target, port, service, status FROM scans")
        rows = cursor.fetchall()

        if not rows:
            print("No past scans found.")
        else:
            for row in rows:
                print(f"[{row[0]}] {row[1]} : Port {row[2]} ({row[3]}) - {row[4]}")

        conn.close()
    except sqlite3.Error:
        print("No past scans found.")


# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":

    # TODO: Get user input with try-except (Step ix)
    # - Target IP (default "127.0.0.1" if empty)
    # - Start port (1-1024)
    # - End port (1-1024, >= start port)
    # - Catch ValueError: "Invalid input. Please enter a valid integer."
    # - Range check: "Port must be between 1 and 1024."
    try:
        # Get and validate user input
        target_ip = input("Enter target IP (Default 127.0.0.1): ") or "127.0.0.1"

        start_p = int(input("Enter start port (1-1024): "))
        end_p = int(input("Enter end port (1-1024): "))

        if not (1 <= start_p <= 1024 and 1 <= end_p <= 1024):
            print("Port must be between 1 and 1024.")
        elif end_p < start_p:
            print("End port must be greater than or equal to start port.")
            # TODO: After valid input (Step x)
            # - Create PortScanner object
            # - Print "Scanning {target} from port {start} to {end}..."
            # - Call scan_range()
            # - Call get_open_ports() and print results
            # - Print total open ports found
            # - Call save_results()
            # - Ask "Would you like to see past scan history? (yes/no): "
            # - If "yes", call load_past_scans()
        else:
            scanner = PortScanner(target_ip)
            print(f"Scanning {scanner.target} from port {start_p} to {end_p}...")

            scanner.scan_range(start_p, end_p)
            open_ports = scanner.get_open_ports()

            print(f"\n--- Scan Results for {scanner.target} ---")
            for p, stat, serv in open_ports:
                print(f"Port {p}: {stat} ({serv})")
            print("-" * 30)
            print(f"Total open ports found: {len(open_ports)}")

            save_results(scanner.target, scanner.scan_results)

            show_history = input("\nWould you like to see past scan history? (yes/no): ").lower()
            if show_history == "yes":
                load_past_scans()

    except ValueError:
        print("Invalid input. Please enter a valid integer.")





# Q5: New Feature Proposal
# TODO: Your 2-3 sentence description here... (Part 2, Q5)
#   I would add a "Service Filter" feature so users can quickly look for a specific service like HTTP.
#   This would use a list comprehension to go through scan_results by checking
#   the service index (result[2]) and return only the ones that match,
#   making it easier to find what we're looking for without scanning everything manually.
# Diagram: See diagram_101577665.png in the repository root
