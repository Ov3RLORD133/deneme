"""
YARA Rule Engine for Malware Signature Detection.

This module provides static analysis capabilities to identify malware families
and specific threat patterns in captured payloads using YARA rules.
"""

import asyncio
import os
from pathlib import Path
from typing import List, Optional

import yara

from app.core.logging import get_logger

logger = get_logger(__name__)


class YaraEngine:
    """
    YARA-based malware detection engine.
    
    Loads YARA rules from the ./rules directory and provides async scanning
    capabilities for payloads received from malware C2 traffic.
    """
    
    def __init__(self, rules_dir: str = "./rules"):
        """
        Initialize the YARA engine.
        
        Args:
            rules_dir: Path to directory containing .yar rule files
        """
        self.rules_dir = Path(rules_dir)
        self.compiled_rules: Optional[yara.Rules] = None
        self._rule_count = 0
        
    async def initialize(self) -> bool:
        """
        Load and compile YARA rules from the rules directory.
        
        Returns:
            True if rules were successfully loaded, False otherwise
        """
        try:
            if not self.rules_dir.exists():
                logger.warning(
                    f"YARA rules directory not found: {self.rules_dir}. "
                    "Creating directory. Add .yar files to enable detection."
                )
                self.rules_dir.mkdir(parents=True, exist_ok=True)
                return False
            
            # Find all .yar and .yara files
            rule_files = list(self.rules_dir.glob("*.yar")) + list(
                self.rules_dir.glob("*.yara")
            )
            
            if not rule_files:
                logger.warning(
                    f"No YARA rules found in {self.rules_dir}. "
                    "Malware detection will be disabled."
                )
                return False
            
            # Build filepaths dictionary for compilation
            filepaths = {
                f"rule_{i}": str(rule_file) 
                for i, rule_file in enumerate(rule_files)
            }
            
            # Compile rules (blocking operation, run in executor)
            loop = asyncio.get_event_loop()
            self.compiled_rules = await loop.run_in_executor(
                None, yara.compile, None, filepaths
            )
            
            self._rule_count = len(rule_files)
            logger.info(
                f"YARA engine initialized with {self._rule_count} rule file(s): "
                f"{', '.join(f.name for f in rule_files)}"
            )
            return True
            
        except yara.SyntaxError as e:
            logger.error(f"YARA rule syntax error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize YARA engine: {e}")
            return False
    
    async def scan_payload(self, data: bytes) -> List[str]:
        """
        Scan payload data for malware signatures.
        
        Args:
            data: Raw payload bytes to scan
            
        Returns:
            List of matched YARA rule names (e.g., ["win_agent_tesla", "infostealer"])
            Empty list if no matches or rules not loaded
        """
        if not self.compiled_rules:
            logger.debug("YARA scan skipped: no rules loaded")
            return []
        
        if not data:
            return []
        
        try:
            # Run YARA scan in executor to avoid blocking
            loop = asyncio.get_event_loop()
            matches = await loop.run_in_executor(
                None, self.compiled_rules.match, data
            )
            
            # Extract rule names from matches
            matched_rules = [match.rule for match in matches]
            
            if matched_rules:
                logger.info(
                    f"YARA detection: {len(matched_rules)} rule(s) matched: "
                    f"{', '.join(matched_rules)}"
                )
            
            return matched_rules
            
        except Exception as e:
            logger.error(f"YARA scan failed: {e}")
            return []
    
    def get_stats(self) -> dict:
        """
        Get YARA engine statistics.
        
        Returns:
            Dictionary with rule count and initialization status
        """
        return {
            "initialized": self.compiled_rules is not None,
            "rule_count": self._rule_count,
            "rules_directory": str(self.rules_dir)
        }


# Global YARA engine instance
_yara_engine: Optional[YaraEngine] = None


def get_yara_engine() -> YaraEngine:
    """
    Get the global YARA engine instance.
    
    Returns:
        Initialized YaraEngine instance
    """
    global _yara_engine
    if _yara_engine is None:
        _yara_engine = YaraEngine()
    return _yara_engine
