# Gastrotech VPS Deployment Guide

**Sunucu:** 187.77.84.4 (Ubuntu 24.04)
**Kullanıcı:** root

## 1. Hazırlık (Lokal)
Dosyaları sunucuya yükleyin. (PowerShell terminalinde çalıştırın):

```powershell
# 1. Backupları yükle
scp -r backups/media.zip backups/gastrotech_final.dump root@187.77.84.4:/root/

# 2. Deployment dosyalarını yükle (Opsiyonel - Git ile çekeceğiz ama elde bulunsun)
scp -r vps-deploy root@187.77.84.4:/root/
```

## 2. Sunucu Kurulumu (VPS)
SSH ile bağlanın: `ssh root@187.77.84.4` (Şifrenizi girin)

Sunucuda aşağıdaki komutları sırasıyla çalıştırın:

```bash
# 1. Klasörleri oluştur ve dosyaları taşı
mkdir -p /opt/gastrotech/backups
mv /root/media.zip /opt/gastrotech/backups/
mv /root/gastrotech_final.dump /opt/gastrotech/backups/

# 2. Repo'yu çek
git clone https://github.com/chvvasss/gastrotech_website.git /opt/gastrotech/repo

# 3. Setup scriptini çalıştır
bash /opt/gastrotech/repo/vps-deploy/setup.sh
```

## 3. SSL Sertifikası (DNS Hazırsa)
DNS (Cloudflare/Hostinger) yönlendirmeleri tamamlandıktan sonra SSL almak için:

```bash
certbot --nginx -d gastrotech.com.tr -d www.gastrotech.com.tr -d api.gastrotech.com.tr -d admin.gastrotech.com.tr
```

## 4. Sorun Giderme
*   **502 Bad Gateway:** `docker compose -f /opt/gastrotech/docker-compose.prod.yml logs -f` ile loglara bakın.
*   **Database Hatası:** `vps-deploy/.env.prod` içindeki şifrelerin doğru olduğundan emin olun.
*   **Media Dosyaları:** `/opt/gastrotech/media` klasörünün dolu olduğunu kontrol edin.
