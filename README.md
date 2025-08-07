# KRI Automation Web System

Bu layihə KRI (Key Risk Indicator) analizini avtomatlaşdırmaq üçün web əsaslı sistem təqdim edir. Sistemdə fayl yükləmə, avtomatik analiz və nəticələrin HTML və Excel formatlarında endirmə imkanı var.

## Xüsusiyyətlər

- **Web İnterfeysi**: Modern və istifadəçi dostu interfeys
- **Fayl Yükləmə**: Risk, Incident və Template fayllarını yükləmə
- **Avtomatik Analiz**: KRI5, KRI6, KRI8, KRI10, KRI12, KRI13, KRI19, KRI27, KRI28 analizləri
- **İkili Çıxış**: HTML və Excel formatlarında report generasiyası
- **Drag & Drop**: Faylları asanlıqla sürükləyib buraxma imkanı

## Quraşdırma

### 1. Lazimi modulları quraşdırın:

```bash
pip install -r requirements.txt
```

### 2. Sistemin strukturu:

```
/
├── index.html          # Ana web interfeysi
├── KRI_AUTOMATION.py   # Flask web server və analiz mühərriki
├── requirements.txt    # Python paketləri
└── README.md          # Bu fayl
```

## İstifadə

### 1. Web serveri işə salın:

```bash
python KRI_AUTOMATION.py
```

### 2. Browserinizi açın və gedən:

```
http://localhost:5000
```

### 3. Faylları yükləyin:

1. **Choose Risk File**: Risk report faylını seçin (.xls və ya .xlsx)
2. **Choose Incident File**: Incident report faylını seçin (.xlsx)
3. **Choose Last KRI Report File**: KRI template faylını seçin (.xlsx)

### 4. Prosesin başladılması:

"Process Files & Generate Report" düyməsini basın

### 5. Nəticələri endirin:

- **HTML Report**: Detallı web formatında report
- **Excel Report**: Excel şablonunda doldurulmuş report

## Fayl Formatları

### Risk File (.xls/.xlsx)
Aşağıdakı sütunlar lazımdır:
- Risk status
- Risk növü  
- Məxsusi risk dərəcəsi
- Riskin aşkarlanma tarixi
- Prosesin sahibi
- Nəzarət tədbirinin təsviri

### Incident File (.xlsx)
Aşağıdakı sütunlar lazımdır:
- Issue Key
- Incident start date
- Incident end date (opsional)
- Incident duration

### Template File (.xlsx)
KRI template faylı ilə KRI5, KRI6, KRI8, KRI10, KRI12, KRI13, KRI19, KRI27, KRI28 olan bölmələr.

## Texniki Detallar

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Data Processing**: Pandas, OpenPyXL
- **File Handling**: Temporary file management
- **Security**: Secure filename handling

## Port Konfiqurasiyası

Default port: 5000. Əgər dəyişdirmək istəyirsinizsə, KRI_AUTOMATION.py faylında son sətiri dəyişdirin:

```python
app.run(host='0.0.0.0', port=SIZIN_PORT, debug=True)
```

## Problemlərin Həlli

### Port məşğuldur:
```bash
# Başqa port istifadə edin
python KRI_AUTOMATION.py
# və ya file-da port-u dəyişdirin
```

### Modul yoxdur xətası:
```bash
pip install -r requirements.txt
```

### Fayl yüklənmir:
- Fayl formatının düzgün olduğunu yoxlayın
- Fayl ölçüsünün 50MB-dan az olduğunu təsdiqləyin
- Internetin işlədiyini yoxlayın

## Məhdudiyyətlər

- Maksimum fayl ölçüsü: 50MB
- Dəstəklənən formatlar: .xls, .xlsx
- Q2 2025 analizinə fokuslanmışdır

## Yardım

Əgər probleminiz varsa:
1. Terminal-da error mesajlarını yoxlayın
2. Browser console-nu yoxlayın (F12)
3. Faylların formatının düzgün olduğunu təsdiqləyin