# Aturan Kerja Tim

- `main` dilindungi: tidak ada push langsung. Semua perubahan lewat Pull Request.
- Satu branch per tugas, bernama sesuai ID di `TASKS.md`: `feat/A2-aes-gcm`, `feat/B3-authz`.
- PR minimal direview **satu anggota lain**. Perubahan pada kontrak (`kcrypto/api.py`, `openapi.yaml`, skema DB, format header) wajib disetujui pemilik modul **dan** pemakainya.
- Pesan commit singkat dan jelas, contoh: `A2: add AES-GCM chunked encrypt`.
- **Jangan pernah commit** password, kunci, `.env`, atau data pasien asli. Data uji hanya data dummy.
- Tiap PR menyertakan tes untuk kode yang ditambah, dan memperbarui status di `TASKS.md`.
