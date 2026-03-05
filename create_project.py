#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# =============================================
# NAMA PROYEK
# =============================================
PROJECT_NAME = "duplicate-detection-enterprise3"

# =============================================
# DAFTAR FOLDER
# =============================================
FOLDERS = [
    "src/core/domain",
    "src/core/usecases",
    "src/core/ports",
    "src/infrastructure/persistence",
    "src/infrastructure/cache",
    "src/infrastructure/storage",
    "src/infrastructure/messaging",
    "src/api/routes",
    "src/api/middlewares",
    "src/api/dtos",
    "src/config",
    "src/worker/tasks",
    "src/worker/consumers",
    "tests/unit",
    "tests/integration",
    "migrations/versions",
    "deployments/docker",
    "deployments/kubernetes",
    "monitoring/prometheus",
    "monitoring/grafana/dashboards",
    "scripts",
]

# =============================================
# ISI FILE LENGKAP
# =============================================

FILE_CONTENTS = {
    # ========== SRC/INIT ==========
    "src/__init__.py": "# src package\n",
    
    # ========== SRC/MAIN.PY ==========
    "src/main.py": '''"""Main FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import upload_router, health_router
from src.config import settings
from src.config.logging import setup_logging

# Setup logging
setup_logging(settings.APP_ENV)

# Create FastAPI app
app = FastAPI(
    title="Duplicate Detection API",
    description="Enterprise-grade duplicate photo detection for claims",
    version="1.0.0",
    docs_url="/api/docs" if settings.APP_DEBUG else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "environment": settings.APP_ENV
    }
''',

    # ========== CORE/INIT ==========
    "src/core/__init__.py": "# core package\n",
    
    # ========== CORE/DOMAIN/INIT ==========
    "src/core/domain/__init__.py": '''from .claim import Claim
from .photo import Photo, PhotoHash
from .hash import DuplicateResult, DuplicateMatch

__all__ = ['Claim', 'Photo', 'PhotoHash', 'DuplicateResult', 'DuplicateMatch']
''',

    # ========== CORE/DOMAIN/CLAIM.PY ==========
    "src/core/domain/claim.py": '''"""Claim domain entity"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ClaimStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVIEW = "review"
    DUPLICATE = "duplicate"


class ClaimType(str, Enum):
    WARRANTY = "warranty"
    INSURANCE = "insurance"
    DAMAGE = "damage"


@dataclass
class Claim:
    id: str
    user_id: str
    container_id: str
    claim_type: ClaimType = ClaimType.WARRANTY
    status: ClaimStatus = ClaimStatus.PENDING
    photo_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_photo(self, photo_id: str) -> None:
        if photo_id not in self.photo_ids:
            self.photo_ids.append(photo_id)
            self.updated_at = datetime.utcnow()
    
    def approve(self) -> None:
        self.status = ClaimStatus.APPROVED
        self.updated_at = datetime.utcnow()
    
    def reject(self, reason: Optional[str] = None) -> None:
        self.status = ClaimStatus.REJECTED
        if reason:
            self.metadata["rejection_reason"] = reason
        self.updated_at = datetime.utcnow()
    
    def dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "container_id": self.container_id,
            "claim_type": self.claim_type.value,
            "status": self.status.value,
            "photo_ids": self.photo_ids,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
''',

    # ========== CORE/DOMAIN/PHOTO.PY ==========
    "src/core/domain/photo.py": '''"""Photo domain entity and PhotoHash value object"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib
import io
from PIL import Image
import imagehash


@dataclass
class PhotoHash:
    phash: str
    dhash: str
    ahash: str
    md5: str
    
    @classmethod
    def from_bytes(cls, data: bytes, target_size: int = 256) -> 'PhotoHash':
        with Image.open(io.BytesIO(data)) as img:
            img_resized = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
            phash = str(imagehash.phash(img_resized))
            dhash = str(imagehash.dhash(img_resized))
            ahash = str(imagehash.average_hash(img_resized))
        
        md5 = hashlib.md5(data).hexdigest()
        
        return cls(
            phash=phash,
            dhash=dhash,
            ahash=ahash,
            md5=md5
        )
    
    def weighted_distance(self, other: 'PhotoHash') -> float:
        def hamming(h1: str, h2: str) -> int:
            if len(h1) != len(h2):
                return 64
            bin1 = bin(int(h1, 16))[2:].zfill(len(h1) * 4)
            bin2 = bin(int(h2, 16))[2:].zfill(len(h2) * 4)
            return sum(b1 != b2 for b1, b2 in zip(bin1, bin2))
        
        dist_phash = hamming(self.phash, other.phash)
        dist_dhash = hamming(self.dhash, other.dhash)
        dist_ahash = hamming(self.ahash, other.ahash)
        
        weighted = (dist_phash * 3 + dist_dhash * 2 + dist_ahash * 1) / 6
        return weighted
    
    def similarity(self, other: 'PhotoHash') -> float:
        distance = self.weighted_distance(other)
        return max(0, 100 * (1 - distance / 64))
    
    def dict(self) -> Dict[str, str]:
        return {
            "phash": self.phash,
            "dhash": self.dhash,
            "ahash": self.ahash,
            "md5": self.md5
        }


@dataclass
class Photo:
    id: str
    claim_id: str
    container_id: str
    url: str
    hash: PhotoHash
    file_size: int
    width: int
    height: int
    metadata: Dict[str, Any] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "claim_id": self.claim_id,
            "container_id": self.container_id,
            "url": self.url,
            "hash": self.hash.dict(),
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
''',

    # ========== CORE/DOMAIN/HASH.PY ==========
    "src/core/domain/hash.py": '''"""Duplicate detection result domain"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class DuplicateAction(str, Enum):
    REJECT = "reject"
    REVIEW = "review"
    APPROVE = "approve"


@dataclass
class DuplicateMatch:
    photo_id: str
    claim_id: str
    container_id: str
    similarity: float
    distance: float
    matched_at: datetime
    photo_url: Optional[str] = None
    
    def dict(self) -> Dict[str, Any]:
        return {
            "photo_id": self.photo_id,
            "claim_id": self.claim_id,
            "container_id": self.container_id,
            "similarity": round(self.similarity, 2),
            "distance": round(self.distance, 2),
            "matched_at": self.matched_at.isoformat(),
            "photo_url": self.photo_url
        }


@dataclass
class DuplicateResult:
    is_duplicate: bool
    confidence: float
    action: DuplicateAction
    matches: List[DuplicateMatch]
    processing_time_ms: float
    photo_id: Optional[str] = None
    
    def dict(self) -> Dict[str, Any]:
        return {
            "is_duplicate": self.is_duplicate,
            "confidence": round(self.confidence, 2),
            "action": self.action.value,
            "matches": [m.dict() for m in self.matches],
            "processing_time_ms": round(self.processing_time_ms, 2),
            "photo_id": self.photo_id
        }
''',

    # ========== CORE/USECASES/INIT ==========
    "src/core/usecases/__init__.py": '''from .detect_duplicate import DetectDuplicateUseCase

__all__ = ['DetectDuplicateUseCase']
''',

    # ========== CORE/USECASES/DETECT_DUPLICATE.PY ==========
    "src/core/usecases/detect_duplicate.py": '''"""Detect duplicate photos use case"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import time

from src.core.domain import PhotoHash, DuplicateResult, DuplicateMatch, DuplicateAction
from src.core.ports import HashRepository, PhotoRepository, ClaimRepository, StorageService, CacheService


class DetectDuplicateUseCase:
    def __init__(
        self,
        hash_repo: HashRepository,
        photo_repo: PhotoRepository,
        claim_repo: ClaimRepository,
        storage: StorageService,
        cache: CacheService,
        config: dict = None
    ):
        self.hash_repo = hash_repo
        self.photo_repo = photo_repo
        self.claim_repo = claim_repo
        self.storage = storage
        self.cache = cache
        self.config = config or {
            'threshold_exact': 5,
            'threshold_similar': 15,
            'time_window_days': 365,
            'max_candidates': 50,
            'top_k': 3
        }
    
    async def execute(
        self,
        image_data: bytes,
        claim_id: str,
        container_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DuplicateResult:
        start_time = time.time()
        
        photo_hash = PhotoHash.from_bytes(image_data)
        
        cached = await self._check_cache(photo_hash)
        if cached:
            return cached
        
        candidates = await self._find_candidates(photo_hash, claim_id)
        
        if not candidates:
            result = DuplicateResult(
                is_duplicate=False,
                confidence=0,
                action=DuplicateAction.APPROVE,
                matches=[],
                processing_time_ms=(time.time() - start_time) * 1000
            )
            await self._cache_result(photo_hash, result)
            return result
        
        matches = await self._evaluate_candidates(photo_hash, candidates)
        result = self._determine_action(matches, claim_id)
        result.processing_time_ms = (time.time() - start_time) * 1000
        
        await self._cache_result(photo_hash, result)
        return result
    
    async def _check_cache(self, photo_hash: PhotoHash) -> Optional[DuplicateResult]:
        cache_key = f"hash:{photo_hash.phash[:16]}"
        cached = await self.cache.get(cache_key)
        if cached:
            matches = [
                DuplicateMatch(
                    photo_id=m["photo_id"],
                    claim_id=m["claim_id"],
                    container_id=m["container_id"],
                    similarity=m["similarity"],
                    distance=m["distance"],
                    matched_at=datetime.fromisoformat(m["matched_at"])
                )
                for m in cached.get("matches", [])
            ]
            return DuplicateResult(
                is_duplicate=cached["is_duplicate"],
                confidence=cached["confidence"],
                action=DuplicateAction(cached["action"]),
                matches=matches,
                processing_time_ms=cached["processing_time_ms"]
            )
        return None
    
    async def _cache_result(self, photo_hash: PhotoHash, result: DuplicateResult):
        cache_key = f"hash:{photo_hash.phash[:16]}"
        await self.cache.set(cache_key, result.dict(), ttl=86400)
    
    async def _find_candidates(self, photo_hash: PhotoHash, exclude_claim_id: str) -> List[Dict]:
        since = datetime.utcnow() - timedelta(days=self.config['time_window_days'])
        
        search_hashes = {
            'phash': photo_hash.phash,
            'dhash': photo_hash.dhash,
            'ahash': photo_hash.ahash
        }
        
        return await self.hash_repo.find_similar(
            hashes=search_hashes,
            since=since,
            exclude_claim_id=exclude_claim_id,
            limit=self.config['max_candidates']
        )
    
    async def _evaluate_candidates(self, photo_hash: PhotoHash, candidates: List[Dict]) -> List[DuplicateMatch]:
        matches = []
        
        for candidate in candidates:
            candidate_hash = PhotoHash(
                phash=candidate["phash"],
                dhash=candidate["dhash"],
                ahash=candidate["ahash"],
                md5=candidate["md5"]
            )
            
            distance = photo_hash.weighted_distance(candidate_hash)
            similarity = photo_hash.similarity(candidate_hash)
            
            matches.append(DuplicateMatch(
                photo_id=candidate["photo_id"],
                claim_id=candidate["claim_id"],
                container_id=candidate["container_id"],
                similarity=similarity,
                distance=distance,
                matched_at=candidate.get("created_at", datetime.utcnow())
            ))
        
        matches.sort(key=lambda x: x.similarity, reverse=True)
        return matches[:self.config['top_k']]
    
    def _determine_action(self, matches: List[DuplicateMatch], current_claim_id: str) -> DuplicateResult:
        if not matches:
            return DuplicateResult(
                is_duplicate=False,
                confidence=0,
                action=DuplicateAction.APPROVE,
                matches=[],
                processing_time_ms=0
            )
        
        best_match = matches[0]
        
        if best_match.distance <= self.config['threshold_exact']:
            return DuplicateResult(
                is_duplicate=True,
                confidence=best_match.similarity,
                action=DuplicateAction.REJECT,
                matches=matches,
                processing_time_ms=0
            )
        
        if best_match.distance <= self.config['threshold_similar']:
            different_claims = any(m.claim_id != current_claim_id for m in matches)
            if different_claims and best_match.similarity >= 80:
                return DuplicateResult(
                    is_duplicate=True,
                    confidence=best_match.similarity,
                    action=DuplicateAction.REJECT,
                    matches=matches,
                    processing_time_ms=0
                )
            return DuplicateResult(
                is_duplicate=False,
                confidence=best_match.similarity,
                action=DuplicateAction.REVIEW,
                matches=matches[:1],
                processing_time_ms=0
            )
        
        return DuplicateResult(
            is_duplicate=False,
            confidence=best_match.similarity,
            action=DuplicateAction.APPROVE,
            matches=[],
            processing_time_ms=0
        )
''',

    # ========== CORE/PORTS/INIT ==========
    "src/core/ports/__init__.py": '''from .repositories import HashRepository, PhotoRepository, ClaimRepository
from .services import StorageService, CacheService, MessageQueue

__all__ = ['HashRepository', 'PhotoRepository', 'ClaimRepository', 'StorageService', 'CacheService', 'MessageQueue']
''',

    # ========== CORE/PORTS/REPOSITORIES.PY ==========
    "src/core/ports/repositories.py": '''"""Repository interfaces"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any


class ClaimRepository(ABC):
    @abstractmethod
    async def save(self, claim: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    async def find_by_id(self, claim_id: str) -> Optional[Dict[str, Any]]:
        pass


class PhotoRepository(ABC):
    @abstractmethod
    async def save(self, photo: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    async def find_by_id(self, photo_id: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def find_by_claim(self, claim_id: str) -> List[Dict[str, Any]]:
        pass


class HashRepository(ABC):
    @abstractmethod
    async def save(self, hash_data: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    async def find_by_md5(self, md5: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def find_similar(
        self,
        hashes: Dict[str, str],
        since: datetime,
        exclude_claim_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def create_index(self) -> None:
        pass
''',

    # ========== CORE/PORTS/SERVICES.PY ==========
    "src/core/ports/services.py": '''"""Service interfaces"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class StorageService(ABC):
    @abstractmethod
    async def upload(self, data: bytes, filename: str, content_type: str) -> str:
        pass
    
    @abstractmethod
    async def download(self, url: str) -> bytes:
        pass
    
    @abstractmethod
    async def delete(self, url: str) -> bool:
        pass


class CacheService(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass


class MessageQueue(ABC):
    @abstractmethod
    async def publish(self, topic: str, message: Dict[str, Any]) -> bool:
        pass
''',

    # ========== INFRASTRUCTURE/INIT ==========
    "src/infrastructure/__init__.py": "# infrastructure package\n",

    # ========== INFRASTRUCTURE/PERSISTENCE/INIT ==========
    "src/infrastructure/persistence/__init__.py": '''from .postgres_repositories import PostgresClaimRepository, PostgresPhotoRepository
from .elasticsearch_hash_repo import ElasticsearchHashRepository

__all__ = ['PostgresClaimRepository', 'PostgresPhotoRepository', 'ElasticsearchHashRepository']
''',

    # ========== INFRASTRUCTURE/PERSISTENCE/POSTGRES_REPOSITORIES.PY ==========
    "src/infrastructure/persistence/postgres_repositories.py": '''"""PostgreSQL implementations"""
from typing import List, Optional, Dict, Any
import asyncpg
import json
from datetime import datetime

from src.core.ports import ClaimRepository, PhotoRepository


class PostgresClaimRepository(ClaimRepository):
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def save(self, claim: Dict[str, Any]) -> str:
        query = """
        INSERT INTO claims (id, user_id, container_id, claim_type, status, photo_ids, metadata, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (id) DO UPDATE SET
            status = EXCLUDED.status,
            metadata = EXCLUDED.metadata,
            updated_at = EXCLUDED.updated_at
        RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            claim_id = await conn.fetchval(
                query,
                claim["id"],
                claim["user_id"],
                claim["container_id"],
                claim.get("claim_type", "warranty"),
                claim.get("status", "pending"),
                claim.get("photo_ids", []),
                json.dumps(claim.get("metadata", {})),
                claim.get("created_at", datetime.utcnow()),
                claim.get("updated_at", datetime.utcnow())
            )
            return claim_id
    
    async def find_by_id(self, claim_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM claims WHERE id = $1"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, claim_id)
            if row:
                return dict(row)
            return None


class PostgresPhotoRepository(PhotoRepository):
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def save(self, photo: Dict[str, Any]) -> str:
        query = """
        INSERT INTO photos (id, claim_id, container_id, url, phash, dhash, ahash, md5, file_size, width, height, metadata, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            photo_id = await conn.fetchval(
                query,
                photo["id"],
                photo["claim_id"],
                photo["container_id"],
                photo["url"],
                photo.get("phash", ""),
                photo.get("dhash", ""),
                photo.get("ahash", ""),
                photo.get("md5", ""),
                photo.get("file_size", 0),
                photo.get("width", 0),
                photo.get("height", 0),
                json.dumps(photo.get("metadata", {})),
                photo.get("created_at", datetime.utcnow())
            )
            return photo_id
    
    async def find_by_id(self, photo_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM photos WHERE id = $1"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, photo_id)
            if row:
                return dict(row)
            return None
    
    async def find_by_claim(self, claim_id: str) -> List[Dict[str, Any]]:
        query = "SELECT * FROM photos WHERE claim_id = $1 ORDER BY created_at DESC"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, claim_id)
            return [dict(row) for row in rows]
''',

    # ========== INFRASTRUCTURE/PERSISTENCE/ELASTICSEARCH_HASH_REPO.PY ==========
    "src/infrastructure/persistence/elasticsearch_hash_repo.py": '''"""Elasticsearch implementation for hash similarity search"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from elasticsearch import AsyncElasticsearch
import structlog


logger = structlog.get_logger()


class ElasticsearchHashRepository:
    def __init__(self, client: AsyncElasticsearch, index: str = "photo_hashes"):
        self.client = client
        self.index = index
    
    async def save(self, hash_data: Dict[str, Any]) -> str:
        try:
            if 'created_at' in hash_data and isinstance(hash_data['created_at'], datetime):
                hash_data['created_at'] = hash_data['created_at'].isoformat()
            
            resp = await self.client.index(
                index=self.index,
                id=hash_data.get('id'),
                document=hash_data,
                refresh='wait_for'
            )
            return resp['_id']
        except Exception as e:
            logger.error("elasticsearch_save_failed", error=str(e))
            raise
    
    async def find_by_md5(self, md5: str) -> List[Dict[str, Any]]:
        try:
            query = {
                "query": {"term": {"md5": md5}},
                "size": 10
            }
            resp = await self.client.search(index=self.index, body=query)
            
            results = []
            for hit in resp['hits']['hits']:
                source = hit['_source']
                if 'created_at' in source:
                    source['created_at'] = datetime.fromisoformat(source['created_at'])
                results.append(source)
            return results
        except Exception:
            return []
    
    async def find_similar(
        self,
        hashes: Dict[str, str],
        since: datetime,
        exclude_claim_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        script = """
        double score = 0.0;
        
        int hammingDistance(String a, String b) {
            if (a == null || b == null) return 64;
            int distance = 0;
            for (int i = 0; i < a.length() && i < b.length(); i++) {
                if (a.charAt(i) != b.charAt(i)) {
                    distance++;
                }
            }
            return distance;
        }
        
        if (doc['phash'].size() > 0) {
            int dist = hammingDistance(doc['phash'].value, params.phash);
            score += (64.0 - dist) * 3.0;
        }
        if (doc['dhash'].size() > 0) {
            int dist = hammingDistance(doc['dhash'].value, params.dhash);
            score += (64.0 - dist) * 2.0;
        }
        if (doc['ahash'].size() > 0) {
            int dist = hammingDistance(doc['ahash'].value, params.ahash);
            score += (64.0 - dist) * 1.0;
        }
        return score;
        """
        
        must_conditions = [{"range": {"created_at": {"gte": since.isoformat()}}}]
        must_not_conditions = []
        if exclude_claim_id:
            must_not_conditions.append({"term": {"claim_id": exclude_claim_id}})
        
        query = {
            "query": {"bool": {"must": must_conditions, "must_not": must_not_conditions}},
            "script_score": {"script": {"source": script, "params": hashes}},
            "size": limit
        }
        
        try:
            resp = await self.client.search(index=self.index, body=query)
            results = []
            for hit in resp['hits']['hits']:
                source = hit['_source']
                source['_score'] = hit['_score']
                if 'created_at' in source:
                    source['created_at'] = datetime.fromisoformat(source['created_at'])
                results.append(source)
            return results
        except Exception as e:
            logger.error("elasticsearch_find_similar_failed", error=str(e))
            return []
    
    async def create_index(self) -> None:
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "photo_id": {"type": "keyword"},
                    "claim_id": {"type": "keyword"},
                    "container_id": {"type": "keyword"},
                    "phash": {"type": "keyword"},
                    "dhash": {"type": "keyword"},
                    "ahash": {"type": "keyword"},
                    "md5": {"type": "keyword"},
                    "file_size": {"type": "integer"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "created_at": {"type": "date"},
                }
            },
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "refresh_interval": "30s"
            }
        }
        
        exists = await self.client.indices.exists(index=self.index)
        if not exists:
            await self.client.indices.create(index=self.index, body=mapping)
''',

    # ========== INFRASTRUCTURE/CACHE/INIT ==========
    "src/infrastructure/cache/__init__.py": '''from .redis_cache import RedisCacheService

__all__ = ['RedisCacheService']
''',

    # ========== INFRASTRUCTURE/CACHE/REDIS_CACHE.PY ==========
    "src/infrastructure/cache/redis_cache.py": '''"""Redis cache implementation"""
from typing import Optional, Dict, Any
import json
from redis.asyncio import Redis


class RedisCacheService:
    def __init__(self, client: Redis, prefix: str = "dupdetect"):
        self.client = client
        self.prefix = prefix
    
    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        data = await self.client.get(self._key(key))
        if data:
            return json.loads(data)
        return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        data = json.dumps(value, default=str)
        if ttl:
            await self.client.setex(self._key(key), ttl, data)
        else:
            await self.client.set(self._key(key), data)
        return True
    
    async def delete(self, key: str) -> bool:
        result = await self.client.delete(self._key(key))
        return result > 0
''',

    # ========== INFRASTRUCTURE/STORAGE/INIT ==========
    "src/infrastructure/storage/__init__.py": '''from .s3_storage import S3StorageService

__all__ = ['S3StorageService']
''',

    # ========== INFRASTRUCTURE/STORAGE/S3_STORAGE.PY ==========
    "src/infrastructure/storage/s3_storage.py": '''"""S3/MinIO storage implementation"""
from typing import Optional
import aioboto3
from botocore.exceptions import ClientError
import uuid
from datetime import datetime


class S3StorageService:
    def __init__(
        self,
        bucket: str,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "us-east-1",
        public_base_url: Optional[str] = None
    ):
        self.bucket = bucket
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.public_base_url = public_base_url or f"https://{bucket}.s3.amazonaws.com"
        self.session = aioboto3.Session()
    
    async def upload(self, data: bytes, filename: str, content_type: str) -> str:
        ext = filename.split('.')[-1] if '.' in filename else 'bin'
        key = f"photos/{datetime.utcnow().strftime('%Y/%m/%d')}/{uuid.uuid4()}.{ext}"
        
        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        ) as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type
            )
            return f"{self.public_base_url.rstrip('/')}/{key}"
    
    async def download(self, url: str) -> bytes:
        key = url.split('/')[-3:]
        key = '/'.join(key)
        
        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        ) as s3:
            response = await s3.get_object(Bucket=self.bucket, Key=key)
            return await response['Body'].read()
    
    async def delete(self, url: str) -> bool:
        key = url.split('/')[-3:]
        key = '/'.join(key)
        
        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        ) as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)
            return True
''',

    # ========== INFRASTRUCTURE/MESSAGING/INIT ==========
    "src/infrastructure/messaging/__init__.py": '''from .kafka_producer import KafkaProducer

__all__ = ['KafkaProducer']
''',

    # ========== INFRASTRUCTURE/MESSAGING/KAFKA_PRODUCER.PY ==========
    "src/infrastructure/messaging/kafka_producer.py": '''"""Kafka messaging implementation"""
from typing import Dict, Any
import json
from aiokafka import AIOKafkaProducer


class KafkaProducer:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
    
    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
    
    async def stop(self):
        if self.producer:
            await self.producer.stop()
    
    async def publish(self, topic: str, message: Dict[str, Any]) -> bool:
        if not self.producer:
            await self.start()
        
        try:
            await self.producer.send(topic, message)
            return True
        except Exception:
            return False
''',

    # ========== INFRASTRUCTURE/CONTAINER.PY ==========
    "src/infrastructure/container.py": '''"""Dependency injection container"""
from functools import lru_cache
import asyncpg
from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis

from src.core.usecases import DetectDuplicateUseCase
from src.infrastructure.persistence import (
    PostgresClaimRepository,
    PostgresPhotoRepository,
    ElasticsearchHashRepository
)
from src.infrastructure.cache import RedisCacheService
from src.infrastructure.storage import S3StorageService
from src.config import settings


class Container:
    def __init__(self):
        self._postgres_pool = None
        self._elasticsearch = None
        self._redis = None
        self._initialized = False
    
    async def init(self):
        if self._initialized:
            return
        
        self._postgres_pool = await asyncpg.create_pool(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            min_size=5,
            max_size=20
        )
        
        self._elasticsearch = AsyncElasticsearch(hosts=settings.ELASTICSEARCH_HOSTS)
        
        self._redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        self._initialized = True
    
    async def close(self):
        if self._postgres_pool:
            await self._postgres_pool.close()
        if self._elasticsearch:
            await self._elasticsearch.close()
        if self._redis:
            await self._redis.close()
    
    @property
    def claim_repo(self):
        return PostgresClaimRepository(self._postgres_pool)
    
    @property
    def photo_repo(self):
        return PostgresPhotoRepository(self._postgres_pool)
    
    @property
    def hash_repo(self):
        return ElasticsearchHashRepository(self._elasticsearch)
    
    @property
    def cache_service(self):
        return RedisCacheService(self._redis)
    
    @property
    def storage_service(self):
        return S3StorageService(
            bucket=settings.S3_BUCKET,
            endpoint_url=settings.S3_ENDPOINT,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            public_base_url=settings.S3_PUBLIC_URL
        )
    
    @property
    def detector_usecase(self):
        return DetectDuplicateUseCase(
            hash_repo=self.hash_repo,
            photo_repo=self.photo_repo,
            claim_repo=self.claim_repo,
            storage=self.storage_service,
            cache=self.cache_service,
            config={
                'threshold_exact': settings.THRESHOLD_EXACT,
                'threshold_similar': settings.THRESHOLD_SIMILAR,
                'time_window_days': 365,
                'max_candidates': 50,
                'top_k': 3
            }
        )


@lru_cache()
def get_container():
    return Container()
''',

    # ========== API/INIT ==========
    "src/api/__init__.py": '''from .routes import upload_router, health_router

__all__ = ['upload_router', 'health_router']
''',

    # ========== API/ROUTES/INIT ==========
    "src/api/routes/__init__.py": '''from .upload import router as upload_router
from .health import router as health_router

__all__ = ['upload_router', 'health_router']
''',

    # ========== API/ROUTES/UPLOAD.PY ==========
    "src/api/routes/upload.py": '''"""Photo upload routes"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import uuid

from src.core.usecases import DetectDuplicateUseCase
from src.api.dtos import UploadResponse, ErrorResponse
from src.infrastructure.container import get_container


router = APIRouter(prefix="/claims", tags=["upload"])


async def get_detector() -> DetectDuplicateUseCase:
    container = get_container()
    if not container._initialized:
        await container.init()
    return container.detector_usecase


@router.post("/photo", response_model=UploadResponse)
async def upload_photo(
    claim_id: str = Form(...),
    container_id: str = Form(...),
    photo: UploadFile = File(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    timestamp: Optional[int] = Form(None),
    device_id: Optional[str] = Form(None),
    detector: DetectDuplicateUseCase = Depends(get_detector)
):
    request_id = str(uuid.uuid4())
    
    try:
        if not photo.content_type or not photo.content_type.startswith('image/'):
            raise HTTPException(400, "File must be an image")
        
        image_data = await photo.read()
        
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(400, "File too large (max 10MB)")
        
        metadata = {
            "filename": photo.filename,
            "content_type": photo.content_type,
            "latitude": latitude,
            "longitude": longitude,
            "client_timestamp": timestamp,
            "device_id": device_id,
            "request_id": request_id
        }
        
        result = await detector.execute(
            image_data=image_data,
            claim_id=claim_id,
            container_id=container_id,
            metadata=metadata
        )
        
        return UploadResponse(
            success=True,
            request_id=request_id,
            photo_id=result.photo_id,
            duplicate=result.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                success=False,
                error=str(e),
                request_id=request_id
            ).dict()
        )
''',

    # ========== API/ROUTES/HEALTH.PY ==========
    "src/api/routes/health.py": '''"""Health check routes"""
from fastapi import APIRouter
from datetime import datetime

from src.config import settings
from src.infrastructure.container import get_container


router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    container = get_container()
    
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {}
    }
    
    try:
        if container._postgres_pool:
            async with container._postgres_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            health_status["dependencies"]["postgresql"] = "healthy"
        else:
            health_status["dependencies"]["postgresql"] = "not_initialized"
    except Exception as e:
        health_status["dependencies"]["postgresql"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/ready")
async def readiness_check():
    container = get_container()
    if not container._initialized:
        return {"status": "not_ready"}
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    return {"status": "alive"}
''',

    # ========== API/MIDDLEWARES/INIT ==========
    "src/api/middlewares/__init__.py": '''from .logging import RequestLoggingMiddleware
from .rate_limit import RateLimitMiddleware

__all__ = ['RequestLoggingMiddleware', 'RateLimitMiddleware']
''',

    # ========== API/MIDDLEWARES/LOGGING.PY ==========
    "src/api/middlewares/logging.py": '''"""Request logging middleware"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid
import structlog


logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()
        
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path
        )
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            logger.info(
                "request_completed",
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2)
            )
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            logger.error("request_failed", request_id=request_id, error=str(e))
            raise
''',

    # ========== API/MIDDLEWARES/RATE_LIMIT.PY ==========
    "src/api/middlewares/rate_limit.py": '''"""Rate limiting middleware"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.infrastructure.container import get_container


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 100, window: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/health", "/ready", "/live", "/metrics"]:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        container = get_container()
        
        if container._redis and container._initialized:
            key = f"rate_limit:{client_ip}"
            current = await container.cache_service.get(key)
            current = current.get("count", 0) if current else 0
            
            if current >= self.limit:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
            
            if current == 0:
                await container.cache_service.set(
                    key,
                    {"count": 1},
                    ttl=self.window
                )
            else:
                await container.cache_service.set(
                    key,
                    {"count": current + 1},
                    ttl=self.window
                )
        
        return await call_next(request)
''',

    # ========== API/DTOS/INIT ==========
    "src/api/dtos/__init__.py": '''from .requests import UploadResponse, ErrorResponse

__all__ = ['UploadResponse', 'ErrorResponse']
''',

    # ========== API/DTOS/REQUESTS.PY ==========
    "src/api/dtos/requests.py": '''"""Request/Response DTOs"""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class UploadResponse(BaseModel):
    success: bool
    request_id: str
    photo_id: Optional[str] = None
    duplicate: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    request_id: str
''',

    # ========== CONFIG/INIT ==========
    "src/config/__init__.py": '''from .settings import settings
from .logging import setup_logging

__all__ = ['settings', 'setup_logging']
''',

    # ========== CONFIG/SETTINGS.PY ==========
    "src/config/settings.py": '''"""Application settings using Pydantic"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional


class Settings(BaseSettings):
    APP_NAME: str = "duplicate-detection"
    APP_ENV: str = Field("development", env="APP_ENV")
    APP_DEBUG: bool = Field(False, env="APP_DEBUG")
    APP_VERSION: str = "1.0.0"
    
    API_HOST: str = Field("0.0.0.0", env="API_HOST")
    API_PORT: int = Field(8000, env="API_PORT")
    
    POSTGRES_HOST: str = Field("localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT")
    POSTGRES_USER: str = Field("postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("postgres", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field("claim_db", env="POSTGRES_DB")
    
    ELASTICSEARCH_HOSTS: List[str] = Field(["http://localhost:9200"], env="ELASTICSEARCH_HOSTS")
    ELASTICSEARCH_INDEX: str = Field("photo_hashes", env="ELASTICSEARCH_INDEX")
    
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    
    S3_BUCKET: str = Field("photos", env="S3_BUCKET")
    S3_ENDPOINT: Optional[str] = Field(None, env="S3_ENDPOINT")
    S3_ACCESS_KEY: Optional[str] = Field(None, env="S3_ACCESS_KEY")
    S3_SECRET_KEY: Optional[str] = Field(None, env="S3_SECRET_KEY")
    S3_PUBLIC_URL: Optional[str] = Field(None, env="S3_PUBLIC_URL")
    
    THRESHOLD_EXACT: int = Field(5, env="THRESHOLD_EXACT")
    THRESHOLD_SIMILAR: int = Field(15, env="THRESHOLD_SIMILAR")
    MAX_FILE_SIZE: int = Field(10 * 1024 * 1024, env="MAX_FILE_SIZE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
''',

    # ========== CONFIG/LOGGING.PY ==========
    "src/config/logging.py": '''"""Logging configuration"""
import logging
import structlog


def setup_logging(env: str = "development"):
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG if env == "development" else logging.INFO,
    )
''',

    # ========== WORKER/INIT ==========
    "src/worker/__init__.py": '''from .celery_app import celery_app

__all__ = ['celery_app']
''',

    # ========== WORKER/CELERY_APP.PY ==========
    "src/worker/celery_app.py": '''"""Celery application"""
from celery import Celery

celery_app = Celery(
    'worker',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['src.worker.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
)
''',

    # ========== WORKER/TASKS/INIT ==========
    "src/worker/tasks/__init__.py": '''from .process_photo import process_photo

__all__ = ['process_photo']
''',

    # ========== WORKER/TASKS/PROCESS_PHOTO.PY ==========
    "src/worker/tasks/process_photo.py": '''"""Photo processing tasks"""
from src.worker.celery_app import celery_app
import structlog


logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3)
def process_photo(self, photo_data: dict):
    try:
        logger.info("processing_photo", task_id=self.request.id)
        return {"status": "success", "photo_id": photo_data.get("id")}
    except Exception as e:
        logger.error("photo_processing_failed", error=str(e))
        self.retry(countdown=60)
''',

    # ========== WORKER/CONSUMERS/INIT ==========
    "src/worker/consumers/__init__.py": '''from .kafka_consumer import PhotoConsumer

__all__ = ['PhotoConsumer']
''',

    # ========== WORKER/CONSUMERS/KAFKA_CONSUMER.PY ==========
    "src/worker/consumers/kafka_consumer.py": '''"""Kafka consumers"""
import json
import structlog
from aiokafka import AIOKafkaConsumer


logger = structlog.get_logger()


class PhotoConsumer:
    def __init__(self, bootstrap_servers: str, topic: str, group_id: str):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.consumer = None
    
    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        await self.consumer.start()
        logger.info("kafka_consumer_started", topic=self.topic)
    
    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
    
    async def consume(self):
        async for msg in self.consumer:
            logger.info("message_received", topic=msg.topic, value=msg.value)
''',

    # ========== TESTS ==========
    "tests/__init__.py": "# tests package\n",
    "tests/unit/__init__.py": "",
    "tests/unit/test_domain.py": "# Unit tests for domain\n",
    "tests/unit/test_usecases.py": "# Unit tests for usecases\n",
    "tests/integration/__init__.py": "",
    "tests/integration/test_api.py": "# Integration tests for API\n",
    "tests/conftest.py": '''"""Pytest fixtures"""
import pytest

@pytest.fixture
def sample_photo():
    return b"dummy photo data"
''',

    # ========== MIGRATIONS ==========
    "migrations/versions/.gitkeep": "",
    "migrations/env.py": "# Alembic environment\n",

    # ========== DEPLOYMENTS ==========
    "deployments/docker/Dockerfile.api": "# Dockerfile for API\nFROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD [\"uvicorn\", \"src.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n",
    "deployments/docker/Dockerfile.worker": "# Dockerfile for worker\nFROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD [\"celery\", \"-A\", \"src.worker.celery_app\", \"worker\"]\n",
    "deployments/docker/docker-compose.yml": '''# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: claim_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  api:
    build:
      context: ../..
      dockerfile: deployments/docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy
    volumes:
      - ../../src:/app/src

  worker:
    build:
      context: ../..
      dockerfile: deployments/docker/Dockerfile.worker
    environment:
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy
    volumes:
      - ../../src:/app/src

volumes:
  postgres_data:
  redis_data:
  es_data:
''',

    # ========== KUBERNETES ==========
    "deployments/kubernetes/namespace.yaml": '''apiVersion: v1
kind: Namespace
metadata:
  name: duplicate-detection
''',

    "deployments/kubernetes/configmap.yaml": '''apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: duplicate-detection
data:
  APP_ENV: production
  POSTGRES_HOST: postgres-service
  REDIS_HOST: redis-service
  ELASTICSEARCH_HOSTS: http://elasticsearch-service:9200
''',

    "deployments/kubernetes/secrets.yaml": '''apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: duplicate-detection
type: Opaque
data:
  POSTGRES_PASSWORD: cG9zdGdyZXM=  # base64 encoded "postgres"
''',

    "deployments/kubernetes/api-deployment.yaml": '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: duplicate-detection
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: your-registry/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: POSTGRES_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: POSTGRES_HOST
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: POSTGRES_PASSWORD
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: duplicate-detection
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
''',

    "deployments/kubernetes/worker-deployment.yaml": '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker
  namespace: duplicate-detection
spec:
  replicas: 2
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
      - name: worker
        image: your-registry/worker:latest
        env:
        - name: POSTGRES_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: POSTGRES_HOST
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: POSTGRES_PASSWORD
''',

    # ========== MONITORING ==========
    "monitoring/prometheus/prometheus.yml": '''# Prometheus config
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['api-service:80']
    metrics_path: '/metrics'
''',

    "monitoring/grafana/dashboards/.gitkeep": "",

    # ========== SCRIPTS ==========
    "scripts/init_elasticsearch.py": '''#!/usr/bin/env python
"""Initialize Elasticsearch index"""
import asyncio
from elasticsearch import AsyncElasticsearch

async def main():
    client = AsyncElasticsearch(['http://localhost:9200'])
    
    # Create index with mapping
    mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "photo_id": {"type": "keyword"},
                "claim_id": {"type": "keyword"},
                "container_id": {"type": "keyword"},
                "phash": {"type": "keyword"},
                "dhash": {"type": "keyword"},
                "ahash": {"type": "keyword"},
                "md5": {"type": "keyword"},
                "created_at": {"type": "date"},
            }
        }
    }
    
    index_name = "photo_hashes"
    exists = await client.indices.exists(index=index_name)
    
    if not exists:
        await client.indices.create(index=index_name, body=mapping)
        print(f"✅ Index {index_name} created")
    else:
        print(f"⚠️ Index {index_name} already exists")
    
    await client.close()

if __name__ == '__main__':
    asyncio.run(main())
''',
}

