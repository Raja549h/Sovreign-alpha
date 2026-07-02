from database import get_connection
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from config import BILLING_DIR, PERFORMANCE_FEE_PCT, logger


class BillingMeter:
    """
    Local SQLite-based billing meter for Sovereign Alpha Fund.
    
    Tracks every inference call, logs timestamps and models,
    calculates performance fees, and generates reports.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or BILLING_DIR
        self.db_path = self.data_dir / "db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn: Optional[any] = None
        
        self._initialize_database()
        
        self.performance_fee_pct = PERFORMANCE_FEE_PCT
        self.total_alpha_generated = 0.0

    def _initialize_database(self):
        """Initialize SQLite database with required tables."""
        self.conn = get_connection()

        try:
            from dashboard.schemas import init_billing_db
            self.conn.close() # Close existing connection since init_billing_db creates its own
            self.conn = init_billing_db(self.db_path)
        except Exception as e:
            logger.warning(f"Meter DB init failed: {e}")
        logger.info(f"Billing database initialized at {self.db_path}")

    def log_inference(self, agent_id: str, model: str, input_tokens: int, 
                     output_tokens: int, latency_ms: float, 
                     decision_id: Optional[str] = None,
                     status: str = "completed") -> int:
        """
        Log an inference call to the database.
        Estimates cost based on Cerebras pricing (approximate).
        """
        total_tokens = input_tokens + output_tokens
        
        cost_per_million = 0.0
        if "70b" in model.lower():
            cost_per_million = 0.88
        elif "8b" in model.lower():
            cost_per_million = 0.10
        elif "large" in model.lower():
            cost_per_million = 0.10
        
        cost_estimate = (total_tokens / 1_000_000) * cost_per_million
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO inference_log 
            (timestamp, agent_id, model, input_tokens, output_tokens, 
             total_tokens, latency_ms, cost_estimate, decision_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datetime.utcnow().isoformat() + 'Z',
            agent_id,
            model,
            input_tokens,
            output_tokens,
            total_tokens,
            latency_ms,
            cost_estimate,
            decision_id,
            status
        ))
        
        self.conn.commit()
        
        return cursor.lastrowid

    def log_performance(self, decision_id: str, trade_action: str, symbol: str,
                       position_value: float, alpha_generated: float,
                       status: str = "pending") -> int:
        """
        Log performance from an approved trade.
        Calculates performance fee at configured rate.
        """
        fee_calculated = alpha_generated * (self.performance_fee_pct / 100)
        
        self.total_alpha_generated += alpha_generated
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO performance_log
            (timestamp, decision_id, trade_action, symbol, position_value,
             alpha_generated, fee_calculated, fee_paid, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datetime.utcnow().isoformat() + 'Z',
            decision_id,
            trade_action,
            symbol,
            position_value,
            alpha_generated,
            fee_calculated,
            0.0,
            status
        ))
        
        self.conn.commit()
        
        logger.info(f"Performance logged: {symbol} {trade_action}, "
                   f"Alpha: ${alpha_generated:,.2f}, Fee: ${fee_calculated:,.2f}")
        
        return cursor.lastrowid

    def get_inference_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get inference statistics for the last N days."""
        cursor = self.conn.cursor()
        
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_calls,
                SUM(total_tokens) as total_tokens,
                SUM(cost_estimate) as total_cost,
                AVG(latency_ms) as avg_latency,
                model,
                agent_id
            FROM inference_log
            WHERE timestamp >= %s
            GROUP BY model, agent_id
            ORDER BY total_calls DESC
        """, (cutoff,))
        
        rows = cursor.fetchall()
        
        stats = {
            'period_days': days,
            'total_calls': sum(r['total_calls'] for r in rows),
            'total_tokens': sum(r['total_tokens'] for r in rows),
            'total_cost': sum(r['total_cost'] for r in rows),
            'avg_latency_ms': sum(r['avg_latency'] for r in rows) / len(rows) if rows else 0,
            'by_model': [
                {
                    'model': r['model'],
                    'calls': r['total_calls'],
                    'tokens': r['total_tokens'],
                    'cost': r['total_cost']
                }
                for r in rows
            ]
        }
        
        return stats

    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get performance summary for the last N days."""
        cursor = self.conn.cursor()
        
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
        
        cursor.execute("""
            SELECT 
                SUM(alpha_generated) as total_alpha,
                SUM(fee_calculated) as total_fees,
                COUNT(*) as total_trades,
                symbol,
                trade_action
            FROM performance_log
            WHERE timestamp >= %s
            GROUP BY symbol, trade_action
            ORDER BY total_alpha DESC
        """, (cutoff,))
        
        rows = cursor.fetchall()
        
        return {
            'period_days': days,
            'total_alpha': sum(r['total_alpha'] for r in rows),
            'total_fees': sum(r['total_fees'] for r in rows),
            'total_trades': sum(r['total_trades'] for r in rows),
            'by_symbol': [
                {
                    'symbol': r['symbol'],
                    'action': r['trade_action'],
                    'alpha': r['total_alpha'],
                    'fees': r['total_fees']
                }
                for r in rows
            ]
        }

    def generate_monthly_report(self, month: Optional[str] = None) -> Dict[str, Any]:
        """Generate monthly billing report."""
        if month is None:
            month = datetime.utcnow().strftime('%Y-%m')
        
        cursor = self.conn.cursor()
        
        month_start = f"{month}-01"
        
        try:
            next_month = datetime.strptime(month_start, '%Y-%m') + timedelta(days=32)
            month_end = next_month.strftime('%Y-%m') + '-01'
        except Exception:
            month_end = f"{month}-31"
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_inferences,
                SUM(total_tokens) as total_tokens,
                SUM(cost_estimate) as total_cost
            FROM inference_log
            WHERE timestamp >= %s AND timestamp < %s
        """, (month_start, month_end))
        
        inference_row = cursor.fetchone()
        
        cursor.execute("""
            SELECT 
                SUM(alpha_generated) as total_alpha,
                SUM(fee_calculated) as total_fees,
                COUNT(*) as total_trades
            FROM performance_log
            WHERE timestamp >= %s AND timestamp < %s
        """, (month_start, month_end))
        
        performance_row = cursor.fetchone()
        
        report = {
            'month': month,
            'inference': {
                'total_calls': inference_row['total_inferences'] or 0,
                'total_tokens': inference_row['total_tokens'] or 0,
                'estimated_cost': inference_row['total_cost'] or 0.0
            },
            'performance': {
                'total_alpha': performance_row['total_alpha'] or 0.0,
                'performance_fees': performance_row['total_fees'] or 0.0,
                'total_trades': performance_row['total_trades'] or 0
            },
            'fee_rate_pct': self.performance_fee_pct,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        cursor.execute("""
            INSERT INTO monthly_summary
            (month, total_inferences, total_tokens, total_cost,
             alpha_generated, performance_fee, report_generated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            month,
            report['inference']['total_calls'],
            report['inference']['total_tokens'],
            report['inference']['estimated_cost'],
            report['performance']['total_alpha'],
            report['performance']['performance_fees'],
            report['generated_at']
        ))
        
        self.conn.commit()
        
        return report

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Billing database connection closed")


