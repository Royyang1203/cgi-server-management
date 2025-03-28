import ldap3
import ssl

LDAP_SERVER = 'ldaps://nas-511.cgilab.nctu.edu.tw'  # 注意使用 ldaps (因有 SSL/TLS)
BASE_DN = 'dc=cgilab,dc=nctu,dc=edu,dc=tw'

def find_user_dn(server, username):
    """搜索用戶的實際 DN"""
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
        # 嘗試匿名綁定
        conn = ldap3.Connection(server, authentication=ldap3.ANONYMOUS)
        if not conn.bind():
            print("Anonymous bind failed, trying with a search account...")
            return None
            
        # 嘗試不同的搜索基礎和過濾器
        for base in search_bases:
            print(f"\nSearching in base: {base}")
            for search_filter in search_filters:
                print(f"Using filter: {search_filter}")
                if conn.search(base, search_filter, attributes=['*']):
                    if len(conn.entries) > 0:
                        user_dn = conn.entries[0].entry_dn
                        print(f"Found user DN: {user_dn}")
                        print(f"User attributes: {conn.entries[0]}")
                        return user_dn
        return None
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return None
    finally:
        if conn.bound:
            conn.unbind()

def ldap_authenticate(username, password):
    # 移除可能的郵件域名部分
    if '@' in username:
        username = username.split('@')[0]

    # 使用正確的 DN 結構
    user_dn = f"uid={username},cn=users,{BASE_DN}"
    
    try:
        print(f"Attempting to authenticate with DN: {user_dn}")
        tls_config = ldap3.Tls(validate=ssl.CERT_NONE)
        server = ldap3.Server(LDAP_SERVER, use_ssl=True, tls=tls_config, get_info=ldap3.ALL)
        conn = ldap3.Connection(
            server,
            user=user_dn,
            password=password,
            authentication=ldap3.SIMPLE
        )
        
        if conn.bind():
            print("Bind successful!")
            # 獲取用戶信息
            conn.search(user_dn, '(objectclass=*)', attributes=['*'])
            if conn.entries:
                user_info = conn.entries[0]
                print(f"\nUser Information:")
                print(f"Display Name: {user_info.displayName.value}")
                print(f"Email: {user_info.mail.value}")
                if hasattr(user_info, 'gecos'):
                    print(f"Full Name: {user_info.gecos.value}")
            conn.unbind()
            return True
        else:
            print(f"Authentication failed. Result: {conn.result}")
            return False
            
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
        return False

if __name__ == "__main__":
    print("Enter your username (if using email, only the part before @)")
    username = input("Username: ")
    password = input("Password: ")
    
    result = ldap_authenticate(username, password)
    
    if result:
        print("\nAuthentication successful! (認證成功！)")
    else:
        print("\nAuthentication failed. (認證失敗。)")