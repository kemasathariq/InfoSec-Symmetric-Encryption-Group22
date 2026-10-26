# Mode comparison (20 MB encryption, median of 30 runs)

| Variant | Median ms | Stdev ms | MB/s |
|---|---|---|---|
| HMAC-SHA256 only | 5.9 | 0.2 | 3404 |
| AES-CTR+HMAC | 62.2 | 0.7 | 321 |
| AES-CBC+HMAC | 71.6 | 3.7 | 279 |
| AES-GCM | 72.7 | 2.4 | 275 |
| DES-CTR+HMAC | 446.6 | 10.8 | 45 |
| DES-OFB+HMAC | 511.6 | 11.5 | 39 |
| DES-CBC+HMAC | 521.2 | 33.8 | 38 |