# =============================================
# ROOT FILES
# =============================================
ROOT_FILES = {
    ".env.example": '''# Application
APP_ENV=development
APP_DEBUG=true

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=claim_db

# Elasticsearch
ELASTICSEARCH_HOSTS=["http://localhost:9200"]
ELASTICSEARCH_INDEX=photo_hashes

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# S3 Storage
S3_BUCKET=photos
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_PUBLIC_URL=http://localhost:9000/photos

# Detection
THRESHOLD_EXACT=5
THRESHOLD_SIMILAR=15
''',

    "requirements.txt": '''# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6

# Database
asyncpg==0.29.0
elasticsearch==8.11.0
redis==5.0.1

# Image Processing
Pillow==10.1.0
imagehash==4.3.1

# Messaging
celery==5.3.4
aiokafka==0.8.1

# Storage
aioboto3==12.0.0

# Monitoring
prometheus-client==0.19.0
structlog==24.1.0

# Utils
python-dotenv==1.0.0
tenacity==8.2.3
''',

    "requirements-dev.txt": '''# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Linting
black==23.12.0
flake8==6.1.0
mypy==1.7.0
isort==5.13.0
''',

    "Makefile": '''.PHONY: help install dev test docker-up docker-down clean

help:
\t@echo "Available commands:"
\t@echo "  make install     - Install dependencies"
\t@echo "  make dev         - Run development server"
\t@echo "  make test        - Run tests"
\t@echo "  make docker-up   - Start all services"
\t@echo "  make docker-down - Stop all services"
\t@echo "  make clean       - Clean cache files"

install:
\tpip install -r requirements.txt -r requirements-dev.txt

dev:
\tuvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
\tpytest tests/ -v

docker-up:
\tdocker-compose -f deployments/docker/docker-compose.yml up -d

docker-down:
\tdocker-compose -f deployments/docker/docker-compose.yml down

clean:
\tfind . -type d -name "__pycache__" -exec rm -rf {} +
\tfind . -type f -name "*.pyc" -delete
'''
}