def create_billing_meter() -> BillingMeter:
    return BillingMeter()


if __name__ == "__main__":
    meter = create_billing_meter()
    
    print("\n=== Testing Billing Meter ===")
    
    meter.log_inference(
        agent_id="analyst",
        model=LLM_MODEL,
        input_tokens=512,
        output_tokens=1024,
        latency_ms=2500.0,
        decision_id="DEC-001",
        status="completed"
    )
    
    meter.log_inference(
        agent_id="risk_manager",
        model=LLM_MODEL,
        input_tokens=384,
        output_tokens=512,
        latency_ms=1800.0,
        decision_id="DEC-001",
        status="completed"
    )
    
    meter.log_performance(
        decision_id="DEC-001",
        trade_action="BUY",
        symbol="NVDA",
        position_value=892400.0,
        alpha_generated=50000.0,
        status="pending"
    )
    
    print("\n=== Inference Stats ===")
    inference_stats = meter.get_inference_stats()
    print(f"Total Calls: {inference_stats['total_calls']}")
    print(f"Total Tokens: {inference_stats['total_tokens']}")
    print(f"Total Cost: ${inference_stats['total_cost']:.4f}")
    
    print("\n=== Performance Summary ===")
    perf_summary = meter.get_performance_summary()
    print(f"Total Alpha: ${perf_summary['total_alpha']:,.2f}")
    print(f"Performance Fees: ${perf_summary['total_fees']:,.2f}")
    print(f"Total Trades: {perf_summary['total_trades']}")
    
    print("\n=== Monthly Report ===")
    report = meter.generate_monthly_report()
    print(f"Month: {report['month']}")
    print(f"Inference Calls: {report['inference']['total_calls']}")
    print(f"Alpha Generated: ${report['performance']['total_alpha']:,.2f}")
    print(f"Performance Fees: ${report['performance']['performance_fees']:,.2f}")
    
    meter.close()