"""Rule resolver for querying the rule registry."""
from typing import List, Dict, Any, Optional
from datetime import date
from src.db.connection import get_db


class RuleResolver:
    """Resolver for querying rules from the registry."""
    
    def __init__(self):
        self.db = get_db()
    
    def get_rule(
        self,
        parameter: str,
        programme: str = 'ALL',
        batch: str = 'ALL',
        as_of_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific rule value.
        
        Args:
            parameter: Rule parameter (e.g., 'min_attendance_pct')
            programme: Student programme code
            batch: Student batch
            as_of_date: Date for rule validity
        
        Returns:
            Rule record or None
        """
        as_of_date = as_of_date or date.today()
        
        with self.db.transaction() as conn:
            # Query with scope matching
            cursor = conn.execute(
                """
                SELECT rule_id, description, parameter, operator, value,
                       scope_programmes, scope_batches, effective_from, effective_to,
                       source_doc_id, source_section, status
                FROM rule_registry
                WHERE parameter = ?
                  AND status = 'active'
                  AND (scope_programmes = 'ALL' OR scope_programmes LIKE ?)
                  AND (scope_batches = 'ALL' OR scope_batches LIKE ?)
                  AND effective_from <= ?
                  AND (effective_to IS NULL OR effective_to = '' OR effective_to > ?)
                ORDER BY 
                  CASE WHEN scope_programmes = 'ALL' THEN 1 ELSE 0 END,
                  CASE WHEN scope_batches = 'ALL' THEN 1 ELSE 0 END,
                  effective_from DESC
                LIMIT 1
                """,
                (
                    parameter,
                    f"%{programme}%",
                    f"%{batch}%",
                    as_of_date.isoformat(),
                    as_of_date.isoformat()
                )
            )
            
            row = cursor.fetchone()
        
        return dict(row) if row else None
    
    def get_all_rules(
        self,
        as_of_date: Optional[date] = None,
        status: str = 'active'
    ) -> List[Dict[str, Any]]:
        """Get all active rules."""
        as_of_date = as_of_date or date.today()
        
        with self.db.transaction() as conn:
            cursor = conn.execute(
                """
                SELECT rule_id, description, parameter, operator, value,
                       scope_programmes, scope_batches, effective_from, effective_to,
                       source_doc_id, source_section, status
                FROM rule_registry
                WHERE status = ?
                  AND effective_from <= ?
                  AND (effective_to IS NULL OR effective_to = '' OR effective_to > ?)
                ORDER BY parameter, effective_from DESC
                """,
                (status, as_of_date.isoformat(), as_of_date.isoformat())
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def resolve_value(
        self,
        parameter: str,
        programme: str = 'ALL',
        batch: str = 'ALL',
        as_of_date: Optional[date] = None,
        default: Any = None
    ) -> Any:
        """
        Resolve a rule value with fallback to default.
        
        Returns:
            Parsed value or default
        """
        rule = self.get_rule(parameter, programme, batch, as_of_date)
        
        if not rule:
            return default
        
        value_str = rule['value']
        
        # Try to parse as number
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            return value_str
