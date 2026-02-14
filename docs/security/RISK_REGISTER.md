# GASTROTECH RISK REGISTER
## Security Vulnerability Assessment

**Generated:** 2026-01-24
**Auditor:** Principal Application Security Engineer
**Methodology:** STRIDE + OWASP Top 10 + CWE

---

## EXECUTIVE SUMMARY

| Severity | Count | Status |
|----------|-------|--------|
| **CRITICAL** | 3 | Requires immediate fix |
| **HIGH** | 6 | Fix before production |
| **MEDIUM** | 8 | Fix in next sprint |
| **LOW** | 5 | Track and monitor |

**Overall Assessment:** The codebase has a solid security foundation with proper JWT authentication, role-based access control, rate limiting, and security headers in production settings. However, several critical and high-severity issues must be addressed before production deployment.

---

## CRITICAL FINDINGS

### SEC-BE-001: JWT Tokens Stored in localStorage (XSS Vulnerable)

| Field | Value |
|-------|-------|
| **Severity** | CRITICAL |
| **Component** | frontend/admin/src/lib/api/token-store.ts |
| **Line** | 18-20, 34-40 |
| **CWE** | CWE-922 (Insecure Storage of Sensitive Information) |
| **CVSS** | 8.1 |

**Description:**
JWT access and refresh tokens are stored in browser localStorage, which is accessible to any JavaScript running on the page. If an XSS vulnerability exists anywhere in the application, an attacker can steal these tokens.

**Exploit Scenario:**
1. Attacker injects malicious script via stored XSS (e.g., product description)
2. Script reads `localStorage.getItem('gastrotech_access_token')`
3. Token is exfiltrated to attacker's server
4. Attacker impersonates admin user

**Current Code:**
```typescript
// token-store.ts:34-40
setTokens(access: string, refresh: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, access);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  ...
}
```

**Recommended Fix:**
Migrate to httpOnly cookies with CSRF protection:
```python
# Backend: Set tokens as httpOnly cookies
response.set_cookie(
    'access_token',
    token,
    httponly=True,
    secure=True,  # HTTPS only
    samesite='Lax',
    max_age=1800  # 30 minutes
)
```

**Verification:**
```bash
# After fix, verify tokens are not in localStorage
# Open browser DevTools > Application > Local Storage
# Should not contain gastrotech_access_token or gastrotech_refresh_token
```

