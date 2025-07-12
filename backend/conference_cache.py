"""
Conference Classification Cache and Management

This module handles loading, caching, and managing conference classifications
from various online sources including CORE, DBLP, and custom databases.
"""

import json
import os
import logging
import requests
import csv
import io
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ConferenceCache:
    """Manages conference classification cache with online updates"""
    
    def __init__(self, cache_file: str = "conference_cache.json"):
        self.cache_file = cache_file
        self.conferences = {}
        self.last_updated = None
        self.load_cache()
    
    def load_cache(self):
        """Load conference classifications from cache file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.conferences = data.get('conferences', {})
                    self.last_updated = data.get('last_updated')
                    logger.info(f"Loaded {len(self.conferences)} conferences from cache")
            except Exception as e:
                logger.warning(f"Failed to load conference cache: {e}")
                self.conferences = {}
        
        # Initialize with basic conference classifications if cache is empty
        if not self.conferences:
            self._initialize_basic_conferences()
    
    def _initialize_basic_conferences(self):
        """Initialize with a comprehensive set of known conferences"""
        basic_conferences = {
            # Computer Vision & AI
            'cvpr': {
                'name': 'Computer Vision and Pattern Recognition',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['computer vision and pattern recognition', 'cvpr', 'ieee conference on computer vision and pattern recognition']
            },
            'iccv': {
                'name': 'International Conference on Computer Vision',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['iccv', 'international conference on computer vision']
            },
            'eccv': {
                'name': 'European Conference on Computer Vision',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['eccv', 'european conference on computer vision']
            },
            'neurips': {
                'name': 'Conference on Neural Information Processing Systems',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['neurips', 'nips', 'neural information processing systems', 
                           'advances in neural information processing systems',
                           'conference on neural information processing systems']
            },
            'icml': {
                'name': 'International Conference on Machine Learning',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['icml', 'international conference on machine learning']
            },
            'iclr': {
                'name': 'International Conference on Learning Representations',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['iclr', 'international conference on learning representations']
            },
            'aaai': {
                'name': 'AAAI Conference on Artificial Intelligence',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['aaai', 'association for the advancement of artificial intelligence']
            },
            'ijcai': {
                'name': 'International Joint Conference on Artificial Intelligence',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['ijcai', 'international joint conference on artificial intelligence']
            },
            
            # Natural Language Processing
            'acl': {
                'name': 'Annual Meeting of the Association for Computational Linguistics',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['acl', 'association for computational linguistics']
            },
            'emnlp': {
                'name': 'Conference on Empirical Methods in Natural Language Processing',
                'domain': 'Computer Science and AI',
                'rank': 'A',
                'aliases': ['emnlp', 'empirical methods in natural language processing']
            },
            'naacl': {
                'name': 'North American Chapter of the Association for Computational Linguistics',
                'domain': 'Computer Science and AI',
                'rank': 'A',
                'aliases': ['naacl', 'north american chapter of the association for computational linguistics']
            },
            
            # Database & Information Systems
            'sigmod': {
                'name': 'ACM SIGMOD International Conference on Management of Data',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['sigmod', 'acm sigmod']
            },
            'vldb': {
                'name': 'Very Large Data Bases',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['vldb', 'very large data bases']
            },
            'icde': {
                'name': 'IEEE International Conference on Data Engineering',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['icde', 'ieee international conference on data engineering']
            },
            
            # Systems & Networks
            'sosp': {
                'name': 'ACM Symposium on Operating Systems Principles',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['sosp', 'symposium on operating systems principles']
            },
            'osdi': {
                'name': 'USENIX Symposium on Operating Systems Design and Implementation',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['osdi', 'operating systems design and implementation']
            },
            'nsdi': {
                'name': 'USENIX Symposium on Networked Systems Design and Implementation',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['nsdi', 'networked systems design and implementation']
            },
            'sigcomm': {
                'name': 'ACM SIGCOMM Conference',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['sigcomm', 'acm sigcomm']
            },
            
            # Theory
            'stoc': {
                'name': 'ACM Symposium on Theory of Computing',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['stoc', 'symposium on theory of computing']
            },
            'focs': {
                'name': 'IEEE Symposium on Foundations of Computer Science',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['focs', 'foundations of computer science']
            },
            'soda': {
                'name': 'ACM-SIAM Symposium on Discrete Algorithms',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['soda', 'symposium on discrete algorithms']
            },
            
            # Graphics & HCI
            'siggraph': {
                'name': 'ACM SIGGRAPH Conference',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['siggraph', 'acm siggraph']
            },
            'chi': {
                'name': 'ACM Conference on Human Factors in Computing Systems',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['chi', 'human factors in computing systems']
            },
            
            # Security & Cryptography
            'ccs': {
                'name': 'ACM Conference on Computer and Communications Security',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['ccs', 'computer and communications security']
            },
            'sp': {
                'name': 'IEEE Symposium on Security and Privacy',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['sp', 'ieee security and privacy', 'oakland']
            },
            'usenix_security': {
                'name': 'USENIX Security Symposium',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['usenix security', 'usenix security symposium']
            },
            
            # Software Engineering
            'icse': {
                'name': 'International Conference on Software Engineering',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['icse', 'international conference on software engineering']
            },
            'fse': {
                'name': 'ACM SIGSOFT Symposium on Foundations of Software Engineering',
                'domain': 'Computer Science and AI',
                'rank': 'A*',
                'aliases': ['fse', 'foundations of software engineering']
            },
            
            # Statistics Conferences
            'aistats': {
                'name': 'International Conference on Artificial Intelligence and Statistics',
                'domain': 'Statistics and Probability',
                'rank': 'A',
                'aliases': ['aistats', 'artificial intelligence and statistics']
            },
            
            # Biology & Bioinformatics
            'recomb': {
                'name': 'Research in Computational Molecular Biology',
                'domain': 'Bioinformatics and Genetics',
                'rank': 'A',
                'aliases': ['recomb', 'research in computational molecular biology']
            },
            'ismb': {
                'name': 'Intelligent Systems for Molecular Biology',
                'domain': 'Bioinformatics and Genetics',
                'rank': 'A',
                'aliases': ['ismb', 'intelligent systems for molecular biology']
            }
        }
        
        self.conferences = basic_conferences
        logger.info(f"Initialized with {len(basic_conferences)} basic conferences")
    
    def get_conference_classification(self, venue: str) -> Optional[Dict]:
        """Get classification for a conference venue"""
        venue_lower = venue.lower().strip()
        
        # Remove common prefixes/suffixes and years
        venue_clean = venue_lower
        for remove in ['proceedings of', 'proc.', 'conference on', 'international', 'acm', 'ieee']:
            venue_clean = venue_clean.replace(remove, '').strip()
        
        # Remove years (e.g., "2015", "2020")
        import re
        venue_clean = re.sub(r'\b(19|20)\d{2}\b', '', venue_clean).strip()
        venue_clean = re.sub(r'\s+', ' ', venue_clean)
        
        # Direct match by conference key
        if venue_clean in self.conferences:
            return self.conferences[venue_clean]
        
        # Match by aliases
        for conf_key, conf_data in self.conferences.items():
            aliases = conf_data.get('aliases', [])
            if venue_lower in aliases:
                return conf_data
            
            # Partial matching for aliases
            for alias in aliases:
                if alias in venue_lower or venue_lower in alias:
                    if len(alias) >= 8 or len(venue_lower) >= 8:  # Avoid short false matches
                        return conf_data
        
        return None
    
    def save_cache(self):
        """Save conference classifications to cache file"""
        try:
            data = {
                'conferences': self.conferences,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.conferences)} conferences to cache")
        except Exception as e:
            logger.error(f"Failed to save conference cache: {e}")
    
    def update_from_core_rankings(self):
        """Update conference classifications from CORE rankings (if available)"""
        # Note: CORE rankings are typically distributed as Excel files
        # This is a placeholder for when we have access to the data
        logger.info("CORE rankings update not implemented yet")
        pass
    
    def add_conference(self, key: str, name: str, domain: str, rank: str = 'Unknown', aliases: List[str] = None):
        """Add a new conference to the cache"""
        if aliases is None:
            aliases = []
        
        self.conferences[key] = {
            'name': name,
            'domain': domain,
            'rank': rank,
            'aliases': aliases
        }
        logger.info(f"Added conference: {name}")
    
    def get_stats(self) -> Dict:
        """Get statistics about the conference cache"""
        domains = {}
        ranks = {}
        
        for conf in self.conferences.values():
            domain = conf.get('domain', 'Unknown')
            rank = conf.get('rank', 'Unknown')
            
            domains[domain] = domains.get(domain, 0) + 1
            ranks[rank] = ranks.get(rank, 0) + 1
        
        return {
            'total_conferences': len(self.conferences),
            'domains': domains,
            'ranks': ranks,
            'last_updated': self.last_updated
        }