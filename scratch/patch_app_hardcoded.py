import sys

with open('dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. get_predictions
old_get_predictions = """def get_predictions(limit: int = 100) -> list:
    \"\"\"Get all predictions ordered by timestamp descending.\"\"\"
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(\"\"\"
            SELECT * FROM prediction_ledger 
            ORDER BY timestamp DESC 
            LIMIT %s
        \"\"\", (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return []"""

new_get_predictions = """def get_predictions(limit: int = 100) -> list:
    \"\"\"Get all predictions ordered by timestamp descending.\"\"\"
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(\"\"\"
                SELECT * FROM prediction_ledger 
                ORDER BY timestamp DESC 
                LIMIT %s
            \"\"\", (limit,))
            rows = c.fetchall()
            return [dict(row) for row in rows]
    except Exception:
        return []"""
content = content.replace(old_get_predictions, new_get_predictions)

# 2. get_veto_archive
old_get_veto_archive = """def get_veto_archive(limit: int = 100) -> list:
    \"\"\"Get all vetoed items ordered by timestamp descending.\"\"\"
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(\"\"\"
            SELECT * FROM veto_archive 
            ORDER BY timestamp DESC 
            LIMIT %s
        \"\"\", (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return []"""

new_get_veto_archive = """def get_veto_archive(limit: int = 100) -> list:
    \"\"\"Get all vetoed items ordered by timestamp descending.\"\"\"
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(\"\"\"
                SELECT * FROM veto_archive 
                ORDER BY timestamp DESC 
                LIMIT %s
            \"\"\", (limit,))
            rows = c.fetchall()
            return [dict(row) for row in rows]
    except Exception:
        return []"""
content = content.replace(old_get_veto_archive, new_get_veto_archive)

# 3. save_prediction
old_save_prediction = """def save_prediction(prediction_data: dict) -> bool:
    \"\"\"Save a prediction to the ledger. Write-once, never update timestamp.\"\"\"
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(\"\"\"
            INSERT INTO prediction_ledger 
            (prediction_id, timestamp, asset, sector, thesis, confidence_score, 
             status, expected_timeline_days, proof_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        \"\"\", (
            prediction_data.get('prediction_id'),
            prediction_data.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
            prediction_data.get('asset'),
            prediction_data.get('sector', ''),
            prediction_data.get('thesis', ''),
            prediction_data.get('confidence_score', 0.0),
            prediction_data.get('status', 'pending'),
            prediction_data.get('expected_timeline_days', 30),
            prediction_data.get('proof_hash', ''),
            datetime.utcnow().isoformat() + 'Z',
            datetime.utcnow().isoformat() + 'Z'
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving prediction: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()"""

new_save_prediction = """def save_prediction(prediction_data: dict) -> bool:
    \"\"\"Save a prediction to the ledger. Write-once, never update timestamp.\"\"\"
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(\"\"\"
                INSERT INTO prediction_ledger 
                (prediction_id, timestamp, asset, sector, thesis, confidence_score, 
                 status, expected_timeline_days, proof_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            \"\"\", (
                prediction_data.get('prediction_id'),
                prediction_data.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
                prediction_data.get('asset'),
                prediction_data.get('sector', ''),
                prediction_data.get('thesis', ''),
                prediction_data.get('confidence_score', 0.0),
                prediction_data.get('status', 'pending'),
                prediction_data.get('expected_timeline_days', 30),
                prediction_data.get('proof_hash', ''),
                datetime.utcnow().isoformat() + 'Z',
                datetime.utcnow().isoformat() + 'Z'
            ))
            return True
    except Exception as e:
        print(f"Error saving prediction: {e}")
        return False"""
content = content.replace(old_save_prediction, new_save_prediction)

# 4. update_prediction_outcome
old_update_prediction_outcome = """def update_prediction_outcome(prediction_id: str, outcome_data: dict) -> bool:
    \"\"\"Update a prediction with its outcome. Can only update outcome fields.\"\"\"
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(\"\"\"
            UPDATE prediction_ledger SET
            actual_outcome = %s,
            actual_return_pct = %s,
            outcome_notes = %s,
            status = %s,
            updated_at = %s
            WHERE prediction_id = %s
        \"\"\", (
            outcome_data.get('outcome', ''),
            outcome_data.get('actual_return_pct', 0.0),
            outcome_data.get('notes', ''),
            'HIT' if outcome_data.get('outcome', '').lower() == 'correct' else 'MISS',
            datetime.utcnow().isoformat() + 'Z',
            prediction_id
        ))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        print(f"Error updating prediction outcome: {e}")
        return False
    finally:
        conn.close()"""

new_update_prediction_outcome = """def update_prediction_outcome(prediction_id: str, outcome_data: dict) -> bool:
    \"\"\"Update a prediction with its outcome. Can only update outcome fields.\"\"\"
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(\"\"\"
                UPDATE prediction_ledger SET
                actual_outcome = %s,
                actual_return_pct = %s,
                outcome_notes = %s,
                status = %s,
                updated_at = %s
                WHERE prediction_id = %s
            \"\"\", (
                outcome_data.get('outcome', ''),
                outcome_data.get('actual_return_pct', 0.0),
                outcome_data.get('notes', ''),
                'HIT' if outcome_data.get('outcome', '').lower() == 'correct' else 'MISS',
                datetime.utcnow().isoformat() + 'Z',
                prediction_id
            ))
            return c.rowcount > 0
    except Exception as e:
        print(f"Error updating prediction outcome: {e}")
        return False"""
content = content.replace(old_update_prediction_outcome, new_update_prediction_outcome)

# 5. save_veto
old_save_veto = """def save_veto(veto_data: dict) -> bool:
    \"\"\"Save a veto to the archive.\"\"\"
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(\"\"\"
            INSERT INTO veto_archive
            (veto_id, prediction_id, timestamp, asset, sector, rejection_reason,
             expected_loss_pct, proof_hash, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        \"\"\", (
            veto_data.get('veto_id'),
            veto_data.get('prediction_id', ''),
            veto_data.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
            veto_data.get('asset'),
            veto_data.get('sector', ''),
            veto_data.get('rejection_reason'),
            veto_data.get('expected_loss_pct', 0.0),
            veto_data.get('proof_hash', ''),
            datetime.utcnow().isoformat() + 'Z'
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving veto: {e}")
        return False
    finally:
        conn.close()"""

new_save_veto = """def save_veto(veto_data: dict) -> bool:
    \"\"\"Save a veto to the archive.\"\"\"
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(\"\"\"
                INSERT INTO veto_archive
                (veto_id, prediction_id, timestamp, asset, sector, rejection_reason,
                 expected_loss_pct, proof_hash, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            \"\"\", (
                veto_data.get('veto_id'),
                veto_data.get('prediction_id', ''),
                veto_data.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
                veto_data.get('asset'),
                veto_data.get('sector', ''),
                veto_data.get('rejection_reason'),
                veto_data.get('expected_loss_pct', 0.0),
                veto_data.get('proof_hash', ''),
                datetime.utcnow().isoformat() + 'Z'
            ))
            return True
    except Exception as e:
        print(f"Error saving veto: {e}")
        return False"""
content = content.replace(old_save_veto, new_save_veto)

# 6. update_veto_outcome
old_update_veto_outcome = """def update_veto_outcome(veto_id: str, outcome_data: dict) -> bool:
    \"\"\"Update veto with actual outcome after time passes.\"\"\"
    conn = get_db_connection()
    c = conn.cursor()
    try:
        actual_return = outcome_data.get('actual_return_pct', 0.0)
        expected_loss = outcome_data.get('expected_loss_pct', 0.0)
        veto_correct = actual_return < 0 if expected_loss > 0 else None
        avoided = abs(expected_loss - actual_return) if veto_correct and actual_return < 0 else 0
        
        c.execute(\"\"\"
            UPDATE veto_archive SET
            actual_outcome = %s,
            actual_return_pct = %s,
            avoided_drawdown = %s,
            veto_correct = %s,
            notes = %s
            WHERE veto_id = %s
        \"\"\", (
            outcome_data.get('outcome', ''),
            actual_return,
            avoided,
            veto_correct,
            outcome_data.get('notes', ''),
            veto_id
        ))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        print(f"Error updating veto outcome: {e}")
        return False
    finally:
        conn.close()"""

new_update_veto_outcome = """def update_veto_outcome(veto_id: str, outcome_data: dict) -> bool:
    \"\"\"Update veto with actual outcome after time passes.\"\"\"
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            actual_return = outcome_data.get('actual_return_pct', 0.0)
            expected_loss = outcome_data.get('expected_loss_pct', 0.0)
            veto_correct = actual_return < 0 if expected_loss > 0 else None
            avoided = abs(expected_loss - actual_return) if veto_correct and actual_return < 0 else 0
            
            c.execute(\"\"\"
                UPDATE veto_archive SET
                actual_outcome = %s,
                actual_return_pct = %s,
                avoided_drawdown = %s,
                veto_correct = %s,
                notes = %s
                WHERE veto_id = %s
            \"\"\", (
                outcome_data.get('outcome', ''),
                actual_return,
                avoided,
                veto_correct,
                outcome_data.get('notes', ''),
                veto_id
            ))
            return c.rowcount > 0
    except Exception as e:
        print(f"Error updating veto outcome: {e}")
        return False"""
content = content.replace(old_update_veto_outcome, new_update_veto_outcome)

# 7. calculate_ledger_stats
# We will do this via regex since it's long and repetitive, but let's just write the exact string replacing since it's safer.
import re
content = re.sub(r'def calculate_ledger_stats\(\) -> dict:.*?(?=def |$)', 
r'''def calculate_ledger_stats() -> dict:
    """Calculate statistics for the prediction ledger."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger")
            total = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'cleared'")
            approved = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'risk-rejected'")
            rejected = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
            with_outcome = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE actual_outcome = 'correct'")
            correct = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'cleared' AND actual_outcome IS NOT NULL AND actual_outcome != ''")
            cleared_with_outcome = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM prediction_ledger WHERE status = 'cleared' AND actual_outcome = 'correct'")
            cleared_correct = c.fetchone()[0] or 0
            
            c.execute("SELECT AVG(confidence_score) FROM prediction_ledger WHERE status = 'cleared'")
            avg_conf = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM veto_archive")
            total_vetoes = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM veto_archive WHERE actual_outcome IS NOT NULL AND actual_outcome != ''")
            vetoes_with_outcome = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM veto_archive WHERE veto_correct = true")
            vetoes_correct = c.fetchone()[0] or 0
            
            c.execute("SELECT SUM(avoided_drawdown) FROM veto_archive")
            avoided = c.fetchone()[0] or 0
            
            c.execute("""
                SELECT asset, status, confidence_score, thesis
                FROM prediction_ledger 
                WHERE status = 'cleared'
                ORDER BY confidence_score DESC LIMIT 1
            """)
            top = c.fetchone()
            
            return {
                'total_predictions': total,
                'approved': approved,
                'rejected': rejected,
                'approval_rate': (approved / total * 100) if total > 0 else 0,
                'accuracy': (correct / with_outcome * 100) if with_outcome > 0 else 0,
                'cleared_accuracy': (cleared_correct / cleared_with_outcome * 100) if cleared_with_outcome > 0 else 0,
                'avg_confidence': avg_conf,
                'total_vetoes': total_vetoes,
                'veto_accuracy': (vetoes_correct / vetoes_with_outcome * 100) if vetoes_with_outcome > 0 else 0,
                'drawdown_avoided': avoided,
                'resolved_outcomes': with_outcome,
                'top_prediction': dict(top) if top else None
            }
    except Exception as e:
        print(f"Error calculating stats: {e}")
        return {
            'total_predictions': 0, 'approved': 0, 'rejected': 0, 'approval_rate': 0,
            'accuracy': 0, 'cleared_accuracy': 0, 'avg_confidence': 0,
            'total_vetoes': 0, 'veto_accuracy': 0, 'drawdown_avoided': 0,
            'resolved_outcomes': 0, 'top_prediction': None
        }

''', content, flags=re.DOTALL)

with open('dashboard/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
