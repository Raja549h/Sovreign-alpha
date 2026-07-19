import re

with open('agents/risk_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace block 1:
old_1 = """def _save_veto(self, veto: Dict):
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute(\"\"\"
                INSERT INTO veto_archive
                (veto_id, prediction_id, timestamp, asset, sector, rejection_reason, expected_loss_pct, proof_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            \"\"\", (
                veto.get('veto_id', str(uuid.uuid4())),
                veto.get('prediction_id', ''),
                veto.get('timestamp', datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')),
                veto.get('asset', ''),
                veto.get('sector', ''),
                veto.get('rejection_reason', ''),
                veto.get('expected_loss_pct', 0.0),
                veto.get('proof_hash', '')
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"2026-07-19 12:21:15 | WARNING | Veto save failed: {e}")"""

new_1 = """def _save_veto(self, veto: Dict):
        try:
            with get_connection() as conn:
                c = conn.cursor()
                c.execute(\"\"\"
                    INSERT INTO veto_archive
                    (veto_id, prediction_id, timestamp, asset, sector, rejection_reason, expected_loss_pct, proof_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                \"\"\", (
                    veto.get('veto_id', str(uuid.uuid4())),
                    veto.get('prediction_id', ''),
                    veto.get('timestamp', datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')),
                    veto.get('asset', ''),
                    veto.get('sector', ''),
                    veto.get('rejection_reason', ''),
                    veto.get('expected_loss_pct', 0.0),
                    veto.get('proof_hash', '')
                ))
        except Exception as e:
            print(f"2026-07-19 12:21:15 | WARNING | Veto save failed: {e}")"""
            
# We don't know the exact print timestamp, so let's just do a regex replace
content = re.sub(r'conn = get_connection\(\)\s+c = conn\.cursor\(\)\s+c\.execute\(\"\"\"\s+INSERT INTO veto_archive.*?conn\.close\(\)', r'''with get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                INSERT INTO veto_archive
                (veto_id, prediction_id, timestamp, asset, sector, rejection_reason, expected_loss_pct, proof_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                veto.get('veto_id', str(uuid.uuid4())),
                veto.get('prediction_id', ''),
                veto.get('timestamp', datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')),
                veto.get('asset', ''),
                veto.get('sector', ''),
                veto.get('rejection_reason', ''),
                veto.get('expected_loss_pct', 0.0),
                veto.get('proof_hash', '')
            ))''', content, flags=re.DOTALL)


content = re.sub(r'def get_veto_stats\(self\) -> Dict:.*?conn\.close\(\).*?return stats', r'''def get_veto_stats(self) -> Dict:
        stats = {'total_vetoes': 0, 'drawdown_avoided': 0.0, 'accuracy': 0.0}
        try:
            with get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) as total FROM veto_archive")
                stats['total_vetoes'] = c.fetchone()['total'] or 0
                
                c.execute("SELECT SUM(avoided_drawdown) as avoided FROM veto_archive")
                stats['drawdown_avoided'] = c.fetchone()['avoided'] or 0.0
                
                c.execute("SELECT COUNT(*) as total FROM veto_archive WHERE actual_outcome IS NOT NULL")
                resolved = c.fetchone()['total'] or 0
                
                if resolved > 0:
                    c.execute("SELECT COUNT(*) as correct FROM veto_archive WHERE veto_correct = true")
                    correct = c.fetchone()['correct'] or 0
                    stats['accuracy'] = (correct / resolved) * 100
        except Exception:
            pass
        return stats''', content, flags=re.DOTALL)

with open('agents/risk_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
