#!/usr/bin/env python3
import socket
from urllib.parse import urlparse

def is_safe_url(url):
    """
    Validates if a URL is safe to fetch (prevents SSRF to localhost/private networks).
    Uses python standard library only.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
            
        hostname = parsed.hostname
        if not hostname:
            return False
            
        # Resolve hostname to IP address
        ip = socket.gethostbyname(hostname)
        parts = list(map(int, ip.split('.')))
        
        # Check for loopback and private networks
        if parts[0] == 127: # 127.0.0.0/8
            return False
        if parts[0] == 10:  # 10.0.0.0/8
            return False
        if parts[0] == 172 and (16 <= parts[1] <= 31): # 172.16.0.0/12
            return False
        if parts[0] == 192 and parts[1] == 168: # 192.168.0.0/16
            return False
        if parts[0] == 169 and parts[1] == 254: # 169.254.0.0/16 (Link-local)
            return False
            
        return True
    except Exception:
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        print(f"URL: {test_url} - Safe: {is_safe_url(test_url)}")
