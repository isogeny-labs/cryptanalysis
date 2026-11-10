"""cryptoscan: inventory and audit of cryptographic configuration across an environment.

Pure standard-library Python (3.9+).  The package discovers cryptographic
material and settings (SSH, TLS, X.509 / CA trust stores, Kerberos, network
device configurations, IPsec, local key files, system crypto policies), grades
each against a selectable policy profile (NIST SP 800-131A / IR 8547 transition
dates, CNSA 2.0, BSI TR-02102, a legacy-tolerant profile) and renders one
consolidated report (JSON, Markdown, HTML, CycloneDX CBOM).
"""

__version__ = "0.1.0"
