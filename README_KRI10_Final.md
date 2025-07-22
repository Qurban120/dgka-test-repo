# KRI10 - Kritik Sistemlərə Təsir Edən İnsidentlərin Avtomatlaşdırılmış Analizi

Bu skript KRI10 (Kritik Sistemlərə Təsir Edən İnsidentlərin Sayı) hesabatını avtomatik olaraq Excel faylından oxuyaraq yaradır.

## 📋 KRI10 Tərifi
- **KRI10**: Kritik sistemlərə təsir edən insidentlərin sayı
- **Hədd**: Hər kritik sistem üçün ayda maksimum 2 insident
- **Dövr**: Q2 2025 (Aprel, May, İyun)

## 📁 Fayl Yolu
```
C:\Users\XaniyevQX\Desktop\AUTOMATION_NEW\Incident_Report_for_GRC__KRI_ (1).xlsx
```

## 🚀 İstifadə Təlimatı

### Addım 1: Excel faylını CSV formatına çevirin
1. Excel faylını açın
2. `File` -> `Save As` seçin
3. `CSV (Comma delimited) (*.csv)` formatını seçin
4. Faylı `incident_data_converted.csv` adı ilə skriptin olduğu qovluqda saxlayın

### Addım 2: Skripti işə salın
```bash
python3 kri10_final.py
```

## 📊 Nəticə Formatı

### Konsol çıxışı:
```
System                    Month      Count
------------------------------------------------------------
BirBank-Business          April      3
BirBank.Payments          May        3
TWO                       June       2
```

### HTML Hesabatı:
- Sadə cədvəl formatında
- Heç bir mürəkkəb CSS yoxdur
- `KRI10_Report.html` adı ilə yaradılır

## 🎯 Nəticə Nümunəsi

Əgər BirBank-Business sistemində Aprel ayında 3 insident varsa:
```
BirBank-Business          April      3
```

TWO sistemində İyun ayında 2 insident varsa:
```
TWO                       June       2
```

## 📈 Analiz Məntigi

1. **Kritik Sistemlər**: Issue Key sütununda olan sistemlər (məs: "BirBank-Business (ITAM-1454566)")
2. **İnsidentlər**: IMP- ilə başlayan sətirlər
3. **Assosiasiya**: Hər IMP- insidenti ən yaxın kritik sistemə aid edilir
4. **Aylıq Sayım**: Q2 ayları üzrə (Aprel, May, İyun) sayılır

## ⚠️ KRI Həddi Aşanlar

Skript avtomatik olaraq ayda 2-dən çox insidenti olan sistemləri göstərir:

```
⚠️ Systems exceeding KRI10 threshold (>2 incidents/month):
   - BirBank-Business in April: 3 incidents
   - Zeus in May: 4 incidents
```

## 📁 Yaradılan Fayllar

- `KRI10_Report.html` - Əsas HTML hesabatı
- Konsol çıxışı - Canlı nəticələr

## 🔧 Texniki Detallar

- **Dil**: Python 3
- **Asılılıqlar**: Standart kitabxanalar (csv, datetime, os)
- **Giriş Formatı**: CSV (Excel-dən çevrilmiş)
- **Çıxış Formatı**: HTML cədvəli

## 📝 Qeydlər

- Skript yalnız Q2 2025 (04, 05, 06 ayları) məlumatlarını analiz edir
- Kritik sistemlər Issue Key sütununda müəyyən edilir
- İnsidentlər IMP- prefiksi ilə tanınır
- Tarixlər DD/MM/YY formatında gözlənilir

## 🎯 İstifadə Ssenarisi

1. Excel faylını CSV formatına çevirin
2. Skripti işə salın
3. HTML hesabatını açın
4. KRI10 nəticələrini təhlil edin
5. Həddi aşan sistemləri müəyyən edin

Bu avtomatlaşdırma GRC KRI monitorinqi üçün tam hazırdır! 🎉