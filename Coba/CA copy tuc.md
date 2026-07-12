
 
# How to Add Commerzbank Internal CA Certificates to a Java Truststore

This guide documents the steps taken to fix the `SSLHandshakeException: PKIX path building failed` error
when the Spring Boot app tries to connect to internal Commerzbank endpoints (e.g. `tokenmanager-tuc.intranet.commerzbank.com`).

---

## Background

The Commerzbank internal servers use TLS certificates signed by an **internal CA chain**:

```
tokenmanager-tuc.intranet.commerzbank.com  (leaf / server cert)
└── CoBa PreTest Sub CA11               (intermediate CA)
       └── CoBa PreTest Root CA02        (root CA)
```

The JVM's default truststore (`cacerts`) only contains public CAs, so it cannot verify this chain.
The fix is to import **Sub CA11** and **Root CA02** into the target JDK's `cacerts`.

---

## Step 1 — Back up the original cacerts

Always make a backup before modifying the truststore.

```powershell
Copy-Item "C:\Program Files\Java\<YOUR-JDK>\lib\security\cacerts" `
         "C:\Program Files\Java\<YOUR-JDK>\lib\security\cacerts.backup_$(Get-Date -Format yyyyMMdd)"
```

Example (JDK 17):
```powershell
Copy-Item "C:\Program Files\Java\openjdk-17.0.16+8\lib\security\cacerts" `
         "C:\Program Files\Java\openjdk-17.0.16+8\lib\security\cacerts.backup_20260310"
```

---

## Step 2 — Download the CA certificates

The CA certificates are available from Commerzbank's internal AIA (Authority Information Access) URLs.
They are published in **DER (binary)** format.

```powershell
# Intermediate CA
Invoke-WebRequest -Uri "http://ca.commerzbank.com/aia/CoBaPreTestSubCA11.crt" `
                 -OutFile "CoBaPreTestSubCA11.crt" -UseBasicParsing

# Root CA
Invoke-WebRequest -Uri "http://ca.commerzbank.com/aia/CoBaPreTestRootCA02.crt" `
                 -OutFile "CoBaPreTestRootCA02.crt" -UseBasicParsing
```

> **Tip:** The AIA URL is embedded in any leaf certificate issued by Commerzbank.
> You can inspect it with:
> ```powershell
> certutil -dump tls.crt | Select-String "http"
> ```

---

## Step 3 — Convert DER to PEM

`keytool` cannot import DER binary files directly in some versions — convert them to PEM first using Windows `certutil`.

```powershell
certutil -encode CoBaPreTestSubCA11.crt CoBaPreTestSubCA11.pem
certutil -encode CoBaPreTestRootCA02.crt CoBaPreTestRootCA02.pem
```

Verify the conversion worked (should start with `-----BEGIN CERTIFICATE-----`):
```powershell
(Get-Content "CoBaPreTestSubCA11.pem")[0]
```

---

## Step 4 — Import the CA certificates into cacerts

Replace `<YOUR-JDK>` with the actual JDK folder. The default keystore password is `changeit`.

```powershell
# Import intermediate CA (Sub CA11)
& "C:\Program Files\Java\<YOUR-JDK>\bin\keytool.exe" `
   -importcert -noprompt `
   -alias "coba-pretest-sub-ca11" `
   -file "CoBaPreTestSubCA11.pem" `
   -keystore "C:\Program Files\Java\<YOUR-JDK>\lib\security\cacerts" `
   -storepass changeit

# Import root CA (Root CA02)
& "C:\Program Files\Java\<YOUR-JDK>\bin\keytool.exe" `
   -importcert -noprompt `
   -alias "coba-pretest-root-ca02" `
   -file "CoBaPreTestRootCA02.pem" `
   -keystore "C:\Program Files\Java\<YOUR-JDK>\lib\security\cacerts" `
   -storepass changeit
```

Expected output for each: `Certificate was added to keystore`

---

## Step 5 — Verify the certificates were imported

```powershell
& "C:\Program Files\Java\<YOUR-JDK>\bin\keytool.exe" `
   -list `
   -alias "coba-pretest-sub-ca11" `
   -keystore "C:\Program Files\Java\<YOUR-JDK>\lib\security\cacerts" `
   -storepass changeit

& "C:\Program Files\Java\<YOUR-JDK>\bin\keytool.exe" `
   -list `
   -alias "coba-pretest-root-ca02" `
   -keystore "C:\Program Files\Java\<YOUR-JDK>\lib\security\cacerts" `
   -storepass changeit
```

Expected output (one line per alias):
```
coba-pretest-sub-ca11, Mar 10, 2026, trustedCertEntry, Certificate fingerprint (SHA-256): 2A:70:...
coba-pretest-root-ca02, Mar 10, 2026, trustedCertEntry, Certificate fingerprint (SHA-256): C9:08:...
```

---

## Step 6 — Restart your application

The JVM loads the truststore **once at startup**. You must fully restart the Spring Boot application
after importing the certificates.

---

## Quick reference — all JDKs in C:\Program Files\Java

Run this to see all installed JDKs:
```powershell
Get-ChildItem "C:\Program Files\Java\" | Select-Object Name
```

To apply to **all** JDKs at once (PowerShell loop):
```powershell
$certs = @(
   @{ alias = "coba-pretest-sub-ca11"; file = "C:\CCB\sources\ccs.a2.tax\CoBaPreTestSubCA11.pem" },
   @{ alias = "coba-pretest-root-ca02"; file = "C:\CCB\sources\ccs.a2.tax\CoBaPreTestRootCA02.pem" }
)

Get-ChildItem "C:\Program Files\Java\" | ForEach-Object {
   $jdk = $_.FullName
   $keytool = "$jdk\bin\keytool.exe"
   $cacerts  = "$jdk\lib\security\cacerts"

   if (-not (Test-Path $keytool)) { Write-Host "Skipping $jdk (no keytool)"; return }

   Write-Host "`n=== Processing $jdk ===" -ForegroundColor Cyan

   foreach ($cert in $certs) {
       & $keytool -importcert -noprompt `
           -alias $cert.alias `
           -file  $cert.file `
           -keystore $cacerts `
           -storepass changeit 2>&1 | Write-Host
   }
}
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Certificate not imported, alias already exists` | Alias already present | Delete first: `keytool -delete -alias <alias> -keystore cacerts -storepass changeit`, then re-import |
| `SSLHandshakeException` still occurs after import | App is still running with the old JVM | Restart the application |
| `SSLHandshakeException` still occurs after restart | Wrong JDK — check which Java the app uses | Run `where.exe java` or check IntelliJ SDK settings (File → Project Structure → SDK) |
| `keytool error: Keystore was tampered with` | Wrong storepass | Default password is `changeit` |

---

## Certificate fingerprints (for verification)

| Certificate | SHA-256 Fingerprint |
|---|---|
| CoBa PreTest Sub CA11 | `2A:70:F8:49:D1:4E:87:00:B1:D1:94:B2:4C:17:23:22:BD:59:81:F9:E2:3A:0A:3A:BF:98:2F:CE:CC:5B:C6:13` |
| CoBa PreTest Root CA02 | `C9:08:69:D2:0D:EF:EA:F9:A9:5E:DE:96:90:FE:CF:A4:91:CC:50:16:1D:2C:64:F4:82:E1:D9:31:FC:69:0F:F7` |

 
 
