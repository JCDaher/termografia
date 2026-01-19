"""
Gerenciador de banco de dados SQLite para o aplicativo de termografia médica.
Fornece interface para todas as operações CRUD.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerencia todas as operações do banco de dados SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa o gerenciador de banco de dados.

        Args:
            db_path: Caminho para o arquivo do banco de dados.
                    Se None, usa 'data/termografia.db'
        """
        if db_path is None:
            self.db_path = Path('data/termografia.db')
        else:
            self.db_path = Path(db_path)

        # Garante que o diretório existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Inicializa o banco de dados
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """
        Cria e retorna uma conexão com o banco de dados.

        Returns:
            Conexão SQLite
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
        return conn

    def init_database(self) -> None:
        """Inicializa o banco de dados executando o schema.sql."""
        try:
            schema_path = Path(__file__).parent / 'schema.sql'

            if not schema_path.exists():
                logger.error(f"Schema SQL não encontrado em {schema_path}")
                raise DatabaseError("Schema SQL não encontrado")

            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            conn = self.get_connection()
            try:
                conn.executescript(schema_sql)
                conn.commit()
                logger.info("Banco de dados inicializado com sucesso")
            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise DatabaseError(f"Erro ao inicializar banco de dados: {e}")

    # ===== PACIENTES =====

    def create_patient(self, name: str, birth_date: Optional[str] = None,
                      gender: Optional[str] = None, medical_record: Optional[str] = None,
                      phone: Optional[str] = None, email: Optional[str] = None,
                      address: Optional[str] = None, notes: Optional[str] = None) -> int:
        """
        Cria um novo paciente.

        Args:
            name: Nome do paciente
            birth_date: Data de nascimento (formato ISO: YYYY-MM-DD)
            gender: Gênero (M/F/Outro)
            medical_record: Número do prontuário
            phone: Telefone
            email: Email
            address: Endereço
            notes: Observações

        Returns:
            ID do paciente criado
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patients (name, birth_date, gender, medical_record, phone, email, address, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, birth_date, gender, medical_record, phone, email, address, notes))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise DatabaseError(f"Erro de integridade ao criar paciente: {e}")
        finally:
            conn.close()

    def get_patient(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca um paciente por ID.

        Args:
            patient_id: ID do paciente

        Returns:
            Dicionário com dados do paciente ou None se não encontrado
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def search_patients(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca pacientes por nome ou prontuário.

        Args:
            query: Texto de busca

        Returns:
            Lista de pacientes encontrados
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM patients
                WHERE name LIKE ? OR medical_record LIKE ?
                ORDER BY name
            """, (f'%{query}%', f'%{query}%'))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_patient(self, patient_id: int, **kwargs) -> None:
        """
        Atualiza dados de um paciente.

        Args:
            patient_id: ID do paciente
            **kwargs: Campos a serem atualizados
        """
        if not kwargs:
            return

        fields = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [patient_id]

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE patients SET {fields} WHERE id = ?", values)
            conn.commit()
        finally:
            conn.close()

    # ===== EXAMES =====

    def create_exam(self, patient_id: int, exam_date: str, exam_type: str,
                   clinical_indication: Optional[str] = None,
                   body_region: Optional[str] = None,
                   symptoms: Optional[str] = None) -> int:
        """
        Cria um novo exame.

        Args:
            patient_id: ID do paciente
            exam_date: Data/hora do exame (formato ISO)
            exam_type: Tipo de exame (Dermatomo/BTT/Corporal/Outro)
            clinical_indication: Indicação clínica
            body_region: Região corporal
            symptoms: Sintomas

        Returns:
            ID do exame criado
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO exams (patient_id, exam_date, exam_type, clinical_indication, body_region, symptoms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (patient_id, exam_date, exam_type, clinical_indication, body_region, symptoms))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_exam(self, exam_id: int) -> Optional[Dict[str, Any]]:
        """Busca um exame por ID."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exams WHERE id = ?", (exam_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_patient_exams(self, patient_id: int) -> List[Dict[str, Any]]:
        """Busca todos os exames de um paciente."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM exams WHERE patient_id = ?
                ORDER BY exam_date DESC
            """, (patient_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_exam_status(self, exam_id: int, status: str) -> None:
        """Atualiza o status de um exame."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE exams SET status = ? WHERE id = ?", (status, exam_id))
            conn.commit()
        finally:
            conn.close()

    # ===== IMAGENS TÉRMICAS =====

    def add_thermal_image(self, exam_id: int, image_path: str, image_type: str,
                         sequence_number: Optional[int] = None,
                         camera_model: Optional[str] = None,
                         emissivity: Optional[float] = None,
                         ambient_temp: Optional[float] = None,
                         min_temp: Optional[float] = None,
                         max_temp: Optional[float] = None,
                         avg_temp: Optional[float] = None) -> int:
        """
        Adiciona uma imagem térmica ao exame.

        Returns:
            ID da imagem criada
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO thermal_images
                (exam_id, image_path, image_type, sequence_number, camera_model,
                 emissivity, ambient_temp, min_temp, max_temp, avg_temp, capture_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (exam_id, image_path, image_type, sequence_number, camera_model,
                  emissivity, ambient_temp, min_temp, max_temp, avg_temp,
                  datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_exam_images(self, exam_id: int) -> List[Dict[str, Any]]:
        """Busca todas as imagens de um exame."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM thermal_images WHERE exam_id = ?
                ORDER BY sequence_number, capture_timestamp
            """, (exam_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    # ===== ROIs (Regions of Interest) =====

    def add_roi(self, image_id: int, name: str, roi_type: str,
               coordinates: List[Tuple[int, int]], laterality: Optional[str] = None,
               min_temp: Optional[float] = None, max_temp: Optional[float] = None,
               avg_temp: Optional[float] = None, std_temp: Optional[float] = None) -> int:
        """
        Adiciona uma ROI a uma imagem.

        Args:
            coordinates: Lista de tuplas (x, y) definindo o polígono da ROI

        Returns:
            ID da ROI criada
        """
        conn = self.get_connection()
        try:
            # Converte coordenadas para JSON
            coords_json = json.dumps(coordinates)

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rois
                (image_id, name, roi_type, coordinates, laterality, min_temp, max_temp, avg_temp, std_temp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (image_id, name, roi_type, coords_json, laterality, min_temp, max_temp, avg_temp, std_temp))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_image_rois(self, image_id: int) -> List[Dict[str, Any]]:
        """Busca todas as ROIs de uma imagem."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rois WHERE image_id = ?", (image_id,))
            rois = [dict(row) for row in cursor.fetchall()]

            # Converte coordenadas de JSON para lista
            for roi in rois:
                roi['coordinates'] = json.loads(roi['coordinates'])

            return rois
        finally:
            conn.close()

    # ===== ANÁLISE DE ASSIMETRIA =====

    def add_asymmetry_analysis(self, exam_id: int, roi_left_id: Optional[int],
                               roi_right_id: Optional[int], delta_t: float,
                               classification: str, clinical_significance: Optional[str] = None,
                               notes: Optional[str] = None) -> int:
        """
        Adiciona uma análise de assimetria térmica.

        Returns:
            ID da análise criada
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO asymmetry_analysis
                (exam_id, roi_left_id, roi_right_id, delta_t, classification, clinical_significance, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (exam_id, roi_left_id, roi_right_id, delta_t, classification, clinical_significance, notes))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_exam_asymmetry_analyses(self, exam_id: int) -> List[Dict[str, Any]]:
        """Busca todas as análises de assimetria de um exame."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM asymmetry_analysis WHERE exam_id = ?", (exam_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    # ===== ANÁLISE BTT =====

    def add_btt_analysis(self, exam_id: int, **kwargs) -> int:
        """
        Adiciona uma análise BTT (Brain Thermal Tunnel).

        Args:
            exam_id: ID do exame
            **kwargs: Dados da análise BTT

        Returns:
            ID da análise criada
        """
        conn = self.get_connection()
        try:
            # Campos possíveis
            fields = ['exam_id'] + list(kwargs.keys())
            placeholders = ', '.join(['?' for _ in fields])
            fields_str = ', '.join(fields)
            values = [exam_id] + list(kwargs.values())

            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO btt_analysis ({fields_str})
                VALUES ({placeholders})
            """, values)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_exam_btt_analysis(self, exam_id: int) -> Optional[Dict[str, Any]]:
        """Busca a análise BTT de um exame."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM btt_analysis WHERE exam_id = ?", (exam_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ===== LAUDOS =====

    def create_report(self, exam_id: int, report_text: str, report_type: str = 'Preliminar',
                     physician_name: Optional[str] = None, physician_crm: Optional[str] = None,
                     conclusion: Optional[str] = None, recommendations: Optional[str] = None) -> int:
        """
        Cria um laudo médico.

        Returns:
            ID do laudo criado
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reports
                (exam_id, report_text, report_type, physician_name, physician_crm, conclusion, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (exam_id, report_text, report_type, physician_name, physician_crm, conclusion, recommendations))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Busca um laudo por ID."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_exam_reports(self, exam_id: int) -> List[Dict[str, Any]]:
        """Busca todos os laudos de um exame."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reports WHERE exam_id = ?
                ORDER BY created_at DESC
            """, (exam_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_report_pdf_path(self, report_id: int, pdf_path: str) -> None:
        """Atualiza o caminho do PDF exportado."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE reports SET pdf_path = ? WHERE id = ?", (pdf_path, report_id))
            conn.commit()
        finally:
            conn.close()

    # ===== CONFIGURAÇÕES =====

    def get_setting(self, key: str) -> Optional[str]:
        """Busca uma configuração por chave."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
        finally:
            conn.close()

    def set_setting(self, key: str, value: str, description: Optional[str] = None) -> None:
        """Define uma configuração."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value, description)
                VALUES (?, ?, ?)
            """, (key, value, description))
            conn.commit()
        finally:
            conn.close()


class DatabaseError(Exception):
    """Exceção para erros de banco de dados."""
    pass


# Instância global
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """
    Retorna a instância global do DatabaseManager (padrão Singleton).

    Returns:
        Instância de DatabaseManager
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


if __name__ == '__main__':
    # Teste básico
    print("=== Teste do DatabaseManager ===\n")

    db = DatabaseManager(Path('test_db.sqlite'))

    # Criar paciente de teste
    patient_id = db.create_patient(
        name="João Silva",
        birth_date="1980-05-15",
        gender="M",
        medical_record="12345"
    )
    print(f"Paciente criado com ID: {patient_id}")

    # Buscar paciente
    patient = db.get_patient(patient_id)
    print(f"Paciente encontrado: {patient['name']}")

    # Criar exame
    exam_id = db.create_exam(
        patient_id=patient_id,
        exam_date=datetime.now().isoformat(),
        exam_type="Dermatomo",
        clinical_indication="Dor radicular C5-C6"
    )
    print(f"Exame criado com ID: {exam_id}")

    print("\nTeste concluído com sucesso!")
