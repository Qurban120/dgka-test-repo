# KRI8 Critical Systems Incident Analysis

Bu Python scripti KRI8 kritik sistemlərdə baş verən insidentləri analiz edir və HTML formatında hesabat yaradır.

## Sistem Qruplaşdırması

Script aşağıdakı qaydaya görə sistemləri qruplaşdırır:

1. **BirBank-Business** - Issue Key-də "BirBank-Business" olan insidentlər
2. **Birbank** - Aşağıdakı Issue Key-ləri olan insidentlər:
   - BirBank.EDV
   - BirBank.Loyalty  
   - BirBank.Payments
   - BirBank.Transfers
   - Birbank
3. **CMS** - Issue Key-də "CMS" olan insidentlər
4. **ELMA BPM** - Issue Key-də "ELMA BPM" olan insidentlər
5. **TWO** - Issue Key-də "TWO" olan insidentlər (Atlas və Telesales daxil)
6. **Zeus** - Issue Key-də "Zeus" olan insidentlər (Optimus daxil)

## Quraşdırma

1. Python 3.7+ quraşdırın
2. Lazımi kitabxanaları quraşdırın:
```bash
pip install -r requirements.txt
```

## İstifadə

1. Excel faylının yolunu `incident_analysis.py` faylında düzəldin
2. Scripti işə salın:
```bash
python incident_analysis.py
```

## Nəticə

Script aşağıdakı nəticələri verir:
- Konsol çıxışında hər sistem üçün məlumat
- `KRI8_Critical_Systems_Report.html` faylında detallı HTML hesabat

## HTML Hesabatında Göstərilən Məlumatlar

- **System** - Sistem adı
- **Incident End Date** - Son insidentin bitdiyi tarix
- **Days until Quarter 2 End** - Q2 sonuna qədər günlərin sayı

Hədəf: Hər sistem üçün 120+ gün olmalıdır.

## Rəng Kodları

- 🟢 Yaşıl: ≥120 gün (Hədəfə çatır)
- 🟡 Sarı: 90-119 gün (Xəbərdarlıq)
- 🔴 Qırmızı: <90 gün (Kritik)