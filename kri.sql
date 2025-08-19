-- Initialize schema (idempotent)
CREATE TABLE IF NOT EXISTS kri_points (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kri_id TEXT NOT NULL,
  period TEXT NOT NULL,
  value REAL NOT NULL,
  UNIQUE(kri_id, period)
);

CREATE TABLE IF NOT EXISTS kri_app_systems (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kri_id TEXT NOT NULL,
  system_name TEXT NOT NULL,
  UNIQUE(kri_id, system_name)
);

CREATE TABLE IF NOT EXISTS kri_app_points (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kri_id TEXT NOT NULL,
  system_name TEXT NOT NULL,
  period TEXT NOT NULL,
  value REAL NOT NULL,
  UNIQUE(kri_id, system_name, period)
);

-- Base KRIs (quarters)
INSERT OR REPLACE INTO kri_points (kri_id, period, value) VALUES
 ('kri2','Q1-2025',100.0),('kri2','Q2-2025',100.0),
 ('kri3','Q1-2025',100.0),('kri3','Q2-2025',100.0),
 ('kri4','Q1-2025',0.0),('kri4','Q2-2025',0.0),
 ('kri5','Q1-2025',0.0),('kri5','Q2-2025',0.0),
 ('kri6','Q1-2025',18.0),('kri6','Q2-2025',0.6),
 ('kri9','Q1-2025',0.0),('kri9','Q2-2025',0.0),
 ('kri15','Q1-2025',71.0),('kri15','Q2-2025',24.0),
 ('kri18','Q1-2025',0.0),('kri18','Q2-2025',38.0),
 ('kri20','Q1-2025',0.0),('kri20','Q2-2025',1.0),
 ('kri21','Q1-2025',0.0),('kri21','Q2-2025',0.0),
 ('kri22','Q1-2025',94.04),('kri22','Q2-2025',95.35),
 ('kri27','Q1-2025',0.0),('kri27','Q2-2025',0.0),
 ('kri28','Q1-2025',0.0),('kri28','Q2-2025',2.4);

-- Systems for app-based KRIs
INSERT OR IGNORE INTO kri_app_systems (kri_id, system_name) VALUES
 ('kri8','BirBank'),('kri8','BirBank-Business'),('kri8','ODIN'),('kri8','ELMA BPM'),('kri8','Optimus'),('kri8','CMS'),('kri8','TWO'),('kri8','Zeus'),
 ('kri10','BirBank-Business'),('kri10','BirBank'),('kri10','CMS'),('kri10','ELMA BPM'),('kri10','TWO'),('kri10','Zeus'),('kri10','Optimus'),('kri10','ODIN'),
 ('kri12','BirBank-Business'),('kri12','BirBank'),('kri12','CMS'),('kri12','ELMA BPM'),('kri12','TWO'),('kri12','Zeus'),('kri12','Optimus'),('kri12','ODIN'),
 ('kri13','BirBank'),('kri13','BirBank-Business'),('kri13','ODIN'),('kri13','ELMA BPM'),('kri13','Optimus'),('kri13','CMS'),('kri13','TWO'),('kri13','Zeus'),
 ('kri19','BirBank'),('kri19','BirBank-Business'),('kri19','ODIN'),('kri19','ELMA BPM'),('kri19','Optimus'),('kri19','CMS'),('kri19','TWO'),('kri19','Zeus');

-- kri8 (quarters)
INSERT OR REPLACE INTO kri_app_points (kri_id, system_name, period, value) VALUES
 ('kri8','BirBank','Q1-2025',22.0),('kri8','BirBank','Q2-2025',7.0),
 ('kri8','BirBank-Business','Q1-2025',29.0),('kri8','BirBank-Business','Q2-2025',63.0),
 ('kri8','ODIN','Q1-2025',194.0),('kri8','ODIN','Q2-2025',285.0),
 ('kri8','ELMA BPM','Q1-2025',29.0),('kri8','ELMA BPM','Q2-2025',13.0),
 ('kri8','Optimus','Q1-2025',51.0),('kri8','Optimus','Q2-2025',142.0),
 ('kri8','CMS','Q1-2025',18.0),('kri8','CMS','Q2-2025',60.0),
 ('kri8','TWO','Q1-2025',36.0),('kri8','TWO','Q2-2025',15.0),
 ('kri8','Zeus','Q1-2025',45.0),('kri8','Zeus','Q2-2025',7.0);

