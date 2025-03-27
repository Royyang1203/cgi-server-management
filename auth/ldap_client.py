import ldap3
import ssl
import logging

# Configure logging
logger = logging.getLogger(__name__)

# LDAP server configuration
LDAP_SERVER = 'ldaps://nas-511.cgilab.nctu.edu.tw'
BASE_DN = 'dc=cgilab,dc=nctu,dc=edu,dc=tw'

def ldap_authenticate(username, password):
    """
    Authenticate user against LDAP server
    
    Args:
        username (str): Username (without domain)
        password (str): User's password
    
    Returns:
        bool: True if authentication successful, False otherwise
    """
    try:
        # Remove email domain if present
        if '@' in username:
            username = username.split('@')[0]

        # Construct user DN
        user_dn = f"uid={username},cn=users,{BASE_DN}"
        
        logger.info(f"Attempting LDAP authentication for user: {username}")
        
        # Configure TLS
        tls_config = ldap3.Tls(validate=ssl.CERT_NONE)
        server = ldap3.Server(
            LDAP_SERVER,
            use_ssl=True,
            tls=tls_config,
            get_info=ldap3.ALL
        )
        
        # Attempt to bind with user credentials
        conn = ldap3.Connection(
            server,
            user=user_dn,
            password=password,
            authentication=ldap3.SIMPLE
        )
        
        if conn.bind():
            logger.info(f"Authentication successful for user: {username}")
            
            # Get user information
            conn.search(user_dn, '(objectclass=*)', attributes=['*'])
            if conn.entries:
                user_info = conn.entries[0]
                logger.info(f"User info retrieved: {user_info.entry_dn}")
            
            conn.unbind()
            return True
        else:
            logger.warning(f"Authentication failed for user: {username}")
            logger.debug(f"LDAP result: {conn.result}")
            return False
            
    except Exception as e:
        logger.error(f"LDAP authentication error: {str(e)}")
        return False

def find_user_dn(username):
    """
    Find user's DN in LDAP directory
    
    Args:
        username (str): Username to search for
    
    Returns:
        str: User's DN if found, None otherwise
    """
    search_bases = [
        f"ou=People,{BASE_DN}",
        f"ou=users,{BASE_DN}",
        BASE_DN
    ]
    
    search_filters = [
        f"(uid={username})",
        f"(mail={username})",
        f"(&(objectClass=person)(uid={username}))",
        f"(&(objectClass=person)(mail={username}))"
    ]
    
    try:
        tls_config = ldap3.Tls(validate=ssl.CERT_NONE)
        server = ldap3.Server(LDAP_SERVER, use_ssl=True, tls=tls_config)
        
        # Try anonymous bind
        conn = ldap3.Connection(server, authentication=ldap3.ANONYMOUS)
        if not conn.bind():
            logger.warning("Anonymous bind failed")
            return None
            
        # Try different search bases and filters
        for base in search_bases:
            logger.debug(f"Searching in base: {base}")
            for search_filter in search_filters:
                logger.debug(f"Using filter: {search_filter}")
                if conn.search(base, search_filter, attributes=['*']):
                    if len(conn.entries) > 0:
                        user_dn = conn.entries[0].entry_dn
                        logger.info(f"Found user DN: {user_dn}")
                        return user_dn
        
        logger.warning(f"No user DN found for username: {username}")
        return None
        
    except Exception as e:
        logger.error(f"Error during DN search: {str(e)}")
        return None
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind() 