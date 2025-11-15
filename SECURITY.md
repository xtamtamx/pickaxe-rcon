# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email the maintainer directly (or use GitHub Security Advisories)
3. Include details about the vulnerability and steps to reproduce
4. Allow reasonable time for a fix before public disclosure

## Security Best Practices

### For Users

#### 1. Authentication
- ✅ **DO** use strong, unique passwords for the admin panel
- ✅ **DO** change default credentials immediately after setup
- ✅ **DO** use a password manager to generate secure passwords
- ❌ **DON'T** share admin credentials
- ❌ **DON'T** use the same password across multiple services

#### 2. Network Security
- ✅ **DO** use HTTPS in production (via reverse proxy)
- ✅ **DO** restrict access to admin panel port with firewall rules
- ✅ **DO** use VPN or SSH tunneling for remote access
- ❌ **DON'T** expose the admin panel directly to the internet
- ❌ **DON'T** use HTTP for production deployments

#### 3. SSH Keys
- ✅ **DO** use SSH key-based authentication
- ✅ **DO** protect private keys with appropriate permissions (chmod 600)
- ✅ **DO** use strong passphrases for SSH keys
- ❌ **DON'T** commit private keys to version control
- ❌ **DON'T** share private keys

#### 4. Environment Variables
- ✅ **DO** use strong, random values for SECRET_KEY
- ✅ **DO** keep .env files out of version control
- ✅ **DO** use different credentials for development and production
- ❌ **DON'T** hardcode secrets in source code
- ❌ **DON'T** commit .env files to Git

#### 5. Docker Security
- ✅ **DO** keep Docker and images up to date
- ✅ **DO** run containers with least privilege
- ✅ **DO** scan images for vulnerabilities
- ❌ **DON'T** run containers as root when possible
- ❌ **DON'T** mount unnecessary host paths

### For Developers

#### 1. Input Validation
- All user input is validated and sanitized
- Command injection is prevented using `shlex.quote()`
- Path traversal attacks are prevented with filename validation
- SQL injection is N/A (no database used)

#### 2. Authentication
- Flask-Login manages user sessions securely
- Passwords are never logged
- Sessions expire appropriately
- Login is required for all admin endpoints

#### 3. File Access
- Backup operations validate filenames
- Path traversal is prevented
- File permissions are checked
- Only specific directories are accessible

#### 4. Command Execution
- Commands are sanitized before execution
- SSH commands use parameterized execution
- Shell injection is prevented
- Output is properly escaped

## Known Security Considerations

### 1. Docker Socket Access
The admin panel requires access to the Docker socket (`/var/run/docker.sock`) to manage containers. This provides significant privileges:

- **Risk**: Container can control Docker daemon
- **Mitigation**: Run panel in isolated environment, restrict network access
- **Alternative**: Use Docker socket proxy with limited permissions

### 2. SSH Key Storage
SSH private keys are mounted into the container for remote server access:

- **Risk**: Keys accessible within container
- **Mitigation**: Use read-only mounts, restrict key permissions
- **Alternative**: Use SSH agent forwarding

### 3. Development Server
The built-in Flask server is not suitable for production:

- **Risk**: Performance and security limitations
- **Mitigation**: Use production WSGI server (Gunicorn, uWSGI)
- **Alternative**: Deploy behind reverse proxy (nginx, Caddy)

### 4. Session Management
Flask sessions are signed but not encrypted:

- **Risk**: Session data readable if secret key is compromised
- **Mitigation**: Use strong SECRET_KEY, rotate periodically
- **Alternative**: Use Flask-Session with Redis backend

## Security Checklist

Before deploying to production:

- [ ] Changed default admin credentials
- [ ] Generated strong SECRET_KEY
- [ ] Configured HTTPS with valid SSL certificate
- [ ] Set up firewall rules
- [ ] Configured SSH key-based authentication
- [ ] Reviewed and secured environment variables
- [ ] Tested authentication and authorization
- [ ] Enabled logging and monitoring
- [ ] Created regular backup schedule
- [ ] Documented emergency procedures

## Compliance

This software:
- ✅ Does not collect or transmit user data
- ✅ Does not include telemetry or analytics
- ✅ Stores configuration locally only
- ✅ Uses industry-standard security practices
- ✅ Provides clear security documentation

## Updates and Patches

- Security updates are released as soon as possible
- Critical vulnerabilities are patched within 48 hours
- Users are notified via GitHub releases
- Changelogs include security fix details

## Auditing

The codebase is open source and available for security review:

1. No obfuscated code
2. Clear separation of concerns
3. Minimal dependencies
4. Well-documented functions
5. Security-focused code comments

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Flask Security](https://flask.palletsprojects.com/en/2.3.x/security/)
- [SSH Key Management](https://www.ssh.com/academy/ssh/key)

## Version History

Track security-related changes in [CHANGELOG.md](CHANGELOG.md)

---

Last Updated: 2025-11-14