-- kri10 (months)
INSERT OR REPLACE INTO kri_app_points (kri_id, system_name, period, value) VALUES
 ('kri10','BirBank-Business','01-2025',1),('kri10','BirBank-Business','02-2025',2),('kri10','BirBank-Business','03-2025',1),('kri10','BirBank-Business','04-2025',3),
 ('kri10','BirBank','01-2025',8),('kri10','BirBank','02-2025',12),('kri10','BirBank','03-2025',12),('kri10','BirBank','04-2025',6),('kri10','BirBank','05-2025',6),('kri10','BirBank','06-2025',9),
 ('kri10','CMS','03-2025',3),('kri10','CMS','04-2025',3),
 ('kri10','ELMA BPM','03-2025',1),('kri10','ELMA BPM','04-2025',2),('kri10','ELMA BPM','06-2025',1),
 ('kri10','TWO','01-2025',1),('kri10','TWO','02-2025',2),('kri10','TWO','03-2025',1),('kri10','TWO','04-2025',1),('kri10','TWO','06-2025',2),
 ('kri10','Zeus','01-2025',3),('kri10','Zeus','02-2025',3),('kri10','Zeus','03-2025',2),('kri10','Zeus','04-2025',1),('kri10','Zeus','05-2025',4),('kri10','Zeus','06-2025',2),
 ('kri10','Optimus','02-2025',2),('kri10','Optimus','06-2025',0);

-- kri12 (quarters)
INSERT OR REPLACE INTO kri_app_points (kri_id, system_name, period, value) VALUES
 ('kri12','BirBank-Business','Q1-2025',2),('kri12','BirBank-Business','Q2-2025',2),
 ('kri12','BirBank','Q1-2025',18),('kri12','BirBank','Q2-2025',12),
 ('kri12','CMS','Q1-2025',1),('kri12','CMS','Q2-2025',2),
 ('kri12','ELMA BPM','Q1-2025',1),('kri12','ELMA BPM','Q2-2025',2),
 ('kri12','TWO','Q1-2025',0),('kri12','TWO','Q2-2025',1),
 ('kri12','Zeus','Q1-2025',6),('kri12','Zeus','Q2-2025',2),
 ('kri12','Optimus','Q1-2025',1),('kri12','Optimus','Q2-2025',0),
 ('kri12','ODIN','Q1-2025',0),('kri12','ODIN','Q2-2025',0);

-- kri13 (quarters)
INSERT OR REPLACE INTO kri_app_points (kri_id, system_name, period, value) VALUES
 ('kri13','BirBank','Q1-2025',14),('kri13','BirBank','Q2-2025',9),
 ('kri13','BirBank-Business','Q1-2025',2),('kri13','BirBank-Business','Q2-2025',1),
 ('kri13','ODIN','Q1-2025',0),('kri13','ODIN','Q2-2025',0),
 ('kri13','ELMA BPM','Q1-2025',0),('kri13','ELMA BPM','Q2-2025',1),
 ('kri13','Optimus','Q1-2025',1),('kri13','Optimus','Q2-2025',0),
 ('kri13','CMS','Q1-2025',2),('kri13','CMS','Q2-2025',1),
 ('kri13','TWO','Q1-2025',4),('kri13','TWO','Q2-2025',2),
 ('kri13','Zeus','Q1-2025',1),('kri13','Zeus','Q2-2025',5);

-- kri19 (quarters; minutes)
INSERT OR REPLACE INTO kri_app_points (kri_id, system_name, period, value) VALUES
 ('kri19','BirBank','Q1-2025',3125.9),('kri19','BirBank','Q2-2025',3973.4),
 ('kri19','BirBank-Business','Q1-2025',407.5),('kri19','BirBank-Business','Q2-2025',1811.0),
 ('kri19','ODIN','Q1-2025',0.0),('kri19','ODIN','Q2-2025',0.0),
 ('kri19','ELMA BPM','Q1-2025',269.0),('kri19','ELMA BPM','Q2-2025',892.3),
 ('kri19','Optimus','Q1-2025',207.5),('kri19','Optimus','Q2-2025',0.0),
 ('kri19','CMS','Q1-2025',73.0),('kri19','CMS','Q2-2025',644.0),
 ('kri19','TWO','Q1-2025',31.25),('kri19','TWO','Q2-2025',353.6),
 ('kri19','Zeus','Q1-2025',1734.4),('kri19','Zeus','Q2-2025',59.1);

