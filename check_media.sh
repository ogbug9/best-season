#!/bin/bash
# Проверка: отдаётся ли медиа, загруженное ПОСЛЕ старта сервера.
# Именно этот сценарий воспроизводит боевой: контейнер стартует с пустым
# /data/media, редактор грузит фото уже потом.
set -e
cd /home/claude/best-season
source .venv/bin/activate
set -a; . ./.env; set +a

export DJANGO_SETTINGS_MODULE=config.settings.production
export SECURE_SSL_REDIRECT=False
export ALLOWED_HOSTS=127.0.0.1,localhost
export MEDIA_ROOT=/home/claude/best-season/media

pkill -f "gunicorn config.wsgi" 2>/dev/null || true
sleep 2
rm -rf media static
mkdir -p media

DJANGO_SETTINGS_MODULE=config.settings.dev python - <<'PY'
import django; django.setup()
from wagtail.images.models import Image
Image.objects.all().delete()
print("медиатека очищена")
PY

python manage.py collectstatic --noinput > /dev/null
nohup gunicorn config.wsgi:application --bind 127.0.0.1:8013 --workers 1 > gunicorn.log 2>&1 &
sleep 7
echo "сервер поднят, media была пуста"

python - <<'PY' > media_urls.txt
import django; django.setup()
from io import BytesIO
from PIL import Image as PILImage
from django.core.files.images import ImageFile
from wagtail.images.models import Image
b = BytesIO(); PILImage.new("RGB", (2000, 1200), (120, 130, 90)).save(b, "JPEG"); b.seek(0)
img = Image.objects.create(title="после старта", file=ImageFile(b, name="p4.jpg"))
print(img.file.url)
print(img.get_rendition("fill-800x450|format-webp").url)
print(img.get_rendition("fill-480x270|format-jpeg").url)
PY

echo "--- файлы, созданные ПОСЛЕ старта сервера ---"
FAIL=0
while read -r U; do
  [ -z "$U" ] && continue
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8013$U")
  [ "$CODE" = "200" ] || FAIL=1
  echo "  $CODE  $U"
done < media_urls.txt

echo "--- рендишен, созданный ещё позже ---"
U2=$(python -c "
import django; django.setup()
from wagtail.images.models import Image
print(Image.objects.first().get_rendition('fill-1440x810|format-webp').url)
" | tail -1)
CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8013$U2")
[ "$CODE" = "200" ] || FAIL=1
echo "  $CODE  $U2"

pkill -f "gunicorn config.wsgi" 2>/dev/null || true
echo ""
if [ "$FAIL" = "0" ]; then echo "ИТОГ: ОК, медиа отдаётся"; else echo "ИТОГ: ПРОВАЛ"; fi