**References:**
- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [CWE-922](https://cwe.mitre.org/data/definitions/922.html)

---

### SEC-BE-002: .env File Committed to Repository

| Field | Value |
|-------|-------|
| **Severity** | CRITICAL |
| **Component** | backend/.env |
| **Line** | 1-11 |
| **CWE** | CWE-798 (Use of Hard-coded Credentials) |
| **CVSS** | 9.1 |

**Description:**
The `.env` file containing development credentials is tracked in git. While these are development credentials, this practice can lead to accidental production secret exposure.

**Current State:**
```bash
# .env file contains:
DJANGO_SECRET_KEY=dev-secret-key-change-in-production-12345
DATABASE_URL=postgres://postgres:postgres@localhost:5432/gastrotech
```

**Recommended Fix:**
1. Add `.env` to `.gitignore`
2. Remove from git history: `git filter-branch --index-filter "git rm --cached --ignore-unmatch backend/.env" HEAD`
3. Rotate all secrets that may have been exposed
4. Use `.env.example` with placeholder values only

**Verification:**
```bash
git ls-files | grep -E "\.env$"
# Should return empty
```

**References:**
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

### SEC-BE-003: No Login Rate Limiting on Authentication Endpoint

| Field | Value |
|-------|-------|
| **Severity** | CRITICAL |
| **Component** | backend/apps/accounts/views.py |
| **Line** | 29-50 |
| **CWE** | CWE-307 (Improper Restriction of Excessive Authentication Attempts) |
| **CVSS** | 7.5 |

**Description:**
The `EmailTokenObtainPairView` does not have specific rate limiting beyond the global throttle. The global rate of 60/min for anonymous users is too permissive for authentication endpoints.

**Current Code:**
```python
class EmailTokenObtainPairView(APIView):
    permission_classes = [AllowAny]
    # No throttle_classes defined - uses global 60/min
```

**Recommended Fix:**
```python
from rest_framework.throttling import AnonRateThrottle

class LoginThrottle(AnonRateThrottle):
    rate = "5/minute"  # 5 attempts per minute per IP

class LoginBurstThrottle(AnonRateThrottle):
    rate = "20/hour"   # 20 attempts per hour per IP

class EmailTokenObtainPairView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle, LoginBurstThrottle]
```

**Verification:**
```bash
# Attempt 6+ logins in 1 minute
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
done
# Should receive 429 Too Many Requests after 5 attempts
```

**References:**
- [OWASP Brute Force Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html#protect-against-automated-attacks)

---

## HIGH FINDINGS

### SEC-BE-004: Django Admin Exposed Without Additional Protection

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Component** | backend/config/urls.py:13 |
| **CWE** | CWE-306 (Missing Authentication for Critical Function) |
| **CVSS** | 6.5 |

**Description:**
Django admin (`/admin/`) is exposed on the same domain without IP restriction, 2FA, or additional authentication layer. Brute force attacks on Django admin could compromise the entire system.

**Recommended Fix:**
1. Add admin-specific rate limiting
2. Consider IP allowlisting for admin panel
3. Implement django-two-factor-auth for admin users

```python
# urls.py - Add admin honeypot or restrict access
from django.conf import settings

urlpatterns = [
    # Consider moving admin to a non-standard path
    path("gastro-mgmt-panel/", admin.site.urls),  # Obscure admin URL
    ...
]
```

**References:**
- [Django Admin Security](https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#module-django.contrib.admin)

---

### SEC-BE-005: Missing IDOR Protection on Cart Item Operations

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Component** | backend/apps/orders/views.py |
| **Line** | 494-556 (CartItemDetailView) |
| **CWE** | CWE-639 (Authorization Bypass Through User-Controlled Key) |
| **CVSS** | 6.1 |

**Description:**
Cart item operations use UUID from path parameter without verifying the item belongs to the user's cart. While the current implementation resolves cart by token/user first, then checks item ownership implicitly, explicit verification is recommended.

**Current Flow:**
```python
def patch(self, request, item_id):
    cart = CartService.resolve_cart(user=user, cart_token=cart_token, ...)
    # item_id from URL is used directly - CartService.set_item_quantity
    # should verify item belongs to cart
```

**Recommended Enhancement:**
Explicitly verify item ownership in CartService:
```python
def set_item_quantity(cart, item_id, quantity):
    item = CartItem.objects.filter(cart=cart, id=item_id).first()
    if not item:
        raise CartItemNotFoundError("Item not found in your cart")
    # ... continue
```

**Verification:**
```bash
# Get cart A's item ID, try to modify with cart B's token
# Should return 404, not modify the item
```

---

### SEC-BE-006: OpenAPI/Swagger Docs Exposed in Production

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Component** | backend/apps/api/v1/urls.py |
| **Line** | 46-51 |
| **CWE** | CWE-200 (Exposure of Sensitive Information) |
| **CVSS** | 5.3 |

**Description:**
API documentation (`/api/v1/docs/` and `/api/v1/schema/`) is available without authentication. This exposes full API structure to potential attackers.

**Recommended Fix:**
```python
# In production settings, disable or protect docs
if not settings.DEBUG:
    # Option 1: Remove docs entirely
    # Option 2: Add authentication
    from rest_framework.permissions import IsAdminUser

    urlpatterns += [
        path("docs/",
             permission_classes=[IsAdminUser],
             SpectacularSwaggerView.as_view(url_name="api_v1:schema")),
    ]
```

---

### SEC-BE-007: Missing Security Headers in Next.js Responses

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Component** | frontend/public/next.config.ts, frontend/admin/next.config.ts |
| **CWE** | CWE-693 (Protection Mechanism Failure) |
| **CVSS** | 5.0 |

**Description:**
Next.js applications do not configure security headers. While Nginx adds headers, direct access to Next.js ports would bypass these protections.

**Recommended Fix:**
Add headers to `next.config.ts`:
```typescript
const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
          },
        ],
      },
    ];
  },
  // ... rest of config
};
```

---

### SEC-BE-008: No Account Lockout Mechanism

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Component** | backend/apps/accounts/ |
| **CWE** | CWE-307 (Improper Restriction of Excessive Authentication Attempts) |
| **CVSS** | 6.5 |

**Description:**
No mechanism exists to lock accounts after repeated failed login attempts. Combined with weak rate limiting, this enables sustained credential stuffing attacks.

**Recommended Fix:**
Implement django-axes or custom lockout:
```python
# requirements.txt
django-axes==6.0.0

# settings.py
INSTALLED_APPS += ['axes']
MIDDLEWARE += ['axes.middleware.AxesMiddleware']
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_TEMPLATE = 'account_locked.html'
```

---

### SEC-BE-009: Missing Input Validation on Import Endpoints

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Component** | backend/apps/ops/ (inferred from management commands) |
| **CWE** | CWE-20 (Improper Input Validation) |
| **CVSS** | 7.2 |

**Description:**
Bulk import functionality processes Excel files. Without proper validation, malicious files could cause:
- Formula injection (CSV injection)
- Resource exhaustion (extremely large files)
- Path traversal via filenames

**Recommended Fix:**
```python
# Import validation
MAX_IMPORT_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = ['.xlsx', '.xls']

def validate_import_file(uploaded_file):
    # Size check
    if uploaded_file.size > MAX_IMPORT_SIZE:
        raise ValidationError("File too large")

    # Extension check
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError("Invalid file type")

    # Content validation - prevent formula injection
    # Strip leading = + - @ from cell values
```

---

## MEDIUM FINDINGS

### SEC-BE-010: Debug Logging May Expose Sensitive Data

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Component** | backend/config/settings/base.py:309 |
| **CWE** | CWE-532 (Information Exposure Through Log Files) |

**Description:**
The `apps` logger is set to DEBUG level, which may log sensitive information like request bodies containing passwords or tokens.

**Recommended Fix:**
```python
# In base.py
"apps": {
    "handlers": ["console"],
    "level": env("APPS_LOG_LEVEL", default="INFO"),  # Allow override
    "propagate": False,
},

# In prod.py
LOGGING["loggers"]["apps"]["level"] = "INFO"
```

---

### SEC-BE-011: No CSRF Protection for API Endpoints

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Component** | REST Framework Configuration |
| **CWE** | CWE-352 (Cross-Site Request Forgery) |

**Description:**
DRF uses JWT authentication which exempts endpoints from CSRF protection. For browser-based admin panel, this could be exploited if combined with token theft.

**Mitigation:**
Current JWT implementation is acceptable, but if migrating to cookie-based tokens, CSRF must be re-enabled.

---

### SEC-BE-012: Missing Referrer-Policy Header

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Component** | backend/config/settings/prod.py |
| **CWE** | CWE-200 |

**Description:**
`SECURE_REFERRER_POLICY` is not set in Django settings. While Nginx adds this header, Django should also set it for defense in depth.

**Recommended Fix:**
```python
# prod.py
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
```

---

### SEC-BE-013: Cart Token Predictability

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Component** | backend/apps/orders/models.py |
| **CWE** | CWE-330 (Use of Insufficiently Random Values) |

**Description:**
Cart tokens use UUID4 which is cryptographically random. However, token validation does not include timing-safe comparison, potentially enabling timing attacks.

**Recommended Fix:**
Use `secrets.compare_digest` for token comparison in performance-critical paths.

---

### SEC-BE-014: No Content-Security-Policy Header

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Component** | backend/docker/nginx/nginx.conf |
| **CWE** | CWE-693 |

**Description:**
CSP header is not configured, leaving the application vulnerable to XSS attacks even with output encoding.

**Recommended Fix:**
```nginx
# nginx.conf
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.gastrotech.com; frame-ancestors 'none';" always;
```

---

### SEC-BE-015: Password Reset Not Implemented

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Component** | backend/apps/accounts/ |
| **CWE** | CWE-640 (Weak Password Recovery Mechanism) |

**Description:**
No password reset functionality exists. Users cannot recover accounts if they forget passwords.

**Recommendation:** Implement secure password reset with:
- Time-limited tokens (1 hour)
- Single-use tokens
- Rate limiting on reset requests

---

### SEC-BE-016: Inquiry Endpoint Spam Protection Insufficient

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Component** | backend/apps/inquiries/views.py:23-26 |
| **CWE** | CWE-770 (Allocation of Resources Without Limits) |

**Description:**
While rate limiting exists (20/hour), there's no CAPTCHA or honeypot validation. Distributed attacks could bypass IP-based limits.

**Current State:**
```python
class InquiryThrottle(AnonRateThrottle):
    rate = "20/hour"
```

**Recommended Enhancement:**
Add honeypot field validation:
```python
def validate_honeypot(self, data):
    # If honeypot field is filled, it's likely a bot
    if data.get('website'):  # Hidden honeypot field
        raise serializers.ValidationError("Invalid submission")
```

---

### SEC-BE-017: Missing Subresource Integrity (SRI)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Component** | Frontend static assets |
| **CWE** | CWE-353 |

**Description:**
External CDN resources (if any) should use SRI hashes to prevent tampering.

**Recommendation:** Next.js bundled assets are self-hosted, which is secure. If external CDNs are added, implement SRI.

---

## LOW FINDINGS

### SEC-BE-018: Verbose Error Messages in Development

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Component** | backend/config/settings/dev.py |
| **CWE** | CWE-209 |

**Description:**
Development settings show detailed error messages. Ensure prod settings are always used in production.

**Verification:**
```bash
# In production
curl http://api.gastrotech.com/api/v1/nonexistent/
# Should return generic 404, not stack trace
```

---

### SEC-BE-019: No Audit Logging for Admin Actions

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Component** | backend/apps/ops/ |
| **CWE** | CWE-778 |

**Description:**
Admin CRUD operations are not logged to an audit trail. This makes incident investigation difficult.

**Recommendation:** Implement django-auditlog or custom middleware.

---

### SEC-BE-020: Cookie SameSite Attribute Not Explicitly Set

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Component** | backend/config/settings/base.py |
| **CWE** | CWE-1275 |

**Description:**
`SESSION_COOKIE_SAMESITE` is not explicitly set (defaults to 'Lax' in Django 4+).

**Recommended Fix:**
```python
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
```

---

### SEC-BE-021: No Permissions-Policy Header

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Component** | Security headers |
| **CWE** | CWE-693 |

**Description:**
Permissions-Policy (formerly Feature-Policy) is not set, allowing features like camera/microphone access by default.

**Recommended Fix:**
```nginx
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
```

---

### SEC-BE-022: Source Maps May Be Exposed

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Component** | frontend/*/next.config.ts |

**Description:**
Next.js may generate source maps that could be accessed in production, exposing source code.

**Recommended Fix:**
```typescript
const nextConfig: NextConfig = {
  productionBrowserSourceMaps: false,  // Disable in production
  // ...
};
```

---

## THREAT MODEL SUMMARY (STRIDE)

| Threat | Applicable | Risk | Mitigation Status |
|--------|-----------|------|-------------------|
| **S**poofing | Yes | HIGH | JWT auth implemented, needs httpOnly cookies |
| **T**ampering | Yes | MEDIUM | HTTPS enforced, integrity checks needed |
| **R**epudiation | Yes | LOW | Audit logging not implemented |
| **I**nformation Disclosure | Yes | HIGH | Debug mode risks, CSP missing |
| **D**enial of Service | Yes | MEDIUM | Rate limiting implemented |
| **E**levation of Privilege | Yes | MEDIUM | RBAC implemented, IDOR checks needed |

---

## ACCEPTANCE CRITERIA FOR PRODUCTION

### Must Fix (Blocking)
- [ ] SEC-BE-001: Migrate JWT to httpOnly cookies OR implement robust CSP
- [ ] SEC-BE-002: Remove .env from git, rotate secrets
- [ ] SEC-BE-003: Implement login rate limiting (5/min)

### Should Fix (Pre-Production)
- [ ] SEC-BE-004: Secure Django admin
- [ ] SEC-BE-005: Verify IDOR protection
- [ ] SEC-BE-006: Protect API docs
- [ ] SEC-BE-007: Add Next.js security headers
- [ ] SEC-BE-008: Implement account lockout
- [ ] SEC-BE-009: Validate import files

### Can Defer (Post-Launch)
- [ ] SEC-BE-010 through SEC-BE-022: Medium/Low priority items

---

**Next Document:** BACKEND_SECURITY_REPORT.md - Detailed patches and implementation
