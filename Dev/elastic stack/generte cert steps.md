To set up TLS between Filebeat and Logstash without client authentication, follow these steps:

### **1. Generate a Logstash Private Key and Certificate Signing Request (CSR)**
Use OpenSSL to create a private key and CSR for Logstash.

```sh
openssl req -new -nodes -newkey rsa:4096 -keyout logstash-tuc.key -out logstash-tuc.csr -config logstash-tuc.cnf
```

- `-newkey rsa:4096`: Creates a 4096-bit RSA private key.
- `-nodes`: Prevents encrypting the private key with a passphrase.
- `-keyout logstash.key`: The private key file.
- `-out logstash.csr`: The CSR file.
- 
#### output

- **logstash-tuc.key**: This is the private key file used for encrypting the connection.
- **logstash-tuc.csr**: This is the Certificate Signing Request (CSR), which contains the information you want in the certificate (excluding the private key). It will be sent to a Certificate Authority (CA) for signing or used with a self-signed CA.

---

### **2. Create a Self-Signed CA (If Not Using a Trusted CA)**
If you don’t have a CA, generate one:

```sh
openssl req -new -x509 -days 365 -nodes -keyout ca.key -out ca.pem -config ca.cnf
```
#### Generating the CA:

You create a CA with ca.key (the private key) and ca.pem (the public certificate).
The ca.key is kept secure and used to sign other certificates.
The ca.pem is distributed to any service that needs to verify your certificates, such as Filebeat.

#### Signing the Logstash Certificate:

You create a CSR for Logstash (logstash-tuc.csr), and then use ca.key to sign the CSR and produce logstash-tuc.crt (Logstash’s signed certificate).
Filebeat will receive logstash-tuc.crt and verify it using ca.pem, ensuring that it’s from a trusted source.
---

### **3. Sign Logstash CSR with the CA**
Use the CA to generate a Logstash certificate (`logstash.crt`).

```sh
openssl x509 -req -in logstash-tuc.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out logstash-tuc.crt -days 365 -extfile logstash-tuc.cnf -extensions req_cert_extensions
```

#### output

- **logstash-tuc.crt**: This is the Logstash certificate file that is signed by your CA. This certificate is used by Logstash to establish a secure TLS connection with clients (like Filebeat). The .crt extension is typically used for certificate files.

*Verify the Certificate: After generating the certificate (logstash-tuc.pem), check that the SAN is correctly included in the certificate by running:*

```text
openssl x509 -in logstash-tuc.crt -text -noout
```

```sh
 ...
 X509v3 extensions:
            X509v3 Subject Alternative Name:
                DNS:logstash.015566-vopf01-tuc.svc.cluster.local, DNS:logstash.015566-vopf02-tuc.svc.cluster.local, DNS:logstash.015566-vopf03-tuc.svc.cluster.local
            X509v3 Subject Key Identifier:
                52:88:2C:49:2E:F0:27:B0:59:DB:E1:
                
                ...
```

---

### **4. Configure Logstash for TLS**
Modify `logstash.conf` to enable TLS:

```sh
base64 -w 0 logstash-tuc.crt
```

```sh
base64 -w 0 logstash-tuc.key
```
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: logstash-tls-secret
type: Opaque
data:
  logstash-tuc.crt: <base64_encoded_logstash_cert>
  logstash-tuc.key: <base64_encoded_logstash_key>

```
update `logstash-secret.yml` with the bas64 crt and key

then update configs

```plaintext
input {
  beats {
    port => 5044
    ssl => true
    ssl_certificate => "/usr/share/logstash/tls/input-beats-cert.crt"
    ssl_key => "/usr/share/logstash/tls/input-beats-cert.key"
  }
}

output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
  }
}
```

---

### **5. Configure Filebeat to Trust Logstash’s Certificate**

update `filebeat-tls-secret.yml` with the bas64 ca
```sh
base64 -w 0 ca.pem
```
Modify `filebeat.yml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: filebeat-tls-secret
type: Opaque
data:
  logstash-ca.pem: <base64_encoded_ca_cert>

```

```yaml
output.logstash:
  hosts: ["logstash:5044"]
  ssl.certificate_authorities: ["/usr/share/filebeat/tls/logstash-ca.pem"]
```

This ensures Filebeat trusts Logstash’s certificate but doesn’t enforce client authentication.

## Debugging 

### Verify the Full Certificate Chain
   Ensure that the Logstash certificate (logstash-tuc.crt) includes the full certificate chain, especially if intermediate certificates are used. If it’s self-signed, the CA certificate should be included in the chain.

```shell
openssl verify -CAfile ca.pem logstash-tuc.crt

```

This should return logstash-tuc.crt: OK if the certificate is valid. 

should match if it's self-signed: The issuer and subject fields of the certificate (logstash-tuc.crt) show that the certificate is issued to and by the same entity (self-signed). This confirms that the certificate is self-signed, which is expected in your case since you're using ca.pem to sign it.


---

## **Requesting Certificate Signing for Logstash**  

### **Case 1: Generating CSR and Sending to CA for Signing**  
1. **Generate private key and CSR:**  
   - Use a configuration file (`logstash-tuc.cnf`) that includes SANs.  
   - Run:  
     ```sh
     openssl req -new -key logstash-tuc.key -out logstash-tuc.csr -config logstash-tuc.cnf
     ```
2. **Send to CA Owner:**  
   - `logstash-tuc.csr`  
   - **List of SANs** (if not included in the CSR explicitly)  
3. **CA Signs the CSR and returns the signed certificate (`logstash-tuc.crt`).**  
4. **Use the received certificate (`logstash-tuc.crt`) along with `logstash-tuc.key`.**  

**Pros:**  
- The private key (`logstash-tuc.key`) stays with you, ensuring security.  
- Simpler process with minimal involvement from the CA.  

### **Case 2: Requesting the CA to Generate and Sign the Key Pair**  
1. **Provide necessary details to the CA:**  
   - Organization details (C, ST, L, O, OU, CN).  
   - Required **SANs**.  
2. **CA generates:**  
   - Private key (`logstash-tuc.key`).  
   - CSR (`logstash-tuc.csr`).  
   - Signed certificate (`logstash-tuc.crt`).  
3. **CA sends back:**  
   - `logstash-tuc.key` (private key).  
   - `logstash-tuc.crt` (signed certificate).  
4. **Use both files in Logstash.**  

**Pros:**  
- CA handles everything, reducing manual work.  
- Ensures SANs are correctly added by CA policies.  

**Key Difference:**  
- **Case 1:** You generate the key and keep it private.  
- **Case 2:** The CA generates everything, and you receive both the key and certificate.