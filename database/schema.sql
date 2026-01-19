-- Schema para banco de dados SQLite do aplicativo de termografia médica
-- Versão 1.0 - FASE 1 MVP

-- Tabela de pacientes
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    birth_date TEXT,  -- Formato ISO 8601: YYYY-MM-DD
    gender TEXT CHECK(gender IN ('M', 'F', 'Outro')),
    medical_record TEXT UNIQUE,  -- Prontuário médico
    phone TEXT,
    email TEXT,
    address TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de exames termográficos
CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    exam_date TEXT NOT NULL,  -- Formato ISO 8601: YYYY-MM-DD HH:MM:SS
    exam_type TEXT NOT NULL CHECK(exam_type IN ('Dermatomo', 'BTT', 'Corporal', 'Outro')),
    clinical_indication TEXT,  -- Indicação clínica
    body_region TEXT,  -- Região corporal examinada
    symptoms TEXT,  -- Sintomas relatados
    status TEXT DEFAULT 'Em andamento' CHECK(status IN ('Em andamento', 'Concluído', 'Cancelado')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- Tabela de imagens termográficas
CREATE TABLE IF NOT EXISTS thermal_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL,
    image_path TEXT NOT NULL,  -- Caminho do arquivo original
    image_type TEXT CHECK(image_type IN ('FLIR', 'Visible', 'Heatmap')),
    sequence_number INTEGER,  -- Ordem na sequência
    capture_timestamp TEXT,  -- Momento da captura

    -- Metadados técnicos
    camera_model TEXT,
    resolution TEXT,
    emissivity REAL,  -- Emissividade
    ambient_temp REAL,  -- Temperatura ambiente em °C
    humidity REAL,  -- Umidade relativa %
    distance REAL,  -- Distância em metros

    -- Dados estatísticos
    min_temp REAL,  -- Temperatura mínima em °C
    max_temp REAL,  -- Temperatura máxima em °C
    avg_temp REAL,  -- Temperatura média em °C

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

-- Tabela de ROIs (Regions of Interest)
CREATE TABLE IF NOT EXISTS rois (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER NOT NULL,
    name TEXT NOT NULL,  -- Ex: "Dermátomo C5 Esquerdo", "Região Frontal BTT"
    roi_type TEXT CHECK(roi_type IN ('Dermatomo', 'BTT', 'Manual', 'Auto')),

    -- Coordenadas da ROI (JSON com polígono ou retângulo)
    coordinates TEXT NOT NULL,  -- JSON: [[x1,y1], [x2,y2], ...]

    -- Lateralidade para análise comparativa
    laterality TEXT CHECK(laterality IN ('Esquerda', 'Direita', 'Central', 'Bilateral')),

    -- Dados estatísticos da ROI
    min_temp REAL,
    max_temp REAL,
    avg_temp REAL,
    std_temp REAL,  -- Desvio padrão

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (image_id) REFERENCES thermal_images(id) ON DELETE CASCADE
);

-- Tabela de análises de assimetria térmica
CREATE TABLE IF NOT EXISTS asymmetry_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL,
    roi_left_id INTEGER,  -- ROI do lado esquerdo
    roi_right_id INTEGER,  -- ROI do lado direito

    -- Resultados da análise
    delta_t REAL NOT NULL,  -- ΔT em °C
    classification TEXT CHECK(classification IN ('Normal', 'Leve', 'Moderada', 'Severa')),

    -- Critérios de classificação
    -- Normal: ΔT < 0.5°C
    -- Leve: 0.5°C ≤ ΔT < 1.0°C
    -- Moderada: 1.0°C ≤ ΔT < 1.5°C
    -- Severa: ΔT ≥ 1.5°C

    clinical_significance TEXT,  -- Significado clínico
    notes TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (roi_left_id) REFERENCES rois(id) ON DELETE SET NULL,
    FOREIGN KEY (roi_right_id) REFERENCES rois(id) ON DELETE SET NULL
);

