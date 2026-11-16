from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import VerificationResult, Report, User
from backend.app.core.dependencies import get_current_user
from backend.app.services.reports.generator import ReportGenerator

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/generate/{verification_id}", status_code=status.HTTP_201_CREATED)
def generate_report(
    verification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    v = db.query(VerificationResult).filter(VerificationResult.id == verification_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification record not found.")

    if v.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    report = ReportGenerator.generate_pdf_report(v, db)
    return {
        "message": "Verification report generated successfully.",
        "report_id": report.id,
        "report_uuid": report.report_uuid,
        "file_size": report.file_size,
        "download_url": f"/api/reports/{report.id}/download"
    }

@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rpt = db.query(Report).filter(Report.id == report_id).first()
    if not rpt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if rpt.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    path = Path(rpt.file_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report PDF file not found on disk.")

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"{rpt.report_uuid}.pdf"
    )

@router.post("/correction-checklist", status_code=status.HTTP_201_CREATED)
def generate_correction_checklist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate and download a tailored pre-submission correction checklist PDF."""
    report = ReportGenerator.generate_correction_checklist_pdf(current_user, db)
    return {
        "message": "Correction checklist PDF generated successfully.",
        "report_id": report.id,
        "report_uuid": report.report_uuid,
        "file_size": report.file_size,
        "download_url": f"/api/reports/{report.id}/download"
    }
