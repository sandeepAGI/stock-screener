#!/usr/bin/env python3
"""
User-Controlled Data Quality Gating System
Core innovation: Analysts control when data is "ready" for analysis
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GateStatus(Enum):
    """Data quality gate status"""
    PENDING = "pending"           # Awaiting user review
    APPROVED = "approved"         # User approved for analysis
    REJECTED = "rejected"         # User rejected - needs refresh
    BLOCKED = "blocked"           # Automatically blocked by quality rules
    EXPIRED = "expired"           # Approval expired due to age


class ComponentType(Enum):
    """Data component types"""
    FUNDAMENTALS = "fundamentals"
    PRICE_DATA = "price_data"
    NEWS_DATA = "news_data"
    SENTIMENT_DATA = "sentiment_data"
    ALL_COMPONENTS = "all_components"


@dataclass
class QualityGateRule:
    """Quality gate rule configuration"""
    component: str
    metric: str
    threshold: float
    operator: str  # >, <, >=, <=, ==
    block_analysis: bool = True
    description: str = ""


@dataclass
class QualityGateResult:
    """Result of quality gate evaluation"""
    component: str
    gate_id: str
    status: GateStatus
    quality_score: float
    approval_timestamp: Optional[datetime]
    approved_by: Optional[str]
    expires_at: Optional[datetime]
    blocking_rules: List[str]
    metadata: Dict[str, Any]


@dataclass
class ComponentQualityStatus:
    """Quality status for a data component"""
    component: ComponentType
    symbol: str
    quality_score: float
    data_freshness_hours: float
    record_count: int
    last_updated: datetime
    quality_issues: List[str]
    gate_status: GateStatus
    gate_result: Optional[QualityGateResult]


class QualityGatingSystem:
    """
    User-Controlled Data Quality Gating System
    
    Core Features:
    - User approval workflow for data analysis
    - Configurable quality thresholds and blocking rules
    - Data version control and staleness tracking
    - Component-level and system-level gating
    - Automatic expiration and re-approval workflows
    """
    
    def __init__(self, db_manager, config_path: Optional[str] = None):
        """Initialize Quality Gating System"""
        self.db_manager = db_manager
        self.config_path = config_path or "config/quality_gates.json"
        
        # Load quality gate rules
        self.rules = self._load_gate_rules()
        
        # Initialize gating database
        self._init_gating_database()
        
        logger.info("Quality Gating System initialized")
    
    def _init_gating_database(self):
        """Initialize quality gating tables in database"""
        if not self.db_manager.connect():
            raise Exception("Failed to connect to database")
        
        cursor = self.db_manager.connection.cursor()
        
        # Quality gates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_gates (
                gate_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                component TEXT NOT NULL,
                status TEXT NOT NULL,
                quality_score REAL,
                approval_timestamp TEXT,
                approved_by TEXT,
                expires_at TEXT,
                blocking_rules TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (symbol) REFERENCES stocks (symbol)
            )
        """)
        
        # Data versions table for tracking approved datasets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_versions (
                version_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                component TEXT NOT NULL,
                data_snapshot TEXT,
                approval_gate_id TEXT,
                created_at TEXT NOT NULL,
                approved_at TEXT,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (symbol) REFERENCES stocks (symbol),
                FOREIGN KEY (approval_gate_id) REFERENCES quality_gates (gate_id)
            )
        """)
        
        # Quality gate rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_gate_rules (
                rule_id TEXT PRIMARY KEY,
                component TEXT NOT NULL,
                metric TEXT NOT NULL,
                threshold REAL NOT NULL,
                operator TEXT NOT NULL,
                block_analysis INTEGER DEFAULT 1,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        self.db_manager.connection.commit()
        self.db_manager.close()
        
        logger.info("Quality gating database initialized")
    
    def _load_gate_rules(self) -> List[QualityGateRule]:
        """Load quality gate rules from configuration"""
        default_rules = [
            QualityGateRule(
                component="fundamentals",
                metric="data_quality_score",
                threshold=0.7,
                operator=">=",
                block_analysis=True,
                description="Fundamental data quality must be >= 70%"
            ),
            QualityGateRule(
                component="price_data",
                metric="data_freshness_hours",
                threshold=48,
                operator="<=",
                block_analysis=True,
                description="Price data must be <= 48 hours old"
            ),
            QualityGateRule(
                component="news_data",
                metric="record_count",
                threshold=3,
                operator=">=",
                block_analysis=False,
                description="News data should have >= 3 articles (warning only)"
            ),
            QualityGateRule(
                component="sentiment_data",
                metric="data_quality_score",
                threshold=0.6,
                operator=">=",
                block_analysis=False,
                description="Sentiment quality should be >= 60% (warning only)"
            )
        ]
        
        # Try to load from file, fall back to defaults
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    rules_data = json.load(f)
                    return [QualityGateRule(**rule) for rule in rules_data.get("rules", [])]
        except Exception as e:
            logger.warning(f"Failed to load gate rules from {self.config_path}: {e}")
        
        return default_rules
    
    # ==================== QUALITY EVALUATION ====================
    
    def evaluate_component_quality(self, symbol: str, component: ComponentType) -> ComponentQualityStatus:
        """
        Evaluate quality status for a specific data component
        
        Args:
            symbol: Stock symbol
            component: Data component to evaluate
            
        Returns:
            ComponentQualityStatus with complete quality assessment
        """
        try:
            logger.info(f"Evaluating {component.value} quality for {symbol}")
            
            if not self.db_manager.connect():
                raise Exception("Failed to connect to database")
            
            cursor = self.db_manager.connection.cursor()
            
            # Get component-specific quality metrics
            quality_metrics = self._get_component_metrics(symbol, component, cursor)
            
            # Evaluate against quality rules
            blocking_rules = []
            warning_rules = []
            
            for rule in self.rules:
                if rule.component == component.value or rule.component == "all_components":
                    if self._evaluate_rule(quality_metrics, rule):
                        if rule.block_analysis:
                            blocking_rules.append(rule.description)
                        else:
                            warning_rules.append(rule.description)
            
            # Check for existing approval first (regardless of blocking status)
            existing_gate = self._get_latest_gate(symbol, component.value, cursor)
            
            # Determine gate status
            if blocking_rules:
                gate_status = GateStatus.BLOCKED
            else:
                if existing_gate and existing_gate.status == GateStatus.APPROVED:
                    # Check if approval is still valid
                    if existing_gate.expires_at and datetime.now() > existing_gate.expires_at:
                        gate_status = GateStatus.EXPIRED
                    else:
                        gate_status = GateStatus.APPROVED
                else:
                    gate_status = GateStatus.PENDING
            
            # Create quality status
            status = ComponentQualityStatus(
                component=component,
                symbol=symbol,
                quality_score=quality_metrics.get("data_quality_score", 0.0),
                data_freshness_hours=quality_metrics.get("data_freshness_hours", 999),
                record_count=quality_metrics.get("record_count", 0),
                last_updated=quality_metrics.get("last_updated", datetime.now()),
                quality_issues=blocking_rules + warning_rules,
                gate_status=gate_status,
                gate_result=existing_gate
            )
            
            return status
            
        except Exception as e:
            logger.error(f"Quality evaluation failed for {symbol}/{component.value}: {str(e)}")
            raise
        finally:
            self.db_manager.close()
    
    def evaluate_system_quality(self, symbol: str) -> Dict[str, ComponentQualityStatus]:
        """
        Evaluate quality status for all components of a stock
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict mapping component names to quality status
        """
        logger.info(f"Evaluating system-wide quality for {symbol}")
        
        results = {}
        components = [ComponentType.FUNDAMENTALS, ComponentType.PRICE_DATA, 
                     ComponentType.NEWS_DATA, ComponentType.SENTIMENT_DATA]
        
        for component in components:
            try:
                results[component.value] = self.evaluate_component_quality(symbol, component)
            except Exception as e:
                logger.error(f"Failed to evaluate {component.value} for {symbol}: {e}")
                # Create error status
                results[component.value] = ComponentQualityStatus(
                    component=component,
                    symbol=symbol,
                    quality_score=0.0,
                    data_freshness_hours=999,
                    record_count=0,
                    last_updated=datetime.now(),
                    quality_issues=[f"Evaluation failed: {str(e)}"],
                    gate_status=GateStatus.BLOCKED,
                    gate_result=None
                )
        
        return results
    
    # ==================== USER APPROVAL WORKFLOW ====================
    
    def request_approval(self, symbol: str, component: ComponentType, 
                        approved_by: str = "user") -> QualityGateResult:
        """
        Request user approval for data component
        
        Args:
            symbol: Stock symbol
            component: Data component
            approved_by: User identifier
            
        Returns:
            QualityGateResult with approval status
        """
        logger.info(f"Requesting approval for {symbol}/{component.value}")
        
        # Evaluate current quality
        quality_status = self.evaluate_component_quality(symbol, component)
        
        # Create new gate
        gate_id = f"{symbol}_{component.value}_{int(datetime.now().timestamp())}"
        
        # Determine if auto-blocked
        if quality_status.gate_status == GateStatus.BLOCKED:
            gate_result = QualityGateResult(
                component=component.value,
                gate_id=gate_id,
                status=GateStatus.BLOCKED,
                quality_score=quality_status.quality_score,
                approval_timestamp=None,
                approved_by=None,
                expires_at=None,
                blocking_rules=quality_status.quality_issues,
                metadata={"auto_blocked": True}
            )
        else:
            # Create pending approval
            gate_result = QualityGateResult(
                component=component.value,
                gate_id=gate_id,
                status=GateStatus.PENDING,
                quality_score=quality_status.quality_score,
                approval_timestamp=None,
                approved_by=None,
                expires_at=None,
                blocking_rules=[],
                metadata={"requested_by": approved_by}
            )
        
        # Save to database
        self._save_gate_result(symbol, gate_result)
        
        return gate_result
    
    def approve_component(self, symbol: str, component: ComponentType, 
                         approved_by: str = "user", 
                         approval_duration_hours: int = 24) -> QualityGateResult:
        """
        User approval of data component for analysis
        
        Args:
            symbol: Stock symbol
            component: Data component
            approved_by: User identifier
            approval_duration_hours: How long approval is valid
            
        Returns:
            QualityGateResult with approval status
        """
        logger.info(f"Approving {symbol}/{component.value} by {approved_by}")
        
        # Get or create gate
        if not self.db_manager.connect():
            raise Exception("Failed to connect to database")
        
        cursor = self.db_manager.connection.cursor()
        existing_gate = self._get_latest_gate(symbol, component.value, cursor)
        self.db_manager.close()
        
        if not existing_gate:
            # Create new approval request first
            existing_gate = self.request_approval(symbol, component, approved_by)
        
        # Check if can be approved (not blocked)
        quality_status = self.evaluate_component_quality(symbol, component)
        if quality_status.gate_status == GateStatus.BLOCKED:
            raise Exception(f"Cannot approve {component.value} - blocked by quality rules: {quality_status.quality_issues}")
        
        # Create approval
        approval_timestamp = datetime.now()
        expires_at = approval_timestamp + timedelta(hours=approval_duration_hours)
        
        gate_result = QualityGateResult(
            component=component.value,
            gate_id=existing_gate.gate_id,
            status=GateStatus.APPROVED,
            quality_score=quality_status.quality_score,
            approval_timestamp=approval_timestamp,
            approved_by=approved_by,
            expires_at=expires_at,
            blocking_rules=[],
            metadata={
                "approval_duration_hours": approval_duration_hours,
                "quality_at_approval": quality_status.quality_score
            }
        )
        
        # Save approval
        self._save_gate_result(symbol, gate_result)
        
        # Create data version snapshot
        self._create_data_version(symbol, component, gate_result)
        
        logger.info(f"Approved {symbol}/{component.value} until {expires_at}")
        
        return gate_result
    
    def reject_component(self, symbol: str, component: ComponentType, 
                        rejected_by: str = "user", 
                        reason: str = "") -> QualityGateResult:
        """
        User rejection of data component
        
        Args:
            symbol: Stock symbol
            component: Data component
            rejected_by: User identifier
            reason: Rejection reason
            
        Returns:
            QualityGateResult with rejection status
        """
        logger.info(f"Rejecting {symbol}/{component.value} by {rejected_by}: {reason}")
        
        # Get current quality
        quality_status = self.evaluate_component_quality(symbol, component)
        
        # Create rejection
        gate_id = f"{symbol}_{component.value}_reject_{int(datetime.now().timestamp())}"
        
        gate_result = QualityGateResult(
            component=component.value,
            gate_id=gate_id,
            status=GateStatus.REJECTED,
            quality_score=quality_status.quality_score,
            approval_timestamp=None,
            approved_by=None,
            expires_at=None,
            blocking_rules=[],
            metadata={
                "rejected_by": rejected_by,
                "rejection_reason": reason,
                "rejection_timestamp": datetime.now().isoformat()
            }
        )
        
        # Save rejection
        self._save_gate_result(symbol, gate_result)
        
        return gate_result
    
    # ==================== ANALYSIS CONTROL ====================
    
    def is_analysis_allowed(self, symbol: str, required_components: Optional[List[ComponentType]] = None) -> Dict[str, Any]:
        """
        Check if analysis is allowed for a stock
        
        Args:
            symbol: Stock symbol
            required_components: Components required for analysis (default: all)
            
        Returns:
            Dict with analysis permission status and details
        """
        if required_components is None:
            required_components = [ComponentType.FUNDAMENTALS, ComponentType.PRICE_DATA, 
                                 ComponentType.NEWS_DATA, ComponentType.SENTIMENT_DATA]
        
        logger.info(f"Checking analysis permission for {symbol}")
        
        # Evaluate all component quality
        component_status = self.evaluate_system_quality(symbol)
        
        # Check each required component
        analysis_allowed = True
        blocking_components = []
        warning_components = []
        component_details = {}
        
        for component in required_components:
            status = component_status[component.value]
            component_details[component.value] = {
                "gate_status": status.gate_status.value,
                "quality_score": status.quality_score,
                "data_freshness_hours": status.data_freshness_hours,
                "quality_issues": status.quality_issues
            }
            
            if status.gate_status in [GateStatus.BLOCKED, GateStatus.REJECTED]:
                analysis_allowed = False
                blocking_components.append(component.value)
            elif status.gate_status in [GateStatus.PENDING, GateStatus.EXPIRED]:
                analysis_allowed = False
                warning_components.append(component.value)
        
        result = {
            "symbol": symbol,
            "analysis_allowed": analysis_allowed,
            "blocking_components": blocking_components,
            "warning_components": warning_components,
            "component_details": component_details,
            "required_components": [c.value for c in required_components],
            "checked_at": datetime.now().isoformat()
        }
        
        logger.info(f"Analysis allowed for {symbol}: {analysis_allowed}")
        
        return result
    
    def get_approved_data_version(self, symbol: str, component: ComponentType) -> Optional[Dict[str, Any]]:
        """
        Get the approved data version for analysis
        
        Args:
            symbol: Stock symbol
            component: Data component
            
        Returns:
            Approved data version or None if not approved
        """
        if not self.db_manager.connect():
            raise Exception("Failed to connect to database")
        
        try:
            cursor = self.db_manager.connection.cursor()
            
            # Get active approved version
            cursor.execute("""
                SELECT version_id, data_snapshot, approved_at, expires_at
                FROM data_versions
                WHERE symbol = ? AND component = ? AND is_active = 1
                AND approved_at IS NOT NULL
                AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY approved_at DESC
                LIMIT 1
            """, (symbol, component.value, datetime.now().isoformat()))
            
            result = cursor.fetchone()
            if result:
                return {
                    "version_id": result[0],
                    "data_snapshot": json.loads(result[1]) if result[1] else None,
                    "approved_at": result[2],
                    "expires_at": result[3]
                }
            
            return None
            
        finally:
            self.db_manager.close()
    
    # ==================== BULK OPERATIONS ====================
    
    def bulk_evaluate_quality(self, symbols: List[str]) -> Dict[str, Dict[str, ComponentQualityStatus]]:
        """
        Evaluate quality for multiple stocks
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dict mapping symbols to component quality status
        """
        logger.info(f"Bulk quality evaluation for {len(symbols)} stocks")
        
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.evaluate_system_quality(symbol)
            except Exception as e:
                logger.error(f"Bulk evaluation failed for {symbol}: {e}")
                results[symbol] = {}
        
        return results
    
    def bulk_approve_components(self, approvals: List[Tuple[str, ComponentType]], 
                               approved_by: str = "user") -> Dict[str, QualityGateResult]:
        """
        Bulk approve multiple components
        
        Args:
            approvals: List of (symbol, component) tuples
            approved_by: User identifier
            
        Returns:
            Dict mapping approval keys to gate results
        """
        logger.info(f"Bulk approving {len(approvals)} components")
        
        results = {}
        
        for symbol, component in approvals:
            try:
                key = f"{symbol}_{component.value}"
                results[key] = self.approve_component(symbol, component, approved_by)
            except Exception as e:
                logger.error(f"Bulk approval failed for {symbol}/{component.value}: {e}")
                # Create error result
                results[key] = QualityGateResult(
                    component=component.value,
                    gate_id=f"error_{key}",
                    status=GateStatus.BLOCKED,
                    quality_score=0.0,
                    approval_timestamp=None,
                    approved_by=None,
                    expires_at=None,
                    blocking_rules=[f"Approval failed: {str(e)}"],
                    metadata={"error": True}
                )
        
        return results
    
    # ==================== HELPER METHODS ====================
    
    def _get_component_metrics(self, symbol: str, component: ComponentType, cursor) -> Dict[str, Any]:
        """Get quality metrics for a specific component"""
        metrics = {
            "data_quality_score": 0.0,
            "data_freshness_hours": 999,
            "record_count": 0,
            "last_updated": datetime.now()
        }
        
        try:
            if component == ComponentType.FUNDAMENTALS:
                cursor.execute("""
                    SELECT reporting_date FROM fundamental_data 
                    WHERE symbol = ? ORDER BY reporting_date DESC LIMIT 1
                """, (symbol,))
                result = cursor.fetchone()
                if result:
                    last_updated = datetime.fromisoformat(result[0])
                    metrics["last_updated"] = last_updated
                    metrics["data_freshness_hours"] = (datetime.now() - last_updated).total_seconds() / 3600
                    metrics["data_quality_score"] = 0.9  # High quality for fundamentals
                    metrics["record_count"] = 1
            
            elif component == ComponentType.PRICE_DATA:
                cursor.execute("""
                    SELECT MAX(date) FROM price_data WHERE symbol = ?
                """, (symbol,))
                result = cursor.fetchone()
                if result and result[0]:
                    # Price data stores date as string, convert to datetime
                    last_date = datetime.strptime(result[0], '%Y-%m-%d')
                    metrics["last_updated"] = last_date
                    metrics["data_freshness_hours"] = (datetime.now() - last_date).total_seconds() / 3600
                    metrics["data_quality_score"] = 0.95  # Very high quality for price data
                    
                    cursor.execute("SELECT COUNT(*) FROM price_data WHERE symbol = ?", (symbol,))
                    count_result = cursor.fetchone()
                    metrics["record_count"] = count_result[0] if count_result else 0
            
            elif component == ComponentType.NEWS_DATA:
                cursor.execute("""
                    SELECT COUNT(*), MAX(publish_date) FROM news_articles WHERE symbol = ?
                """, (symbol,))
                result = cursor.fetchone()
                if result and result[1]:
                    metrics["record_count"] = result[0]
                    last_updated = datetime.fromisoformat(result[1])
                    metrics["last_updated"] = last_updated
                    metrics["data_freshness_hours"] = (datetime.now() - last_updated).total_seconds() / 3600
                    # Quality based on article count
                    metrics["data_quality_score"] = min(0.9, result[0] / 10.0) if result[0] > 0 else 0.0
            
            elif component == ComponentType.SENTIMENT_DATA:
                cursor.execute("""
                    SELECT COUNT(*), MAX(date) FROM daily_sentiment WHERE symbol = ?
                """, (symbol,))
                result = cursor.fetchone()
                if result and result[1]:
                    metrics["record_count"] = result[0]
                    last_date = datetime.strptime(result[1], '%Y-%m-%d')
                    metrics["last_updated"] = last_date
                    metrics["data_freshness_hours"] = (datetime.now() - last_date).total_seconds() / 3600
                    # Quality based on sentiment record count
                    metrics["data_quality_score"] = min(0.8, result[0] / 30.0) if result[0] > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"Failed to get metrics for {symbol}/{component.value}: {e}")
        
        return metrics
    
    def _evaluate_rule(self, metrics: Dict[str, Any], rule: QualityGateRule) -> bool:
        """Evaluate a quality rule against metrics"""
        if rule.metric not in metrics:
            return False
        
        value = metrics[rule.metric]
        threshold = rule.threshold
        
        if rule.operator == ">=":
            return value < threshold  # Rule fails if value is below threshold
        elif rule.operator == "<=":
            return value > threshold  # Rule fails if value is above threshold
        elif rule.operator == ">":
            return value <= threshold
        elif rule.operator == "<":
            return value >= threshold
        elif rule.operator == "==":
            return value != threshold
        
        return False
    
    def _get_latest_gate(self, symbol: str, component: str, cursor) -> Optional[QualityGateResult]:
        """Get latest gate result for symbol/component"""
        cursor.execute("""
            SELECT gate_id, status, quality_score, approval_timestamp, 
                   approved_by, expires_at, blocking_rules, metadata
            FROM quality_gates
            WHERE symbol = ? AND component = ?
            ORDER BY updated_at DESC
            LIMIT 1
        """, (symbol, component))
        
        result = cursor.fetchone()
        if result:
            return QualityGateResult(
                component=component,
                gate_id=result[0],
                status=GateStatus(result[1]),
                quality_score=result[2] or 0.0,
                approval_timestamp=datetime.fromisoformat(result[3]) if result[3] else None,
                approved_by=result[4],
                expires_at=datetime.fromisoformat(result[5]) if result[5] else None,
                blocking_rules=json.loads(result[6]) if result[6] else [],
                metadata=json.loads(result[7]) if result[7] else {}
            )
        
        return None
    
    def _save_gate_result(self, symbol: str, gate_result: QualityGateResult):
        """Save gate result to database"""
        if not self.db_manager.connect():
            raise Exception("Failed to connect to database")
        
        try:
            cursor = self.db_manager.connection.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO quality_gates
                (gate_id, symbol, component, status, quality_score, approval_timestamp,
                 approved_by, expires_at, blocking_rules, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gate_result.gate_id,
                symbol,
                gate_result.component,
                gate_result.status.value,
                gate_result.quality_score,
                gate_result.approval_timestamp.isoformat() if gate_result.approval_timestamp else None,
                gate_result.approved_by,
                gate_result.expires_at.isoformat() if gate_result.expires_at else None,
                json.dumps(gate_result.blocking_rules),
                json.dumps(gate_result.metadata),
                now,
                now
            ))
            
            self.db_manager.connection.commit()
            
        finally:
            self.db_manager.close()
    
    def _create_data_version(self, symbol: str, component: ComponentType, gate_result: QualityGateResult):
        """Create data version snapshot for approved component"""
        if not self.db_manager.connect():
            raise Exception("Failed to connect to database")
        
        try:
            cursor = self.db_manager.connection.cursor()
            
            # Deactivate previous versions
            cursor.execute("""
                UPDATE data_versions 
                SET is_active = 0 
                WHERE symbol = ? AND component = ?
            """, (symbol, component.value))
            
            # Create new version
            version_id = f"{symbol}_{component.value}_v_{int(datetime.now().timestamp())}"
            
            # Get current data snapshot (simplified - in production would be more comprehensive)
            data_snapshot = {"component": component.value, "snapshot_timestamp": datetime.now().isoformat()}
            
            cursor.execute("""
                INSERT INTO data_versions
                (version_id, symbol, component, data_snapshot, approval_gate_id,
                 created_at, approved_at, expires_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version_id,
                symbol,
                component.value,
                json.dumps(data_snapshot),
                gate_result.gate_id,
                datetime.now().isoformat(),
                gate_result.approval_timestamp.isoformat() if gate_result.approval_timestamp else None,
                gate_result.expires_at.isoformat() if gate_result.expires_at else None,
                1
            ))
            
            self.db_manager.connection.commit()
            
        finally:
            self.db_manager.close()
    
    # ==================== UTILITY METHODS ====================
    
    def get_gate_summary(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of all quality gates"""
        if not self.db_manager.connect():
            raise Exception("Failed to connect to database")
        
        try:
            cursor = self.db_manager.connection.cursor()
            
            base_query = """
                SELECT symbol, component, status, COUNT(*) as count
                FROM quality_gates
            """
            
            if symbol:
                cursor.execute(base_query + " WHERE symbol = ? GROUP BY symbol, component, status", (symbol,))
            else:
                cursor.execute(base_query + " GROUP BY symbol, component, status")
            
            results = cursor.fetchall()
            
            summary = {
                "total_gates": 0,
                "by_status": {},
                "by_component": {},
                "by_symbol": {}
            }
            
            for row in results:
                symbol_name, component, status, count = row
                summary["total_gates"] += count
                
                if status not in summary["by_status"]:
                    summary["by_status"][status] = 0
                summary["by_status"][status] += count
                
                if component not in summary["by_component"]:
                    summary["by_component"][component] = 0
                summary["by_component"][component] += count
                
                if symbol_name not in summary["by_symbol"]:
                    summary["by_symbol"][symbol_name] = 0
                summary["by_symbol"][symbol_name] += count
            
            return summary
            
        finally:
            self.db_manager.close()
    
    def cleanup_expired_gates(self) -> int:
        """Clean up expired quality gates"""
        if not self.db_manager.connect():
            raise Exception("Failed to connect to database")
        
        try:
            cursor = self.db_manager.connection.cursor()
            
            # Update expired approvals
            cursor.execute("""
                UPDATE quality_gates 
                SET status = 'expired', updated_at = ?
                WHERE status = 'approved' 
                AND expires_at IS NOT NULL 
                AND expires_at < ?
            """, (datetime.now().isoformat(), datetime.now().isoformat()))
            
            expired_count = cursor.rowcount
            
            # Deactivate expired data versions
            cursor.execute("""
                UPDATE data_versions 
                SET is_active = 0
                WHERE expires_at IS NOT NULL 
                AND expires_at < ?
                AND is_active = 1
            """, (datetime.now().isoformat(),))
            
            self.db_manager.connection.commit()
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired quality gates")
            
            return expired_count
            
        finally:
            self.db_manager.close()