-- Tabela de análise BTT (Brain Thermal Tunnel)
CREATE TABLE IF NOT EXISTS btt_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL,

    -- Regiões BTT
    frontal_temp REAL,
    parietal_left_temp REAL,
    parietal_right_temp REAL,
    occipital_temp REAL,
    temporal_left_temp REAL,
    temporal_right_temp REAL,

    -- Análise de padrão térmico
    thermal_pattern TEXT,  -- Descrição do padrão
    asymmetry_detected BOOLEAN,
    max_delta_t REAL,  -- Maior ΔT encontrado

    -- Correlação com sintomas
    headache_type TEXT,  -- Tipo de cefaleia
    pain_location TEXT,  -- Localização da dor
    pain_intensity INTEGER CHECK(pain_intensity BETWEEN 0 AND 10),

    findings TEXT,  -- Achados
    clinical_correlation TEXT,  -- Correlação clínica

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

-- Tabela de laudos gerados
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL,

    -- Conteúdo do laudo
    report_text TEXT NOT NULL,  -- Texto completo do laudo
    report_type TEXT CHECK(report_type IN ('Preliminar', 'Final', 'Complementar')),

    -- Dados do profissional
    physician_name TEXT,
    physician_crm TEXT,

    -- Metadados
    generated_by TEXT DEFAULT 'Claude AI',  -- Sistema que gerou
    reviewed BOOLEAN DEFAULT 0,  -- Se foi revisado por médico
    reviewed_by TEXT,
    reviewed_at TEXT,

    -- Conclusão e recomendações
    conclusion TEXT,
    recommendations TEXT,

    -- Arquivo PDF exportado
    pdf_path TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

-- Tabela de configurações do sistema
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_patients_medical_record ON patients(medical_record);
CREATE INDEX IF NOT EXISTS idx_exams_patient_id ON exams(patient_id);
CREATE INDEX IF NOT EXISTS idx_exams_exam_date ON exams(exam_date);
CREATE INDEX IF NOT EXISTS idx_thermal_images_exam_id ON thermal_images(exam_id);
CREATE INDEX IF NOT EXISTS idx_rois_image_id ON rois(image_id);
CREATE INDEX IF NOT EXISTS idx_asymmetry_exam_id ON asymmetry_analysis(exam_id);
CREATE INDEX IF NOT EXISTS idx_btt_exam_id ON btt_analysis(exam_id);
CREATE INDEX IF NOT EXISTS idx_reports_exam_id ON reports(exam_id);

-- Inserir configurações padrão
INSERT OR IGNORE INTO settings (key, value, description) VALUES
    ('app_version', '1.0.0', 'Versão do aplicativo'),
    ('db_version', '1.0', 'Versão do schema do banco'),
    ('temp_unit', 'Celsius', 'Unidade de temperatura padrão'),
    ('asymmetry_threshold_normal', '0.5', 'Limiar ΔT para classificação Normal (°C)'),
    ('asymmetry_threshold_mild', '1.0', 'Limiar ΔT para classificação Leve (°C)'),
    ('asymmetry_threshold_moderate', '1.5', 'Limiar ΔT para classificação Moderada (°C)'),
    ('default_emissivity', '0.98', 'Emissividade padrão para pele humana'),
    ('export_folder', '', 'Pasta padrão para exportação de relatórios'),
    ('image_storage', 'local', 'Modo de armazenamento de imagens (local/cloud)');

-- Triggers para atualizar updated_at automaticamente
CREATE TRIGGER IF NOT EXISTS update_patients_timestamp
AFTER UPDATE ON patients
BEGIN
    UPDATE patients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_exams_timestamp
AFTER UPDATE ON exams
BEGIN
    UPDATE exams SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_reports_timestamp
AFTER UPDATE ON reports
BEGIN
    UPDATE reports SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_settings_timestamp
AFTER UPDATE ON settings
BEGIN
    UPDATE settings SET updated_at = CURRENT_TIMESTAMP WHERE key = NEW.key;
END;
