"""RC4 + HMAC-SHA256, encrypt-then-MAC (A4).

PERINGATAN (tulis juga di laporan): RC4 punya bias keystream dan tidak punya IV; dipakai hanya karena diwajibkan tugas.
TODO: bagaimana menjamin satu kunci tidak pernah dipakai dua kali? Perlukah membuang awal keystream?
"""
