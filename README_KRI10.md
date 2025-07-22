# KRI10 - Critical Systems Incident Analysis

Bu skript KRI10 (Kritik Sistemlərə Təsir Edən İnsidentlərin Sayı) hesabatını avtomatik olaraq yaradır.

## KRI10 Tərifi
- **KRI10**: Kritik sistemlərə təsir edən insidentlərin sayı
- **Hədd**: Hər kritik sistem üçün ayda maksimum 2 insident
- **Dövr**: Q2 2025 (Aprel, May, İyun)

## İstifadə

```bash
python3 kri10_analysis.py
```

## Nəticə

Skript aşağıdakı nəticələri verir:

1. **Konsol çıxışı**: Bütün kritik sistemlər üçün aylıq insident sayları
2. **HTML hesabatı**: `KRI10_Critical_Systems_Report.html` - təfərrüatlı hesabat

## Kritik Sistemlər

Aşağıdakı sistemlər kritik sistem kimi qiymətləndirilir:
- BirBank-Business
- BirBank.EDV  
- BirBank.Loyalty
- BirBank.Payments
- BirBank.Transfers
- Birbank
- CMS
- ELMA BPM
- TWO
- Zeus

## Nəticə Formatı

HTML hesabatında aşağıdakı məlumatlar göstərilir:

| System | Month | Count of Incidents | KRI Status |
|--------|-------|-------------------|------------|
| BirBank-Business | April | 3 | EXCEEDED |
| TWO | June | 4 | EXCEEDED |
| Zeus | May | 4 | EXCEEDED |

## Xülasə Statistikaları

- Ümumi sistem-ay kombinasiyaları
- Ümumi insident sayı
- KRI həddi aşan sistem-ay kombinasiyalarının sayı
- Uyğunluq dərəcəsi

## Fayllar

- `kri10_analysis.py` - Əsas analiz skripti
- `KRI10_Critical_Systems_Report.html` - HTML hesabatı
- `README_KRI10.md` - Bu təlimat faylı