"""
TruthLens - Verification Pipeline Orchestrator
Drives the asynchronous state machine for evidence-based news verification:
QUEUED -> EXTRACTING -> SEARCHING -> RETRIEVING -> VERIFYING -> GENERATING_REPORT -> COMPLETED.
Persists every state transition, isolates failures, and allows clean deduplicated retries.
"""
from datetime import datetime, timezone
import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.verification import VerificationClaimRecord, VerificationJob
from app.nlp.registry import language_registry
from app.schemas.evidence import EvidencePassage
from app.schemas.verification import ClaimVerificationResult, VerificationReport
from app.services.claim_extractor import claim_extractor
from app.services.evidence_collector import evidence_collector
from app.services.nli_verifier import nli_verifier
from app.services.report_generator import report_generator
from app.services.search_service import search_service
from app.services.verdict_engine import verdict_engine

logger = logging.getLogger("truthlens.orchestrator")


class VerificationOrchestrator:
    """
    Coordinates end-to-end evidence collection, NLI verification, and report synthesis.
    """

    def process_job(self, job_id: str, db: Optional[Session] = None) -> None:
        """
        Executes the full pipeline for a given job.
        Operates in provided DB session or creates a new SessionLocal.
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        try:
            job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found in database.")
                return

            if job.status == "CANCELLED":
                logger.info(f"Job {job_id} was cancelled before processing.")
                return

            # Stage 1: EXTRACTING CLAIMS (20%)
            self._update_job_state(
                db, job, status="EXTRACTING", step="Extracting atomic checkable claims", progress=20
            )

            # Language detection
            if not job.language or job.language == "auto":
                detected_lang, _, is_mixed = language_registry.detect_language(
                    f"{job.headline or ''} {job.original_text}"
                )
                job.language = detected_lang
                job.is_code_mixed = is_mixed
                db.commit()

            extraction_resp = claim_extractor.extract_claims(
                text=job.original_text, headline=job.headline
            )

            # Check if cancelled mid-flight
            job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
            if job.status == "CANCELLED":
                return

            if not extraction_resp.claims:
                logger.warning(f"No verifiable claims found in text for job {job_id}")
                empty_report = report_generator.generate_report(
                    original_content=job.original_text,
                    original_title=job.headline,
                    detected_language=job.language,
                    is_code_mixed=job.is_code_mixed,
                    claim_results=[],
                    search_providers_used=[],
                    extraction_method=extraction_resp.extraction_method,
                    nli_inference_method="heuristic_fallback"
                )
                job.status = "COMPLETED"
                job.current_step = "Verification complete (no checkable claims found)"
                job.progress_percent = 100
                job.overall_verdict = empty_report.overall_verdict.value
                job.overall_confidence = empty_report.overall_confidence
                job.report_json = json.dumps(empty_report.model_dump(), ensure_ascii=False)
                job.updated_at = datetime.now(timezone.utc)
                db.commit()
                return

            # Stage 2: SEARCHING FOR EVIDENCE (40%)
            self._update_job_state(
                db, job, status="SEARCHING", step="Searching live internet evidence across multi-tier providers", progress=40
            )

            search_leads_by_claim = {}
            providers_used = set()

            for claim in extraction_resp.claims:
                job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
                if job.status == "CANCELLED":
                    return

                # Search using neutral query
                neutral_resp = search_service.search(
                    claim.neutral_search_query, lang=job.language, max_results=6
                )
                for p in neutral_resp.successful_providers:
                    providers_used.add(p)

                # Search using counter-hypothesis query
                counter_resp = search_service.search(
                    claim.counter_search_query, lang=job.language, max_results=4
                )
                for p in counter_resp.successful_providers:
                    providers_used.add(p)

                # Combine unique search result items
                combined_items = []
                seen_urls = set()
                for it in neutral_resp.items + counter_resp.items:
                    if it.url not in seen_urls:
                        seen_urls.add(it.url)
                        combined_items.append(it)

                search_leads_by_claim[claim.id] = combined_items

            # Stage 3: RETRIEVING & CHUNKING ARTICLES (60%)
            self._update_job_state(
                db, job, status="RETRIEVING", step="Fetching articles, chunking passages, and detecting syndication", progress=60
            )

            passages_by_claim = {}
            for claim in extraction_resp.claims:
                job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
                if job.status == "CANCELLED":
                    return

                leads = search_leads_by_claim.get(claim.id, [])
                evidence_resp = evidence_collector.collect_evidence_for_claim(
                    claim=claim, search_results=leads
                )
                passages_by_claim[claim.id] = evidence_resp.passages

            # Stage 4: NLI VERIFICATION & CLAIM VERDICTS (80%)
            self._update_job_state(
                db, job, status="VERIFYING", step="Evaluating evidence entailment and contradiction with NLI", progress=80
            )

            # Ensure NLI model load is attempted once if enabled
            nli_verifier.load_model()

            claim_results: List[ClaimVerificationResult] = []

            for claim in extraction_resp.claims:
                job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
                if job.status == "CANCELLED":
                    return

                passages = passages_by_claim.get(claim.id, [])
                evaluations = []

                for p in passages:
                    eval_res = nli_verifier.evaluate_passage(
                        claim_text=claim.claim_text, passage=p, lang=job.language
                    )
                    evaluations.append(eval_res)

                # Synthesize claim-level verdict
                claim_verdict_res = verdict_engine.synthesize_claim_verdict(
                    claim=claim, evaluations=evaluations
                )
                claim_results.append(claim_verdict_res)

                # Persist claim record in database
                claim_record = VerificationClaimRecord(
                    id=claim.id,
                    job_id=job.id,
                    claim_text=claim.claim_text,
                    claim_type=claim.claim_type.value,
                    language=job.language,
                    verdict=claim_verdict_res.verdict.value,
                    confidence=claim_verdict_res.confidence,
                    supporting_sources_count=claim_verdict_res.supporting_evidence_count,
                    contradicting_sources_count=claim_verdict_res.contradicting_evidence_count,
                    explanation=claim_verdict_res.explanation,
                    evaluations_json=json.dumps([e.model_dump() for e in evaluations], ensure_ascii=False)
                )
                db.add(claim_record)

            db.commit()

            # Determine actual NLI inference method based on what genuinely succeeded
            all_eval_methods = {
                ev.inference_method
                for cres in claim_results
                for ev in cres.evaluations
            }
            if "neural" in all_eval_methods:
                nli_inference_method = "neural"
            elif "hf_inference_api" in all_eval_methods:
                nli_inference_method = "hf_inference_api"
            else:
                nli_inference_method = "heuristic_fallback"

            # Stage 5: GENERATING REPORT (95%)
            self._update_job_state(
                db, job, status="GENERATING_REPORT", step="Synthesizing final executive summary and audit trail", progress=95
            )

            report = report_generator.generate_report(
                original_content=job.original_text,
                original_title=job.headline,
                detected_language=job.language,
                is_code_mixed=job.is_code_mixed,
                claim_results=claim_results,
                search_providers_used=list(providers_used),
                extraction_method=extraction_resp.extraction_method,
                nli_inference_method=nli_inference_method
            )

            # Stage 6: COMPLETED (100%)
            job.status = "COMPLETED"
            job.current_step = "Verification complete"
            job.progress_percent = 100
            job.overall_verdict = report.overall_verdict.value
            job.overall_confidence = report.overall_confidence
            job.report_json = json.dumps(report.model_dump(), ensure_ascii=False)
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

            logger.info(f"Verification job {job_id} successfully completed. Verdict: {job.overall_verdict}")

        except Exception as err:
            logger.exception(f"Verification pipeline failed for job {job_id}: {err}")
            try:
                job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
                if job and job.status != "CANCELLED":
                    job.status = "FAILED"
                    job.current_step = "Pipeline encountered an error"
                    job.error_message = str(err)
                    job.updated_at = datetime.now(timezone.utc)
                    db.commit()
            except Exception as commit_err:
                logger.error(f"Failed to record failure status: {commit_err}")
        finally:
            if should_close:
                db.close()

    def cancel_job(self, job_id: str, db: Optional[Session] = None) -> Optional[VerificationJob]:
        """Cancels an active or queued verification job."""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        try:
            job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
            if not job:
                return None
            if job.status not in ("COMPLETED", "FAILED"):
                job.status = "CANCELLED"
                job.current_step = "Verification cancelled by user"
                job.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(job)
            return job
        finally:
            if should_close:
                db.close()

    def retry_job(self, job_id: str, db: Session) -> Optional[VerificationJob]:
        """
        Retries a failed verification job without duplicate records.
        """
        job = db.query(VerificationJob).filter(VerificationJob.id == job_id).first()
        if not job:
            return None

        # Clean existing partial claim records for this job
        db.query(VerificationClaimRecord).filter(VerificationClaimRecord.job_id == job_id).delete()

        job.status = "QUEUED"
        job.current_step = "Queued for retry"
        job.progress_percent = 0
        job.error_message = None
        job.overall_verdict = None
        job.overall_confidence = None
        job.report_json = None
        job.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(job)
        return job

    def _update_job_state(
        self,
        db: Session,
        job: VerificationJob,
        status: str,
        step: str,
        progress: int
    ) -> None:
        """Atomically updates job state machine fields and timestamps."""
        job.status = status
        job.current_step = step
        job.progress_percent = progress
        job.updated_at = datetime.now(timezone.utc)
        db.commit()


# Global singleton
verification_orchestrator = VerificationOrchestrator()
