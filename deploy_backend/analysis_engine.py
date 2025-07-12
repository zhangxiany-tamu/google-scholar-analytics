import re
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from collections import defaultdict, Counter
from datetime import datetime
import statistics
from semantic_scholar_api import SemanticScholarClassifier
from journal_cache import JournalCache
from conference_cache import ConferenceCache

logger = logging.getLogger(__name__)

class ProfileAnalyzer:
    """
    Comprehensive analysis engine for Google Scholar profiles
    """
    
    def __init__(self, use_semantic_scholar: bool = False):
        # Initialize classification method
        self.use_semantic_scholar = use_semantic_scholar
        self.semantic_classifier = SemanticScholarClassifier() if use_semantic_scholar else None
        
        # Journal classification will be loaded from external sources
        self.journal_classifications = {}  # journal_name -> classification
        self.venue_types = {}  # venue_name -> 'journal' or 'conference'
        self.journal_cache = JournalCache()
        self.conference_cache = ConferenceCache()
        self._load_journal_classifications()
        
        # Keyword-based classification as fallback
        # Update to use SCImago-style subject areas for keyword fallback
        self.keyword_domains = {
            'Statistics and Probability': [
                'statistical', 'statistics', 'probability', 'inference', 'estimation', 
                'hypothesis', 'regression', 'anova', 'bayesian', 'frequentist', 
                'multivariate', 'correlation', 'variance', 'distribution', 'bootstrap',
                'monte carlo', 'sampling', 'likelihood', 'significance', 'p-value',
                'change-point', 'change point', 'high-dimensional', 'dimensional',
                'homogeneity', 'detection', 'test', 'testing', 'linear models',
                'differential abundance', 'compositional data', 'linda', 'asymptotic',
                'limit theorem', 'martingale', 'stochastic', 'random process',
                'time series analysis', 'statistical method', 'statistical theory',
                'confidence interval', 'hypothesis test', 'nonparametric',
                'semiparametric', 'wild bootstrap', 'spectral theory'
            ],
            'Applied Mathematics': [
                'mathematics', 'mathematical', 'theorem', 'proof', 'algebra', 'geometry',
                'topology', 'analysis', 'differential equations', 'partial differential',
                'ordinary differential', 'calculus', 'optimization', 'numerical analysis',
                'linear algebra', 'abstract algebra', 'number theory', 'combinatorics',
                'graph theory', 'logic', 'set theory', 'measure theory', 'functional analysis',
                'real analysis', 'complex analysis', 'harmonic analysis', 'approximation theory',
                'discrete mathematics', 'applied mathematics', 'pure mathematics'
            ],
            'Computer Science and AI': [
                'machine learning', 'deep learning', 'neural network', 'artificial intelligence',
                'classification', 'clustering', 'supervised', 'unsupervised', 'reinforcement',
                'feature selection', 'random forest', 'svm', 'support vector', 'gradient',
                'algorithm', 'training', 'prediction', 'tensorflow', 'pytorch',
                'computer vision', 'pattern recognition', 'image processing', 'image analysis',
                'object detection', 'face recognition', 'visual', 'image classification',
                'software', 'programming', 'computer science'
            ],
            'Bioinformatics and Genetics': [
                'bioinformatics', 'genomics', 'proteomics', 'microbiome', 'rna', 'dna', 
                'gene', 'genome', 'sequencing', 'gene expression', 'biological data',
                'molecular biology', 'biomarker', 'pathway', 'transcriptome', 'chromosome',
                'mutation', 'variant', 'snp', 'genome-wide', 'phylogenetic'
            ],
            'Environmental and Earth Sciences': [
                'environmental', 'ecology', 'climate', 'ecosystem', 'biodiversity',
                'conservation', 'sustainability', 'pollution', 'carbon', 'species',
                'ecological', 'habitat', 'conservation', 'earth sciences', 'geology'
            ],
            'Economics and Finance': [
                'econometrics', 'economics', 'financial markets', 'economic growth', 'gdp',
                'economic policy', 'finance', 'financial crisis', 'stock market', 'trading', 
                'investment', 'portfolio', 'asset pricing', 'monetary policy', 'fiscal policy',
                'labor economics', 'development economics', 'international trade'
            ],
            'Social Sciences': [
                'psychology', 'sociology', 'survey', 'social', 'behavioral',
                'demographic', 'population', 'policy', 'human', 'community', 'survey',
                'education', 'anthropology', 'political science'
            ],
            'Medicine and Health Sciences': [
                'medicine', 'medical', 'health', 'clinical', 'epidemiology', 
                'public health', 'biomedical', 'therapeutic', 'treatment'
            ]
        }
        
    def _load_journal_classifications(self):
        """Load journal classifications from SCImago local database"""
        try:
            # Load from local SCImago database file
            self._load_scimago_database()
            
            # Add critical journals to ensure key journals are never missed
            self._add_critical_journals()
            
            logger.info(f"Total journal classifications loaded: {len(self.journal_classifications)}")
            
        except Exception as e:
            logger.error(f"Failed to load SCImago database, falling back to local journals: {str(e)}")
            # Fallback to minimal local database
            self._load_fallback_journals()
            self._add_critical_journals()
            logger.info(f"Using fallback database with {len(self.journal_classifications)} journals")
    
    def _load_scimago_database(self):
        """Load journal classifications from local SCImago database file"""
        import json
        import os
        
        database_file = "scimago_journals.json"
        
        if not os.path.exists(database_file):
            raise FileNotFoundError(f"SCImago database file {database_file} not found")
        
        logger.info(f"Loading SCImago database from {database_file}...")
        
        with open(database_file, 'r', encoding='utf-8') as f:
            database = json.load(f)
        
        # Extract journal classifications - store ALL categories, not just primary
        self.journal_classifications = {}
        for journal_name, journal_data in database['journals'].items():
            categories_string = journal_data.get('categories', '')
            # Extract all subject categories from the string
            all_subjects = self._extract_all_scimago_subjects(categories_string)
            # Map each subject to research domains
            research_domains = []
            for subject in all_subjects:
                domain = self._map_scimago_to_research_domain(subject, journal_name)
                if domain and domain not in research_domains:
                    research_domains.append(domain)
            
            # Store all applicable domains for this journal
            self.journal_classifications[journal_name] = research_domains if research_domains else [journal_data['subject']]
        
        # Log metadata
        metadata = database.get('metadata', {})
        logger.info(f"Loaded SCImago database:")
        logger.info(f"  Source: {metadata.get('source', 'Unknown')}")
        logger.info(f"  Year: {metadata.get('year', 'Unknown')}")
        logger.info(f"  Total journals: {metadata.get('total_journals', len(self.journal_classifications))}")
        logger.info(f"  Subject areas: {len(metadata.get('subject_areas', []))}")
        
        # Log sample journals
        sample_journals = list(self.journal_classifications.keys())[:5]
        logger.info(f"Sample journals: {sample_journals}")
    
    def _extract_all_scimago_subjects(self, categories: str) -> list:
        """Extract all subject areas from SCImago categories string"""
        if not categories:
            return []
            
        # Categories format: "Subject1 (Q1); Subject2 (Q2); Subject3 (Q3); ..."
        subjects = []
        for category in categories.split(';'):
            # Remove quartile info (Q1), (Q2), etc. and clean
            subject = category.split('(')[0].strip()
            if subject:
                subjects.append(subject)
        
        return subjects
    
    def _map_scimago_to_research_domain(self, scimago_subject: str, journal_name: str) -> str:
        """Map SCImago subjects to broader research domains, considering journal names"""
        
        # First check for well-known statistical journals by name
        stats_journals = {
            'biometrika', 'biometrics', 'biostatistics', 'statistical science',
            'annals of statistics', 'journal of the american statistical association',
            'journal of the royal statistical society', 'statistics and computing',
            'computational statistics and data analysis', 'electronic journal of statistics',
            'scandinavian journal of statistics', 'canadian journal of statistics',
            'journal of multivariate analysis', 'journal of time series analysis',
            'journal of nonparametric statistics', 'bernoulli', 'test',
            'journal of statistical planning and inference', 'statistics in medicine',
            'statistical methods in medical research', 'journal of computational and graphical statistics'
        }
        
        if journal_name in stats_journals:
            return 'Statistics and Probability'
        
        # Map SCImago subjects to broader domains
        subject_lower = scimago_subject.lower()
        
        # Check for genetic journals that should be genetics
        genetics_journals = {'plos genetics', 'nature genetics', 'genome biology', 'genomics'}
        if journal_name in genetics_journals:
            return 'Bioinformatics and Genetics'
        
        # Statistics and Probability
        if any(term in subject_lower for term in [
            'statistics', 'probability', 'econometrics', 'biostatistics',
            'statistical', 'stochastic'
        ]):
            return 'Statistics and Probability'
        
        # Computer Science and AI
        elif any(term in subject_lower for term in [
            'artificial intelligence', 'machine learning', 'computer vision', 
            'pattern recognition', 'neural networks', 'deep learning',
            'computer science', 'software', 'algorithms', 'computational theory',
            'computer graphics', 'human-computer interaction', 'computer networks',
            'computer security', 'databases', 'programming languages'
        ]):
            return 'Computer Science and AI'
        
        # Mathematics
        elif any(term in subject_lower for term in [
            'mathematics', 'mathematical', 'algebra', 'geometry', 'topology',
            'analysis', 'number theory', 'logic', 'discrete mathematics',
            'applied mathematics', 'computational mathematics'
        ]):
            return 'Mathematics'
        
        # Bioinformatics and Genetics
        elif any(term in subject_lower for term in [
            'bioinformatics', 'computational biology', 'genetics', 'genomics',
            'molecular biology', 'cell biology', 'biochemistry', 'biotechnology'
        ]):
            return 'Bioinformatics and Genetics'
        
        # Economics and Finance
        elif any(term in subject_lower for term in [
            'economics', 'finance', 'econometrics', 'business', 'accounting',
            'management', 'marketing', 'organizational'
        ]):
            return 'Economics and Finance'
        
        # Medicine and Health
        elif any(term in subject_lower for term in [
            'medicine', 'medical', 'health', 'clinical', 'epidemiology',
            'public health', 'nursing', 'pharmacy', 'oncology', 'cardiology',
            'surgery', 'psychiatry', 'radiology', 'pathology'
        ]):
            return 'Medicine and Health Sciences'
        
        # Environmental and Earth Sciences
        elif any(term in subject_lower for term in [
            'environmental', 'ecology', 'climate', 'atmospheric', 'oceanography',
            'geology', 'geography', 'earth sciences', 'sustainability',
            'conservation', 'biodiversity'
        ]):
            return 'Environmental and Earth Sciences'
        
        # Physics and Chemistry
        elif any(term in subject_lower for term in [
            'physics', 'chemistry', 'materials', 'chemical', 'physical',
            'quantum', 'particle physics', 'condensed matter'
        ]):
            return 'Physics and Chemistry'
        
        # Engineering
        elif any(term in subject_lower for term in [
            'engineering', 'mechanical', 'electrical', 'civil', 'aerospace',
            'industrial', 'chemical engineering', 'biomedical engineering'
        ]):
            return 'Engineering'
        
        # Social Sciences
        elif any(term in subject_lower for term in [
            'psychology', 'sociology', 'anthropology', 'political science',
            'social sciences', 'education', 'linguistics', 'communication'
        ]):
            return 'Social Sciences'
        
        # Default: return original SCImago subject
        return scimago_subject
    
    def _find_best_journal_match(self, venue_lower: str) -> tuple:
        """
        SYSTEMATIC JOURNAL MATCHING with quality control
        Returns: (domains, matched_journal_name) or None
        """
        import re
        
        # Clean venue for better matching
        venue_clean = venue_lower.replace('(', ' ').replace(')', ' ').replace(',', ' ').replace('.', ' ')
        venue_clean = re.sub(r'\s+', ' ', venue_clean).strip()
        
        candidates = []
        
        # STEP 1: High-confidence exact matches (case-insensitive substring)
        for journal_name, domains in self.journal_classifications.items():
            
            # Method 1: Direct substring match (both directions)
            if journal_name in venue_lower and len(journal_name) >= 10:
                candidates.append((100, len(journal_name), journal_name, domains, "exact_substring"))
            elif venue_lower in journal_name and len(venue_lower) >= 10:
                candidates.append((95, len(venue_lower), journal_name, domains, "reverse_substring"))
        
        # STEP 2: High-quality acronym matches
        for journal_name, domains in self.journal_classifications.items():
            if len(journal_name) <= 8:  # Only for short names/acronyms
                # Check if acronym appears as whole word
                if re.search(r'\b' + re.escape(journal_name) + r'\b', venue_lower, re.IGNORECASE):
                    candidates.append((90, len(journal_name), journal_name, domains, "acronym"))
        
        # STEP 3: Smart word-based matching with quality control
        venue_words = set(w for w in venue_clean.split() if len(w) > 2)  # Ignore short words
        
        for journal_name, domains in self.journal_classifications.items():
            if len(journal_name) >= 15:  # Only for longer journal names
                journal_words = set(w for w in journal_name.split() if len(w) > 2)
                
                if len(journal_words) >= 3:  # Only journals with 3+ meaningful words
                    common_words = venue_words.intersection(journal_words)
                    
                    # STRICT criteria to avoid false matches
                    match_ratio = len(common_words) / len(journal_words)
                    
                    # Require high match ratio AND specific meaningful matches
                    if (match_ratio >= 0.8 and len(common_words) >= 3) or \
                       (match_ratio >= 0.9 and len(common_words) >= 2):
                        
                        # Additional quality check: avoid generic words causing false matches
                        meaningful_matches = common_words - {'journal', 'of', 'the', 'and', 'for', 'in', 'on', 'international', 'society', 'research'}
                        
                        if len(meaningful_matches) >= 2:  # Must have at least 2 non-generic word matches
                            score = 60 + int(match_ratio * 30)
                            candidates.append((score, len(journal_name), journal_name, domains, "word_match"))
        
        # STEP 4: Special pattern matching for common cases
        special_patterns = self._get_special_venue_patterns()
        for pattern, domains, matched_name in special_patterns:
            if pattern in venue_lower:
                candidates.append((85, len(pattern), matched_name, domains, "special_pattern"))
        
        # STEP 5: Select best candidate based on score and length
        if candidates:
            # Sort by score (descending), then by length (descending)
            candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
            
            best_score, best_length, best_journal, best_domains, match_type = candidates[0]
            
            # Quality threshold: only accept high-confidence matches
            if best_score >= 80:
                logger.info(f"HIGH-QUALITY match ({match_type}, score={best_score}): '{venue_lower}' -> '{best_journal}'")
                return (best_domains, best_journal)
            else:
                logger.info(f"LOW-QUALITY match rejected (score={best_score}): '{venue_lower}' -> '{best_journal}'")
        
        return None
    
    def _get_special_venue_patterns(self) -> list:
        """Define special venue patterns for common cases"""
        return [
            # Statistics journals
            ('royal statistical society', ['Statistics and Probability'], 'journal of the royal statistical society'),
            ('american statistical association', ['Statistics and Probability'], 'journal of the american statistical association'),
            ('biometrika', ['Statistics and Probability'], 'biometrika'),
            ('statistica sinica', ['Statistics and Probability'], 'statistica sinica'),
            ('annals of statistics', ['Statistics and Probability'], 'annals of statistics'),
            ('journal of econometrics', ['Statistics and Probability'], 'journal of econometrics'),
            ('econometric theory', ['Statistics and Probability'], 'econometric theory'),
            ('bernoulli', ['Statistics and Probability'], 'bernoulli'),
            
            # Preprint servers
            ('arxiv', ['Preprints & Working Papers'], 'arxiv'),
            ('biorxiv', ['Preprints & Working Papers'], 'biorxiv'),
            ('medrxiv', ['Preprints & Working Papers'], 'medrxiv'),
            ('ssrn', ['Preprints & Working Papers'], 'ssrn'),
            
            # AI/ML venues
            ('neurips', ['Computer Science and AI'], 'neurips'),
            ('nips', ['Computer Science and AI'], 'neurips'),
            ('icml', ['Computer Science and AI'], 'icml'),
            ('iclr', ['Computer Science and AI'], 'iclr'),
            ('cvpr', ['Computer Science and AI'], 'cvpr'),
            ('iccv', ['Computer Science and AI'], 'iccv'),
            ('ijcai', ['Computer Science and AI'], 'ijcai'),
            ('aaai', ['Computer Science and AI'], 'aaai'),
        ]
    
    def _add_critical_journals(self):
        """Add critical journals that must always be classified correctly"""
        critical_journals = {
            # Top AI/ML Journals
            'ieee transactions on pattern analysis and machine intelligence': 'Computer Science and AI',
            'ieee trans pattern anal mach intell': 'Computer Science and AI',
            'ieee trans. pattern anal. mach. intell.': 'Computer Science and AI',
            'tpami': 'Computer Science and AI',
            'pattern analysis and machine intelligence': 'Computer Science and AI',
            'journal of machine learning research': 'Computer Science and AI',
            'jmlr': 'Computer Science and AI',
            'machine learning': 'Computer Science and AI',
            'neural networks': 'Computer Science and AI',
            'artificial intelligence': 'Computer Science and AI',
            'pattern recognition': 'Computer Science and AI',
            'ieee transactions on image processing': 'Computer Science and AI',
            'ieee transactions on neural networks and learning systems': 'Computer Science and AI',
            'international journal of computer vision': 'Computer Science and AI',
            'ijcv': 'Computer Science and AI',
            'computer vision and image understanding': 'Computer Science and AI',
            'journal of artificial intelligence research': 'Computer Science and AI',
            'jair': 'Computer Science and AI',
            
            # Top CS Journals
            'communications of the acm': 'Computer Science and AI',
            'acm computing surveys': 'Computer Science and AI',
            'ieee transactions on computers': 'Computer Science and AI',
            'ieee transactions on software engineering': 'Computer Science and AI',
            'acm transactions on graphics': 'Computer Science and AI',
            'ieee computer': 'Computer Science and AI',
            
            # Top Statistics Journals
            'journal of the american statistical association': 'Statistics and Probability',
            'jasa': 'Statistics and Probability',
            'biometrika': 'Statistics and Probability',
            'annals of statistics': 'Statistics and Probability',
            'journal of the royal statistical society': 'Statistics and Probability',
            'statistical science': 'Statistics and Probability'
        }
        
        # Add or override with critical classifications
        for journal, classification in critical_journals.items():
            self.journal_classifications[journal] = [classification]  # Store as list for consistency
        
        logger.info(f"Added {len(critical_journals)} critical journal classifications")
        logger.info(f"Total journal classifications loaded: {len(self.journal_classifications)}")
        
        # Log some sample journal names for debugging
        sample_journals = list(self.journal_classifications.keys())[:10]
        logger.info(f"Sample journals: {sample_journals}")
    
    def _load_from_scimago(self):
        """Load journal and conference classifications from multiple trusted sources"""
        try:
            # Load journals from SCImago
            self._load_scimago_journals()
            
            # Load conferences from DBLP and CORE
            self._load_conference_rankings()
            
        except Exception as e:
            logger.warning(f"Failed to load venue data: {str(e)}")
    
    def _load_scimago_journals(self):
        """Load journal classifications from SCImago Journal Rank (SJR)"""
        import requests
        import csv
        import io
        
        try:
            # SCImago provides CSV data with journal categories
            url = "https://www.scimagojr.com/journalrank.php"
            params = {
                'out': 'xls',
                'year': '2023',
                'min': '0',
                'max': '50000'  # Get all journals
            }
            
            logger.info("Downloading SCImago journal data (this may take a moment)...")
            
            response = requests.get(url, params=params, timeout=60)  # Longer timeout for large data
            if response.status_code == 200:
                # Parse CSV data
                csv_data = io.StringIO(response.text)
                reader = csv.DictReader(csv_data, delimiter=';')
                
                scimago_count = 0
                for row in reader:
                    journal_name = row.get('Title', '').strip().lower()
                    categories = row.get('Categories', '').strip()
                    
                    if journal_name and categories:
                        # Use SCImago categories directly (extract main subject areas)
                        main_subjects = self._extract_scimago_subjects(categories)
                        if main_subjects:
                            # Store direct mapping: journal -> SCImago subject areas
                            self.journal_classifications[journal_name] = main_subjects
                            scimago_count += 1
                
                logger.info(f"Successfully loaded {scimago_count} journals from SCImago")
            else:
                logger.warning(f"SCImago request failed with status {response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to load SCImago journals: {str(e)}")
    
    def _extract_scimago_subjects(self, categories: str) -> str:
        """Extract main subject areas from SCImago categories string"""
        if not categories:
            return None
            
        # Categories format: "Subject1 (Q1); Subject2 (Q2); ..."
        # Extract just the subject names without quartiles
        subjects = []
        for category in categories.split(';'):
            # Remove quartile info (Q1), (Q2), etc. and clean
            subject = category.split('(')[0].strip()
            if subject:
                subjects.append(subject)
        
        # Return primary subject (first one) for simplicity, or could return all
        return subjects[0] if subjects else None
    
    def _load_conference_rankings(self):
        """Load conference classifications from CORE Rankings and DBLP"""
        try:
            # Load CORE Rankings (Australian Research Council)
            self._load_core_rankings()
            
            # Load DBLP venue data
            self._load_dblp_venues()
            
        except Exception as e:
            logger.warning(f"Failed to load conference rankings: {str(e)}")
    
    def _load_core_rankings(self):
        """Load conference rankings from CORE (Computing Research and Education)"""
        import requests
        
        try:
            # CORE provides comprehensive conference rankings
            # This is a public dataset of computer science conference rankings
            core_url = "http://portal.core.edu.au/conf-ranks/export-excel/all"
            
            response = requests.get(core_url, timeout=30)
            if response.status_code == 200:
                # Parse the Excel/CSV data
                import pandas as pd
                import io
                
                # Read as CSV (CORE exports as CSV despite the URL name)
                df = pd.read_csv(io.StringIO(response.text))
                
                for _, row in df.iterrows():
                    try:
                        conf_title = str(row.get('Title', '')).strip().lower()
                        conf_acronym = str(row.get('Acronym', '')).strip().lower()
                        field = str(row.get('Field of Research', '')).strip()
                        
                        if conf_title or conf_acronym:
                            # Map CORE field to our research domains
                            domain = self._map_core_field(field)
                            
                            if domain:
                                if conf_title:
                                    self.journal_classifications[conf_title] = domain
                                if conf_acronym and conf_acronym != conf_title:
                                    self.journal_classifications[conf_acronym] = domain
                                    
                    except Exception as e:
                        continue
                        
            logger.info("Loaded CORE conference rankings")
                        
        except Exception as e:
            logger.warning(f"Failed to load CORE rankings: {str(e)}")
            # Fallback to hardcoded important conferences if API fails
            self._load_fallback_conferences()
    
    def _load_dblp_venues(self):
        """Load venue data from DBLP (optional, as backup)"""
        try:
            # DBLP provides comprehensive venue data for computer science
            # We can use their API to get venue information
            # This is more complex and might need XML parsing
            
            # For now, we'll use a simplified approach with known patterns
            dblp_patterns = {
                # Common conference name patterns
                'conference on': 'Machine Learning & AI',
                'symposium on': 'Computer Science & Engineering',
                'workshop on': 'Computer Science & Engineering',
                'international conference': 'Computer Science & Engineering',
                'annual conference': 'Computer Science & Engineering',
                'proceedings of': 'Computer Science & Engineering'
            }
            
            # This would be expanded with actual DBLP API integration
            for pattern, domain in dblp_patterns.items():
                self.journal_classifications[pattern] = domain
                
        except Exception as e:
            logger.warning(f"Failed to load DBLP venues: {str(e)}")
    
    def _map_core_field(self, field: str) -> str:
        """Map CORE field to our research domains"""
        field_lower = field.lower()
        
        if any(term in field_lower for term in ['artificial intelligence', 'machine learning', 'computer vision', 'pattern recognition']):
            return 'Machine Learning & AI'
        elif any(term in field_lower for term in ['information systems', 'software engineering', 'computer systems']):
            return 'Computer Science & Engineering'
        elif any(term in field_lower for term in ['applied mathematics', 'statistics', 'numerical']):
            return 'Statistics & Probability'
        elif any(term in field_lower for term in ['bioinformatics', 'computational biology']):
            return 'Bioinformatics & Genomics'
        elif any(term in field_lower for term in ['economics', 'econometrics']):
            return 'Economics & Finance'
        
        # Default for computer science conferences
        return 'Computer Science & Engineering'
    
    def _load_fallback_conferences(self):
        """Load essential conferences as fallback when APIs fail"""
        fallback_conferences = {
            # Computer Vision & ML
            'cvpr': 'Machine Learning & AI',
            'computer vision and pattern recognition': 'Machine Learning & AI',
            'iccv': 'Machine Learning & AI', 
            'international conference on computer vision': 'Machine Learning & AI',
            'eccv': 'Machine Learning & AI',
            'european conference on computer vision': 'Machine Learning & AI',
            'neurips': 'Machine Learning & AI',
            'nips': 'Machine Learning & AI',
            'icml': 'Machine Learning & AI',
            'iclr': 'Machine Learning & AI',
            'aaai': 'Machine Learning & AI',
            'ijcai': 'Machine Learning & AI',
            
            # Systems
            'sigcomm': 'Computer Science & Engineering',
            'nsdi': 'Computer Science & Engineering', 
            'osdi': 'Computer Science & Engineering',
            'sosp': 'Computer Science & Engineering',
            
            # Theory
            'stoc': 'Computer Science & Engineering',
            'focs': 'Computer Science & Engineering',
            'soda': 'Computer Science & Engineering',
            
            # Databases
            'sigmod': 'Computer Science & Engineering',
            'vldb': 'Computer Science & Engineering',
            'icde': 'Computer Science & Engineering'
        }
        
        for conf, domain in fallback_conferences.items():
            if conf not in self.journal_classifications:
                self.journal_classifications[conf] = domain
        
        # Also store venue types for proper labeling
        self.venue_types = getattr(self, 'venue_types', {})
        
        # Known conferences (should be labeled as "Conference:")
        conference_venues = {
            'cvpr', 'computer vision and pattern recognition', 'computer vision and pattern recognition (cvpr)',
            'iccv', 'international conference on computer vision', 'international conference on computer vision (iccv)',
            'eccv', 'european conference on computer vision', 'european conference on computer vision (eccv)',
            'neurips', 'nips', 'neural information processing systems', 'advances in neural information processing systems',
            'neural information processing systems (neurips)', 'neural information processing systems (nips)',
            'icml', 'international conference on machine learning', 'international conference on machine learning (icml)',
            'iclr', 'international conference on learning representations', 'international conference on learning representations (iclr)',
            'aaai', 'ijcai', 'sigcomm', 'nsdi', 'osdi', 'sosp', 'stoc', 'focs', 'soda', 'sigmod', 'vldb', 'icde'
        }
        
        for venue in conference_venues:
            self.venue_types[venue] = 'conference'
                
        logger.info("Loaded fallback conferences")
    
    
    def _map_scimago_category(self, categories: str) -> str:
        """Map SCImago categories to our research domains"""
        categories_lower = categories.lower()
        
        # Check for Statistics first (most specific)
        if any(term in categories_lower for term in [
            'statistics', 'probability', 'mathematical statistics', 
            'theoretical statistics', 'statistical'
        ]):
            return 'Statistics & Probability'
        # Check for Mathematics (but not applied math that might be stats)
        elif any(term in categories_lower for term in [
            'pure mathematics', 'mathematical analysis', 'algebra', 'geometry', 
            'topology', 'number theory', 'differential equations', 'mathematics'
        ]) and 'statistics' not in categories_lower:
            return 'Mathematics'
        # Check for AI/ML (specific)
        elif any(term in categories_lower for term in ['artificial intelligence', 'machine learning']):
            return 'Machine Learning & AI'
        elif any(term in categories_lower for term in ['computer science']):
            return 'Computer Science & Engineering'
        elif any(term in categories_lower for term in ['biochemistry', 'genetics', 'molecular biology', 'bioinformatics']):
            return 'Bioinformatics & Genomics'
        elif any(term in categories_lower for term in ['environmental', 'ecology', 'biodiversity']):
            return 'Environmental & Ecological'
        elif any(term in categories_lower for term in ['economics', 'finance', 'business']):
            return 'Economics & Finance'
        elif any(term in categories_lower for term in ['psychology', 'sociology', 'social sciences']):
            return 'Social & Behavioral Sciences'
        elif any(term in categories_lower for term in ['medicine', 'health', 'clinical']):
            return 'Biomedical & Health Sciences'
        elif any(term in categories_lower for term in ['physics', 'chemistry', 'materials']):
            return 'Physics & Chemistry'
        
        return None
    
    def _map_doaj_subject(self, subject: str) -> str:
        """Map DOAJ subjects to our research domains"""
        subject_lower = subject.lower()
        
        if any(term in subject_lower for term in ['statistics', 'probability', 'mathematics']):
            return 'Statistics & Probability'
        elif any(term in subject_lower for term in ['computer', 'technology', 'information']):
            return 'Computer Science & Engineering'
        elif any(term in subject_lower for term in ['biology', 'genetics', 'bioinformatics']):
            return 'Bioinformatics & Genomics'
        elif any(term in subject_lower for term in ['environmental', 'ecology', 'sustainability']):
            return 'Environmental & Ecological'
        elif any(term in subject_lower for term in ['economics', 'finance', 'business']):
            return 'Economics & Finance'
        elif any(term in subject_lower for term in ['psychology', 'sociology', 'social']):
            return 'Social & Behavioral Sciences'
        elif any(term in subject_lower for term in ['medicine', 'health', 'medical']):
            return 'Biomedical & Health Sciences'
        elif any(term in subject_lower for term in ['physics', 'chemistry', 'science']):
            return 'Physics & Chemistry'
        
        return None
    
    def _load_fallback_journals(self):
        """Load a minimal set of well-known journals as fallback"""
        fallback_journals = {
            # Statistics Journals - Core
            'journal of the american statistical association': 'Statistics & Probability',
            'biometrika': 'Statistics & Probability',
            'annals of statistics': 'Statistics & Probability',
            'journal of the royal statistical society': 'Statistics & Probability',
            'statistical science': 'Statistics & Probability',
            'biostatistics': 'Statistics & Probability',
            'statistics in medicine': 'Statistics & Probability',
            
            # Electronic Statistics Journals
            'electronic journal of statistics': 'Statistics & Probability',
            'electronic journal of probability': 'Statistics & Probability',
            'electronic communications in probability': 'Statistics & Probability',
            
            # Mathematics Journals
            'electronic journal of differential equations': 'Mathematics',
            'journal of differential equations': 'Mathematics',
            'nonlinear analysis': 'Mathematics',
            'advances in mathematics': 'Mathematics',
            'journal of mathematical analysis and applications': 'Mathematics',
            'proceedings of the american mathematical society': 'Mathematics',
            'transactions of the american mathematical society': 'Mathematics',
            'communications in mathematical physics': 'Mathematics',
            'journal of functional analysis': 'Mathematics',
            'calculus of variations and partial differential equations': 'Mathematics',
            
            # Other Important Statistics Journals
            'journal of statistical planning and inference': 'Statistics & Probability',
            'computational statistics and data analysis': 'Statistics & Probability',
            'statistics and computing': 'Statistics & Probability',
            'journal of computational and graphical statistics': 'Statistics & Probability',
            'canadian journal of statistics': 'Statistics & Probability',
            'scandinavian journal of statistics': 'Statistics & Probability',
            'journal of multivariate analysis': 'Statistics & Probability',
            'journal of nonparametric statistics': 'Statistics & Probability',
            'journal of time series analysis': 'Statistics & Probability',
            'bernoulli': 'Statistics & Probability',
            'probability theory and related fields': 'Statistics & Probability',
            'stochastic processes and their applications': 'Statistics & Probability',
            
            # Additional Statistics Journals from logs
            'statistics in medicine': 'Statistics & Probability',
            'statistics and computing': 'Statistics & Probability',
            'bayesian analysis': 'Statistics & Probability',
            'spatial statistics': 'Statistics & Probability',
            'econometrics and statistics': 'Statistics & Probability',
            'chemometrics and intelligent laboratory systems': 'Statistics & Probability',
            'journal of statistical software': 'Statistics & Probability',
            'annals of applied statistics': 'Statistics & Probability',
            'electronic journal of statistics': 'Statistics & Probability',
            'journal of business and economic statistics': 'Statistics & Probability',
            'statistical methods in medical research': 'Statistics & Probability',
            'biostatistics': 'Statistics & Probability',
            'journal of the royal statistical society series b': 'Statistics & Probability',
            'journal of the royal statistical society series c': 'Statistics & Probability',
            'test': 'Statistics & Probability',
            'computational statistics': 'Statistics & Probability',
            'statistical science': 'Statistics & Probability',
            'journal of machine learning research': 'Machine Learning & AI',
            'machine learning': 'Machine Learning & AI',
            'neural networks': 'Machine Learning & AI',
            'artificial intelligence': 'Machine Learning & AI',
            'pattern recognition': 'Machine Learning & AI',
            'bioinformatics': 'Bioinformatics & Genomics',
            'nature genetics': 'Bioinformatics & Genomics',
            'genome research': 'Bioinformatics & Genomics',
            'genome biology': 'Bioinformatics & Genomics',
            'nucleic acids research': 'Bioinformatics & Genomics',
            'plos computational biology': 'Bioinformatics & Genomics',
            'bmc bioinformatics': 'Bioinformatics & Genomics',
            'nature biotechnology': 'Bioinformatics & Genomics',
            'ecology': 'Environmental & Ecological',
            'journal of ecology': 'Environmental & Ecological',
            'conservation biology': 'Environmental & Ecological',
            'ecological applications': 'Environmental & Ecological',
            'global change biology': 'Environmental & Ecological',
            'environmental science & technology': 'Environmental & Ecological',
            'american economic review': 'Economics & Finance',
            'journal of political economy': 'Economics & Finance',
            'quarterly journal of economics': 'Economics & Finance',
            'econometrica': 'Economics & Finance',
            'journal of finance': 'Economics & Finance',
            'review of financial studies': 'Economics & Finance',
            'psychological science': 'Social & Behavioral Sciences',
            'journal of personality and social psychology': 'Social & Behavioral Sciences',
            'american journal of sociology': 'Social & Behavioral Sciences',
            'social forces': 'Social & Behavioral Sciences',
            'new england journal of medicine': 'Biomedical & Health Sciences',
            'lancet': 'Biomedical & Health Sciences',
            'jama': 'Biomedical & Health Sciences',
            'nature medicine': 'Biomedical & Health Sciences',
            'cell': 'Biomedical & Health Sciences',
            'science': 'Biomedical & Health Sciences',
            'communications of the acm': 'Computer Science & Engineering',
            'ieee transactions on computers': 'Computer Science & Engineering',
            'ieee transactions on software engineering': 'Computer Science & Engineering',
            'acm computing surveys': 'Computer Science & Engineering',
            
            # IEEE Computer Science & AI Journals
            'ieee transactions on pattern analysis and machine intelligence': 'Machine Learning & AI',
            'ieee trans pattern anal mach intell': 'Machine Learning & AI',
            'ieee trans. pattern anal. mach. intell.': 'Machine Learning & AI',
            'tpami': 'Machine Learning & AI',
            'pattern analysis and machine intelligence': 'Machine Learning & AI',
            'ieee transactions on image processing': 'Machine Learning & AI',
            'ieee transactions on neural networks and learning systems': 'Machine Learning & AI',
            'ieee transactions on evolutionary computation': 'Machine Learning & AI',
            'ieee transactions on cybernetics': 'Machine Learning & AI',
            'ieee transactions on automation science and engineering': 'Computer Science & Engineering',
            'ieee transactions on robotics': 'Computer Science & Engineering',
            'ieee transactions on systems man and cybernetics': 'Computer Science & Engineering',
            'ieee computer graphics and applications': 'Machine Learning & AI',
            'ieee transactions on visualization and computer graphics': 'Machine Learning & AI',
            'ieee transactions on multimedia': 'Computer Science & Engineering',
            'ieee transactions on knowledge and data engineering': 'Computer Science & Engineering',
            'ieee transactions on parallel and distributed systems': 'Computer Science & Engineering',
            'ieee transactions on mobile computing': 'Computer Science & Engineering',
            
            # Additional AI/ML/CS Journals
            'journal of artificial intelligence research': 'Machine Learning & AI',
            'jair': 'Machine Learning & AI',
            'artificial intelligence': 'Machine Learning & AI',
            'international journal of computer vision': 'Machine Learning & AI',
            'ijcv': 'Machine Learning & AI',
            'computer vision and image understanding': 'Machine Learning & AI',
            'cviu': 'Machine Learning & AI',
            'ieee computer': 'Computer Science & Engineering',
            'acm transactions on graphics': 'Computer Science & Engineering',
            'acm transactions on computer systems': 'Computer Science & Engineering',
            'acm transactions on programming languages and systems': 'Computer Science & Engineering',
            
            # Health & Medical Journals
            'journal of physical activity and health': 'Biomedical & Health Sciences',
            'jmir research protocols': 'Biomedical & Health Sciences',
            'preventive medicine': 'Biomedical & Health Sciences',
            'american journal of preventive medicine': 'Biomedical & Health Sciences',
            
            # Remote Sensing & GIS
            'remote sensing': 'Environmental & Ecological',
            'ieee transactions on geoscience and remote sensing': 'Environmental & Ecological',
            'remote sensing of environment': 'Environmental & Ecological',
            
            # Preprint Servers
            'arxiv': 'Preprints & Working Papers',
            'biorxiv': 'Preprints & Working Papers',
            'medrxiv': 'Preprints & Working Papers',
            'ssrn': 'Preprints & Working Papers'
        }
        
        self.journal_classifications = fallback_journals
        
    def analyze_profile_comprehensive(self, profile_data: Dict, publications: List[Dict]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a scholar profile
        """
        try:
            logger.info(f"Starting comprehensive analysis for profile: {profile_data.get('name', 'Unknown')}")
            
            # Basic metrics
            basic_metrics = self._calculate_basic_metrics(profile_data, publications)
            
            # Authorship analysis
            authorship_analysis = self._analyze_authorship(profile_data, publications)
            
            # Research areas analysis
            research_areas = self._classify_research_areas(publications)
            
            # Citation analysis
            citation_analysis = self._analyze_citations(publications)
            
            # Collaboration analysis
            collaboration_analysis = self._analyze_collaborations(publications)
            
            # Productivity analysis
            productivity_analysis = self._analyze_productivity(publications)
            
            # Venue analysis
            venue_analysis = self._analyze_venues(publications)
            
            return {
                'basic_metrics': basic_metrics,
                'authorship_analysis': authorship_analysis,
                'research_areas': research_areas,
                'citation_analysis': citation_analysis,
                'collaboration_analysis': collaboration_analysis,
                'productivity_analysis': productivity_analysis,
                'venue_analysis': venue_analysis,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {str(e)}")
            raise
    
    def _calculate_basic_metrics(self, profile_data: Dict, publications: List[Dict]) -> Dict[str, Any]:
        """Calculate basic profile metrics"""
        total_publications = len(publications)
        total_citations = sum(pub.get('citation_count', 0) for pub in publications)
        
        # Calculate h-index
        h_index = self._calculate_h_index([pub.get('citation_count', 0) for pub in publications])
        
        # Calculate i10-index
        i10_index = sum(1 for pub in publications if pub.get('citation_count', 0) >= 10)
        
        # Average citations per paper
        avg_citations = total_citations / total_publications if total_publications > 0 else 0
        
        # Years active
        years = [pub.get('year') for pub in publications if pub.get('year')]
        years_active = max(years) - min(years) + 1 if years else 0
        
        return {
            'total_publications': total_publications,
            'total_citations': total_citations,
            'h_index': h_index,
            'i10_index': i10_index,
            'avg_citations_per_paper': round(avg_citations, 2),
            'years_active': years_active,
            'publications_per_year': round(total_publications / years_active, 2) if years_active > 0 else 0,
            'first_publication_year': min(years) if years else None,
            'latest_publication_year': max(years) if years else None
        }
    
    def _calculate_h_index(self, citations: List[int]) -> int:
        """Calculate h-index from citation counts"""
        citations = sorted(citations, reverse=True)
        h_index = 0
        for i, citation_count in enumerate(citations):
            if citation_count >= i + 1:
                h_index = i + 1
            else:
                break
        return h_index
    
    def _analyze_authorship(self, profile_data: Dict, publications: List[Dict]) -> Dict[str, Any]:
        """Analyze authorship patterns"""
        profile_name = profile_data.get('name', '').lower()
        name_parts = profile_name.split()
        
        authorship_stats = {
            'first_author': {'count': 0, 'citations': 0, 'papers': []},
            'second_author': {'count': 0, 'citations': 0, 'papers': []},
            'last_author': {'count': 0, 'citations': 0, 'papers': []},
            'middle_author': {'count': 0, 'citations': 0, 'papers': []},
            'single_author': {'count': 0, 'citations': 0, 'papers': []},
            'corresponding_author': {'count': 0, 'citations': 0, 'papers': []},  # Estimated
            'unknown': {'count': 0, 'citations': 0, 'papers': []}
        }
        
        for pub in publications:
            authors = pub.get('authors', '')
            citations = pub.get('citation_count', 0)
            
            # Parse authors
            author_list = self._parse_authors(authors)
            position = self._determine_author_position(profile_name, name_parts, author_list)
            
            # Debug logging for problematic cases
            if position == 'unknown' and len(author_list) > 1:
                logger.warning(f"Could not determine author position for '{pub.get('title', 'Unknown')}' with authors: {author_list}")
                logger.warning(f"Profile name: '{profile_name}', Name parts: {name_parts}")
            
            # Create paper data
            paper_data = {
                'title': pub.get('title', ''),
                'year': pub.get('year'),
                'citations': citations
            }
            
            # Update statistics for the primary position
            authorship_stats[position]['count'] += 1
            authorship_stats[position]['citations'] += citations
            authorship_stats[position]['papers'].append(paper_data)
            
            # Special handling for single author papers - they are also first AND last author
            if position == 'single_author':
                # Also count as first author
                authorship_stats['first_author']['count'] += 1
                authorship_stats['first_author']['citations'] += citations
                authorship_stats['first_author']['papers'].append(paper_data)
                
                # Also count as last author  
                authorship_stats['last_author']['count'] += 1
                authorship_stats['last_author']['citations'] += citations
                authorship_stats['last_author']['papers'].append(paper_data)
            
            # Special handling for second author when there are only 2 authors - they are also last author
            elif position == 'second_author' and len(author_list) == 2:
                # Also count as last author
                authorship_stats['last_author']['count'] += 1
                authorship_stats['last_author']['citations'] += citations
                authorship_stats['last_author']['papers'].append(paper_data)
        
        # Calculate percentages and averages
        total_papers = len(publications)
        for role in authorship_stats:
            count = authorship_stats[role]['count']
            authorship_stats[role]['percentage'] = round(count / total_papers * 100, 1) if total_papers > 0 else 0
            authorship_stats[role]['avg_citations'] = round(
                authorship_stats[role]['citations'] / count, 1
            ) if count > 0 else 0
        
        return authorship_stats
    
    def _parse_authors(self, authors_string: str) -> List[str]:
        """Parse author string into list of individual authors, handling truncation"""
        if not authors_string:
            return []
        
        # Check for truncation indicators
        is_truncated = self._is_author_list_truncated(authors_string)
        
        # Remove truncation indicators before parsing
        clean_authors_string = self._clean_truncation_markers(authors_string)
        
        # Common separators - improved regex for better parsing
        # Split on comma, semicolon, or ' and ' (but not 'and' within names)
        authors = re.split(r',|;|\s+and\s+', clean_authors_string)
        authors = [author.strip() for author in authors if author.strip()]
        
        # Further clean up each author name
        cleaned_authors = []
        for author in authors:
            # Remove common prefixes/suffixes
            author = re.sub(r'^(Dr\.?|Prof\.?|Mr\.?|Ms\.?|Mrs\.?)\s+', '', author)
            author = re.sub(r'\s+(Jr\.?|Sr\.?|III?|IV)$', '', author)
            author = author.strip()
            # Filter out truncation indicators that might have escaped cleaning
            if author and author not in ['...', '…', 'et al', 'et al.', 'and others', 'and more', 'etc']:
                cleaned_authors.append(author)
        
        # Store truncation info for later use
        if is_truncated:
            cleaned_authors.append('__TRUNCATED__')  # Marker for truncated list
        
        return cleaned_authors
    
    def _is_author_list_truncated(self, authors_string: str) -> bool:
        """Check if the author list is truncated"""
        truncation_indicators = [
            '...', '…', 'et al', 'et al.', 'and others', 
            'and more', '+ more', '+ others', 'etc'
        ]
        
        authors_lower = authors_string.lower()
        
        # Check for simple indicators
        if any(indicator in authors_lower for indicator in truncation_indicators):
            return True
        
        # Check for pattern "+ N more" where N is a number
        import re
        if re.search(r'\+\s*\d+\s*more', authors_lower):
            return True
        
        return False
    
    def _clean_truncation_markers(self, authors_string: str) -> str:
        """Remove truncation markers from author string"""
        # Remove common truncation indicators
        truncation_patterns = [
            r'\.\.\..*$',  # Everything after ...
            r'….*$',       # Everything after ellipsis
            r'\bet\s+al\.?.*$',  # Everything after "et al"
            r'\band\s+others.*$',  # Everything after "and others"
            r'\band\s+more.*$',   # Everything after "and more"
            r'\+\s*\d+\s*more.*$', # Everything after "+ N more"
            r'\+\s*others.*$',    # Everything after "+ others"
            r'\betc\.?.*$'        # Everything after "etc"
        ]
        
        cleaned = authors_string
        for pattern in truncation_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip().rstrip(',').strip()
    
    def _determine_author_position(self, profile_name: str, name_parts: List[str], author_list: List[str]) -> str:
        """Determine the position of the profile owner in the author list, handling truncation"""
        if not author_list:
            return 'unknown'
        
        # Check if the list is truncated
        is_truncated = '__TRUNCATED__' in author_list
        if is_truncated:
            # Remove the truncation marker for processing
            author_list = [author for author in author_list if author != '__TRUNCATED__']
        
        if len(author_list) == 1 and not is_truncated:
            return 'single_author'
        
        # Find the profile owner in the author list
        profile_index = None
        for i, author in enumerate(author_list):
            author_lower = author.lower().strip()
            
            # Method 1: Check for exact name match
            if profile_name.lower() in author_lower:
                profile_index = i
                break
            
            # Method 2: Check for reverse name match (Last, First)
            if len(name_parts) >= 2:
                # Try "Last, First" pattern
                reverse_name = f"{name_parts[-1]}, {name_parts[0]}".lower()
                if reverse_name in author_lower:
                    profile_index = i
                    break
                    
                # Try "First Last" in author
                full_name = f"{name_parts[0]} {name_parts[-1]}".lower()
                if full_name in author_lower:
                    profile_index = i
                    break
            
            # Method 3: Check for initials + last name pattern (K He, K. He)
            if len(name_parts) >= 2:
                first_initial = name_parts[0][0].lower()
                last_name = name_parts[-1].lower()
                
                # Try "F Last" pattern
                initial_name = f"{first_initial} {last_name}"
                if initial_name in author_lower:
                    profile_index = i
                    break
                    
                # Try "F. Last" pattern  
                initial_name_dot = f"{first_initial}. {last_name}"
                if initial_name_dot in author_lower:
                    profile_index = i
                    break
                    
                # Try "Last, F" pattern
                reverse_initial = f"{last_name}, {first_initial}"
                if reverse_initial in author_lower:
                    profile_index = i
                    break
                    
                # Try "Last, F." pattern
                reverse_initial_dot = f"{last_name}, {first_initial}."
                if reverse_initial_dot in author_lower:
                    profile_index = i
                    break
            
            # Method 4: Check for last name only (more lenient)
            if len(name_parts) >= 2:
                last_name = name_parts[-1].lower()
                if len(last_name) > 2 and last_name in author_lower:
                    # Additional check: make sure it's not a common word and surrounded by word boundaries
                    if not any(common in last_name for common in ['the', 'and', 'for', 'with', 'from', 'van', 'de', 'la', 'le']):
                        # Check if it appears as a separate word
                        import re
                        if re.search(r'\b' + re.escape(last_name) + r'\b', author_lower):
                            profile_index = i
                            break
        
        if profile_index is None:
            logger.warning(f"Could not find profile owner '{profile_name}' in author list: {author_list[:3]}...")
            logger.warning(f"Name parts: {name_parts}")
            return 'unknown'
        
        # Determine position with truncation awareness
        if profile_index == 0:
            return 'first_author'
        elif profile_index == 1:
            return 'second_author'
        elif profile_index == len(author_list) - 1 and not is_truncated:
            # Only consider as last author if the list is NOT truncated
            return 'last_author'
        elif profile_index == len(author_list) - 1 and is_truncated:
            # If truncated and at the end of visible list, it's middle author
            return 'middle_author'
        else:
            return 'middle_author'
    
    def _classify_research_areas(self, publications: List[Dict]) -> Dict[str, Any]:
        """Classify research areas using Semantic Scholar API or keyword-based approach"""
        if self.use_semantic_scholar and self.semantic_classifier:
            try:
                logger.info("Using hybrid Semantic Scholar + keyword classification")
                
                # Set a timeout for the API classification
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("API classification took too long")
                
                # Set a 60-second timeout
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(60)
                
                try:
                    result = self.semantic_classifier.classify_publications(publications)
                    signal.alarm(0)  # Cancel the alarm
                    return result
                except TimeoutError:
                    logger.warning("Semantic Scholar API timeout, falling back to keywords")
                    signal.alarm(0)  # Cancel the alarm
                    return self._keyword_based_classification(publications)
                    
            except Exception as e:
                logger.error(f"Semantic Scholar API failed, falling back to keywords: {str(e)}")
                # Fall through to keyword-based approach
        
        return self._journal_based_classification(publications)
    
    def _journal_based_classification(self, publications: List[Dict]) -> Dict[str, Any]:
        """Multi-category journal classification: each paper can contribute to multiple research areas"""
        area_scores = defaultdict(float)
        area_papers = defaultdict(list)
        
        for pub in publications:
            venue = pub.get('venue', '').strip()
            paper_domains = []
            matched_journal = None
            classification_method = None
            
            # Try venue-based classification (prioritize conferences over journals)
            if venue:
                venue_lower = venue.lower()
                
                # STEP 1: Check conference database first (highest priority)
                conference_result = self.conference_cache.get_conference_classification(venue_lower)
                if conference_result:
                    paper_domains = [conference_result['domain']]
                    matched_journal = conference_result['name'].lower()
                    classification_method = 'conference'
                    logger.info(f"Conference match: '{venue}' -> '{conference_result['name']}' -> {paper_domains}")
                
                # STEP 2: If no conference match, try journal classification
                elif venue_lower in self.journal_classifications:
                    paper_domains = self.journal_classifications[venue_lower]
                    matched_journal = venue_lower
                    classification_method = 'journal'
                    logger.info(f"Direct journal match: '{venue}' -> {paper_domains}")
                else:
                    # STEP 3: SYSTEMATIC FUZZY MATCHING with proper quality control
                    match_result = self._find_best_journal_match(venue_lower)
                    if match_result:
                        paper_domains, matched_journal = match_result
                        classification_method = 'journal'
                        logger.info(f"Fuzzy journal match: '{venue}' -> '{matched_journal}' -> {paper_domains}")
                    else:
                        logger.warning(f"No venue match for: '{venue}'")
            
            # If no journal match or no venue, fall back to keyword matching
            if not paper_domains:
                keyword_domain = self._classify_by_keywords(pub)
                if keyword_domain:
                    paper_domains = [keyword_domain]
                    classification_method = 'keyword'
                    logger.warning(f"Using keyword fallback for: '{pub.get('title', 'Unknown')}' in '{venue}' -> {keyword_domain}")
            
            # Add paper to results - each paper can contribute to multiple domains
            if paper_domains:
                # Determine venue type based on classification method
                if classification_method == 'conference':
                    venue_type = 'conference'
                else:
                    venue_type = self._determine_venue_type(venue, matched_journal)
                
                # Adjust classification method based on venue type
                if venue_type == 'preprint':
                    classification_method = 'preprint'
                elif venue_type == 'conference' and classification_method == 'journal':
                    classification_method = 'conference'
                
                # Create paper data
                paper_data = {
                    'title': pub.get('title', ''),
                    'year': pub.get('year'),
                    'citations': pub.get('citation_count', 0),
                    'venue': venue if venue else 'Unknown',
                    'venue_type': venue_type,
                    'classification_method': classification_method,
                    'domains': paper_domains  # Store all domains this paper belongs to
                }
                
                if matched_journal:
                    paper_data['matched_journal'] = matched_journal
                
                # Each paper contributes fractional weight to each domain
                weight_per_domain = 1.0 / len(paper_domains)
                
                for domain in paper_domains:
                    area_scores[domain] += weight_per_domain
                    area_papers[domain].append(paper_data)
        
        # Calculate results
        total_papers = sum(area_scores.values())
        if total_papers > 0:
            area_percentages = {area: round(count / total_papers * 100, 1) 
                             for area, count in area_scores.items()}
        else:
            area_percentages = {}
        
        # Sort by percentage
        sorted_areas = sorted(area_percentages.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate classification statistics
        journal_classified = sum(1 for papers in area_papers.values() 
                               for paper in papers if paper.get('classification_method') == 'journal')
        keyword_classified = sum(1 for papers in area_papers.values() 
                               for paper in papers if paper.get('classification_method') == 'keyword')
        
        return {
            'area_percentages': dict(sorted_areas),
            'area_papers': dict(area_papers),
            'primary_area': sorted_areas[0][0] if sorted_areas else None,
            'interdisciplinary_score': len(area_scores) / 9 if area_scores else 0,  # 9 main domains
            'method': 'journal_based_with_keyword_fallback',
            'classification_stats': {
                'journal_classified': journal_classified,
                'keyword_classified': keyword_classified,
                'total_classified': total_papers,
                'journal_coverage': round(journal_classified / total_papers * 100, 1) if total_papers > 0 else 0
            }
        }
    
    def _determine_venue_type(self, venue: str, matched_journal: str = None) -> str:
        """Determine if venue is a journal or conference"""
        if not venue:
            return 'unknown'
            
        venue_lower = venue.lower().strip()
        
        # Check explicit venue types first
        if matched_journal and matched_journal in self.venue_types:
            return self.venue_types[matched_journal]
        
        if venue_lower in self.venue_types:
            return self.venue_types[venue_lower]
        
        # Pattern-based detection
        conference_indicators = [
            'conference', 'workshop', 'symposium', 'proceedings', 
            'cvpr', 'iccv', 'eccv', 'neurips', 'nips', 'icml', 'iclr',
            'aaai', 'ijcai', 'sigcomm', 'nsdi', 'osdi', 'sosp',
            'stoc', 'focs', 'soda', 'sigmod', 'vldb', 'icde'
        ]
        
        journal_indicators = [
            'journal', 'review', 'letters', 'magazine', 'transactions',
            'annals', 'bulletin', 'quarterly', 'monthly', 'annual review'
        ]
        
        # Check for conference indicators
        for indicator in conference_indicators:
            if indicator in venue_lower:
                return 'conference'
        
        # Check for journal indicators
        for indicator in journal_indicators:
            if indicator in venue_lower:
                return 'journal'
        
        # Special cases for preprints
        if any(term in venue_lower for term in ['arxiv', 'biorxiv', 'medrxiv', 'preprint']):
            return 'preprint'
        
        # Default to journal for unknown cases
        return 'journal'
    
    def _classify_by_keywords(self, publication: Dict) -> str:
        """Fallback classification using keywords when journal not found"""
        title = publication.get('title', '').lower()
        venue = publication.get('venue', '').lower()
        text = f"{title} {venue}"
        
        # Special priority for mathematics journals by venue name
        if venue and any(math_term in venue for math_term in [
            'differential equations', 'mathematical analysis', 'pure mathematics',
            'applied mathematics', 'mathematics', 'mathematical'
        ]) and 'statistics' not in venue:
            return 'Mathematics'
        
        # Special priority for statistics journals by venue name
        elif venue and any(stat_term in venue for stat_term in [
            'statistics', 'statistical', 'probability', 'stochastic', 
            'bernoulli', 'biometrika', 'biostatistics'
        ]):
            return 'Statistics & Probability'
        
        # Check for specific CS/AI terms that should override statistical classification
        cs_ai_indicators = [
            'computer vision', 'pattern recognition', 'machine learning', 'deep learning',
            'neural network', 'artificial intelligence', 'image processing', 'computer graphics',
            'robotics', 'natural language processing', 'computer science'
        ]
        
        is_cs_ai = any(indicator in text for indicator in cs_ai_indicators)
        
        paper_scores = {}
        
        for domain, keywords in self.keyword_domains.items():
            score = 0
            
            for keyword in keywords:
                # Use word boundaries for short keywords to avoid false matches
                if len(keyword) <= 3:
                    import re
                    if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                        score += len(keyword.split())
                else:
                    if keyword in text:
                        score += len(keyword.split())
            
            # Boost CS/AI classification when CS/AI terms are present
            if is_cs_ai and domain == 'Machine Learning & AI' and score > 0:
                score *= 2  # Boost AI/ML classification for CS papers
            
            # Penalize statistics classification for clear CS/AI papers
            elif is_cs_ai and domain == 'Statistics & Probability':
                score *= 0.2  # Reduce stats classification for CS/AI papers
            
            if score > 0:
                paper_scores[domain] = score
        
        # Return domain with highest score
        if paper_scores:
            return max(paper_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def _analyze_citations(self, publications: List[Dict]) -> Dict[str, Any]:
        """Analyze citation patterns"""
        citations = [pub.get('citation_count', 0) for pub in publications]
        
        if not citations:
            return {'error': 'No citation data available'}
        
        # Basic statistics
        total_citations = sum(citations)
        avg_citations = statistics.mean(citations)
        median_citations = statistics.median(citations)
        
        # Distribution analysis
        highly_cited = sum(1 for c in citations if c >= 100)
        moderately_cited = sum(1 for c in citations if 10 <= c < 100)
        lowly_cited = sum(1 for c in citations if 1 <= c < 10)
        uncited = sum(1 for c in citations if c == 0)
        
        # Top papers
        pub_citations = [(pub.get('title', ''), pub.get('citation_count', 0), pub.get('year'))
                        for pub in publications]
        top_papers = sorted(pub_citations, key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_citations': total_citations,
            'avg_citations': round(avg_citations, 2),
            'median_citations': median_citations,
            'max_citations': max(citations),
            'citation_distribution': {
                'highly_cited_100plus': highly_cited,
                'moderately_cited_10to99': moderately_cited,
                'lowly_cited_1to9': lowly_cited,
                'uncited': uncited
            },
            'top_papers': top_papers
        }
    
    def _analyze_collaborations(self, publications: List[Dict]) -> Dict[str, Any]:
        """Analyze collaboration patterns with enhanced co-author metrics"""
        all_authors = []
        collaboration_counts = defaultdict(int)
        coauthor_papers = defaultdict(list)
        coauthor_citations = defaultdict(int)
        
        # Identify profile owner name for exclusion
        profile_owner = None
        author_freq_all = Counter()
        
        for pub in publications:
            authors = self._parse_authors(pub.get('authors', ''))
            # Filter out truncation markers for frequency analysis
            authors = [author for author in authors if author != '__TRUNCATED__']
            for author in authors:
                author_freq_all[author] += 1
        
        # The most frequent author is likely the profile owner
        if author_freq_all:
            profile_owner = author_freq_all.most_common(1)[0][0]
        
        truncated_papers_count = 0
        
        for pub in publications:
            authors = self._parse_authors(pub.get('authors', ''))
            
            # Check if this paper's author list was truncated
            is_truncated = '__TRUNCATED__' in authors
            if is_truncated:
                truncated_papers_count += 1
                # Remove truncation marker for processing
                authors = [author for author in authors if author != '__TRUNCATED__']
            
            num_authors = len(authors)
            citations = pub.get('citation_count', 0)
            
            if num_authors > 1:
                collaboration_counts[num_authors] += 1
                
                # Track co-authors for this paper (excluding profile owner)
                coauthors = [author for author in authors if author != profile_owner]
                for coauthor in coauthors:
                    coauthor_papers[coauthor].append({
                        'title': pub.get('title', ''),
                        'year': pub.get('year'),
                        'citations': citations,
                        'venue': pub.get('venue', ''),
                        'total_authors': num_authors,
                        'truncated': is_truncated  # Mark if author list was truncated
                    })
                    coauthor_citations[coauthor] += citations
            
            all_authors.extend(authors)
        
        # Remove profile owner from all_authors for accurate counts
        all_authors = [author for author in all_authors if author != profile_owner]
        author_freq = Counter(all_authors)
        
        # Enhanced co-author analysis
        coauthor_analysis = {}
        for author, papers in coauthor_papers.items():
            coauthor_analysis[author] = {
                'collaboration_count': len(papers),
                'total_citations': coauthor_citations[author],
                'avg_citations': round(coauthor_citations[author] / len(papers), 1) if papers else 0,
                'papers': papers,
                'years_active': list(set(p['year'] for p in papers if p['year'])),
                'collaboration_span': self._calculate_collaboration_span(papers),
                'avg_team_size': round(sum(p['total_authors'] for p in papers) / len(papers), 1) if papers else 0
            }
        
        # Sort collaborators by collaboration count
        top_collaborators = sorted(coauthor_analysis.items(), 
                                 key=lambda x: x[1]['collaboration_count'], 
                                 reverse=True)[:15]
        
        # Calculate collaboration metrics
        total_papers = len(publications)
        collaborative_papers = sum(collaboration_counts.values())
        solo_papers = total_papers - collaborative_papers
        avg_authors_per_paper = len(all_authors) / total_papers if total_papers > 0 else 0
        
        # Collaboration network metrics
        unique_collaborators = len(set(all_authors))
        core_collaborators = len([author for author, count in author_freq.items() if count >= 3])
        occasional_collaborators = len([author for author, count in author_freq.items() if count == 1])
        
        # Calculate collaboration intensity
        if collaborative_papers > 0:
            collaboration_intensity = round(len(all_authors) / collaborative_papers, 1)
        else:
            collaboration_intensity = 0
        
        return {
            'total_unique_collaborators': unique_collaborators,
            'collaborative_papers': collaborative_papers,
            'solo_papers': solo_papers,
            'collaboration_rate': round(collaborative_papers / total_papers * 100, 1) if total_papers > 0 else 0,
            'avg_authors_per_paper': round(avg_authors_per_paper, 1),
            'collaboration_intensity': collaboration_intensity,
            'collaboration_distribution': dict(collaboration_counts),
            'core_collaborators': core_collaborators,
            'occasional_collaborators': occasional_collaborators,
            'top_collaborators': [(name, data) for name, data in top_collaborators],
            'coauthor_details': dict(coauthor_analysis),
            'collaboration_networks': self._analyze_collaboration_networks(coauthor_papers),
            'profile_owner': profile_owner,
            'truncated_papers': truncated_papers_count,
            'truncation_rate': round(truncated_papers_count / total_papers * 100, 1) if total_papers > 0 else 0
        }
    
    def _calculate_collaboration_span(self, papers: List[Dict]) -> int:
        """Calculate the span of years for collaboration"""
        years = [p['year'] for p in papers if p['year']]
        if not years:
            return 0
        return max(years) - min(years) + 1
    
    def _analyze_collaboration_networks(self, coauthor_papers: Dict) -> Dict[str, Any]:
        """Analyze collaboration network patterns"""
        # Find collaborators who have worked together
        collaborator_pairs = defaultdict(int)
        collaborator_sets = defaultdict(set)
        
        # Group papers by collaborator combinations
        for author, papers in coauthor_papers.items():
            collaborator_sets[author] = set(coauthor_papers.keys()) & set(coauthor_papers.keys())
        
        # Calculate network density and clustering
        total_possible_pairs = len(coauthor_papers) * (len(coauthor_papers) - 1) / 2
        actual_connections = sum(len(connections) for connections in collaborator_sets.values()) / 2
        
        network_density = round(actual_connections / total_possible_pairs * 100, 1) if total_possible_pairs > 0 else 0
        
        return {
            'network_density': network_density,
            'total_collaborators': len(coauthor_papers),
            'highly_connected': len([author for author, connections in collaborator_sets.items() if len(connections) > 5])
        }
    
    def _analyze_productivity(self, publications: List[Dict]) -> Dict[str, Any]:
        """Analyze productivity trends over time"""
        year_counts = defaultdict(int)
        year_citations = defaultdict(int)
        
        for pub in publications:
            year = pub.get('year')
            if year:
                year_counts[year] += 1
                year_citations[year] += pub.get('citation_count', 0)
        
        if not year_counts:
            return {'error': 'No year data available'}
        
        # Sort by year
        sorted_years = sorted(year_counts.keys())
        
        # Calculate trends
        recent_years = sorted_years[-5:] if len(sorted_years) >= 5 else sorted_years
        early_years = sorted_years[:5] if len(sorted_years) >= 5 else sorted_years
        
        recent_avg = sum(year_counts[year] for year in recent_years) / len(recent_years)
        early_avg = sum(year_counts[year] for year in early_years) / len(early_years)
        
        trend = "increasing" if recent_avg > early_avg else "decreasing" if recent_avg < early_avg else "stable"
        
        return {
            'publications_by_year': dict(year_counts),
            'citations_by_year': dict(year_citations),
            'total_active_years': len(year_counts),
            'most_productive_year': max(year_counts.items(), key=lambda x: x[1]),
            'productivity_trend': trend,
            'recent_avg_per_year': round(recent_avg, 1),
            'career_avg_per_year': round(sum(year_counts.values()) / len(year_counts), 1)
        }
    
    def _analyze_venues(self, publications: List[Dict]) -> Dict[str, Any]:
        """Analyze publication venues"""
        venue_counts = defaultdict(int)
        venue_citations = defaultdict(int)
        
        for pub in publications:
            venue = pub.get('venue', '').strip()
            if venue:
                venue_counts[venue] += 1
                venue_citations[venue] += pub.get('citation_count', 0)
        
        # Sort venues by publication count
        top_venues = sorted(venue_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Calculate venue impact
        venue_impact = {}
        for venue, count in venue_counts.items():
            avg_citations = venue_citations[venue] / count if count > 0 else 0
            venue_impact[venue] = {
                'publications': count,
                'total_citations': venue_citations[venue],
                'avg_citations': round(avg_citations, 1)
            }
        
        return {
            'total_unique_venues': len(venue_counts),
            'top_venues': top_venues,
            'venue_impact': venue_impact,
            'venue_diversity': len(venue_counts) / len(publications) if publications else 0
        }